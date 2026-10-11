// NEW isolated service gate; companion uses the complete qualified source
// catalog and CUSTOM_TEST opaque instances. No accepted0067 file is changed.
#define main owned_foreign_repository_companion_main
#include "storage_owned_foreign_bank_0068.cpp"
#undef main
#include "handlers/OwnedForeignBankService.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iomanip>
#include <sstream>

namespace {
using ForeignService=OwnedForeignBankService;
using Kind=RecoveredBankItems::Kind;
struct ServiceHarness {
    Fixture fixture;Repo repository;SqliteOwnedArmorBankRepository armor_repo;SqliteBankItemsRepository plain_repo;
    std::optional<RecoveredBankService::Peer> peer;
    bool permit=true,fail_projection=false;unsigned renews{},serial{},projection_failures{};
    std::optional<std::string> fixed_receipt;
    ForeignService service;
    explicit ServiceHarness(unsigned slots=50,bool file=false):fixture(slots,file),repository(fixture.repo()),
        armor_repo(fixture.db,armor,armor_exact),plain_repo(fixture.db),
        peer(RecoveredBankService::Peer{77,1,fixture.ids[0],1,1,1,1,true}),
        service(repository,armor_repo,plain_repo,[this](auto id){return id==77?peer:std::nullopt;},
            [this](auto,auto target,auto){return permit&&target==279;},[this](auto,auto){++renews;},
            [](const auto& row){return row.item_id==3107&&row.count&&row.source_sha256==SqliteArmorSlotRepository::source_sha256;},
            [this](auto slot,const auto& row){if(fail_projection){++projection_failures;throw DatabaseError("CUSTOM_TEST plain prepare projection failed");}
                RecoveredInventoryProjection::Metadata metadata{};metadata[0]=static_cast<std::uint8_t>(row.item_id);metadata[1]=static_cast<std::uint8_t>(row.item_id>>8);return RecoveredInventoryProjection::encode({slot,row.count,metadata}).value();},
            [this]{if(fixed_receipt)return *fixed_receipt;std::ostringstream out;out<<std::string(56,'d')<<std::hex<<std::setw(8)<<std::setfill('0')<<serial++;return out.str();},
            [this](auto id){if(fail_projection){++projection_failures;throw DatabaseError("CUSTOM_TEST full prepare projection failed");}return fixture.definitions.contains(id);}){fixture.install();}
    static auto now(){return ForeignService::Clock::now();}
    auto open(){return service.open(77,279,now());}
    auto handle(Kind kind,std::uint8_t source,std::uint8_t destination,std::uint8_t quantity=1,std::uint8_t page=0,std::uint16_t target=279){const std::array requests{RecoveredBankItems::Request{kind,target,page,source,destination,quantity}};return service.handle(77,requests,now());}
};
std::vector<std::uint8_t> service_flatten(const ForeignService::Batches& batches){std::vector<std::uint8_t> bytes;for(const auto& batch:batches){require(!batch.empty()&&batch.size()<=RecoveredWorldFrame::max_logical_size,"Foreign service response frame exceeds native bound");bytes.insert(bytes.end(),batch.begin(),batch.end());}return bytes;}
std::vector<std::uint8_t> service_bank_record(std::uint8_t slot,std::uint8_t count,const std::array<std::uint8_t,20>& bytes){const auto record=RecoveredBankItems::slot(0,slot,count,bytes).value();return {record.begin(),record.end()};}
void service_append(std::vector<std::uint8_t>& target,const std::vector<std::uint8_t>& bytes){target.insert(target.end(),bytes.begin(),bytes.end());}

void service_transport_and_original_routes(){
    ServiceHarness h;auto& f=h.fixture;
    const auto a=f.add(0,1,0xa1,7),same=f.add(1,1,0xb2,11),tw=f.add(2,19001,0xc3,13),gem=f.add(3,16055,0xd4,17);
    f.add_armor(4,1001);f.add_armor(30,1201);f.add(34,2,0xe5,21);f.add(0,16055,0xf6,9,1);f.scalar(5,3107,127,3);
    const auto other=f.load(1);const auto money=dump(f.db,"SELECT * FROM foreign_bank_test_money ORDER BY character_id");
    auto opened=service_flatten(h.open());require(opened.size()==300*29,"Foreign service open requires all300 original48 records");
    auto result=h.handle(Kind::Deposit,0,2);require(result.committed&&!result.rejected,"WPN1 native63 service did not commit");
    auto expected=service_bank_record(2,1,a);service_append(expected,RecoveredInventoryProjection::encode({0,0,{}}).value());require(service_flatten(result.batches)==expected,"WPN1 deposit flattened full20 or wrong native48/3B41");
    require(h.handle(Kind::Deposit,1,3).committed,"Same-ID second WPN1 deposit failed");const auto before=f.load();
    result=h.handle(Kind::Move,2,3);expected=service_bank_record(2,1,same);service_append(expected,service_bank_record(3,1,a));require(result.committed&&service_flatten(result.batches)==expected,"Same-ID native65 service lost distinct full20");
    const auto swapped=f.load();require(foreign(swapped,2).revision==before.base.vault[2].revision+1&&foreign(swapped,3).revision==before.base.vault[3].revision+1,"Same-ID native65 did not increment physical revisions");
    require(h.handle(Kind::Deposit,2,4).committed&&h.handle(Kind::Deposit,3,5).committed,"TWP25/Gem8 native63 failed");
    result=h.handle(Kind::Move,4,5);expected=service_bank_record(4,1,gem);service_append(expected,service_bank_record(5,1,tw));require(result.committed&&service_flatten(result.batches)==expected,"Cross foreign native65 lost weapon/gem20");
    opened=service_flatten(h.open());require(std::equal(gem.begin(),gem.end(),opened.begin()+4*29+9)&&std::equal(tw.begin(),tw.end(),opened.begin()+5*29+9),"Full300 reopen did not preserve TWP/Gem opaque20");
    for(const auto pair:{std::pair{2u,0u},std::pair{3u,1u},std::pair{4u,3u},std::pair{5u,2u}}){const auto bytes=foreign(f.load(),pair.first).logical20;result=h.handle(Kind::Withdraw,static_cast<std::uint8_t>(pair.first),static_cast<std::uint8_t>(pair.second));expected=service_bank_record(static_cast<std::uint8_t>(pair.first),0,{});service_append(expected,RecoveredInventoryProjection::encode({static_cast<std::uint8_t>(pair.second),1,bytes}).value());require(result.committed&&service_flatten(result.batches)==expected,"Foreign native64 did not restore exact instance/native3B41");}
    const auto restored=f.load();require(restored.base.bag.weapons[0].logical20==same&&restored.base.bag.weapons[1].logical20==a&&restored.base.bag.weapons[2].logical20==tw&&restored.base.bag.gems[0].logical20==gem,"Foreign service ownership restore lost full20");
    require(h.handle(Kind::Deposit,4,6).committed,"Original armor63 route no longer works");
    const auto foreign_before=f.load();require(h.handle(Kind::Deposit,5,7,7).committed&&h.handle(Kind::Withdraw,7,6,2).committed,"Original MED partial63/64 route changed");
    require(h.handle(Kind::Withdraw,6,4).committed,"Original armor64 route changed");const auto after=f.load();
    require(after.base.bag.weapons==foreign_before.base.bag.weapons&&after.base.bag.gems==foreign_before.base.bag.gems&&after.base.bag.scalar[34]==restored.base.bag.scalar[34]&&after.base.bag.armor.size()==2&&after.base.bag.armor[1]==restored.base.bag.armor[1]&&after.base.bag.armor[0].logical20==restored.base.bag.armor[0].logical20&&after.base.bag.armor[0].revision==restored.base.bag.armor[0].revision+2&&after.base.bag.scalar[5]->count==120&&after.base.bag.scalar[6]->count==2&&after.base.vault[7].count==5,"Armor/MED routing changed foreign/equipment/quantity state");
    require(f.load(1)==other&&dump(f.db,"SELECT * FROM foreign_bank_test_money ORDER BY character_id")==money&&h.renews==14,"Foreign service changed other owner/money or renewal count");
}

void service_empty_tail_destination_regression(){
    for(unsigned route:{0u,1u,2u}){
        ServiceHarness h;auto& f=h.fixture;
        if(route==0)f.add(0,1,0xa1,7);
        else if(route==1)f.add_armor(0,1001);
        else f.scalar(0,3107,7,3);
        h.open();require(h.handle(Kind::Deposit,0,2,route==2?2:1).committed,"Empty-tail regression deposit failed");
        std::array<std::uint8_t,20> tail{};tail[2]=0xc1;tail[19]=0x7f;
        sqlite_detail::Statement insert(f.db,"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,1,'EMPTY_SLOT_POLICY','CUSTOM_TEST opaque empty destination29',?,?,'CUSTOM-0046')");
        insert.bind_id(1,f.ids[0]);insert.bind(2,29);insert.bind_blob(3,tail);insert.bind(4,SqliteWeaponSlotRepository::source_sha256);insert.bind(5,SqliteWeaponSlotRepository::client_sha256);insert.done();
        const auto before=f.load();const auto other=f.load(1);
        require(before.base.bag.scalar[29]->count==0&&std::any_of(before.base.bag.weapons.begin(),before.base.bag.weapons.end(),[&](const auto& item){return item.slot==29&&item.origin=="EMPTY_SLOT_POLICY"&&item.logical20==tail;}),"Opaque empty-tail fixture not read by real repository");
        h.open(); // Refresh the real context after explicit isolated fixture insertion.
        const auto result=h.handle(Kind::Withdraw,2,29);
        require(result.committed&&!result.rejected,"EMPTY_SLOT_POLICY tail falsely classified occupied for foreign/armor/MED withdrawal");
        const auto after=f.load();require(after.base.bag.scalar[29]->count==1&&after.base.bag.scalar[29]->revision==2&&f.load(1)==other,"Empty-tail destination scalar/peer conservation failed");
        if(route==0){require(std::any_of(after.base.bag.weapons.begin(),after.base.bag.weapons.end(),[&](const auto& item){return item.slot==29&&item.logical20[19]==0xa1&&item.origin=="CUSTOM_TEST_NOT_NATIVE";}),"Foreign withdrawal failed to replace empty tail with owned full20");}
        else {require(std::none_of(after.base.bag.weapons.begin(),after.base.bag.weapons.end(),[](const auto& item){return item.slot==29&&item.origin=="EMPTY_SLOT_POLICY";}),"Original trigger failed to retire EMPTY_SLOT_POLICY metadata");}
    }
}

void service_access_and_cross_refusal(){
    ServiceHarness h(30,true);auto& f=h.fixture;f.add(0,19001,0xa1,7);f.add_armor(4,1001);f.scalar(5,3107,7,3);h.open();
    require(h.handle(Kind::Deposit,0,2).committed&&h.handle(Kind::Deposit,4,3).committed&&h.handle(Kind::Deposit,5,4,2).committed,"Cross route refusal seeds failed");
    auto denied=[&](auto call){h.open();const auto rows=f.rows();const auto result=call();require(result.rejected&&!result.committed&&f.rows()==rows,"Foreign service refused operation changed saved state");};
    for(const auto pair:{std::pair{2,3},std::pair{3,2},std::pair{2,4},std::pair{4,2}})denied([&]{return h.handle(Kind::Move,static_cast<std::uint8_t>(pair.first),static_cast<std::uint8_t>(pair.second));});
    denied([&]{return h.handle(Kind::Withdraw,2,30);});denied([&]{return h.handle(Kind::Withdraw,2,0,2);});denied([&]{return h.handle(Kind::Withdraw,2,0,1,3);});denied([&]{return h.handle(Kind::Withdraw,2,0,1,0,280);});
    h.open();auto rows=f.rows();h.peer->account=2;auto result=h.handle(Kind::Withdraw,2,0);require(result.rejected&&!result.committed&&result.batches.empty()&&f.rows()==rows,"Foreign owner change disclosed/mutated old inventory");h.peer->account=1;
    h.open();h.permit=false;result=h.handle(Kind::Withdraw,2,0);require(result.rejected&&!result.committed&&f.rows()==rows,"Foreign expired lease committed");h.permit=true;
    h.open();h.service.disconnect(77);result=h.handle(Kind::Withdraw,2,0);require(result.rejected&&result.batches.empty()&&f.rows()==rows,"Foreign disconnected context accepted");
    h.open();const std::array requests{RecoveredBankItems::Request{Kind::Withdraw,279,0,2,0,1},RecoveredBankItems::Request{Kind::Withdraw,279,0,2,1,1}};result=h.service.handle(77,requests,h.now());require(result.rejected&&!result.committed&&f.rows()==rows,"Foreign mixed request batch committed");
    h.open();f.sql("INSERT INTO diagnostic_inventory_slots VALUES(1,44,0,0,1,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','CUSTOM-0015')");rows=f.rows();result=h.handle(Kind::Withdraw,2,0);require(result.rejected&&!result.committed&&f.rows()==rows,"Foreign stale optional-row CAS committed");
}

void service_receipts_preparation_and_real_triggers(){
    ServiceHarness h;auto& f=h.fixture;f.add(0,1,0xa1,7);f.add_armor(4,1001);f.scalar(5,3107,7,3);
    h.fixed_receipt=std::string(64,'a');h.open();require(h.handle(Kind::Deposit,0,2).committed,"Foreign ledger seed failed");
    h.fixed_receipt=std::string(64,'b');h.open();require(h.handle(Kind::Deposit,4,3).committed,"Armor ledger seed failed");
    h.fixed_receipt=std::string(64,'c');h.open();require(h.handle(Kind::Deposit,5,4,2).committed,"MED ledger seed failed");
    for(char ledger:{'a','b','c'})for(unsigned route:{0u,1u,2u}){h.fixed_receipt=std::string(64,ledger);h.open();const auto rows=f.rows();const auto result=route==0?h.handle(Kind::Withdraw,2,0):route==1?h.handle(Kind::Withdraw,3,4):h.handle(Kind::Deposit,5,6);require(result.rejected&&!result.committed&&f.rows()==rows,"All3 receipt ledger replay through service committed");}h.fixed_receipt.reset();
    for(unsigned route:{0u,1u,2u}){h.open();const auto rows=f.rows();const auto failures=h.projection_failures;h.fail_projection=true;const auto result=route==0?h.handle(Kind::Withdraw,2,0):route==1?h.handle(Kind::Withdraw,3,4):h.handle(Kind::Deposit,5,6);h.fail_projection=false;require(result.rejected&&!result.committed&&result.batches.empty()&&f.rows()==rows&&h.projection_failures>failures,"Service prepare failure was skipped or changed storage");}
    const auto other=f.load(1);
    // Actual committed SQL attempts modify a valid unrelated tail byte. The
    // trigger must run AND perform the UPDATE before complete proof rolls back.
    for(bool med:{false,true}){
        f.sql(std::string("CREATE TRIGGER injected AFTER INSERT ON ")+(med?"character_bank_item_receipts":"character_bank_armor_receipts")+" BEGIN UPDATE character_bank_foreign_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE character_id=NEW.character_id AND slot=2; END");
        h.open();const auto rows=f.rows();struct Proof {bool triggered=false,updated=false;} proof;
        sqlite3_trace_v2(f.db,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))static_cast<Proof*>(context)->triggered=true;return 0;},&proof);
        sqlite3_update_hook(f.db,[](void* context,int operation,const char*,const char* table,sqlite3_int64){if(operation==SQLITE_UPDATE&&std::strcmp(table,"character_bank_foreign_metadata")==0)static_cast<Proof*>(context)->updated=true;},&proof);
        const auto result=med?h.handle(Kind::Deposit,5,6):h.handle(Kind::Withdraw,3,4);
        sqlite3_trace_v2(f.db,0,nullptr,nullptr);sqlite3_update_hook(f.db,nullptr,nullptr);
        require(proof.triggered&&proof.updated&&result.rejected&&!result.committed&&f.rows()==rows&&f.load(1)==other,"Armor/MED actual unrelated foreign20 trigger was skipped or failed full rollback");f.sql("DROP TRIGGER injected");
    }
    const std::array ledgers{std::pair{"character_bank_foreign_receipts","CUSTOM-0068"},std::pair{"character_bank_armor_receipts","CUSTOM-0067"},std::pair{"character_bank_item_receipts","CUSTOM-0065"}};
    for(unsigned route=0;route<3;++route)for(unsigned destination=0;destination<3;++destination){if(route==destination)continue;
        f.sql(std::string("CREATE TRIGGER injected AFTER INSERT ON ")+ledgers[route].first+" BEGIN INSERT INTO "+ledgers[destination].first+" VALUES(NEW.receipt,NEW.account_id,NEW.character_id,NEW.operation,NEW.page,NEW.source,NEW.destination,1,'late','late','"+ledgers[destination].second+"'); END");h.open();const auto rows=f.rows();bool triggered=false;
        sqlite3_trace_v2(f.db,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&triggered);
        const auto result=route==0?h.handle(Kind::Withdraw,2,0):route==1?h.handle(Kind::Withdraw,3,4):h.handle(Kind::Deposit,5,6);sqlite3_trace_v2(f.db,0,nullptr,nullptr);
        require(triggered&&result.rejected&&!result.committed&&f.rows()==rows,"Service late cross-ledger insertion skipped or committed");f.sql("DROP TRIGGER injected");
    }
}
}
int main(){try{service_transport_and_original_routes();service_empty_tail_destination_regression();service_access_and_cross_refusal();service_receipts_preparation_and_real_triggers();std::cout<<"PASS CUSTOM0068 unified foreign bank service: qualified WPN1/TWP25/Gem8 exact48/3B41 full20 custody, same-ID distinct-tail65, armor/MED original routes, owner/lease/disconnect/batch/sparse-CAS, 9 all3-ledger replays, 3 preparation failures, actual armor/MED SQL UPDATE triggers and6 late cross-ledger rollback; no live activation/grants/stat formula\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
