#include "handlers/RecoveredOwnedPetReserveMove.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>

namespace {
using namespace god2;
void require(bool value,const char* message) {if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F&& f) {try{f();}catch(const std::exception&){return;}throw std::runtime_error("Expected rejection");}
std::vector<std::uint8_t> raw(const StoredPet2Slot& value) {
    if(value.pet1) {auto b=RecoveredPet1Stats::encode_logical(value.pet1->stats);return {b.begin(),b.end()};}
    if(value.pet) {auto b=RecoveredPet2Stats::encode_logical(value.pet->stats);return {b.begin(),b.end()};}
    return {};
}
bool same(const StoredPet2Slot& a,const StoredPet2Slot& b) {
    return a.slot==b.slot && a.revision==b.revision && a.provenance==b.provenance &&
        raw(a)==raw(b) && bool(a.pet)==bool(b.pet) && bool(a.pet1)==bool(b.pet1) &&
        (!a.pet || a.pet->inventory==b.pet->inventory) && (!a.pet1 || a.pet1->inventory==b.pet1->inventory);
}
CompanionProvenance provenance(){return {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","pet-reserve-isolated-fixture"};}
struct Fixture {
    struct Close {void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
    std::unique_ptr<sqlite3,Close> db;
    std::uint64_t character{};
    Fixture() {
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'first','hash'),(2,'other','hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='P';character=roles().create(1,profile).id;
        for(const auto key:{28001,28002}) {
            sqlite_detail::Statement row(raw,"INSERT INTO native_companion_metadata VALUES('NCP',?,?,1,X'41',?,zeroblob(396))");
            row.bind(1,key);row.bind(2,std::string(SqliteCompanionRepository::source_sha256));row.bind(3,std::string(64,'a'));row.done();
        }
        sql("INSERT INTO native_pet1_metadata VALUES('COM',24001,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',1,X'41','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',zeroblob(396))");
    }
    void sql(const char* text){sqlite_detail::execute(db.get(),text);}
    SqliteCompanionRepository repo(){return SqliteCompanionRepository(db.get());}
    SqliteRecoveredCharacterRepository roles(){return SqliteRecoveredCharacterRepository(db.get());}
    StoredPet2Slot get(std::uint8_t slot){const auto rows=repo().load_pet2_slots(1,character);return *std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});}
    void seed(std::uint8_t slot,bool first=false,std::uint16_t key=28001) {
        auto repository=repo();
        if(first) {
            RecoveredPet1Stats::LogicalRecord bytes{};bytes[0]=0xe3;bytes[0x1d]=0xc1;bytes[0x1e]=0x5d;bytes[0x27]=slot;
            bytes[9]=0xff;bytes[10]=0xfe;bytes[0x24]=123;
            RecoveredPet1Lifecycle::Metadata meta{};meta[0]=0xc1;meta[1]=0x5d;meta[2]=32;meta[19]=0xa5;
            repository.store_pet1(1,character,slot,{{1,character},meta,*RecoveredPet1Stats::parse_logical(bytes)},get(slot).revision,provenance());
        } else {
            RecoveredPet2Stats::LogicalRecord bytes{};bytes[0]=0xfb;bytes[1]=static_cast<std::uint8_t>(key);bytes[2]=static_cast<std::uint8_t>(key>>8);bytes[3]=slot;
            bytes[4]=255;bytes[17]=31;bytes[19]=12;bytes[5]=0xff;bytes[6]=0xfe;
            RecoveredPet2Lifecycle::Metadata meta{};meta[0]=bytes[1];meta[1]=bytes[2];meta[2]=34;meta[19]=0x5a;
            repository.store_pet2(1,character,slot,{{1,character},meta,*RecoveredPet2Stats::parse_logical(bytes)},get(slot).revision,provenance());
        }
    }
};
// SOURCE regression only. Exercise the actual shared C24/C28 transaction, not
// a separate test-only save or a claimed socket/native acceptance.
void reserve_source_fences() {
    using Move=RecoveredOwnedPetReserveMove;using Batch=Move::Batch;
    const auto batch=[](std::vector<RecoveredWorldRecords::Record> records){return Move::classify(records);};
    const RecoveredInventoryMoveRequest::Request request{42,43};
    require(batch({request,RecoveredWorldRecords::Tick{}})==Batch::Reserve,"Reserve with Tick rejected");
    require(batch({RecoveredMovement::Request{},request})==Batch::Rejected,"Reserve movement prefix escaped");
    require(batch({request,RecoveredSelectionItemRequest::Request{28001,42}})==Batch::Rejected,"C24/C28 mixed mutation escaped");
    require(batch({request,RecoveredWorldRecords::ClientControl1F{}})==Batch::Rejected,"Unproven C24 control tail admitted");
    require(batch({RecoveredInventoryMoveRequest::Request{0,42}})==Batch::Rejected,"Bag/pet namespace mixed move admitted");
    require(batch({RecoveredInventoryMoveRequest::Request{42,44}})==Batch::Rejected,"C24 borrowed active44 activation");
    require(batch({RecoveredInventoryMoveRequest::Request{0,1}})==Batch::Absent,"Ordinary bag borrowed companion custody");
    for(unsigned mode=0;mode<6;++mode) {
        Fixture f;auto repo=f.repo();repo.provision_pet2_slots(1,f.character);f.seed(42);f.seed(43,true);f.seed(44,false,28002);
        const auto a=f.get(42),b=f.get(43),active=f.get(44);
        struct Observe {sqlite3* db;SqliteCompanionRepository* repo;std::uint64_t character;StoredPet2Slot a,active;
            unsigned mode,loads=0;bool live=true,wrote=false,fired=false,nested=false;int ddl=SQLITE_ERROR;
        } observed{f.db.get(),&repo,f.character,a,active,mode};
        const auto trace=[](unsigned type,void* context,void* statement,void*)->int {
            auto& o=*static_cast<Observe*>(context);const auto* text=sqlite3_sql(static_cast<sqlite3_stmt*>(statement));
            if(!text)return 0;const std::string_view sql(text);
            if(type==SQLITE_TRACE_PROFILE) {
                if((o.mode==1||o.mode==4)&&o.wrote&&!o.fired&&sql=="COMMIT") {
                    o.fired=true;if(o.mode==1)o.live=false;
                    else sqlite3_exec(o.db,"UPDATE main.character_pet2_slots SET evidence_id='late-profile-active-change' WHERE slot=44",nullptr,nullptr,nullptr);
                }
                return 0;
            }
            if(type!=SQLITE_TRACE_STMT)return 0;
            if(sql.starts_with("SELECT slot,metadata,stats")) {
                ++o.loads;if(o.mode==0&&o.loads==3){o.fired=true;o.live=false;}
            }
            if(o.mode==5&&o.wrote&&o.loads==2&&!o.fired&&sql.starts_with("SELECT 1 FROM main.recovered_characters")) {
                o.fired=true;o.ddl=sqlite3_exec(o.db,"ALTER TABLE main.character_pet2_slots RENAME TO replaced_pet_cells; CREATE TEMP VIEW character_pet2_slots AS SELECT * FROM main.replaced_pet_cells",nullptr,nullptr,nullptr);
            }
            if(sql.starts_with("UPDATE main.character_pet2_slots")) {
                o.wrote=true;
                if((o.mode==2||o.mode==3)&&!o.fired) {
                    o.fired=true;
                    try{if(o.mode==2)(void)o.repo->transfer_pet2(1,o.character,o.a,o.active);
                        else {SqliteCompanionRepository other(o.db);(void)other.transfer_pet2(1,o.character,o.a,o.active);}}
                    catch(const std::exception&){o.nested=true;}
                }
            }
            return 0;
        };
        struct TraceEnd {sqlite3* db;~TraceEnd(){sqlite3_trace_v2(db,0,nullptr,nullptr);}} end{f.db.get()};
        require(sqlite3_trace_v2(f.db.get(),SQLITE_TRACE_STMT|SQLITE_TRACE_PROFILE,trace,&observed)==SQLITE_OK,"Reserve trace registration failed");
        rejects([&]{(void)Move::move(repo,1,f.character,request,[&]{return observed.live;});});
        sqlite3_trace_v2(f.db.get(),0,nullptr,nullptr);
        require(observed.fired,"Reserve observer did not reach intended shared cut");
        if(mode==1||mode==4) {
            require(f.get(42).pet1.has_value()&&f.get(43).pet.has_value(),"Durable reserve swap was falsely rolled back");
            if(mode==4)require(f.get(44).provenance.evidence_id=="late-profile-active-change","Late durable write was hidden");
            else require(same(active,f.get(44)),"Reserve changed active44");
        }else require(same(a,f.get(42))&&same(b,f.get(43))&&same(active,f.get(44)),"Rejected reserve transaction changed full population");
        if(mode==2||mode==3)require(observed.nested,"C24/C28 shared-connection reentry was not rejected");
        if(mode==5)require(observed.ddl==SQLITE_OK,"Reserve final owner-read namespace replacement was not reached");
    }
    for(const char* claim:{"owned_pk_room_members","owned_pve_character_claims"}) {
        Fixture f;auto repo=f.repo();repo.provision_pet2_slots(1,f.character);f.seed(42);
        const auto a=f.get(42),b=f.get(43);
        const auto create=std::string("CREATE TABLE ")+claim+"(character INTEGER PRIMARY KEY)";f.sql(create.c_str());
        const auto insert=std::string("INSERT INTO ")+claim+" VALUES("+std::to_string(f.character)+")";f.sql(insert.c_str());
        rejects([&]{Move::move(repo,1,f.character,request,[]{return true;});});
        require(same(a,f.get(42))&&same(b,f.get(43)),"Actual room claim allowed reserve mutation");
    }
}
}
int main() {
    try {
        reserve_source_fences();
        using Move=RecoveredOwnedPetReserveMove;
        for(unsigned a=0;a<256;++a)for(unsigned b=0;b<256;++b)
            require(Move::handles({static_cast<std::uint8_t>(a),static_cast<std::uint8_t>(b)})==
                ((a==42||a==43)&&(b==42||b==43)),"Reserve domain widened");
        Fixture f;auto repo=f.repo();const auto c=f.character;
        require(!Move::move(repo,1,c,{42,43}),"Absent capacity invented cells");
        repo.provision_pet2_slots(1,c);f.seed(42);f.seed(43,true);f.seed(44,false,28002);
        const auto before42=f.get(42),before43=f.get(43),active=f.get(44);
        rejects([&]{Move::move(repo,2,c,{42,43});});
        const auto changes=sqlite3_total_changes64(f.db.get());
        require(!Move::move(repo,1,c,{42,44}) && Move::move(repo,1,c,{42,42})->empty() &&
            sqlite3_total_changes64(f.db.get())==changes,"No-op/outside-domain changed rows");
        const auto reply=Move::move(repo,1,c,{42,43});require(reply.has_value(),"Mixed reserve swap failed");
        const auto logical=RecoveredWorldFrame::decode(*reply);require(logical && logical->size()==196,"Mixed projection size");
        const std::array<std::uint8_t,10> clears{0x41,0,0,42,0,0x41,0,0,43,0};
        require(std::equal(clears.begin(),clears.end(),logical->begin()),"Did not clear both old families first");
        require((*logical)[10]==0x3b && (*logical)[12]==42 && (*logical)[40]==0xe3 && (*logical)[40+0x27]==42 &&
            (*logical)[93]==0x3b && (*logical)[95]==43 && (*logical)[123]==0xfb && (*logical)[126]==43,"Native E3/FB routing changed");
        const auto after42=f.get(42),after43=f.get(43);
        auto moved1=raw(before43);moved1[0x27]=42;auto moved2=raw(before42);moved2[3]=43;
        require(raw(after42)==moved1 && raw(after43)==moved2 &&
            after42.pet1->inventory==before43.pet1->inventory && after43.pet->inventory==before42.pet->inventory &&
            after42.revision==before42.revision+1 && after43.revision==before43.revision+1 &&
            after42.provenance==before43.provenance && after43.provenance==before42.provenance && same(active,f.get(44)),
            "Swap changed instance/provenance or active slot");
        rejects([&]{repo.move_pet_reserves(1,c,before42,before43,[](const auto&){});});
        rejects([&]{repo.move_pet_reserves(1,c,after42,after43,[](const auto&){throw std::runtime_error("encoding failure");});});
        require(same(after42,f.get(42)) && same(after43,f.get(43)),"Reply failure committed");
        f.sql("CREATE TRIGGER fail_second AFTER UPDATE ON character_pet2_slots WHEN NEW.slot=43 BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{Move::move(repo,1,c,{42,43});});
        require(same(after42,f.get(42)) && same(after43,f.get(43)),"Second write did not roll back first");
        f.sql("DROP TRIGGER fail_second");
        f.sql("CREATE TRIGGER damage_active AFTER UPDATE ON character_pet2_slots WHEN NEW.slot=43 BEGIN UPDATE character_pet2_slots SET revision=revision+1 WHERE slot=44; END");
        rejects([&]{Move::move(repo,1,c,{42,43});});
        require(same(after42,f.get(42)) && same(after43,f.get(43)) && same(active,f.get(44)),"Active readback mutation survived");
        f.sql("DROP TRIGGER damage_active");
        const auto resources=f.roles().commit_resources(1,c,{}, {52,120,2,80,0,"CUSTOM-0012"});
        const auto battle=f.roles().reserve_battle(1,c,resources);
        rejects([&]{Move::move(repo,1,c,{42,43});});
        require(same(after42,f.get(42)) && same(after43,f.get(43)) && f.roles().load_resources(1,c)==resources,"Pending battle changed state");
        f.roles().settle_battle(1,c,battle,resources,resources,true,0);
        require(Move::move(repo,1,c,{43,42}).has_value(),"Reverse reserve swap rejected");
        require(raw(f.get(42))==raw(before42) && raw(f.get(43))==raw(before43) && same(active,f.get(44)),"Reverse swap changed bytes");
        Fixture empty;auto er=empty.repo();er.provision_pet2_slots(1,empty.character);empty.seed(42);
        const auto original=empty.get(42);const auto empty44=empty.get(44);
        require(Move::move(er,1,empty.character,{42,43}).has_value() && !empty.get(42).occupied() && empty.get(43).pet.has_value(),"Move to explicit empty failed");
        const auto empty_changes=sqlite3_total_changes64(empty.db.get());
        require(Move::move(er,1,empty.character,{42,43})->empty() &&
            sqlite3_total_changes64(empty.db.get())==empty_changes,"Empty source wrote state");
        require(Move::move(er,1,empty.character,{43,42}).has_value() && raw(empty.get(42))==raw(original) &&
            same(empty44,empty.get(44)),"Empty reverse changed bytes or active capacity");
        empty.sql("DELETE FROM character_pet2_slots WHERE slot=43");
        require(!Move::move(er,1,empty.character,{42,43}),"Missing destination allocated capacity");
        std::cout<<"Pet reserve move assertions passed\n";return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
