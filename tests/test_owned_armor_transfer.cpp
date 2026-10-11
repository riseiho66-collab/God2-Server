#include "handlers/OwnedArmorTransferService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void rejects(F&& call){try{call();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected armor service rejection");}
std::optional<std::uint8_t> mapping(std::uint16_t key){switch(key){case 60001:case 60003:return 30;case 60002:return 31;default:return {};}}
struct Fixture{
    sqlite3* raw{};std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db{nullptr,sqlite3_close_v2};std::uint64_t character{};
    Fixture(){require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");auto migrations=default_sqlite_migrations();require(migrations.back().version>=42,"Armor migration boundary");while(migrations.back().version>=42)migrations.pop_back();SqliteMigrationManager(raw,std::move(migrations)).migrate();sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'armor-ui','hash')");
        SqliteRecoveredCharacterRepository characters(raw);std::array<std::uint8_t,40> profile{};profile[0]='A';character=characters.create(1,profile).id;
        for(unsigned slot=0;slot<50;++slot){sqlite_detail::Statement insert(raw,"INSERT INTO diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,character);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}
        sqlite_detail::execute(raw,SqliteArmorSlotRepository::schema());
    }
    std::array<std::uint8_t,20> armor(unsigned slot,std::uint16_t item,std::uint8_t fill){
        sqlite_detail::Statement scalar(raw,"UPDATE diagnostic_inventory_slots SET item_id=?,count=1 WHERE character_id=? AND slot=?");scalar.bind(1,item);scalar.bind_id(2,character);scalar.bind(3,slot);scalar.done();std::array<std::uint8_t,20> bytes;bytes.fill(fill);bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);bytes[2]=static_cast<std::uint8_t>((fill&0xc0)|2);
        sqlite_detail::Statement insert(raw,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE','isolated-service-instance',?,?,'CUSTOM-0066')");insert.bind_id(1,character);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind(4,SqliteArmorSlotRepository::source_sha256);insert.bind(5,SqliteArmorSlotRepository::client_sha256);insert.done();return bytes;
    }
};
void preflight(){
    using W=RecoveredWorldRecords;const W::Record use=RecoveredSelectionItemRequest::Request{60001,0};
    const std::array<W::Record,4> valid{W::Tick{},use,W::Tick{},W::ClientControl1F{}};require(OwnedArmorTransferService::request(valid).has_value(),"Armor28+tick+trailing control denied");
    const std::array<W::Record,2> duplicate{use,use};require(!OwnedArmorTransferService::request(duplicate),"Duplicate armor mutation admitted");
    const std::array<W::Record,2> mixed{use,RecoveredBankItems::Request{RecoveredBankItems::Kind::Move,531,0,2,3,1}};require(!OwnedArmorTransferService::request(mixed),"Mixed bank/armor admitted");
    const std::array<W::Record,2> prefix{W::ClientControl1F{},use};require(!OwnedArmorTransferService::request(prefix),"Prefix control admitted");
    const std::array<W::Record,1> protected_slot{RecoveredSelectionItemRequest::Request{60001,34}};require(!OwnedArmorTransferService::request(protected_slot),"Weapon34 captured by armor");
    const std::array<W::Record,1> pet{RecoveredSelectionItemRequest::Request{60001,44}};require(!OwnedArmorTransferService::request(pet),"Pet44 captured by armor");
}
void flow(){
    Fixture f;const auto a=f.armor(4,60001,0xa1),b=f.armor(7,60003,0xb2);f.armor(8,60002,0xc3);SqliteArmorSlotRepository repo(f.raw,mapping);OwnedArmorTransferService service(repo);
    auto result=service.select(1,f.character,{60001,4});require(result&&result->changed&&result->state.destination.slot==30&&result->state.destination.logical20==a,"Armor mapped equip failed");
    const auto expected=OwnedArmorTransferService::pair_logical(result->state);const auto frame=RecoveredWorldFrame::decode(result->wire);require(frame&&*frame==expected,"Armor wire differs from prepared full instance");
    // Both cells clear before any installed3B; exact bytes must be present.
    require(expected.size()==40&&expected[0]==0x41&&expected[3]==4&&expected[4]==0&&expected[5]==0x41&&expected[8]==30&&expected[10]==0x3b&&expected[11]==1&&expected[12]==30&&std::equal(a.begin(),a.end(),expected.begin()+15),"Armor clear/3B/41 ordering or20 bytes incorrect");
    result=service.select(1,f.character,{60003,7});require(result&&result->state.source.logical20==a&&result->state.destination.logical20==b,"Armor same-part equipped exchange failed");
    result=service.select(1,f.character,{60003,30});require(result&&result->state.destination.slot==0&&result->state.destination.logical20==b,"Armor unequip did not choose lowest explicitly owned empty bag");
    // Ordinary bag exchange may exchange different armor parts as whole cells.
    result=service.bag_move(1,f.character,{0,8});require(result&&result->state.source.item_id==60002&&result->state.destination.item_id==60003,"Different armor parts cannot reorder in bag");
    const auto before=repo.load_snapshot(1,f.character);require(!service.select(1,f.character,{60001,0}),"Wrong key authorized armor");require(!service.select(1,f.character,{60003,34}),"Weapon domain authorized armor");
    result=service.bag_move(1,f.character,{8,8});require(result&&!result->changed&&repo.load_snapshot(1,f.character)==before,"Same-cell drag changed revision");
    try{service.select(1,f.character,{60003,8},[](const auto&){return std::vector<std::uint8_t>(RecoveredWorldFrame::max_logical_size+1,0);});throw std::runtime_error("Expected framing bounds rejection");}catch(const std::invalid_argument&){}require(repo.load_snapshot(1,f.character)==before,"Oversized precommit reply changed saves");
    // Saved restoration presents complete armor metadata only; no scalar grant.
    const auto restored=repo.load_saved(1,f.character);for(const auto& row:restored)if(row.count){const auto logical=OwnedArmorTransferService::slot_logical(row);require(logical.size()==35&&std::equal(row.logical20.begin(),row.logical20.end(),logical.begin()+10),"Saved armor restoration lost full20 bytes");}
}
void instance_family(){
    Fixture f;f.armor(0,60001,0xa1);SqliteArmorSlotRepository repo(f.raw,mapping);
    const auto baseline=repo.load_snapshot(1,f.character);const auto original=baseline.armor.front();
    for(unsigned flags=0;flags<4;++flags)for(unsigned family=0;family<64;++family){
        auto row=original;row.logical20[2]=static_cast<std::uint8_t>((flags<<6)|family);
        sqlite_detail::Statement update(f.raw,"UPDATE character_armor_slot_metadata SET logical20=? WHERE character_id=? AND slot=0");
        update.bind_blob(1,row.logical20);update.bind_id(2,f.character);update.done();
        if(family==2||family==26){require(repo.load_snapshot(1,f.character).armor.front().logical20==row.logical20,"Native armor family flags rejected");require(!OwnedArmorTransferService::slot_logical(row).empty(),"Native family projection rejected");}
        else{rejects([&]{repo.load_snapshot(1,f.character);});rejects([&]{OwnedArmorTransferService::slot_logical(row);});}
    }
    sqlite_detail::Statement restore(f.raw,"UPDATE character_armor_slot_metadata SET logical20=? WHERE character_id=? AND slot=0");restore.bind_blob(1,original.logical20);restore.bind_id(2,f.character);restore.done();
    require(repo.load_snapshot(1,f.character)==baseline,"Family validation mutated physical instance");
}
void full_bag_and_cross_category(){
    Fixture f;f.armor(30,60001,0xa1);SqliteArmorSlotRepository repo(f.raw,mapping);OwnedArmorTransferService service(repo);
    sqlite_detail::execute(f.raw,"UPDATE diagnostic_inventory_slots SET item_id=3107,count=1 WHERE slot<30");const auto before=repo.load_snapshot(1,f.character);
    require(!service.select(1,f.character,{60001,30})&&repo.load_snapshot(1,f.character)==before,"Full bag unequip fabricated capacity or overwrote MED");
    require(!service.bag_move(1,f.character,{0,1})&&repo.load_snapshot(1,f.character)==before,"Armor service captured scalar MED bag24");
}
}
int main(){try{preflight();flow();instance_family();full_bag_and_cross_category();std::cout<<"Armor28/bag24 preflight, mapped selection, lossless projection, cross-domain/full-bag denial and precommit framing passed; native UI/appearance/stats OPEN\n";}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
