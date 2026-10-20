// NEW CUSTOM-0070 storage/service gate, not original server-policy recovery.
// Frozen0068 fixture supplies the complete qualified current weapon catalog.
#define main owned_mixed_bank_service_fixture_companion_main
#include "storage_owned_foreign_bank_0068.cpp"
#undef main
#include "handlers/OwnedMixedBankService.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iomanip>
#include <sstream>
#include "BankCallbackRegression.h"

namespace {
using MixedService=OwnedMixedBankService;
using MixedRepo=SqliteOwnedMixedBankRepository;
using MixedKind=RecoveredBankItems::Kind;
std::optional<std::uint8_t> mixed_armor(std::uint16_t id){if(id==20001)return 31;return armor(id);}
bool mixed_armor_exact(std::uint16_t id,const std::array<std::uint8_t,20>& bytes){return mixed_armor(id)&&RecoveredArmorSourceInstance::matches(id,id==20001?"TEQ":"EQU",bytes);}
struct MixedHarness {
    Fixture f;Repo foreign_repo;MixedRepo mixed_repo;SqliteOwnedArmorBankRepository armor_repo;SqliteBankItemsRepository plain_repo;
    std::optional<RecoveredBankService::Peer> peer;
    bool permit=true,fail_prepare=false,throw_renew=false;unsigned renews{},serial{},prepare_failures{},late_hits{};
    std::optional<std::string> fixed_receipt;
    std::function<void(std::string_view)> callback;
    void observe(std::string_view stage){const auto hook=callback;if(hook)hook(stage);}
    std::function<void()> late;
    MixedService service;
    MixedHarness():f(50,true),foreign_repo(f.db,mixed_armor,mixed_armor_exact,[this](auto id)->std::optional<NativeWeaponRecord>{const auto found=f.definitions.find(id);return found==f.definitions.end()?std::nullopt:std::optional(found->second);}),
        mixed_repo(f.db,foreign_repo,[](auto id){return id==3107;}),armor_repo(f.db,mixed_armor,mixed_armor_exact),plain_repo(f.db),
        peer(RecoveredBankService::Peer{77,1,f.ids[0],4,3,126,132,true}),
        service(mixed_repo,foreign_repo,armor_repo,plain_repo,
            [this](auto id)->std::optional<RecoveredBankService::Peer>{observe("lookup");if(sqlite3_get_autocommit(f.db)==0&&late){++late_hits;late();}return id==77?peer:std::nullopt;},
            [this](auto,auto target,auto){observe("permit");return permit&&target==279;},
            [this](auto,auto){observe("renew");++renews;if(throw_renew)throw 7;},
            [this](const auto& row){observe("eligible");return row.item_id==3107&&row.count&&row.source_sha256==SqliteArmorSlotRepository::source_sha256;},
            [this](auto slot,const auto& row){observe("plain");if(fail_prepare){++prepare_failures;throw DatabaseError("CUSTOM_TEST plain prepare");}RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);return RecoveredInventoryProjection::encode({slot,row.count,bytes}).value();},
            [this]{observe("receipt");if(fixed_receipt)return *fixed_receipt;std::ostringstream out;out<<std::string(56,'7')<<std::hex<<std::setw(8)<<std::setfill('0')<<serial++;return out.str();},
            [this](auto id){observe("weapon");if(fail_prepare){++prepare_failures;throw DatabaseError("CUSTOM_TEST instance prepare");}return f.definitions.contains(id);}){f.install();f.sql(MixedRepo::schema());}
    static auto now(){return MixedService::Clock::now();}
    auto load(unsigned owner=0){return mixed_repo.load(owner+1,f.ids[owner]);}
    auto open(){return service.open(77,279,now());}
    auto handle(MixedKind kind,std::uint8_t source,std::uint8_t destination,std::uint8_t count=1,std::uint8_t page=0,std::uint16_t target=279){const std::array requests{RecoveredBankItems::Request{kind,target,page,source,destination,count}};return service.handle(77,requests,now());}
    std::array<std::uint8_t,20> seed(unsigned family,unsigned bag,unsigned vault,std::uint8_t page=0,std::uint8_t fill=0xa2){
        std::array<std::uint8_t,20> raw{};unsigned qty=1;
        if(family==0){f.scalar(bag,3107,7,3);raw[0]=0x23;raw[1]=0x0c;qty=7;}
        else if(family==1||family==2){const auto id=static_cast<std::uint16_t>(family==1?1001:20001);f.scalar(bag,id,1,9);raw.fill(fill);raw[0]=static_cast<std::uint8_t>(id);raw[1]=static_cast<std::uint8_t>(id>>8);raw[2]=static_cast<std::uint8_t>((fill&0xc0u)|(family==1?2u:26u));sqlite_detail::Statement insert(f.db,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,9,'CUSTOM_TEST_NOT_NATIVE','NEW0070 opaque armor fixture',?,?,'CUSTOM-0066')");insert.bind_id(1,f.ids[0]);insert.bind(2,bag);insert.bind_blob(3,raw);insert.bind(4,SqliteArmorSlotRepository::source_sha256);insert.bind(5,SqliteArmorSlotRepository::client_sha256);insert.done();}
        else raw=f.add(bag,static_cast<std::uint16_t>(family==3?1:family==4?19001:16055),fill,11);
        open();require(handle(MixedKind::Deposit,static_cast<std::uint8_t>(bag),static_cast<std::uint8_t>(vault),static_cast<std::uint8_t>(qty),page).committed,"NEW0070 ordinary63 seed route failed");return raw;
    }
};
std::vector<std::uint8_t> mixed_flatten(const MixedService::Batches& batches){std::vector<std::uint8_t> bytes;for(const auto& batch:batches){require(!batch.empty()&&batch.size()<=RecoveredWorldFrame::max_logical_size,"NEW0070 response frame bound");bytes.insert(bytes.end(),batch.begin(),batch.end());}return bytes;}
std::vector<std::uint8_t> mixed_vault(std::uint8_t page,std::uint8_t slot,std::uint8_t qty,const std::array<std::uint8_t,20>& raw){const auto value=RecoveredBankItems::slot(page,slot,qty,raw).value();return {value.begin(),value.end()};}
void add_bytes(std::vector<std::uint8_t>& a,const std::vector<std::uint8_t>& b){a.insert(a.end(),b.begin(),b.end());}
void mixed_full_ordered_pairs(){
    // Six qualifying categories: MED/EQU/TEQ/WPN/TWP/gem, all36 ordered pairs.
    // No claim that original server admitted these new custody combinations.
    for(unsigned a=0;a<6;++a)for(unsigned b=0;b<6;++b){
        MixedHarness h;const auto left=h.seed(a,0,2,2,0xa2),right=h.seed(b,1,49,2,0xb3);h.f.add(34,2,0xc1,19);h.f.add_armor(30,1201);h.f.add(0,16055,0xd4,7,1);h.open();
        const auto before=h.load(),other=h.load(1);const auto money=dump(h.f.db,"SELECT * FROM foreign_bank_test_money ORDER BY character_id");
        const auto old_foreign=dump(h.f.db,"SELECT * FROM character_bank_foreign_receipts ORDER BY rowid"),old_armor=dump(h.f.db,"SELECT * FROM character_bank_armor_receipts ORDER BY rowid"),old_plain=dump(h.f.db,"SELECT * FROM character_bank_item_receipts ORDER BY rowid");
        const auto result=h.handle(MixedKind::Move,2,49,1,2);
        auto wire=mixed_vault(2,2,b==0?7:1,right);add_bytes(wire,mixed_vault(2,49,a==0?7:1,left));
        require(result.committed&&!result.rejected&&mixed_flatten(result.batches)==wire,"NEW0070 whole mixed65 wrong exact native48/full20");
        sqlite_detail::Statement native_marker_receipt(h.f.db,"SELECT quantity FROM character_bank_mixed_receipts WHERE character_id=? ORDER BY rowid DESC LIMIT 1");native_marker_receipt.bind_id(1,h.f.ids[0]);require(native_marker_receipt.row()&&native_marker_receipt.number<unsigned>(0)==(a==0?7u:1u),"NEW0070 receipt confused native65 marker1 with actual whole MED quantity");
        const auto after=h.load();require(after.base.vault[102].item_id==before.base.vault[149].item_id&&after.base.vault[102].count==before.base.vault[149].count&&after.base.vault[149].item_id==before.base.vault[102].item_id&&after.base.vault[149].count==before.base.vault[102].count&&after.base.vault[102].revision==before.base.vault[102].revision+1&&after.base.vault[149].revision==before.base.vault[149].revision+1,"NEW0070 scalar whole/revision swap wrong");
        require(after.base.bag==before.base.bag&&h.load(1)==other&&dump(h.f.db,"SELECT * FROM foreign_bank_test_money ORDER BY character_id")==money,"NEW0070 vault65 touched owner/equipment/money");
        require(old_foreign==dump(h.f.db,"SELECT * FROM character_bank_foreign_receipts ORDER BY rowid")&&old_armor==dump(h.f.db,"SELECT * FROM character_bank_armor_receipts ORDER BY rowid")&&old_plain==dump(h.f.db,"SELECT * FROM character_bank_item_receipts ORDER BY rowid"),"NEW0070 native65 incorrectly wrote old ledgers");
        const auto reopened=mixed_flatten(h.open());require(reopened.size()==300*29&&std::equal(wire.begin(),wire.begin()+29,reopened.begin()+102*29)&&std::equal(wire.begin()+29,wire.end(),reopened.begin()+149*29),"NEW0070 complete vault reopen lost exchanged full20");
        auto restored=h.handle(MixedKind::Move,49,2,1,2);require(restored.committed,"NEW0070 reverse65 failed");
        require(h.handle(MixedKind::Withdraw,2,0,a==0?7:1,2).committed&&h.handle(MixedKind::Withdraw,49,1,b==0?7:1,2).committed,"NEW0070 original64 custody restore failed");
    }
    for(unsigned family=0;family<6;++family){MixedHarness h;const auto raw=h.seed(family,0,2);h.open();const auto result=h.handle(MixedKind::Move,2,49,1);auto wire=mixed_vault(0,2,0,{});add_bytes(wire,mixed_vault(0,49,family==0?7:1,raw));require(result.committed&&mixed_flatten(result.batches)==wire,"NEW0070 empty destination65 lost whole category");}
}
void mixed_rejections_and_context(){
    MixedHarness h;h.seed(0,0,2);h.seed(1,1,3);h.seed(3,2,4);h.open();
    auto deny=[&](auto call){h.open();const auto rows=h.f.rows();const auto result=call();require(result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 rejected operation changed typed complete storage");};
    for(auto q:{0u,2u,6u,7u,8u,127u})deny([&]{return h.handle(MixedKind::Move,2,3,static_cast<std::uint8_t>(q));});
    for(auto slot:{0u,1u,50u,255u}){deny([&]{return h.handle(MixedKind::Move,static_cast<std::uint8_t>(slot),3);});deny([&]{return h.handle(MixedKind::Move,3,static_cast<std::uint8_t>(slot));});}
    deny([&]{return h.handle(MixedKind::Move,3,4,1,3);});deny([&]{return h.handle(MixedKind::Move,3,4,1,0,280);});deny([&]{return h.handle(MixedKind::Move,49,3);});deny([&]{return h.handle(MixedKind::Move,3,3);});
    deny([&]{return h.handle(MixedKind::Withdraw,3,30);});
    auto peer=h.peer;h.open();auto rows=h.f.rows();h.peer->scene++;auto result=h.handle(MixedKind::Move,3,4);require(result.rejected&&result.batches.empty()&&h.f.rows()==rows,"NEW0070 different-world rejection disclosed old storage");h.peer=peer;
    h.open();h.peer->account=2;result=h.handle(MixedKind::Move,3,4);require(result.rejected&&result.batches.empty()&&h.f.rows()==rows,"NEW0070 owner-change rejection leaked storage");h.peer=peer;
    h.open();h.peer->ready=false;result=h.handle(MixedKind::Move,3,4);require(result.rejected&&result.batches.empty()&&h.f.rows()==rows,"NEW0070 nonready accepted");h.peer=peer;
    h.open();h.permit=false;result=h.handle(MixedKind::Move,3,4);require(result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 expired permit accepted");h.permit=true;
    h.open();h.service.disconnect(77);result=h.handle(MixedKind::Move,3,4);require(result.rejected&&result.batches.empty()&&h.f.rows()==rows,"NEW0070 disconnected context accepted");
    h.open();const std::array requests{RecoveredBankItems::Request{MixedKind::Move,279,0,3,4,1},RecoveredBankItems::Request{MixedKind::Move,279,0,4,3,1}};result=h.service.handle(77,requests,h.now());require(result.rejected&&h.f.rows()==rows,"NEW0070 multiple batch committed");
    h.open();h.f.sql("UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE slot=44 AND character_id=1");rows=h.f.rows();result=h.handle(MixedKind::Move,3,4);require(result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 stale full optional row accepted");
}
void mixed_late_world_and_preparation(){
    // Actual postwrite live lease callback must execute inside each route's SQL
    // transaction, and rollback both all rows and receipt. Renew failure is
    // independently tested as postCOMMIT success with contextual disconnect.
    for(unsigned route=0;route<4;++route)for(unsigned guard=0;guard<6;++guard){
        MixedHarness h;h.seed(3,0,2);h.seed(1,1,3);h.f.scalar(4,3107,7,3);h.open();auto rows=h.f.rows();const auto before=h.peer;
        h.late=[&]{switch(guard){case 0:h.peer->ready=false;break;case 1:++h.peer->scene;break;case 2:++h.peer->area;break;case 3:++h.peer->account;break;case 4:++h.peer->session;break;case 5:h.permit=false;break;}};
        const auto result=route==0?h.handle(MixedKind::Move,2,3):route==1?h.handle(MixedKind::Withdraw,2,0):route==2?h.handle(MixedKind::Withdraw,3,1):h.handle(MixedKind::Deposit,4,4,2);
        h.late={};h.peer=before;h.permit=true;
        require(h.late_hits>0&&result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 late live peer/ready/lease/world callback failed full rollback");
    }
    for(unsigned route=0;route<4;++route){MixedHarness h;h.seed(3,0,2);h.seed(1,1,3);h.f.scalar(4,3107,7,3);h.f.add(8,1,0xa1,7);h.open();const auto rows=h.f.rows();h.fail_prepare=true;const auto result=route==0?h.handle(MixedKind::Move,2,3):route==1?h.handle(MixedKind::Withdraw,2,0):route==2?h.handle(MixedKind::Withdraw,3,1):h.handle(MixedKind::Deposit,4,4,2);h.fail_prepare=false;require(h.prepare_failures>0&&result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 exact whole reply preparation failed to rollback");}
    MixedHarness h;h.seed(3,0,2);h.seed(1,1,3);h.open();h.throw_renew=true;const auto result=h.handle(MixedKind::Move,2,3);require(result.committed&&!result.rejected&&h.load().base.vault[2].item_id==1001,"NEW0070 postcommit renewal throw reported false rollback");const auto rows=h.f.rows();require(h.handle(MixedKind::Move,2,3).rejected&&h.f.rows()==rows,"NEW0070 renew failed context not disconnected");
}
void mixed_sql_rollback_replay(){
    MixedHarness h;h.fixed_receipt=std::string(64,'a');h.seed(3,0,2);h.fixed_receipt=std::string(64,'b');h.seed(1,1,3);h.fixed_receipt=std::string(64,'c');h.seed(0,4,4);h.fixed_receipt=std::string(64,'d');h.open();require(h.handle(MixedKind::Move,2,3).committed,"NEW0070 fourth ledger seed failed");
    for(char ledger:{'a','b','c','d'})for(unsigned route=0;route<4;++route){h.fixed_receipt=std::string(64,ledger);h.open();const auto rows=h.f.rows();const auto result=route==0?h.handle(MixedKind::Move,2,3):route==1?h.handle(MixedKind::Withdraw,3,0):route==2?h.handle(MixedKind::Withdraw,2,1):h.handle(MixedKind::Withdraw,4,4,2);require(result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 all4 ledger replay route accepted");}h.fixed_receipt.reset();
    // Repository already covers full mutation failures; this service gate
    // independently proves a real executed trigger cannot corrupt untouched
    // equipped/other-owner rows or add a pending battle at postwrite time.
    SqliteRecoveredCharacterRepository chars(h.f.db);const auto resources=chars.commit_resources(1,h.f.ids[0],{},{52,120,2,80,0,"CUSTOM-0012"});
    for(const auto& sql:std::vector<std::string>{
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_mixed_receipts BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE slot=44 AND character_id=NEW.character_id; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_mixed_receipts BEGIN INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(NEW.character_id,"+std::to_string(resources.revision)+",'CUSTOM-0012'); END"
    }){h.f.sql(sql);h.open();const auto rows=h.f.rows();bool executed=false;sqlite3_trace_v2(h.f.db,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&executed);const auto result=h.handle(MixedKind::Move,2,3);sqlite3_trace_v2(h.f.db,0,nullptr,nullptr);require(executed&&result.rejected&&!result.committed&&h.f.rows()==rows,"NEW0070 actual SQL injected typed-storage/battle did not rollback");h.f.sql("DROP TRIGGER injected");}
    chars.reserve_battle(1,h.f.ids[0],resources);h.open();const auto rows=h.f.rows();require(h.handle(MixedKind::Move,2,3).rejected&&h.f.rows()==rows,"NEW0070 existing pending battle accepted");
}
void callback_lifecycle_regression(){
    for(unsigned route=0;route<4;++route){
        MixedHarness h;h.seed(3,0,2);h.seed(1,1,3);h.f.scalar(5,3107,7,3);h.open();const auto before=h.f.rows();
        const auto result=god2_test::bank_revoke_on_receipt(h.f.db,h.service,[&]{return route==0?h.handle(MixedKind::Move,2,3):route==1?h.handle(MixedKind::Withdraw,2,0):route==2?h.handle(MixedKind::Withdraw,3,1):h.handle(MixedKind::Deposit,5,4,2);});
        require(result.rejected&&!result.committed&&result.batches.empty()&&h.f.rows()==before,"Mixed/foreign/armor/plain postwrite callback escaped rollback");
    }
    god2_test::bank_callback_regressions<MixedHarness>([](auto& h){h.f.add(0,1,0xa1,7);h.f.add_armor(4,1001);h.f.scalar(5,3107,7,3);},[](auto& h){return h.f.rows();},[](auto& h){return h.handle(MixedKind::Deposit,5,2,2);});
    MixedHarness h;h.seed(3,0,2);h.seed(1,1,3);const auto before=h.f.rows();unsigned cuts=0;bool refused=false;
    try{h.mixed_repo.commit(std::string(64,'f'),{h.load(),0,2,3,1},[](const auto&){},{},[&]{if(++cuts==2)throw DatabaseError("final current cut");});}catch(const DatabaseError&){refused=true;}
    require(refused&&cuts==2&&h.f.rows()==before,"Mixed final postverify lifecycle cut did not rollback");
}
}
int main(){try{callback_lifecycle_regression();mixed_full_ordered_pairs();mixed_rejections_and_context();mixed_late_world_and_preparation();mixed_sql_rollback_replay();std::cout<<"CUSTOM0070 mixed bank service:36 ordered pairs/6 empty;exact48/full20;old63/64;late leases;all4 receipts;typed rollback PASS\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
