#include "db/NativeWeaponCatalog.h"
#include "handlers/RecoveredWeaponSexRestriction.h"
#include "protocol/RecoveredEquipmentRejection.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "scripting/LuaEngine.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>

namespace {
void require(bool v,const char* text){if(!v)throw std::runtime_error(text);}
template<class F>void rejected(F f){try{f();}catch(const god2::DatabaseError&){return;}throw std::runtime_error("Corrupt weapon catalog accepted");}
struct Close{void operator()(sqlite3* p)const{sqlite3_close_v2(p);}};
using Db=std::unique_ptr<sqlite3,Close>;
Db open(const std::string& path,int flags=SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE){sqlite3* p=nullptr;int rc=sqlite3_open_v2(path.c_str(),&p,flags,nullptr);Db db(p);require(rc==SQLITE_OK,"Open fixture DB");return db;}
struct Temporary {
 std::filesystem::path root;
 Temporary(){auto stamp=std::chrono::steady_clock::now().time_since_epoch().count();for(int i=0;i<100;++i){root=std::filesystem::temp_directory_path()/("god2-native-weapons-test-"+std::to_string(stamp)+"-"+std::to_string(i));if(std::filesystem::create_directory(root))return;}throw std::runtime_error("Create temp directory");}
 ~Temporary(){std::error_code ec;std::filesystem::remove_all(root,ec);}
 void write(const char* name,const std::string& text){std::ofstream f(root/name,std::ios::binary);f<<text;f.close();require(!f.fail(),"Write Lua fixture");}
};
std::vector<std::uint8_t> unhex(const std::string& text){require(text.size()%2==0,"Odd cache hex");std::vector<std::uint8_t> out;for(size_t i=0;i<text.size();i+=2){auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Bad cache hex");};out.push_back(static_cast<std::uint8_t>(digit(text[i])*16+digit(text[i+1])));}return out;}
void seed_real_cache(sqlite3* db){
 std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-weapons-20260926/records.json");require(file.good(),"Missing current native cache");nlohmann::json groups;file>>groups;
 require(groups.is_array()&&groups.size()==2&&groups[0].size()==2&&groups[1].size()==1259,"Cache denominator");
 god2::SqliteMigrationManager(db,god2::default_sqlite_migrations()).migrate();
 god2::sqlite_detail::execute(db,"BEGIN");
 for(size_t g=0;g<2;++g)for(const auto& row:groups[g]){
  require(row.size()==10,"Cache row width");
  god2::sqlite_detail::Statement insert(db,g==0?"INSERT INTO native_weapon_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_weapon_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
  for(int i=0;i<10;++i){if(g==1&&(i==6||i==8)){auto bytes=unhex(row[i].get<std::string>());insert.bind_blob(i+1,bytes);}else if((g==0&&i==7)||(g==1&&i>=1&&i<=4)){require(row[i].is_number_integer(),"Cache integer type");insert.bind(i+1,row[i].get<std::int64_t>());}else insert.bind(i+1,row[i].get<std::string>());}
  insert.done();
 }
 god2::sqlite_detail::execute(db,"COMMIT");
 require(god2::NativeWeaponCatalog(db).populated(),"Real cached full fingerprint");
}
std::string lua_bytes(const std::vector<std::uint8_t>& bytes){std::string result="\"";for(auto b:bytes){result+='\\';result+=char('0'+b/100);result+=char('0'+b/10%10);result+=char('0'+b%10);}return result+'"';}
void copy(sqlite3* from,sqlite3* to){auto* b=sqlite3_backup_init(to,"main",from,"main");require(b!=nullptr,"Begin backup");int step=sqlite3_backup_step(b,-1);int finish=sqlite3_backup_finish(b);require(step==SQLITE_DONE&&finish==SQLITE_OK,"Backup actual catalog");}
void check_reader(sqlite3* original){
 rejected([]{god2::NativeWeaponCatalog bad(nullptr);});
 god2::NativeWeaponCatalog source(original);require(source.populated(),"Populated real DB");
 const auto first=source.lookup(1), second=source.lookup(2),tw=source.lookup(19001);
 require(first&&second&&tw&&first->family=="WPN"&&first->source_line==4804&&second->source_line==4805&&tw->family=="TWP"&&tw->source_line==15478,"Known native records");
 require(first->parsed_record.size()==396&&first->parsed_record[0x114]==1&&first->parsed_record[0x120]==2,"Exact native metadata");
 using Restriction=god2::RecoveredWeaponSexRestriction;
 require(Restriction::requirement(*first)==Restriction::Requirement::None,"Unrestricted real WPN source");
 unsigned male=0,female=0;
 god2::sqlite_detail::Statement restrictions(original,"SELECT item_id,parsed_record FROM native_weapon_rows WHERE family='TWP'");
 while(restrictions.row()) {
  god2::NativeWeaponRecord row{};row.family="TWP";row.item_id=restrictions.number<std::uint16_t>(0);
  const auto bytes=restrictions.blob(1,396,396);row.parsed_record.assign(bytes.begin(),bytes.end());
  const auto rule=Restriction::requirement(row);
  if(rule==Restriction::Requirement::Male) {++male;require(Restriction::permits(rule,Restriction::Sex::Male)&&!Restriction::permits(rule,Restriction::Sex::Female),"Male source restriction");}
  if(rule==Restriction::Requirement::Female) {++female;require(Restriction::permits(rule,Restriction::Sex::Female)&&!Restriction::permits(rule,Restriction::Sex::Male),"Female source restriction");}
 }
 require(male==35&&female==34,"All69 native source restrictions");
 std::array<std::uint8_t,40> profile{};profile[0]='A';profile[31]=1;
 for(unsigned paired=1;paired<=8;++paired) {
  profile[29]=static_cast<std::uint8_t>(paired);profile[33]=static_cast<std::uint8_t>((paired-1)&1);profile[38]=profile[33];
  require(Restriction::profile_sex(profile)==(paired%2?Restriction::Sex::Male:Restriction::Sex::Female),"Native paired profile sex");
  auto bad=profile;bad[38]^=1;
  bool denied=false;try{(void)Restriction::profile_sex(bad);}catch(const std::invalid_argument&){denied=true;}
  require(denied,"Inconsistent packed sex accepted");
 }
 const auto message=god2::RecoveredEquipmentRejection::logical(19071);
 require(message.size()==23&&message[0]==2&&message[1]==27&&message[2]==0&&message[3]==0x7f&&message[4]==0x4a,"Native rejection layout");
 require(std::all_of(message.begin()+5,message.end(),[](auto byte){return byte==0;}),"Native bounded rejection tail");
 require(!source.lookup(0)&&!source.lookup(65535)&&!source.lookup(32767),"Unknown keys must be absent");
 auto db=open(":memory:");copy(original,db.get());god2::NativeWeaponCatalog c(db.get());
 for(const char* sql:{
  "DELETE FROM native_weapon_rows WHERE item_id=1",
  "DELETE FROM native_weapon_sources WHERE family='WPN'",
  "UPDATE native_weapon_sources SET source_sha256=replace(source_sha256,'7','6') WHERE family='WPN'",
  "UPDATE native_weapon_rows SET raw_record=CAST(X'00'||substr(raw_record,2) AS BLOB) WHERE item_id=1",
  "UPDATE native_weapon_rows SET parsed_record=CAST(X'00'||substr(parsed_record,2) AS BLOB) WHERE item_id=1",
  "UPDATE native_weapon_rows SET parsed_record=zeroblob(395) WHERE item_id=1",
  "UPDATE native_weapon_rows SET parsed_record=CAST(parsed_record AS TEXT) WHERE item_id=1",
  "UPDATE native_weapon_rows SET decoded_offset=decoded_offset+1 WHERE item_id=1",
  "UPDATE native_weapon_rows SET item_id=32767 WHERE item_id=1"}){
   god2::sqlite_detail::execute(db.get(),"PRAGMA foreign_keys=OFF; PRAGMA ignore_check_constraints=ON; BEGIN");
   god2::sqlite_detail::execute(db.get(),sql);rejected([&]{(void)c.populated();});rejected([&]{(void)c.lookup(32767);});
   require(sqlite3_get_autocommit(db.get())==0,"Reader ended caller transaction");god2::sqlite_detail::execute(db.get(),"ROLLBACK");require(c.populated(),"Rollback did not restore real records");
 }
 god2::sqlite_detail::execute(db.get(),"DELETE FROM native_weapon_rows; DELETE FROM native_weapon_sources");require(!c.populated()&&!c.lookup(1),"Empty catalog invented data");
 auto missing=open(":memory:");rejected([&]{(void)god2::NativeWeaponCatalog(missing.get()).populated();});
}
void check_lua(sqlite3* db,Temporary& temp){
 god2::NativeWeaponCatalog reader(db);auto record=reader.lookup(1);require(record.has_value(),"Lua native source");size_t calls=0;
 temp.write("weapon.lua",R"LUA(
assert(GOD2_FIXTURE_MODE==false)
local function check()
 local r=native_weapon_catalog(1)
 assert(r.item_id==1 and r.family=='WPN' and r.source_line==4804 and r.source_record_index==0)
 assert(r.authority=='NATIVE_PARSED_DEFINITION_ONLY')
 assert(r.raw_record==)LUA"+lua_bytes(record->raw_record)+R"LUA( and r.parsed_record==)LUA"+lua_bytes(record->parsed_record)+R"LUA()
 assert(r.record_sha256==')LUA"+record->record_sha256+R"LUA(' and r.parsed_sha256==')LUA"+record->parsed_sha256+R"LUA(')
 assert(native_weapon_catalog(19001).family=='TWP' and native_weapon_catalog(32767)==nil)
 r.raw_record='changed';r.parsed_record='changed';r.item_id=9
 assert(native_weapon_catalog(1).item_id==1 and #native_weapon_catalog(1).parsed_record==396)
end
check()
for _,arg in ipairs({0,-1,32768,1.5,'1',true,{},math.huge,0/0}) do assert(not pcall(native_weapon_catalog,arg)) end
assert(not pcall(native_weapon_catalog));assert(not pcall(native_weapon_catalog,nil));assert(not pcall(native_weapon_catalog,1,2))
register_gm_command('weapon_check',check)
)LUA");
 god2::LuaEngine engine(temp.root,false,{},{},{},[&](std::uint16_t item){++calls;return reader.lookup(item);});
 require(engine.initialize()&&engine.load_script("weapon.lua"),"Lua actual DB checks/invalid selectors");
 auto invoke=[&]{engine.call_gm_command("weapon_check",{1,"isolated-test"},{});};invoke();const auto before=calls;
 require(engine.reload_all(),"Lua reload lost binding");invoke();require(calls>before,"Reload callback not retained");
 require(sqlite3_total_changes(db)==0,"Read-only Lua mutated DB");
 temp.write("unavailable.lua","assert(not pcall(native_weapon_catalog,1))");
 god2::LuaEngine unavailable(temp.root,false);require(unavailable.initialize()&&unavailable.load_script("unavailable.lua"),"Unavailable callback false success");
}
}
int main(int argc,char** argv){try{
 require(argc==1||argc==2,"Usage: native-weapon-catalog [readonly-imported-test.db]");Temporary temp;
 std::filesystem::path path;
 if(argc==2)path=argv[1];else{path=temp.root/"native.sqlite";auto db=open(path.string());seed_real_cache(db.get());}
 auto ro=open(path.string(),SQLITE_OPEN_READONLY);require(sqlite3_db_readonly(ro.get(),"main")==1,"Expected read-only input");
 check_reader(ro.get());check_lua(ro.get(),temp);require(sqlite3_get_autocommit(ro.get())!=0,"Reader leaked transaction");
 std::cout<<"PASS: pinned native weapon reader, corruption/partial/empty/unknown/read-only, Lua actual DB/invalid selectors/snapshot/reload\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
