#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include <nlohmann/json.hpp>
#include <array>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
using namespace god2;
using Repo=SqliteOwnedArmorBankRepository;
using Op=Repo::Operation;
void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
template<class F>void rejects(F&& action){try{action();}catch(const DatabaseError&){return;}throw std::runtime_error("Production bank adapter accepted invalid input");}
std::int64_t number(sqlite3* db,const char* sql){sqlite_detail::Statement read(db,sql);require(read.row(),"Missing test scalar");return read.integer(0);}
std::string dump(sqlite3* db,const std::string& query){
    sqlite3_stmt* statement=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,query.c_str(),-1,&statement,nullptr));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> guard(statement,sqlite3_finalize);std::string result;int code;
    while((code=sqlite3_step(statement))==SQLITE_ROW){
        for(int i=0;i<sqlite3_column_count(statement);++i){const auto kind=sqlite3_column_type(statement,i);const auto* data=kind==SQLITE_BLOB?sqlite3_column_blob(statement,i):sqlite3_column_text(statement,i);const auto length=sqlite3_column_bytes(statement,i);result+=std::to_string(kind)+":"+std::to_string(length)+":";if(length)result.append(static_cast<const char*>(data),length);result+=';';}result+='\n';
    }require(code==SQLITE_DONE,"Typed test read failed");return result;
}
std::map<std::string,std::string> tables(sqlite3* db,bool history_prefix=false){
    sqlite_detail::Statement names(db,"SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name");std::map<std::string,std::string> result;
    while(names.row()){const auto name=names.text(0);require(name.find('"')==std::string::npos,"Unsafe test table name");result[name]=dump(db,"SELECT * FROM \""+name+"\""+(history_prefix&&name=="schema_migrations"?" WHERE version<=42":"")+" ORDER BY rowid");}return result;
}
std::map<std::string,std::string> objects(sqlite3* db){
    sqlite_detail::Statement names(db,"SELECT name FROM sqlite_schema ORDER BY name");std::map<std::string,std::string> result;
    while(names.row()){const auto name=names.text(0);require(name.find('\'')==std::string::npos,"Unsafe test object name");result[name]=dump(db,"SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name='"+name+"'");}return result;
}
std::vector<Migration> prefix42(){auto value=default_sqlite_migrations();require(value.back().version>=43,"Test needs actual schema43 migration included");value.resize(42);return value;}
struct File {
    std::filesystem::path directory,path;
    File(){directory=std::filesystem::temp_directory_path()/("god2-bank-armor-production0067-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));require(std::filesystem::create_directory(directory),"Cannot own test directory");path=directory/"isolated.sqlite";}
    ~File(){std::error_code ignored;for(const auto* suffix:{"","-journal","-wal","-shm"})std::filesystem::remove(std::filesystem::path(path.string()+suffix),ignored);std::filesystem::remove(directory,ignored);}
};
using Raw=std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)>;
Raw open(const std::filesystem::path& path){sqlite3* db=nullptr;require(sqlite3_open(path.string().c_str(),&db)==SQLITE_OK,"Test writer open failed");Raw result(db,sqlite3_close_v2);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON;PRAGMA busy_timeout=5000");return result;}
std::vector<std::uint8_t> unhex(const std::string& value){
    const auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Invalid catalog hex");};require(value.size()%2==0,"Odd catalog hex");std::vector<std::uint8_t> result;
    for(std::size_t i=0;i<value.size();i+=2)result.push_back(static_cast<std::uint8_t>(digit(value[i])*16+digit(value[i+1])));return result;
}
void catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-armor-20261002/records.json");require(file.good(),"Complete original-source catalog unavailable");nlohmann::json groups;file>>groups;
    require(groups.size()==2&&groups[0].size()==2&&groups[1].size()==1354,"Source denominator differs");sqlite_detail::Transaction transaction(db);
    for(std::size_t group=0;group<2;++group)for(const auto& row:groups[group]){
        require(row.size()==10,"Source row width differs");sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_armor_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_armor_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<10;++i){if(group==1&&(i==6||i==8))insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if((group==0&&i==7)||(group==1&&i>=1&&i<=4))insert.bind(i+1,row[i].get<std::int64_t>());else insert.bind(i+1,row[i].get<std::string>());}insert.done();
    }transaction.commit();
}
void fresh_schema(){
    File file;SqliteDatabase database(file.path);rejects([&]{(void)database.armor_bank();});database.initialize();rejects([&]{(void)database.armor_bank();});database.migrate();auto raw=open(file.path);
    require(number(raw.get(),"SELECT max(version) FROM schema_migrations")==default_sqlite_migrations().back().version,"Fresh current migration missing");
    for(const auto* table:{"accounts","recovered_characters","diagnostic_inventory_slots","character_bank_item_slots","character_bank_item_receipts","character_bank_armor_metadata","character_bank_armor_receipts"})require(dump(raw.get(),std::string("SELECT * FROM ")+table).empty(),"Fresh migration granted rows or capacity");
    const auto before=tables(raw.get());(void)database.armor_bank();rejects([&]{(void)database.armor_bank().load(1,1);});require(tables(raw.get())==before,"Unallocated read installed data");database.migrate();require(tables(raw.get())==before,"Migration43 was not idempotent");
    require(dump(raw.get(),"PRAGMA foreign_key_check").empty(),"Fresh foreign key failure");
    // Legacy Application can still install its schema after migration43.
    const auto schema=dump(raw.get(),"SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name");database.bank_items().install_schema();require(dump(raw.get(),"SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")==schema,"Legacy scalar installer changed migrated DDL");
}
struct Fixture {
    File file;SqliteDatabase historical{file.path,prefix42()};Raw raw{nullptr,sqlite3_close_v2};std::unique_ptr<SqliteDatabase> current;
    std::uint64_t character{},peer{};std::array<std::array<std::uint8_t,20>,2> bytes;std::array<std::uint16_t,2> keys{1001,20001};
    Fixture(){
        historical.initialize();historical.migrate();raw=open(file.path);
        require(number(raw.get(),"SELECT count(*) FROM sqlite_schema WHERE name='character_bank_item_slots'")==0,"Historical42 unexpectedly includes scalar bank");
        historical.bank_items().install_schema();catalog(raw.get());
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'test-prod0067-a','hash'),(2,'test-prod0067-b','hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='A';character=historical.recovered_characters().create(1,profile).id;profile[0]='B';peer=historical.recovered_characters().create(2,profile).id;
        for(auto owner:{character,peer})for(unsigned slot=0;slot<50;++slot){sqlite_detail::Statement insert(raw.get(),"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,owner);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}
        historical.bank_items().provision_empty(1,character);historical.bank_items().provision_empty(2,peer);
        for(unsigned n=0;n<2;++n){bytes[n].fill(static_cast<std::uint8_t>(0xa5+n));bytes[n][0]=static_cast<std::uint8_t>(keys[n]);bytes[n][1]=static_cast<std::uint8_t>(keys[n]>>8);bytes[n][2]=static_cast<std::uint8_t>((bytes[n][2]&0xc0u)|(n==0?2u:26u));bytes[n][19]=static_cast<std::uint8_t>(0xf0+n);
            sqlite_detail::Statement scalar(raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=1,revision=? WHERE character_id=? AND slot=?");scalar.bind(1,keys[n]);scalar.bind(2,7+n);scalar.bind_id(3,character);scalar.bind(4,n);scalar.done();
            sqlite_detail::Statement insert(raw.get(),"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE','isolated-production0067-opaque',?,?,'CUSTOM-0066')");insert.bind_id(1,character);insert.bind(2,n);insert.bind_blob(3,bytes[n]);insert.bind(4,7+n);insert.bind(5,SqliteArmorSlotRepository::source_sha256);insert.bind(6,SqliteArmorSlotRepository::client_sha256);insert.done();
        }
        sql("UPDATE diagnostic_inventory_slots SET item_id=3107,count=7 WHERE character_id=1 AND slot=5");
        sql("INSERT INTO character_bank_item_receipts VALUES('"+std::string(64,'f')+"',1,1,99,0,5,2,3,'existing-before','existing-after','CUSTOM-0065')");
        const auto before=tables(raw.get());const auto prior_objects=objects(raw.get());
        current=std::make_unique<SqliteDatabase>(file.path);current->initialize();current->migrate();
        const auto after=tables(raw.get(),true);for(const auto& [table,value]:before)require(after.at(table)==value,"Upgrade changed prior table/history/typed row");
        const auto after_objects=objects(raw.get());for(const auto& [name,value]:prior_objects)require(after_objects.at(name)==value,"Upgrade altered a historical schema object");
        require(number(raw.get(),"SELECT count(*) FROM character_bank_armor_metadata")==0&&number(raw.get(),"SELECT count(*) FROM character_bank_armor_receipts")==0,"Upgrade granted armor custody");
        require(current->native_armor_catalog().populated(),"Production full1354 catalog pin failed");
    }
    void sql(const std::string& value){sqlite_detail::execute(raw.get(),value);}
    Repo& repo(){return current->armor_bank();}
    auto load(){return repo().load(1,character);}
    auto request(Op op,unsigned source,unsigned dest,unsigned page=0){return Repo::Request{load(),op,static_cast<std::uint8_t>(page),static_cast<std::uint8_t>(source),static_cast<std::uint8_t>(dest),1};}
    auto commit(const std::string& receipt,const Repo::Request& value){return repo().commit(receipt,value,[](const auto&){});}
    void metadata(bool vault,unsigned slot,const std::array<std::uint8_t,20>& value){sqlite_detail::Statement update(raw.get(),vault?"UPDATE character_bank_armor_metadata SET logical20=? WHERE character_id=? AND slot=?":"UPDATE character_armor_slot_metadata SET logical20=? WHERE character_id=? AND slot=?");update.bind_blob(1,value);update.bind_id(2,character);update.bind(3,slot);update.done();}
};
void source_family_and_transfer(){
    Fixture f;auto correct=f.load();require(correct.bag.armor.size()==2,"Production bag reader lost source instances");
    for(unsigned n=0;n<2;++n){auto bad=f.bytes[n];bad[2]=static_cast<std::uint8_t>((bad[2]&0xc0u)|(n==0?26u:2u));f.metadata(false,n,bad);const auto before=tables(f.raw.get());rejects([&]{(void)f.load();});require(tables(f.raw.get())==before,"Strict family read rejection wrote rows");f.metadata(false,n,f.bytes[n]);require(f.load()==correct,"Same-key family correction did not preserve snapshot");}
    const auto peer=f.repo().load(2,f.peer);const auto a=f.commit(std::string(64,'a'),f.request(Op::Deposit,0,2));const auto b=f.commit(std::string(64,'b'),f.request(Op::Deposit,1,49));
    require(a.after.armor[0].logical20==f.bytes[0]&&b.after.armor[1].logical20==f.bytes[1],"Production63 changed full20");
    for(unsigned n=0;n<2;++n){const auto slot=n==0?2u:49u;auto bad=f.bytes[n];bad[2]=static_cast<std::uint8_t>((bad[2]&0xc0u)|(n==0?26u:2u));f.metadata(true,slot,bad);const auto before=tables(f.raw.get());rejects([&]{(void)f.load();});require(tables(f.raw.get())==before,"Vault family rejection wrote rows");f.metadata(true,slot,f.bytes[n]);}
    const auto swapped=f.commit(std::string(64,'c'),f.request(Op::Move,2,49));require(swapped.after.armor[0].logical20==f.bytes[1]&&swapped.after.armor[1].logical20==f.bytes[0],"Production65 lost opaque full20/high flags");
    const auto returned=f.commit(std::string(64,'d'),f.request(Op::Withdraw,49,29));require(returned.after.bag.armor[0].slot==29&&returned.after.bag.armor[0].logical20==f.bytes[0],"Production64 did not restore original full20");require(f.repo().load(2,f.peer)==peer,"Bank commit changed another owner");
    const auto before=tables(f.raw.get());rejects([&]{(void)f.repo().load(2,f.character);});rejects([&]{f.commit(std::string(64,'d'),f.request(Op::Withdraw,2,28));});require(tables(f.raw.get())==before,"Owner/replay rejection wrote rows");
}
void production_cas_and_rollback(){
    Fixture f;const auto expected=f.request(Op::Deposit,0,2);f.sql("UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=1 AND slot=44");const auto stale=tables(f.raw.get());rejects([&]{f.commit(std::string(64,'e'),expected);});require(tables(f.raw.get())==stale,"Production full50 CAS rejection wrote rows");
    // Real SQL mutates the source-family bits after the receipt. Schema key/CAS
    // guards allow this same-key value; only actual production qualifier rejects.
    f.sql("CREATE TRIGGER adapter_bad_family AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_bank_armor_metadata SET logical20=CAST(substr(logical20,1,2)||X'9A'||substr(logical20,4) AS BLOB) WHERE character_id=NEW.character_id AND slot=2; END");
    // f.raw is the separate fixture writer, not SqliteDatabase's connection;
    // tracing it cannot observe the real production transaction. Instead prove
    // the specific post-receipt qualification failure: before is already valid,
    // and this trigger is the only writer of the wrong family bytes.
    const auto valid=f.request(Op::Deposit,0,2);const auto before=tables(f.raw.get());std::string error;
    try{(void)f.commit(std::string(64,'e'),valid);}catch(const DatabaseError& rejected){error=rejected.what();}
    require(error=="Vault armor full-instance qualification failed","Production postwrite did not reach the injected vault-family rejection");require(tables(f.raw.get())==before,"Production postwrite family failure did not rollback scalar/metadata/receipt");f.sql("DROP TRIGGER adapter_bad_family");
    const auto result=f.commit(std::string(64,'e'),f.request(Op::Deposit,0,2));require(result.after.armor[0].logical20==f.bytes[0],"Valid production commit was blanket rejected");
    const auto scalar_before=f.current->bank_items().load(1,f.character);const auto legacy=f.current->bank_items().commit(std::string(64,'9'),{scalar_before,Op::Deposit,0,5,3,3});require(legacy.bag[5].count==4&&legacy.vault[3].count==3,"Legacy scalar MED behavior changed");require(f.load().armor[0].logical20==f.bytes[0],"Legacy MED commit changed bank armor");
    f.sql("UPDATE native_armor_rows SET parsed_record=zeroblob(396) WHERE item_id=20001");const auto poisoned=tables(f.raw.get());rejects([&]{(void)f.load();});require(tables(f.raw.get())==poisoned,"Broken original-source pin read mutated rows");
}
}
int main(){try{fresh_schema();source_family_and_transfer();production_cas_and_rollback();std::cout<<"PASS CUSTOM0067 actual SqliteDatabase schema43: fresh empty scalar dependencies + history42/old typed rows preserved; full1354 source + strict EQU2/TEQ26; 63/64/65 full20; owner/replay/full50 CAS; production postwrite family rollback; unchanged peer + legacy MED; no grants\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
