#include "db/NativeArmorCatalog.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredArmorSourceSlots.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void rejected(F action){try{action();}catch(const god2::DatabaseError&){return;}throw std::runtime_error("Corrupt armor catalog accepted");}
struct Close{void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
using Db=std::unique_ptr<sqlite3,Close>;
Db open(){sqlite3* raw=nullptr;const auto rc=sqlite3_open(":memory:",&raw);Db db(raw);require(rc==SQLITE_OK,"Open isolated armor database");return db;}
std::vector<std::uint8_t> unhex(const std::string& text){
 require(text.size()%2==0,"Odd native cache hex");std::vector<std::uint8_t> out;
 const auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Bad native cache hex");};
 for(std::size_t i=0;i<text.size();i+=2)out.push_back(static_cast<std::uint8_t>(digit(text[i])*16+digit(text[i+1])));return out;
}
void seed(sqlite3* db){
 std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-armor-20261002/records.json");require(file.good(),"Missing independently executed original armor records");
 nlohmann::json groups;file>>groups;
 require(groups.is_array()&&groups.size()==2&&groups[0].size()==2&&groups[1].size()==1354,"Native armor denominator");
 god2::sqlite_detail::execute(db,god2::NativeArmorCatalog::schema());
 god2::sqlite_detail::Transaction transaction(db);
 for(std::size_t group=0;group<2;++group)for(const auto& row:groups[group]){
  require(row.size()==10,"Native armor row width");
  god2::sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_armor_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_armor_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
  for(int i=0;i<10;++i){
   if(group==1&&(i==6||i==8)){const auto bytes=unhex(row[i].get<std::string>());insert.bind_blob(i+1,bytes);}
   else if((group==0&&i==7)||(group==1&&i>=1&&i<=4)){require(row[i].is_number_integer(),"Native cache integer");insert.bind(i+1,row[i].get<std::int64_t>());}
   else insert.bind(i+1,row[i].get<std::string>());
  }insert.done();
 }transaction.commit();
}
std::string lua_bytes(const std::vector<std::uint8_t>& bytes){
 std::string result="\"";for(auto byte:bytes){result+='\\';result+=char('0'+byte/100);result+=char('0'+byte/10%10);result+=char('0'+byte%10);}return result+'"';
}
void lua_reader(sqlite3* db){
 const auto stamp=std::chrono::steady_clock::now().time_since_epoch().count();
 const auto root=std::filesystem::temp_directory_path()/("god2-armor-lookup-"+std::to_string(stamp));
 require(std::filesystem::create_directory(root),"Own isolated Lua lookup directory");
 struct Cleanup{std::filesystem::path root;~Cleanup(){std::error_code ec;std::filesystem::remove(root/"armor.lua",ec);std::filesystem::remove(root,ec);}} cleanup{root};
 god2::NativeArmorCatalog catalog(db);const auto one=catalog.lookup(1001);require(one.has_value(),"Lua source instance");
 std::ofstream file(root/"armor.lua",std::ios::binary);
 file<<R"LUA(
assert(GOD2_FIXTURE_MODE==false)
local r=native_armor_catalog(1001)
assert(r.item_id==1001 and r.family=='EQU' and r.source_record_index==0)
assert(r.authority=='NATIVE_PARSED_DEFINITION_ONLY' and #r.parsed_record==396)
assert(r.raw_record==)LUA"<<lua_bytes(one->raw_record)<<" and r.parsed_record=="<<lua_bytes(one->parsed_record)<<R"LUA()
assert(native_armor_catalog(1)==nil)
for _,bad in ipairs({0,-1,32768,1.5,'1001',true}) do assert(not pcall(native_armor_catalog,bad)) end
assert(not pcall(native_armor_catalog))
assert(not pcall(native_armor_catalog,1001,1201))
r.parsed_record='local mutation'
assert(#native_armor_catalog(1001).parsed_record==396)
)LUA";file.close();require(!file.fail(),"Write owned Lua source lookup");
 std::size_t calls=0;
 god2::LuaEngine engine(root,false,{},{},{},{},[&](std::uint16_t item){++calls;return catalog.lookup(item);});
 require(engine.initialize()&&engine.load_script("armor.lua"),"Actual Lua armor definition lookup");
 const auto first=calls;require(first==3,"Only valid Lua selectors reach borrowed catalog");
 require(engine.load_script("armor.lua")&&calls>first,"Staged Lua VM retains armor reader across reload");
}
void reader(){
 rejected([]{god2::NativeArmorCatalog catalog(nullptr);});
 auto missing=open();rejected([&]{(void)god2::NativeArmorCatalog(missing.get()).populated();});
 auto db=open();seed(db.get());god2::NativeArmorCatalog catalog(db.get());require(catalog.populated(),"Complete native armor fingerprint");
 for(const auto item:{1001,1201,1501,1601,20001}){
  const auto record=catalog.lookup(static_cast<std::uint16_t>(item));
  require(record&&record->item_id==item&&record->parsed_record.size()==396&&!record->raw_record.empty(),"Exact original armor definition");
  require(record->family==(item<20000?"EQU":"TEQ"),"Armor namespace");
 }
 require(!catalog.lookup(1)&&!catalog.lookup(0)&&!catalog.lookup(65535),"Armor catalog must not invent weapon/unknown records");
 require(catalog.equipment_slot(1001)==31&&catalog.equipment_slot(1201)==30&&
         catalog.equipment_slot(1501)==32&&catalog.equipment_slot(1601)==33,"Source-supported ordinary armor parts");
 std::ifstream qualification(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-armor-20261002/oracle.json");
 require(qualification.good(),"Missing independently checked source classifications");nlohmann::json classes;qualification>>classes;
 require(classes["qualified_count"]==1286&&classes["unknown_count"]==68,"Armor qualification boundary");
 for(const auto& row:classes["qualifications"]){
  const auto actual=god2::RecoveredArmorSourceSlots::find(row["item_id"].get<std::uint16_t>());
  if(row["slot"].is_null())require(!actual,"Ambiguous special item was assigned a guessed part");
  else require(actual==row["slot"].get<std::uint8_t>(),"Generated parts differ from source evidence");
 }
 lua_reader(db.get());
 for(const auto* sql:{
  "DELETE FROM native_armor_rows WHERE item_id=1001",
  "DELETE FROM native_armor_sources WHERE family='TEQ'",
  "UPDATE native_armor_sources SET source_sha256=replace(source_sha256,'7','6') WHERE family='EQU'",
  "UPDATE native_armor_rows SET raw_record=CAST(X'00'||substr(raw_record,2) AS BLOB) WHERE item_id=1001",
  "UPDATE native_armor_rows SET parsed_record=CAST(X'00'||substr(parsed_record,2) AS BLOB) WHERE item_id=1001",
  "UPDATE native_armor_rows SET parsed_record=zeroblob(395) WHERE item_id=1001",
  "UPDATE native_armor_rows SET parsed_record=CAST(parsed_record AS TEXT) WHERE item_id=1001",
  "UPDATE native_armor_rows SET decoded_offset=decoded_offset+1 WHERE item_id=1001",
  "UPDATE native_armor_rows SET item_id=32767 WHERE item_id=1001"}){
  god2::sqlite_detail::execute(db.get(),"PRAGMA foreign_keys=OFF; PRAGMA ignore_check_constraints=ON; BEGIN");
  god2::sqlite_detail::execute(db.get(),sql);rejected([&]{(void)catalog.populated();});rejected([&]{(void)catalog.lookup(1001);});
  require(sqlite3_get_autocommit(db.get())==0,"Reader ended caller transaction");god2::sqlite_detail::execute(db.get(),"ROLLBACK");require(catalog.populated(),"Catalog corruption rollback");
 }
 god2::sqlite_detail::execute(db.get(),"DELETE FROM native_armor_rows; DELETE FROM native_armor_sources");
 require(!catalog.populated()&&!catalog.lookup(1001),"Empty armor catalog has no inferred defaults");
 god2::SqliteDatabase database(":memory:");database.initialize();rejected([&]{(void)database.native_armor_catalog();});database.migrate();
 require(!database.native_armor_catalog().populated(),"Migration must not grant armor definitions or player instances");
}
}
int main(){try{reader();std::cout<<"PASS native armor catalog:1354 definitions, corruption/transaction guards, no instance or gameplay inference\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
