#include "db/SqliteTeleportGemRepository.h"
#include "db/SqliteSupport.h"
#include "db/Migration.h"
#include <iostream>
#include <limits>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value,const char* message="Teleport gem repository check failed"){
    ++checks;if(!value)throw std::runtime_error(message);
}
template<class F>void rejects(F action){bool rejected=false;try{action();}catch(const std::exception&){rejected=true;}check(rejected,"Expected rejection");}
void sql(sqlite3* db,const std::string& statement){sqlite_detail::execute(db,statement);}
std::string snapshot(sqlite3* db){
    std::string out;
    for(const char* table:{"recovered_characters","diagnostic_inventory_slots","character_teleport_gem_metadata",
                           "recovered_positions","battle_reservations","battle_settlements","character_weapon_slot_metadata"}){
        out+=table;sqlite3_stmt* query=nullptr;
        const auto text="SELECT * FROM "+std::string(table)+" ORDER BY 1,2";
        if(sqlite3_prepare_v2(db,text.c_str(),-1,&query,nullptr)!=SQLITE_OK)throw std::runtime_error(sqlite3_errmsg(db));
        while(sqlite3_step(query)==SQLITE_ROW){
            out+='[';
            for(int column=0;column<sqlite3_column_count(query);++column){
                out+=std::to_string(sqlite3_column_type(query,column))+":";
                const auto* bytes=static_cast<const char*>(sqlite3_column_blob(query,column));
                const auto count=sqlite3_column_bytes(query,column);
                out+=std::to_string(count)+":";if(count)out.append(bytes,static_cast<std::size_t>(count));out+=';';
            }
            out+=']';
        }
        sqlite3_finalize(query);
    }
    return out;
}
struct Fixture {
    sqlite3* db=nullptr;
    SqliteTeleportGemRepository repository;
    static sqlite3* open(){sqlite3* value=nullptr;if(sqlite3_open(":memory:",&value)!=SQLITE_OK)throw std::runtime_error("sqlite open");return value;}
    Fixture():db(open()),repository(db){
        sql(db,"PRAGMA foreign_keys=ON");
        const auto migrations=default_sqlite_migrations();
        check(migrations.size()>=40 && migrations[39].version==40 && migrations[39].name=="owned_teleport_gem_instances");
        for(const auto& migration:migrations)sql(db,migration.sql);
        sql(db,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'gem-owner','test'),(2,'gem-other','test')");
        for(std::uint64_t id:{1ULL,2ULL}){
            std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+id-1);
            sqlite_detail::Statement insert(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes) VALUES(?,?,0,?,?)");
            insert.bind_id(1,id);insert.bind_id(2,id);insert.bind_blob(3,profile);insert.bind_blob(4,std::span(profile).first(1));insert.done();
        }
        sql(db,"INSERT INTO recovered_positions VALUES(1,2,0,477,210,5),(2,2,0,477,210,8)");
        scalar(0,16055,1,7);scalar(1,0,0,9);scalar(2,16055,1,11);scalar(3,3101,1,13);
    }
    ~Fixture(){sqlite3_close(db);}
    void scalar(unsigned slot,unsigned key,unsigned count,unsigned revision){
        sql(db,"INSERT INTO diagnostic_inventory_slots VALUES(1,"+std::to_string(slot)+","+std::to_string(key)+","+
            std::to_string(count)+","+std::to_string(revision)+",'"+SqliteTeleportGemRepository::source_sha256+"','CUSTOM-0015')");
    }
    RecoveredTeleportGem::Metadata metadata(unsigned charges,unsigned salt=0)const{
        RecoveredTeleportGem::Metadata value{};value[0]=0xb7;value[1]=0x3e;value[2]=0xc8;value[3]=static_cast<std::uint8_t>(1u|(charges<<1));
        for(unsigned index=4;index<20;++index)value[index]=static_cast<std::uint8_t>(index*7+salt);
        return value;
    }
    StoredTeleportGemSlot attach(unsigned slot,unsigned charges,unsigned salt=0){
        const auto revision=slot==0?7u:11u;
        return repository.save_existing(1,1,static_cast<std::uint8_t>(slot),
            {16055,1,revision,SqliteTeleportGemRepository::source_sha256},metadata(charges,salt),"CUSTOM_TEST_NOT_NATIVE","owned-test-evidence");
    }
    template<class F>void unchanged_failure(F action){const auto before=snapshot(db);rejects(action);check(snapshot(db)==before,"Failure changed owned rows");}
};
}

