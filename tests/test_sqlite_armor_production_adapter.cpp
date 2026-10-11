#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "handlers/OwnedBagProjectionService.h"
#include <nlohmann/json.hpp>
#include <array>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace god2;
void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
template<class F> std::string rejected(F&& action){
    try{action();}catch(const DatabaseError& error){return error.what();}
    throw std::runtime_error("Production adapter accepted invalid owned armor");
}
std::vector<std::uint8_t> unhex(const std::string& value){
    require(value.size()%2==0,"Odd source hex");std::vector<std::uint8_t> bytes;
    const auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Invalid source hex");};
    for(std::size_t i=0;i<value.size();i+=2)bytes.push_back(static_cast<std::uint8_t>(digit(value[i])*16+digit(value[i+1])));
    return bytes;
}
// Same independently executed original-source cache as native-armor-catalog.
// The production migrations install tables; this fixture only inserts rows.
void seed_catalog(sqlite3* raw){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-armor-20261002/records.json");
    require(file.good(),"Original complete armor records missing");nlohmann::json groups;file>>groups;
    require(groups.is_array()&&groups.size()==2&&groups[0].size()==2&&groups[1].size()==1354,"Original catalog denominator changed");
    sqlite_detail::Transaction transaction(raw);
    for(std::size_t group=0;group<2;++group)for(const auto& row:groups[group]){
        require(row.size()==10,"Original catalog row width changed");
        sqlite_detail::Statement write(raw,group==0?"INSERT INTO native_armor_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_armor_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<10;++i){
            if(group==1&&(i==6||i==8)){const auto bytes=unhex(row[i].get<std::string>());write.bind_blob(i+1,bytes);}
            else if((group==0&&i==7)||(group==1&&i>=1&&i<=4)){require(row[i].is_number_integer(),"Source integer expected");write.bind(i+1,row[i].get<std::int64_t>());}
            else write.bind(i+1,row[i].get<std::string>());
        }write.done();
    }transaction.commit();
}
struct OwnedFile {
    std::filesystem::path directory,path;
    OwnedFile(){
        const auto stamp=std::chrono::steady_clock::now().time_since_epoch().count();
        directory=std::filesystem::absolute(std::filesystem::temp_directory_path()/("god2-production-armor-"+std::to_string(stamp)));
        require(std::filesystem::create_directory(directory),"Cannot own isolated fixture directory");path=directory/"fixture.sqlite";
    }
    ~OwnedFile(){
        // Only exact children of the uniquely owned directory, no recursive deletion.
        std::error_code ignored;
        for(const auto* suffix:{"","-journal","-wal","-shm"})std::filesystem::remove(std::filesystem::path(path.string()+suffix),ignored);
        std::filesystem::remove(directory,ignored);
    }
};
using Raw=std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)>;
std::vector<std::uint8_t> plain(std::uint8_t slot,const StoredInventorySlot& item){
    if(item.count&&(item.item_id!=3107||item.source_sha256!=SqliteArmorSlotRepository::source_sha256))throw DatabaseError("Fixture original MED scalar encoder denied category");
    RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(item.item_id);bytes[1]=static_cast<std::uint8_t>(item.item_id>>8);
    return RecoveredInventoryProjection::encode({slot,item.count,bytes}).value();
}
struct Fixture {
    OwnedFile file;
    SqliteDatabase database{file.path};
    Raw raw{nullptr,sqlite3_close_v2};
    std::unique_ptr<OwnedBagProjectionService> projector;
    std::uint64_t character{};
    std::array<std::uint16_t,2> keys{1001,20001};
    std::array<RecoveredInventoryProjection::Metadata,2> bytes;
    Fixture(){
        require(default_sqlite_migrations().back().version>=42,"Production fixture must include armor schema 42");
        database.initialize();database.migrate();
        sqlite3* connection=nullptr;require(sqlite3_open(file.path.string().c_str(),&connection)==SQLITE_OK,"Open second isolated fixture writer");raw.reset(connection);
        sql("PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000");
        require(number("SELECT count(*) FROM schema_migrations WHERE version=42")==1,"Production migration 42 absent");
        seed_catalog(raw.get());require(database.native_armor_catalog().populated(),"Actual production catalog failed complete fingerprint");
        require(database.native_armor_catalog().lookup(keys[0])->family=="EQU"&&database.native_armor_catalog().lookup(keys[1])->family=="TEQ","Source namespace changed");
        for(auto key:keys)require(database.native_armor_catalog().equipment_slot(key).has_value(),"Real source key not qualified");
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'production-armor-fixture','test-hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='A';character=database.recovered_characters().create(1,profile).id;
        for(unsigned slot=0;slot<50;++slot){
            sqlite_detail::Statement insert(raw.get(),"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");
            insert.bind_id(1,character);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();
        }
        for(unsigned slot=0;slot<2;++slot){
            // Opaque synthetic test instances, NOT recovered native grants/stats.
            bytes[slot].fill(static_cast<std::uint8_t>(0xa0+slot));
            bytes[slot][0]=static_cast<std::uint8_t>(keys[slot]);bytes[slot][1]=static_cast<std::uint8_t>(keys[slot]>>8);
            bytes[slot][2]=static_cast<std::uint8_t>((bytes[slot][2]&0xc0u)|(slot==0?2u:26u));
            scalar(slot,keys[slot],1,7+slot);
            sqlite_detail::Statement insert(raw.get(),"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE','isolated-production-wiring',?,?,'CUSTOM-0066')");
            insert.bind_id(1,character);insert.bind(2,slot);insert.bind_blob(3,bytes[slot]);insert.bind(4,7+slot);
            insert.bind(5,SqliteArmorSlotRepository::source_sha256);insert.bind(6,SqliteArmorSlotRepository::client_sha256);insert.done();
        }
        scalar(5,3107,7,3);database.bank_items().install_schema();database.bank_items().provision_empty(1,character);
        // Neither constructor receives a test qualifier: both are real factories.
        projector=database.make_bag_projection(plain);correct();
    }
    void sql(const std::string& value){sqlite_detail::execute(raw.get(),value);}
    std::int64_t number(const char* query){sqlite_detail::Statement read(raw.get(),query);require(read.row(),"Missing fixture count");return read.integer(0);}
    void scalar(unsigned slot,unsigned key,unsigned count,unsigned revision){
        sqlite_detail::Statement write(raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=?");
        write.bind(1,key);write.bind(2,count);write.bind(3,revision);write.bind_id(4,character);write.bind(5,slot);write.done();
    }
    void metadata(unsigned slot,const RecoveredInventoryProjection::Metadata& value){
        sqlite_detail::Statement write(raw.get(),"UPDATE character_armor_slot_metadata SET logical20=? WHERE character_id=? AND slot=?");
        write.bind_blob(1,value);write.bind_id(2,character);write.bind(3,slot);write.done();
    }
    auto wrong(unsigned slot) const {auto value=bytes[slot];value[2]=static_cast<std::uint8_t>((value[2]&0xc0u)|(slot==0?26u:2u));return value;}
    void correct(){
        const auto snapshot=database.armor_slots().load_snapshot(1,character);require(snapshot.armor.size()==2,"Actual production armor reader lost correct source instance");
        for(std::uint8_t slot=0;slot<2;++slot){
            const auto row=database.armor_slots().load(1,character,slot);require(row&&row->logical20==bytes[slot],"Production reader changed full20/high flags");
            const auto expected=RecoveredInventoryProjection::encode({slot,1,bytes[slot]}).value();
            require(projector->project(1,character,slot,snapshot.scalar[slot].value())==expected,"Production projector did not preserve full20");
        }
    }
    // Exact values/types of all mutable rows relevant to commit/rollback.
    // No SQL dump timestamps or inferred instance projections hide corruption.
    nlohmann::json saved(){
        nlohmann::json result=nlohmann::json::array();
        for(const auto* table:{"accounts","recovered_characters","diagnostic_inventory_slots","character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata","character_bank_item_slots","character_bank_item_receipts"}){
            const auto query=std::string("SELECT * FROM ")+table+" ORDER BY 1,2";
            sqlite3_stmt* statement=nullptr;sqlite_detail::check(raw.get(),sqlite3_prepare_v2(raw.get(),query.c_str(),-1,&statement,nullptr));
            std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> owned(statement,sqlite3_finalize);nlohmann::json rows=nlohmann::json::array();
            int code=SQLITE_OK;
            while((code=sqlite3_step(statement))==SQLITE_ROW){
                nlohmann::json row=nlohmann::json::array();
                for(int c=0;c<sqlite3_column_count(statement);++c){
                    const auto kind=sqlite3_column_type(statement,c);nlohmann::json value;
                    if(kind==SQLITE_INTEGER)value=sqlite3_column_int64(statement,c);
                    else if(kind==SQLITE_NULL)value=nullptr;
                    else if(kind==SQLITE_TEXT)value=std::string(reinterpret_cast<const char*>(sqlite3_column_text(statement,c)),static_cast<std::size_t>(sqlite3_column_bytes(statement,c)));
                    else if(kind==SQLITE_BLOB){const auto* data=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,c));const auto length=sqlite3_column_bytes(statement,c);value=nlohmann::json::array();for(int i=0;i<length;++i)value.push_back(data[i]);}
                    else throw std::runtime_error("Unexpected mutable fixture column type");
                    row.push_back({kind,value});
                }rows.push_back(row);
            }require(code==SQLITE_DONE,"Cannot read fixture rows");result.push_back({table,rows});
        }return result;
    }
    static auto changes(const auto& before,const auto& after){
        std::vector<OwnedBagProjectionService::ScalarChange> result;
        for(std::uint8_t slot=0;slot<30;++slot)if(before.bag[slot]!=after.bag[slot])result.push_back({slot,before.bag[slot],after.bag[slot]});
        return result;
    }
    auto deposit(){return SqliteBankItemsRepository::Request{database.bank_items().load(1,character),SqliteBankItemsRepository::Operation::Deposit,0,5,2,1};}
    SqliteBankItemsRepository::CommitProof proof(const SqliteBankItemsRepository::Request& request,bool& pre,bool& post,bool* observed_bad=nullptr){
        const auto immutable=projector->capture_proof(1,character);
        const auto delta=changes(request.expected,SqliteBankItemsRepository::plan(request));
        // Capture is before writes; planned state is derived, never loaded as baseline.
        return {[this,immutable,&pre]{pre=true;projector->verify_proof_in_transaction(immutable);},
            [this,immutable,delta,&post,observed_bad]{
                post=true;
                if(observed_bad){
                    const auto message=rejected([&]{(void)database.armor_slots().load_snapshot(1,character);});
                    require(message=="Unqualified armor instance","SQL trigger did not actually reach production per-item family guard");*observed_bad=true;
                }
                projector->verify_planned_in_transaction(immutable,delta);
            }};
    }
};
void production_family(){
    Fixture f;const auto correct_saved=f.saved();
    for(std::uint8_t slot=0;slot<2;++slot){
        f.metadata(slot,f.wrong(slot));const auto poisoned=f.saved();const auto scalar=f.database.bank_items().load(1,f.character).bag[slot];
        require(rejected([&]{(void)f.database.armor_slots().load(1,f.character,slot);})=="Unqualified armor instance","Production repository rejection was not per-item source family");
        require(rejected([&]{(void)f.projector->project(1,f.character,slot,scalar);})=="Bag armor overlay category/family conflict","Production projector rejection was not per-item source family");
        rejected([&]{(void)f.projector->capture_proof(1,f.character);});
        require(f.saved()==poisoned,"Read rejection modified stored rows");
        f.metadata(slot,f.bytes[slot]);f.correct();require(f.saved()==correct_saved,"Fixture family restoration changed unrelated rows");
    }
}
void production_prewrite(){
    Fixture f;
    for(std::uint8_t slot=0;slot<2;++slot){
        const auto request=f.deposit();bool pre=false,post=false;const auto proof=f.proof(request,pre,post);
        f.metadata(slot,f.wrong(slot));const auto poisoned=f.saved();
        const auto message=rejected([&]{(void)f.database.bank_items().commit(std::string(64,slot==0?'a':'b'),request,proof);});
        require(pre&&!post&&message=="Unqualified armor instance","Production prewrite proof did not reject before writes");
        require(f.saved()==poisoned,"Prewrite rejection changed scalar/metadata/receipt rows");f.metadata(slot,f.bytes[slot]);f.correct();
    }
}
void production_postwrite(){
    Fixture f;
    for(std::uint8_t slot=0;slot<2;++slot){
        const auto request=f.deposit();bool pre=false,post=false,observed_bad=false;const auto proof=f.proof(request,pre,post,&observed_bad);
        const auto wrong=f.wrong(slot);std::string hex;
        for(auto byte:wrong){hex+="0123456789abcdef"[byte>>4];hex+="0123456789abcdef"[byte&15];}
        f.sql("CREATE TRIGGER production_bad_family AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_armor_slot_metadata SET logical20=X'"+hex+"' WHERE character_id=NEW.character_id AND slot="+std::to_string(slot)+"; END");
        const auto before=f.saved();
        const auto message=rejected([&]{(void)f.database.bank_items().commit(std::string(64,slot==0?'c':'d'),request,proof);});
        require(pre&&post&&observed_bad&&message=="Unqualified armor instance","Production postwrite proof did not catch actual family trigger inside transaction");
        require(f.saved()==before,"Postwrite family proof failed rollback of full scalar/meta/receipt rows");
        f.sql("DROP TRIGGER production_bad_family");f.correct();
    }
    // Success control ensures hooks are not simply blanket-rejecting every commit.
    const auto before=f.database.armor_slots().load_snapshot(1,f.character);const auto request=f.deposit();bool pre=false,post=false;
    const auto proof=f.proof(request,pre,post);const auto committed=f.database.bank_items().commit(std::string(64,'e'),request,proof);
    require(pre&&post&&committed.bag[5].count==6&&committed.vault[2].count==1,"Correct production owner proof blocked ordinary scalar deposit");
    require(f.database.armor_slots().load_snapshot(1,f.character).armor==before.armor,"Successful scalar commit changed full armor instances");f.correct();
}
}
int main(){
    try{production_family();production_prewrite();production_postwrite();
        std::cout<<"PASS actual SqliteDatabase schema42 + complete1354 armor catalog: production EQU2/TEQ26 readers/projector, same-key family refusal, unchanged saved rows, transaction pre/post trigger rollback and successful scalar control\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
