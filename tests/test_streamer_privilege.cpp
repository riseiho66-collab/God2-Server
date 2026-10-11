#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
void require(bool v,const char* m){if(!v)throw std::runtime_error(m);}
int main(){try{
 sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"open");
 std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
 sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
 auto old=default_sqlite_migrations();require(old.back().version==38,"schema version");old.resize(37);
 SqliteMigrationManager(raw,old).migrate();
 sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'owner','preserve'),(2,'other','preserve2')");
 std::array<std::uint8_t,40> profile{};profile[0]='A';
 sqlite_detail::Statement insert(raw,"INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(1,0,?,X'41')");
 insert.bind_blob(1,profile);insert.done();
 SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
 SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
 SqliteRecoveredCharacterRepository roles(raw);
 const auto before=roles.list_for_account(1).at(0);
 require(before.streamer_privilege==0 && before.profile==profile,"Existing role default/preservation");
 for(int value:{1,2,3,0}) {
   sqlite_detail::Statement update(raw,"UPDATE recovered_characters SET streamer_privilege=? WHERE id=?");
   update.bind(1,value);update.bind_id(2,before.id);update.done();
   const auto after=roles.list_for_account(1).at(0);
   require(after.streamer_privilege==value && after.profile==before.profile && after.id==before.id && after.created_at==before.created_at,"Privilege readback/preservation");
 }
 for(const char* value:{"-1","4","256","NULL","1.5","'youtube'"}){
   bool rejected=false;try{sqlite_detail::execute(raw,(std::string("UPDATE recovered_characters SET streamer_privilege=")+value).c_str());}catch(const DatabaseError&){rejected=true;}
   require(rejected,"Invalid privilege accepted");
 }
 profile[0]='B';const auto fresh=roles.create(2,profile);
 require(fresh.streamer_privilege==0,"New role inherited privilege");
 require(roles.list_for_account(1).size()==1 && roles.list_for_account(2).size()==1,"Ownership changed");
 sqlite_detail::Statement account(raw,"SELECT password_hash FROM accounts ORDER BY id");
 require(account.row() && account.text(0)=="preserve" && account.row() && account.text(0)=="preserve2","Credentials changed");
 std::cout<<"PASS schema37 upgrade, rerun, values0..3, invalid inputs, new-role default and saved ownership\n";
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