int main(){
    try {
        rejects([]{SqliteTeleportGemRepository bad(nullptr);});
        {
            Fixture f;
            check(!f.repository.load(1,1,29));check(!f.repository.load(1,1,3));
            check(f.repository.load(1,1,1)->count==0);
            f.unchanged_failure([&]{f.repository.load(1,1,0);}); // Never infer10 charges from scalar.
            const auto no_evidence=snapshot(f.db);
            check(f.repository.load_saved(1,1).empty()); // Legacy scalar cannot block world restoration.
            check(snapshot(f.db)==no_evidence);
            for(const auto owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,99u}})
                f.unchanged_failure([&]{f.repository.load(owner.first,owner.second,1);});
            f.unchanged_failure([&]{f.repository.load(1,1,30);});
            for(const unsigned charge:{0u,11u,127u})f.unchanged_failure([&]{f.attach(0,charge);});
            for(const unsigned byte:{0u,1u,2u}){
                auto metadata=f.metadata(3);metadata[byte]^=1;
                f.unchanged_failure([&]{f.repository.save_existing(1,1,0,{16055,1,7,SqliteTeleportGemRepository::source_sha256},metadata,"CUSTOM_TEST_NOT_NATIVE","evidence");});
            }
            f.unchanged_failure([&]{f.repository.save_existing(2,1,0,{16055,1,7,SqliteTeleportGemRepository::source_sha256},f.metadata(3),"CUSTOM_TEST_NOT_NATIVE","evidence");});
            f.unchanged_failure([&]{f.repository.save_existing(1,1,0,{16055,1,8,SqliteTeleportGemRepository::source_sha256},f.metadata(3),"CUSTOM_TEST_NOT_NATIVE","evidence");});
            f.unchanged_failure([&]{f.repository.save_existing(1,1,0,{16055,1,7,SqliteTeleportGemRepository::source_sha256},f.metadata(3),"CUSTOM_DESIGNED","guessed");});
            const auto saved=f.attach(0,3);check(saved.metadata20==f.metadata(3) && saved.revision==7 && saved.count==1);
            check(f.repository.load(1,1,0)==std::optional(saved));
            f.unchanged_failure([&]{f.attach(0,10);}); // No reset/refill through evidence attachment.
            f.attach(2,10,11);
            const auto all=f.repository.load_saved(1,1);check(all.size()==2 && all[0]==saved);
            const auto old=snapshot(f.db);
            auto changed=saved;changed.metadata20[19]^=1;
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,changed,{2,0,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(2,1,saved,{2,0,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,6},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{4,0,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,4,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},{});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[](const auto&){throw std::runtime_error("encode failed");});});
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[&](const auto&){sql(f.db,"UPDATE recovered_positions SET x=57 WHERE character_id=1");});});
            check(snapshot(f.db)==old);
            bool prepared=false;
            const auto result=f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[&](const auto& next){
                check(sqlite3_get_autocommit(f.db)==0);check(next.before==saved);
                check(next.position_before==RecoveredPosition{2,0,477,210,5});
                check(next.position_after==RecoveredPosition{2,4,56,75,6});
                check(next.after.count==1 && next.after.revision==8 && next.after.metadata_present);
                check(RecoveredTeleportGem::displayed_charges(next.after.metadata20)==2);
                prepared=true;
            });
            check(prepared && f.repository.load(1,1,0)==std::optional(result.after));
            check((RecoveredTeleportGem::header(result.after.metadata20)&0x1ffffffu)==(RecoveredTeleportGem::header(saved.metadata20)&0x1ffffffu));
            check(std::equal(result.after.metadata20.begin()+4,result.after.metadata20.end(),saved.metadata20.begin()+4));
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[](const auto&){});});
        }
        {
            Fixture f;const auto saved=f.attach(0,1);
            const auto result=f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[](const auto&){});
            check(result.after.item_id==0 && result.after.count==0 && !result.after.metadata_present && result.after.revision==8);
            check(result.after.metadata20==RecoveredTeleportGem::Metadata{} && result.after.origin.empty());
            check(f.repository.load(1,1,0)==std::optional(result.after));
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,result.after,{2,4,56,75,6},[](const auto&){});});
        }
        {
            Fixture f;const auto source=f.attach(0,4),other=f.attach(2,9,77);
            const auto empty=*f.repository.load(1,1,1);
            const auto moved=f.repository.move_whole(1,1,source,empty,[&](const auto& state){
                check(sqlite3_get_autocommit(f.db)==0 && !state.source.metadata_present);
                check(state.destination.metadata20==source.metadata20 && state.destination.provenance==source.provenance);
            });
            check(moved.source.slot==0 && moved.source.revision==8 && moved.source.count==0);
            check(moved.destination.slot==1 && moved.destination.revision==10 && moved.destination.count==1);
            f.unchanged_failure([&]{f.repository.move_whole(1,1,source,empty,[](const auto&){});});
            const auto swapped=f.repository.move_whole(1,1,moved.destination,other,[](const auto&){});
            check(swapped.source.metadata20==other.metadata20 && swapped.destination.metadata20==source.metadata20);
            check(swapped.source.revision==11 && swapped.destination.revision==12);
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,swapped.source,[](const auto&){});});
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,swapped.destination,[](const auto&){throw std::runtime_error("encode");});});
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,swapped.destination,[&](const auto&){sql(f.db,"UPDATE character_teleport_gem_metadata SET metadata20=zeroblob(20) WHERE character_id=1 AND slot=1");});});
            auto ordinary=empty;ordinary.slot=3;ordinary.item_id=3101;ordinary.count=1;ordinary.revision=13;
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,ordinary,[](const auto&){});});
            auto missing=empty;missing.slot=29;
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,missing,[](const auto&){});});
            // Weapon overlay must be refused, even an explicitly empty one.
            sql(f.db,"INSERT INTO character_weapon_slot_metadata VALUES(1,0,zeroblob(20),8,'EMPTY_SLOT_POLICY','test','"+
                std::string(SqliteTeleportGemRepository::source_sha256)+"','6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98','CUSTOM-0046')");
            f.unchanged_failure([&]{f.repository.load(1,1,0);});
            f.unchanged_failure([&]{f.repository.move_whole(1,1,swapped.source,moved.source,[](const auto&){});});
        }
        {
            Fixture f;const auto source=f.attach(0,2);
            sqlite_detail::Statement reservation(f.db,"INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(1,1,'CUSTOM-0012')");
            reservation.done();
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,source,{2,0,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.move_whole(1,1,source,*f.repository.load(1,1,1),[](const auto&){});});
            f.unchanged_failure([&]{f.attach(2,2);});
        }
        {
            Fixture f;f.attach(0,2);
            sql(f.db,"UPDATE diagnostic_inventory_slots SET revision=9223372036854775807 WHERE character_id=1 AND slot=0");
            sql(f.db,"UPDATE character_teleport_gem_metadata SET revision=9223372036854775807 WHERE character_id=1 AND slot=0");
            const auto exhausted=*f.repository.load(1,1,0);
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,exhausted,{2,0,477,210,5},[](const auto&){});});
            f.unchanged_failure([&]{f.repository.move_whole(1,1,exhausted,*f.repository.load(1,1,1),[](const auto&){});});
            sql(f.db,"UPDATE diagnostic_inventory_slots SET source_sha256='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' WHERE character_id=1 AND slot=0");
            f.unchanged_failure([&]{f.repository.load(1,1,0);});
        }
        {
            Fixture f;const auto saved=f.attach(0,3);
            sql(f.db,"UPDATE recovered_positions SET revision=9223372036854775807 WHERE character_id=1");
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,9223372036854775807ULL},[](const auto&){});});
            sql(f.db,"UPDATE character_teleport_gem_metadata SET revision=8 WHERE character_id=1 AND slot=0");
            f.unchanged_failure([&]{f.repository.load(1,1,0);});
            sql(f.db,"UPDATE character_teleport_gem_metadata SET revision=7 WHERE character_id=1 AND slot=0");
            // SQLite trigger failure after the gem debit must roll back both
            // the overlay deletion/reinsert and scalar revision.
            sql(f.db,"UPDATE recovered_positions SET revision=5 WHERE character_id=1");
            sql(f.db,"CREATE TRIGGER deny_gem_position BEFORE UPDATE ON recovered_positions BEGIN SELECT RAISE(ABORT,'position write denied'); END");
            f.unchanged_failure([&]{f.repository.prepare_transfer(1,1,saved,{2,0,477,210,5},[](const auto&){});});
            sql(f.db,"DROP TRIGGER deny_gem_position");
            sql(f.db,"DELETE FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=0");
            check(!f.repository.load(1,1,0));
            sqlite_detail::Statement orphan(f.db,"SELECT count(*) FROM character_teleport_gem_metadata WHERE character_id=1 AND slot=0");
            check(orphan.row() && orphan.integer(0)==0);
        }
        std::cout<<"Teleport gem repository PASS "<<checks<<" checks\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<" after "<<checks<<" checks\n";return 1;}
}
