#include "handlers/RecoveredBattleService.h"
#include "handlers/RecoveredWorldDisplays.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <string>
namespace {
using namespace god2;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void rejects(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}require(failed,"Expected rejection");}
RecoveredBattleDelta::Bytes result_bytes(std::uint8_t selector=0,std::uint16_t amount=0xffe2) {
    RecoveredBattleDelta::Bytes b{0x83,0x0d,0,1,0,0,0,1,0,0,0,1};
    b[9]=static_cast<std::uint8_t>(amount);b[10]=static_cast<std::uint8_t>(amount>>8);b[13]=selector;b[14]=28;return b;
}
void delta_target_selection_test() {
    // Native51E5E0 returns the first mask bit, rather than expanding one
    // received amount to every marked actor. Keep all raw bits on roundtrip.
    auto bothSides=result_bytes();bothSides[5]=1;
    const auto first=*RecoveredBattleDelta::parse(bothSides);
    require(first.selected_mask_target()==0 && RecoveredBattleDelta::encode(first)==bothSides,
        "Native mask selection or raw bits changed");
    const std::array<BattleActor,3> actors{{{0,7,100,200,50,80,10,10,10,10},
        {14,0,100,200,50,80,10,10,10,10},{19,0,100,200,50,80,10,10,10,10}}};
    const auto encode=[](const auto&,auto){return std::vector<std::uint8_t>{1};};
    Battle sidePriority(101,actors,123);
    const std::array firstRecords{first};
    sidePriority.apply_native_deltas(7,1,firstRecords,encode);
    require(sidePriority.inspect().actors[0]->hp==70 && sidePriority.inspect().actors[14]->hp==100 &&
        sidePriority.inspect().actors[19]->hp==100,"Effect fanned out across both sides");

    auto multiple=result_bytes();multiple[7]=0x21;
    const auto selected=*RecoveredBattleDelta::parse(multiple);
    require(selected.selected_mask_target()==14 && RecoveredBattleDelta::encode(selected)==multiple,
        "Native lowest-slot selection or raw mask changed");
    Battle slotPriority(102,actors,123);
    const std::array selectedRecords{selected};
    slotPriority.apply_native_deltas(7,1,selectedRecords,encode);
    require(slotPriority.inspect().actors[14]->hp==70 && slotPriority.inspect().actors[19]->hp==100,
        "Effect fanned out across marked slots");
    const std::array<BattleActor,2> present{{actors[0],actors[1]}};
    Battle ignoredAbsent(103,present,123);
    ignoredAbsent.apply_native_deltas(7,1,selectedRecords,encode);
    require(ignoredAbsent.inspect().actors[14]->hp==70,"Unselected absent actor blocked native target");

    const std::array<BattleActor,2> missing{{actors[0],actors[2]}};
    Battle selectedAbsent(104,missing,123);
    const auto before=selectedAbsent.checkpoint();bool encoded=false;
    rejects([&]{selectedAbsent.apply_native_deltas(7,1,selectedRecords,[&](const auto&,auto){
        encoded=true;return std::vector<std::uint8_t>{1};});});
    require(!encoded && selectedAbsent.checkpoint()==before,
        "Missing first target fell through to a later bit or published state");

    // Each receive entry gets its own indexed accumulator. Applying +150 then
    // -150 at HP100/max200 yields50; merging or reversing them changes HP.
    Battle ordered(105,present,123);
    const std::array orderedRecords{*RecoveredBattleDelta::parse(result_bytes(0,150)),
        *RecoveredBattleDelta::parse(result_bytes(0,0xff6a))};
    ordered.apply_native_deltas(7,1,orderedRecords,encode);
    require(ordered.inspect().actors[14]->hp==50,"Repeated target entries were merged or reordered");
}
void projection_test(const char* path) {
    SqliteDatabase db(path);db.initialize();db.migrate();
    const std::array<std::uint16_t,2> npcKeys{3793,3954};
    const std::array<std::uint16_t,1> missingNpc{65535};
    require(db.native_npc_display_catalog().contains_all(npcKeys) && !db.native_npc_display_catalog().contains_all(missingNpc),"Scene catalog membership qualification failed");
    StoredWorldDisplay npc{4,3,{0x72},"ISOLATED_TEST_ONLY","synthetic supplied coordinates, native catalog membership only"};
    auto parsed=*RecoveredNpcRecord::parse(npc.logical);parsed.setRawSelector(3793);parsed.setPosition(32767,32767);parsed.setFacing(7);npc.logical=parsed.encode();
    StoredWorldDisplay enemy{4,3,{0x71},"ISOLATED_TEST_ONLY",npc.provenance};
    auto monster=*RecoveredMonsterRecord::parse(enemy.logical);
    monster.setIdentity(123);monster.setCatalog(1,0,1);monster.setPosition(126,127);monster.setFacing(6);enemy.logical=monster.encode();
    db.world_displays().insert(npc);db.world_displays().insert(enemy);
    const StoredMonsterLevel level{4,3,123,27,"ISOLATED_TEST_ONLY","synthetic level, native78 consumer acceptance operand"};
    db.world_displays().insert_level(level);
    require(db.world_displays().load_levels(4,3).empty() && db.world_displays().load_levels(4,3,true)==std::vector{level},"Level isolation failed");
    auto wrong=level;wrong.identity=124;rejects([&]{db.world_displays().insert_level(wrong);});
    require(recovered_world_display_batches(db.world_displays(),db.native_npc_display_catalog(),db.native_enemy_display_catalog(),4,3).empty(),"Test rows escaped production admission");
    const auto batches=recovered_world_display_batches(db.world_displays(),db.native_npc_display_catalog(),db.native_enemy_display_catalog(),4,3,true);
    require(batches.size()==1 && batches[0].size()==47,"Full scene/level projection absent");
    const auto decoded=RecoveredWorldFrame::decode(RecoveredWorldFrame::encode(batches[0]));
    require(decoded && *decoded==batches[0],"World frame changed record bytes");
    require(std::equal(enemy.logical.begin(),enemy.logical.end(),decoded->begin()) &&
        std::equal(npc.logical.begin(),npc.logical.end(),decoded->begin()+26) &&
        RecoveredMonsterLevel::parse(std::span(*decoded).subspan(21,5))==RecoveredMonsterLevel::Record{123,27},"Scene record lost fields/level ordering");
    std::cout<<"PASS isolated current-catalog71/72 scene projection\n";
}
void self_test() {
    delta_target_selection_test();
    for(unsigned level=0;level<=65535;++level) {
        const RecoveredMonsterLevel::Record record{static_cast<std::uint16_t>(65535-level),static_cast<std::uint16_t>(level)};
        require(RecoveredMonsterLevel::parse(RecoveredMonsterLevel::encode(record))==record,"Monster level WORD roundtrip mismatch");
    }
    for(std::size_t size=0;size<12;++size) {
        std::vector<std::uint8_t> rawLevel(size,0x78);
        require(RecoveredMonsterLevel::parse(rawLevel).has_value()==(size==5),"Monster level length mismatch");
    }
    require(!RecoveredMonsterLevel::parse(RecoveredMonsterLevel::Bytes{0x71}),"Wrong level opcode accepted");
    RecoveredMonsterRecord::Bytes raw{};raw.fill(0xa5);raw[0]=0x71;
    auto monster=*RecoveredMonsterRecord::parse(raw);
    for(unsigned facing=0;facing<8;++facing) {
        require(monster.setFacing(facing) && monster.facing()==facing,"Monster facing mismatch");
        require(monster.setPosition(32767,32767) && monster.x()==32767 && monster.y()==32767,"Monster coordinates mismatch");
    }
    require(monster.setIdentity(123) && monster.setCatalog(16,1023,8191),"Monster keys rejected");
    require(monster.identity()==123 && monster.catalogArea()==16 && monster.catalogScene()==1023 && monster.catalogOrdinal()==8191,"Instance/catalog conflation");
    const auto before=monster.encode();
    require(!monster.setFacing(8) && !monster.setPosition(32768,0) && !monster.setIdentity(65536) &&
        !monster.setCatalog(17,0,1) && !monster.setCatalog(0,1024,1) && !monster.setCatalog(0,0,0) && monster.encode()==before,"Monster rejection mutated data");
    for(std::size_t i=0;i<21;++i)if(i!=1 && i!=2 && i!=4 && i!=5 && i!=6 && !(i>=9 && i<=12) && i!=19 && i!=20)
        require(before[i]==raw[i],"Monster opaque field changed");
    auto npc=*RecoveredNpcRecord::parse(RecoveredNpcRecord::Bytes{0x72});
    for(unsigned facing=0;facing<8;++facing)require(npc.setFacing(facing) && npc.facing()==facing,"NPC facing mismatch");
    require(!npc.setFacing(8) && npc.facing()==7,"NPC rejected facing mutated data");
    for(unsigned selector=0;selector<256;++selector) {
        const auto parsed=RecoveredBattleDelta::parse(result_bytes(static_cast<std::uint8_t>(selector)));
        const bool qualified=selector<=5 || selector==7 || selector==8 || selector==9 || selector==20;
        require(parsed.has_value()==qualified,"Unqualified selector admitted");
        if(parsed) {
            require(parsed->amount()==-30 && RecoveredBattleDelta::encode(*parsed)==result_bytes(static_cast<std::uint8_t>(selector)),"Signed amount or opaque bytes lost");
            const auto acc=parsed->accumulate({10,20});
            const std::uint32_t a=selector<=5?0xffffffec:selector==20?0xffffffe2:10;
            const std::uint32_t b=selector==9?0xfffffff6:20;
            require(acc.hp==a && acc.mp==b,"Native selector arithmetic mismatch");
        }
    }
    for(std::size_t size=0;size<=32;++size){std::vector<std::uint8_t> b(size,0x71);require(RecoveredMonsterRecord::parse(b).has_value()==(size==21),"Monster length mismatch");}
    auto bad=result_bytes();bad[11]=0;require(!RecoveredBattleDelta::parse(bad),"Unknown zero-kind branch admitted");
    bad=result_bytes();bad[8]=0x80;require(!RecoveredBattleDelta::parse(bad),"Invalid mask admitted");
    require(!RecoveredWorldRecords::decode(result_bytes()),"S2C83 exposed as C2S command");
    require(RecoveredBattleDelta::apply(0x7fffffff,1,0x7fffffff)==0 &&
        RecoveredBattleDelta::apply(0xffffffff,2,100)==1 &&
        RecoveredBattleDelta::apply(0,1,0xffffffff)==0xffffffff,"Native wrapping/signed cap mismatch");
    sqlite3* rawDb=nullptr;require(sqlite3_open(":memory:",&rawDb)==SQLITE_OK,"DB allocation");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(rawDb,sqlite3_close_v2);
    sqlite_detail::execute(rawDb,"PRAGMA foreign_keys=ON");SqliteMigrationManager(rawDb,default_sqlite_migrations()).migrate();
    SqliteWorldDisplayRepository placements(rawDb);
    StoredWorldDisplay fixture{4,3,npc.encode(),"ISOLATED_TEST_ONLY","isolated supplied position"};
    placements.insert(fixture);rejects([&]{placements.insert(fixture);});
    require(placements.load(4,3).empty() && placements.load(4,3,true)==std::vector{fixture} && placements.load(2,4,true).empty(),"Scene/test isolation failed");
    sqlite_detail::execute(rawDb,"UPDATE world_display_records SET identity=123");
    rejects([&]{(void)placements.load(4,3,true);});
    sqlite_detail::execute(rawDb,"DELETE FROM world_display_records");
    for(unsigned id=0;id<256;++id) {
        npc.setRawSelector(id);fixture.logical=npc.encode();placements.insert(fixture);
    }
    require(placements.load(4,3,true).size()==256,"Native NPC pool boundary rejected");
    npc.setRawSelector(256);fixture.logical=npc.encode();placements.insert(fixture);
    rejects([&]{(void)placements.load(4,3,true);});
    sqlite_detail::execute(rawDb,"DELETE FROM world_display_records");
    sqlite_detail::execute(rawDb,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'native-result-test','test')");
    SqliteRecoveredCharacterRepository repository(rawDb);std::array<std::uint8_t,40> profile{};profile[0]='T';
    const auto character=repository.create(7,profile);
    auto resources=repository.commit_resources(7,character.id,{},CharacterResources{100,200,50,80,0,"CUSTOM-0012"});
    const auto id=repository.reserve_battle(7,character.id,resources);
    const std::array<BattleActor,2> actors{{{0,character.id,100,200,50,80,10,10,10,10},{14,0,100,200,50,80,10,10,10,10}}};
    Battle battle(id,actors,123);
    auto checkpoint=repository.commit_checkpoint(7,character.id,{},resources,battle.checkpoint(),resources,"CUSTOM-0012/diagnostic-v1");
    resources=*repository.load_resources(7,character.id);
    asio::io_context io;Session session(asio::ip::tcp::socket(io),io.get_executor(),91,false,{},{});
    session.account_id=7;session.character_id=character.id;session.set_state(SessionState::InBattle);
    RecoveredBattleService service([](const CombatRuleInput&){return CombatRuleResult{1,0,false};});
    RecoveredBattleService::Policy policy{0,0,0,0,{0,{},false,100,100,0,0,150},{}};
    service.bind(session,battle,policy,[](const BattleSnapshot&,const BattleActionResult&){return std::vector<std::uint8_t>{};},{},
        [&](const BattleCheckpoint& old,const BattleCheckpoint& next){
            require(old==checkpoint.checkpoint,"Checkpoint baseline mismatch");
            const auto& actor=*next.snapshot.actors[0];
            auto nextResources=resources;nextResources.hp=actor.hp;nextResources.mp=actor.mp;
            auto saved=repository.commit_checkpoint(7,character.id,checkpoint,resources,next,nextResources,checkpoint.policy_id);
            nextResources.revision=saved.resource_revision;checkpoint=std::move(saved);resources=nextResources;
        });
    const auto seed=checkpoint;
    // Preserve selector20's raw accumulator view, but reject a mixed exchange
    // before encoding/persistence: native playback skips its HP/MP updates.
    const std::array replacementRecords{*RecoveredBattleDelta::parse(result_bytes()),
        *RecoveredBattleDelta::parse(result_bytes(20))};
    bool replacementEncoded=false;
    rejects([&]{service.apply_native_deltas(session,1,replacementRecords,
        [&](const auto&,auto){replacementEncoded=true;return std::vector<std::uint8_t>{1};});});
    require(!replacementEncoded && service.inspect(91)==seed.checkpoint.snapshot &&
        repository.load_checkpoint(7,character.id,id)==seed,"Selector20 exchange published scalar state");
    for(const std::uint16_t kind:{2,3,65535}) {
        auto rawKind=result_bytes();rawKind[11]=static_cast<std::uint8_t>(kind);
        rawKind[12]=static_cast<std::uint8_t>(kind>>8);
        const auto parsedKind=RecoveredBattleDelta::parse(rawKind);
        require(parsedKind && parsedKind->accumulator_kind_bits()==kind &&
            RecoveredBattleDelta::encode(*parsedKind)==rawKind,"Accumulator kind raw bits lost");
        const std::array kindRecords{*RecoveredBattleDelta::parse(result_bytes()),*parsedKind};
        bool kindEncoded=false;
        rejects([&]{service.apply_native_deltas(session,1,kindRecords,
            [&](const auto&,auto){kindEncoded=true;return std::vector<std::uint8_t>{1};});});
        require(!kindEncoded && service.inspect(91)==seed.checkpoint.snapshot &&
            repository.load_checkpoint(7,character.id,id)==seed,"Unqualified accumulator kind published scalar state");
    }
    auto inconsistent=result_bytes();inconsistent[14]=0;
    const std::array inconsistentRecords{*RecoveredBattleDelta::parse(inconsistent)};
    rejects([&]{service.apply_native_deltas(session,1,inconsistentRecords,
        [](const auto&,auto){return std::vector<std::uint8_t>{1};});});
    require(service.inspect(91)==seed.checkpoint.snapshot && repository.load_checkpoint(7,character.id,id)==seed,"Inconsistent native target status published");
    // Two existing source-owned result entries: enemy HP-30, player MP-10.
    auto mp=result_bytes(9,0xfff6);mp[7]=0;mp[5]=1;
    const std::array records{*RecoveredBattleDelta::parse(result_bytes()),*RecoveredBattleDelta::parse(mp)};
    bool corrupt=false;
    const auto encode=[&](const BattleSnapshot&,std::span<const RecoveredBattleDelta::Record> list){
        std::vector<std::uint8_t> bytes;for(const auto& record:list){const auto b=RecoveredBattleDelta::encode(record);bytes.insert(bytes.end(),b.begin(),b.end());}
        auto wire=RecoveredWorldFrame::encode(bytes);if(corrupt)wire.back()^=1;return wire;
    };
    corrupt=true;rejects([&]{service.apply_native_deltas(session,1,records,encode);});corrupt=false;
    require(service.inspect(91)==seed.checkpoint.snapshot && repository.load_checkpoint(7,character.id,id)==seed,"Encoding failure published");
    sqlite_detail::execute(rawDb,"CREATE TRIGGER reject_native_checkpoint BEFORE INSERT ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'injected'); END");
    rejects([&]{service.apply_native_deltas(session,1,records,encode);});
    require(service.inspect(91)==seed.checkpoint.snapshot && repository.load_checkpoint(7,character.id,id)==seed,"Storage failure published");
    sqlite_detail::execute(rawDb,"DROP TRIGGER reject_native_checkpoint");
    const auto reply=service.apply_native_deltas(session,1,records,encode);
    require(RecoveredWorldFrame::decode(reply)->size()==30 && service.inspect(91).actors[14]->hp==70 && resources.mp==40 &&
        checkpoint.checkpoint.snapshot==service.inspect(91),"Native result state/storage/reply mismatch");
    require(Battle::restore(repository.load_checkpoint(7,character.id,id)->checkpoint).inspect()==service.inspect(91),"Native result restart lost state");
    rejects([&]{service.apply_native_deltas(session,1,records,encode);});
    require(repository.load_checkpoint(7,character.id,id)==checkpoint,"Replay changed state");
    std::cout<<"PASS native71/72/83-0D/HP/MP, scene storage, atomic battle persistence/restart/replay\n";
}
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--oracle") {
            std::string mode;std::uint32_t a,b,c,d;
            while(std::cin>>mode>>a>>b>>c) {
                if(mode=="scalar")std::cout<<god2::RecoveredBattleDelta::apply(a,b,c)<<'\n';
                else if(mode=="acc" && (std::cin>>d)) {
                    auto raw=result_bytes(static_cast<std::uint8_t>(b),static_cast<std::uint16_t>(a));
                    const auto record=god2::RecoveredBattleDelta::parse(raw);require(record.has_value(),"Invalid oracle input");
                    const auto acc=record->accumulate({c,d});std::cout<<acc.hp<<' '<<acc.mp<<'\n';
                }else throw std::runtime_error("Invalid oracle command");
            }
            return 0;
        }
        if(argc==3 && std::string(argv[1])=="--projection"){projection_test(argv[2]);return 0;}
        self_test();return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
