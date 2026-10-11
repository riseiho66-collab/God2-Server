#include "handlers/OwnedWeaponTransferService.h"
#include "db/Migration.h"
#include "db/SqliteSupport.h"
#include <iostream>
using namespace god2;
namespace {
unsigned checks=0;void require(bool value){++checks;if(!value)throw std::runtime_error("Weapon transfer policy/projection test failed");}
void seed(sqlite3* db,unsigned slot,unsigned key) {
 sqlite_detail::Statement scalar(db,"INSERT INTO diagnostic_inventory_slots VALUES(1,?,?,?,1,?,'CUSTOM-0015')");
 scalar.bind(1,slot);scalar.bind(2,key);scalar.bind(3,key?1:0);scalar.bind(4,SqliteWeaponSlotRepository::source_sha256);scalar.done();
 if(key){std::array<std::uint8_t,20> raw{};raw[0]=static_cast<std::uint8_t>(key);raw[2]=1;for(unsigned i=4;i<20;++i)raw[i]=static_cast<std::uint8_t>(i*19+key);
 sqlite_detail::Statement meta(db,"INSERT INTO character_weapon_slot_metadata VALUES(1,?,?,1,'CUSTOM_TEST_NOT_NATIVE','owned-transfer-test',?,?,'CUSTOM-0046')");
 meta.bind(1,slot);meta.bind_blob(2,raw);meta.bind(3,SqliteWeaponSlotRepository::source_sha256);meta.bind(4,SqliteWeaponSlotRepository::client_sha256);meta.done();}
}
}
int main(){sqlite3* db=nullptr;if(sqlite3_open(":memory:",&db)!=SQLITE_OK)return 2;int status=0;try {
 for(const auto& migration:default_sqlite_migrations())sqlite_detail::execute(db,migration.sql);
 sqlite_detail::execute(db,"PRAGMA foreign_keys=ON; INSERT INTO accounts(id,username,password_hash) VALUES(1,'weapon-policy','x'); INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes) VALUES(1,1,0,CAST(X'41'||zeroblob(39) AS BLOB),X'41')");
 seed(db,0,1);seed(db,1,2);seed(db,5,0);seed(db,34,0);
 SqliteWeaponSlotRepository repository(db,[](auto key){return key==1 || key==2;});OwnedWeaponTransferService service(repository);
 const auto first=repository.load(1,1,0).value(),second=repository.load(1,1,1).value();
 const auto equipped=service.select(1,1,{1,0});require(equipped && equipped->changed && equipped->state.source.count==0 && equipped->state.destination.slot==34 && equipped->state.destination.logical20==first.logical20);
 const auto logical=OwnedWeaponTransferService::pair_logical(equipped->state);
 require(logical.size()==40 && logical[0]==0x41 && logical[3]==0 && logical[5]==0x41 && logical[8]==34 && logical[10]==0x3b && logical[11]==1 && logical[12]==34);
 require(std::equal(first.logical20.begin(),first.logical20.end(),logical.begin()+15));
 require(logical[35]==0x41 && logical[36]==1 && logical[38]==34 && logical[39]==1);
 auto swapped=service.select(1,1,{2,1});require(swapped && swapped->state.source.logical20==first.logical20 && swapped->state.destination.logical20==second.logical20);
 const auto no_wrong_key=service.select(1,1,{1,34});require(!no_wrong_key && repository.load(1,1,34)->logical20==second.logical20);
 const auto unequipped=service.select(1,1,{2,34});require(unequipped && unequipped->state.destination.slot==0 && unequipped->state.destination.logical20==second.logical20);
 require(unequipped->state.source.logical20[0]==0 && unequipped->state.source.logical20[1]==0 && std::equal(second.logical20.begin()+2,second.logical20.end(),unequipped->state.source.logical20.begin()+2));
 auto moved=service.bag_move(1,1,{0,5});require(moved && moved->state.destination.logical20==second.logical20 && moved->state.source.count==0);
 const auto revision=repository.load(1,1,5)->revision;
 const auto noop=service.bag_move(1,1,{5,5});require(noop && !noop->changed && repository.load(1,1,5)->revision==revision);
 require(!service.select(1,1,{2,0}) && !service.select(1,1,{2,42}) && !service.select(1,1,{2,4}));
 auto again=service.select(1,1,{2,5});require(again && again->state.destination.slot==34);
 // Wire28 has no target; missing cells are never selected as empty.
 sqlite_detail::execute(db,"DELETE FROM character_weapon_slot_metadata WHERE slot!=34; DELETE FROM diagnostic_inventory_slots WHERE slot!=34");
 require(!service.select(1,1,{2,34}) && repository.load_saved(1,1).size()==1);
 const std::array<std::uint8_t,5> valid{0x28,1,0,0,1};
 auto parsed=RecoveredWorldRecords::decode(valid);require(parsed && OwnedWeaponTransferService::request(*parsed));
 for(const auto& bytes:std::vector<std::vector<std::uint8_t>>{
  {0x28,1,0,0,1,0x28,2,0,1,1},{0x28,1,0,0,1,0x24,0,1},{0x28,1,0,30,1},
  {0x28,1,0,37,1},{0x28,1,0,0,1,0x26,0,0,0,0,0},
  {0x24,0,34}}) {auto records=RecoveredWorldRecords::decode(bytes);require(!records || !OwnedWeaponTransferService::request(*records));}
 auto legal=RecoveredWorldRecords::decode(std::array<std::uint8_t,7>{0x28,1,0,0,1,0x1f,0});require(legal && OwnedWeaponTransferService::request(*legal));
 std::cout<<"PASS "<<checks<<" weapon destination/whole-instance/projection/frame-atomicity checks\n";
 }catch(const std::exception& error){std::cerr<<error.what()<<'\n';status=1;}sqlite3_close(db);return status;}
