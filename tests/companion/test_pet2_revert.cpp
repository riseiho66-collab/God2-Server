#include "handlers/RecoveredPet2RevertGate.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
using namespace god2;
void require(bool value,const char* message) {if(!value) throw std::runtime_error(message);}
void codec() {
    using Codec=RecoveredPet2Revert;
    for(unsigned byte=0;byte<256;++byte) {
        const auto b=static_cast<std::uint8_t>(byte);
        for(const auto request:{Codec::Request{b,43,1},Codec::Request{7,b,1},Codec::Request{7,43,b}})
            require(Codec::decode(Codec::encode(request))==std::optional{request},"D6 lossy raw byte roundtrip");
    }
    for(unsigned item=0;item<256;++item)for(unsigned pet=0;pet<256;++pet)
        for(unsigned option=0;option<6;++option) {
            const Codec::Request request{static_cast<std::uint8_t>(item),static_cast<std::uint8_t>(pet),static_cast<std::uint8_t>(option)};
            require(Codec::has_qualified_operands(request)==(item<30 && pet>=42 && pet<=44 && option>=1 && option<=4),
                "D6 operand gate admits a producer inventory miss or invalid selection");
        }
    const auto raw=Codec::encode({7,43,1});
    for(std::size_t length=0;length<4;++length) require(!Codec::decode(std::span{raw}.first(length)),"D6 truncated record accepted");
    require(!Codec::decode(std::array<std::uint8_t,5>{0xd6,7,43,1,0}),"D6 overlong record accepted");
    require(!Codec::decode(std::array<std::uint8_t,4>{0xd5,7,43,1}),"D6 wrong opcode accepted");
    for(const auto option:{1,2,3,4})
        require(Codec::required_item_key(static_cast<std::uint8_t>(option))==std::optional{static_cast<std::uint16_t>(option==4?0x4010:0x400f)},
            "Native fixed inventory key changed");
}
void repository_gate() {
    using Gate=RecoveredPet2RevertGate;using Decision=Gate::Decision;
    struct Close {void operator()(sqlite3* db) const {sqlite3_close_v2(db);}};
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"DB open failed");
    const std::unique_ptr<sqlite3,Close> db(raw);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'first','hash'),(2,'other','hash')");
    SqliteRecoveredCharacterRepository characters(raw);SqliteCompanionRepository companions(raw);
    std::array<std::uint8_t,40> profile{};profile[0]='A';const auto character=characters.create(1,profile).id;
    Gate gate(characters,companions);Gate::Context context{1,character,true,false};
    const RecoveredPet2Revert::Request request{7,43,1};
    const auto inspect=[&](Decision expected,RecoveredPet2Revert::Request value) {
        const auto changes=sqlite3_total_changes(raw);
        require(gate.inspect(context,value)==expected,"D6 unexpected admission decision");
        require(sqlite3_total_changes(raw)==changes,"D6 denial mutated state");
    };
    context.world_ready=false;inspect(Decision::NotWorldReady,request);context.world_ready=true;
    context.in_battle=true;inspect(Decision::InBattle,request);context.in_battle=false;
    for(const auto invalid:{RecoveredPet2Revert::Request{0x20,43,1},RecoveredPet2Revert::Request{0x60,43,1},
            RecoveredPet2Revert::Request{7,41,1},RecoveredPet2Revert::Request{7,43,0}})
        inspect(Decision::InvalidOperands,invalid);
    inspect(Decision::MissingItem,request);
    const auto insert_item=[&](std::uint16_t key,const char* sha) {
        sqlite_detail::Statement insert(raw,"INSERT OR REPLACE INTO diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) VALUES(?,7,?,1,1,?,'CUSTOM-0015')");
        insert.bind_id(1,character);insert.bind(2,key);insert.bind(3,std::string(sha));insert.done();
    };
    insert_item(0x4010,SqliteCompanionRepository::source_sha256);inspect(Decision::WrongItem,request);
    insert_item(0x400f,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");inspect(Decision::WrongItemSource,request);
    insert_item(0x400f,SqliteCompanionRepository::source_sha256);inspect(Decision::MissingPet2,request);
    companions.provision_pet2_slots(1,character);inspect(Decision::MissingPet2,request);
    sqlite_detail::Statement metadata(raw,"INSERT INTO native_companion_metadata VALUES('NCP',28001,?,1,X'41',?,zeroblob(396))");
    metadata.bind(1,std::string(SqliteCompanionRepository::source_sha256));metadata.bind(2,std::string(64,'a'));metadata.done();
    RecoveredPet2Stats::LogicalRecord bytes{};bytes[0]=0xfb;bytes[1]=0x61;bytes[2]=0x6d;bytes[3]=43;
    RecoveredPet2Lifecycle::Metadata inventory{};inventory[0]=0x61;inventory[1]=0x6d;inventory[2]=34;
    companions.store_pet2(1,character,43,{{1,character},inventory,*RecoveredPet2Stats::parse_logical(bytes)},1,
        {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","pet2-revert-denial-fixture"});
    const auto before=companions.load_pet2_slots(1,character);
    for(const auto option:{1,2,3})inspect(Decision::EffectUnqualified,{7,43,static_cast<std::uint8_t>(option)});
    insert_item(0x4010,SqliteCompanionRepository::source_sha256);inspect(Decision::EffectUnqualified,{7,43,4});
    const auto after=companions.load_pet2_slots(1,character);
    require(before[1].revision==after[1].revision &&
        RecoveredPet2Stats::encode_logical(before[1].pet->stats)==RecoveredPet2Stats::encode_logical(after[1].pet->stats),
        "Unqualified revert changed the full saved FB snapshot");
    const auto item=characters.load_inventory_slot(1,character,7);
    require(item && item->count==1 && item->revision==1,"Unqualified revert consumed the stone");
    context.account=2;bool denied_owner=false;
    try{(void)gate.inspect(context,request);}catch(const std::exception&){denied_owner=true;}
    require(denied_owner,"D6 admitted another account's character");context.account=1;
    const auto resources=characters.commit_resources(1,character,{}, {52,120,2,80,0,"CUSTOM-0012"});
    (void)characters.reserve_battle(1,character,resources);
    inspect(Decision::PendingBattle,request);
}
}
int main() {
    try {codec();repository_gate();std::cout<<"D6 exact grammar, native operands and read-only owned denial passed\n";return 0;}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
