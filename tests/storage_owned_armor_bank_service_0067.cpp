// Reuse only the isolated companion fixture; no production database or runtime.
#define main owned_armor_storage_companion_main
#include "storage_owned_armor_bank_0067.cpp"
#undef main
#include "handlers/OwnedArmorBankService.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iomanip>
#include <sstream>

namespace {
using Service=OwnedArmorBankService;
struct Harness {
    Fixture fixture;Repo repository;SqliteBankItemsRepository plain_repo;
    std::optional<RecoveredBankService::Peer> peer;
    bool permit=true,fail_projection=false;unsigned renews{},serial{};
    std::optional<std::string> fixed_receipt;
    Service service;
    explicit Harness(unsigned slots=50,bool file=false):fixture(slots,file),repository(fixture.repo()),plain_repo(fixture.raw),
        peer(RecoveredBankService::Peer{77,1,fixture.ids[0],1,1,1,1,true}),
        service(repository,plain_repo,[this](auto session){return session==77?peer:std::nullopt;},[this](auto,auto target,auto){return permit&&target==279;},
            [this](auto,auto){++renews;},[](const auto& row){return row.item_id==3107&&row.count&&row.source_sha256==SqliteArmorSlotRepository::source_sha256;},
            [this](auto slot,const auto& row){if(fail_projection)throw DatabaseError("injected projection failure");RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);return RecoveredInventoryProjection::encode({slot,row.count,bytes}).value();},
            [this]{if(fixed_receipt)return *fixed_receipt;std::ostringstream stream;stream<<std::string(56,'e')<<std::hex<<std::setw(8)<<std::setfill('0')<<serial++;return stream.str();},[](auto key){return key==60010;}){fixture.install();}
    static auto now(){return Service::Clock::now();}
    auto open(){return service.open(77,279,now());}
    auto handle(RecoveredBankItems::Kind kind,std::uint8_t source,std::uint8_t destination,std::uint8_t quantity=1,std::uint8_t page=0,std::uint16_t target=279){const std::array requests{RecoveredBankItems::Request{kind,target,page,source,destination,quantity}};return service.handle(77,requests,now());}
};
std::vector<std::uint8_t> flatten(const Service::Batches& batches){std::vector<std::uint8_t> out;for(const auto& batch:batches){require(!batch.empty()&&batch.size()<=RecoveredWorldFrame::max_logical_size,"Response frame boundary invalid");out.insert(out.end(),batch.begin(),batch.end());}return out;}
std::vector<std::uint8_t> bank_record(std::uint8_t page,std::uint8_t slot,std::uint8_t count,const std::array<std::uint8_t,20>& bytes){const auto record=RecoveredBankItems::slot(page,slot,count,bytes).value();return {record.begin(),record.end()};}
void add(std::vector<std::uint8_t>& target,const std::vector<std::uint8_t>& data){target.insert(target.end(),data.begin(),data.end());}
void unified_full_projection(){
    Harness h;auto& f=h.fixture;f.foreign();const auto a=f.add(0,1001,0xa1,7),b=f.add(1,1001,0xb2,11);f.add(0,1201,0xc3,3,1);f.scalar(5,3107,127,3);f.transfer(f.request(Op::Deposit,0,2));
    h.plain_repo.commit(std::string(64,'c'),{h.plain_repo.load(1,f.ids[0]),Op::Deposit,0,5,3,7});const auto initial=f.load();const auto peer=f.load(1);
    const auto opened=flatten(h.open());require(opened.size()==300*29,"Unified open did not send complete300 native48");require(std::equal(a.begin(),a.end(),opened.begin()+2*29+9),"Unified open flattened armor metadata");
    using K=RecoveredBankItems::Kind;auto result=h.handle(K::Withdraw,2,0);require(result.committed&&!result.rejected,"Armor withdrawal service failed");std::vector<std::uint8_t> expected=bank_record(0,2,0,{});add(expected,RecoveredInventoryProjection::encode({0,1,a}).value());require(flatten(result.batches)==expected,"Armor withdrawal did not send exact48+3B41 full20");
    result=h.handle(K::Deposit,0,2);require(result.committed,"Armor deposit service failed");expected=bank_record(0,2,1,a);add(expected,RecoveredInventoryProjection::encode({0,0,{}}).value());require(flatten(result.batches)==expected,"Armor deposit response wrong");
    require(h.handle(K::Deposit,1,4).committed,"Second same-ID armor deposit failed");result=h.handle(K::Move,2,4);require(result.committed,"Same-ID complete armor service swap failed");expected=bank_record(0,2,1,b);add(expected,bank_record(0,4,1,a));require(flatten(result.batches)==expected,"Native65 same ID lost distinct full20");
    const auto armor=f.load().armor;require(h.handle(K::Deposit,5,5,3).committed,"MED partial deposit in mixed vault failed");require(h.handle(K::Move,5,3).committed,"MED occupied whole swap failed");require(h.handle(K::Withdraw,3,6,2).committed,"MED partial withdrawal failed");const auto after=f.load();require(after.armor==armor&&after.bag.scalar[6]->count==2&&after.vault[3].count==1,"MED changed armor or old quantity semantics");require(after.bag.weapons==initial.bag.weapons&&after.bag.gems==initial.bag.gems&&f.load(1)==peer&&h.renews==7,"Service lost foreign/peer metadata or renewal");
}
void sparse_and_access(){
    Harness h(30,true);auto& f=h.fixture;f.add(0,20001,0xd4,9);h.open();using K=RecoveredBankItems::Kind;require(h.handle(K::Deposit,0,2).committed&&h.handle(K::Withdraw,2,29).committed,"30-only real player service rejected");for(unsigned slot=30;slot<50;++slot)require(!f.load().bag.scalar[slot],"Service provisioned protected rows");
    auto denied=[&](auto call){h.open();const auto rows=f.rows();const auto result=call();require(result.rejected&&!result.committed&&f.rows()==rows,"Service refusal mutated state or claimed success");};
    denied([&]{return h.handle(K::Deposit,29,0);});denied([&]{return h.handle(K::Deposit,29,2,1,3);});denied([&]{return h.handle(K::Deposit,29,2,2);});denied([&]{return h.handle(K::Deposit,29,2,1,0,280);});
    h.open();const auto rows=f.rows();h.peer->account=2;auto result=h.handle(K::Deposit,29,2);require(result.rejected&&!result.committed&&result.batches.empty()&&f.rows()==rows,"Owner change emitted old owner rows");h.peer->account=1;
    h.open();h.permit=false;result=h.handle(K::Deposit,29,2);require(result.rejected&&!result.committed&&f.rows()==rows,"Expired lease committed");h.permit=true;
    h.open();h.service.disconnect(77);result=h.handle(K::Deposit,29,2);require(result.rejected&&result.batches.empty(),"Disconnected session retained context");
    h.open();f.sql("INSERT INTO diagnostic_inventory_slots VALUES(1,44,0,0,1,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','CUSTOM-0015')");const auto changed=f.rows();result=h.handle(K::Deposit,29,2);require(result.rejected&&!result.committed&&f.rows()==changed,"Optional protected CAS lost absence change");
}
void failures_mixed_and_receipts(){
    Harness h;auto& f=h.fixture;f.foreign();f.add(0,1001,0xa1,7);f.scalar(5,3107,7,3);using K=RecoveredBankItems::Kind;
    h.fixed_receipt=std::string(64,'a');h.open();require(h.handle(K::Deposit,0,2).committed,"Armor receipt seed failed");h.open();auto rows=f.rows();auto result=h.handle(K::Deposit,5,3,2);require(result.rejected&&!result.committed&&f.rows()==rows,"Armor receipt replay through MED committed");
    h.fixed_receipt=std::string(64,'b');h.open();require(h.handle(K::Deposit,5,3,2).committed,"MED receipt seed failed");h.open();rows=f.rows();result=h.handle(K::Withdraw,2,0);require(result.rejected&&!result.committed&&f.rows()==rows,"MED receipt replay through armor committed");h.fixed_receipt.reset();
    for(auto pair:{std::pair{2,3},std::pair{3,2}}){h.open();rows=f.rows();result=h.handle(K::Move,static_cast<std::uint8_t>(pair.first),static_cast<std::uint8_t>(pair.second));require(result.rejected&&!result.committed&&f.rows()==rows,"Mixed armor/MED65 committed");}
    h.open();h.fail_projection=true;rows=f.rows();result=h.handle(K::Withdraw,3,6);require(result.rejected&&!result.committed&&result.batches.empty()&&f.rows()==rows,"Prepare failure wrote or emitted success projection");h.fail_projection=false;
    // Corrupt unrelated full armor20 during MED commit, then unrelated scalar
    // during armor commit. Both paths must really execute and rollback.
    for(bool med:{true,false}){f.sql(med?"CREATE TRIGGER injected AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_armor_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB); END":"CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=44; END");h.open();rows=f.rows();bool exercised=false;
        sqlite3_trace_v2(f.raw,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&exercised);
        result=med?h.handle(K::Deposit,5,4):h.handle(K::Withdraw,2,0);sqlite3_trace_v2(f.raw,0,nullptr,nullptr);require(exercised&&result.rejected&&!result.committed&&f.rows()==rows,"Commit trigger was skipped or did not rollback");f.sql("DROP TRIGGER injected");}
    // A late ledger insertion must not defeat the two-way replay guard.
    for(bool med:{true,false}){f.sql(med?"CREATE TRIGGER injected AFTER INSERT ON character_bank_item_receipts BEGIN INSERT INTO character_bank_armor_receipts VALUES(NEW.receipt,NEW.account_id,NEW.character_id,NEW.operation,NEW.page,NEW.source,NEW.destination,1,'late','late','CUSTOM-0067'); END":"CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN INSERT INTO character_bank_item_receipts VALUES(NEW.receipt,NEW.account_id,NEW.character_id,NEW.operation,NEW.page,NEW.source,NEW.destination,NEW.quantity,'late','late','CUSTOM-0065'); END");h.open();rows=f.rows();result=med?h.handle(K::Deposit,5,4):h.handle(K::Withdraw,2,0);require(result.rejected&&!result.committed&&f.rows()==rows,"Late cross-ledger trigger committed");f.sql("DROP TRIGGER injected");}
    SqliteRecoveredCharacterRepository characters(f.raw);const auto resources=characters.commit_resources(1,f.ids[0],{},{52,120,2,80,0,"CUSTOM-0012"});
    for(bool med:{true,false}){const auto sql=std::string("CREATE TRIGGER injected AFTER INSERT ON ")+(med?"character_bank_item_receipts":"character_bank_armor_receipts")+" BEGIN INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(NEW.character_id,"+std::to_string(resources.revision)+",'CUSTOM-0012'); END";f.sql(sql);h.open();rows=f.rows();bool exercised=false;
        sqlite3_trace_v2(f.raw,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&exercised);result=med?h.handle(K::Deposit,5,4):h.handle(K::Withdraw,2,0);sqlite3_trace_v2(f.raw,0,nullptr,nullptr);require(exercised&&result.rejected&&!result.committed&&f.rows()==rows,"Late pending battle trigger was skipped or committed");f.sql("DROP TRIGGER injected");}
    h.open();characters.reserve_battle(1,f.ids[0],resources);rows=f.rows();result=h.handle(K::Withdraw,2,0);require(result.rejected&&!result.committed&&f.rows()==rows,"Pending battle armor service committed");h.open();result=h.handle(K::Deposit,5,4);require(result.rejected&&!result.committed&&f.rows()==rows,"Pending battle MED service committed");
}
void foreign_admission(){
    for(unsigned defect:{0u,1u,2u}){Harness h;auto& f=h.fixture;if(defect==0){f.foreign();f.scalar(10,60011,1,9);f.sql("UPDATE character_weapon_slot_metadata SET logical20=CAST(X'6BEA'||substr(logical20,3) AS BLOB) WHERE character_id=1 AND slot=10");}
        else if(defect==1){f.foreign();f.sql("UPDATE character_teleport_gem_metadata SET metadata20=CAST(substr(metadata20,1,3)||X'00'||substr(metadata20,5) AS BLOB) WHERE character_id=1");}
        else f.scalar(7,60010,1,3);
        const auto before=f.rows();rejects([&]{h.open();});require(f.rows()==before,"Foreign qualification failure changed saved rows");}
}
}
int main(){try{unified_full_projection();sparse_and_access();failures_mixed_and_receipts();foreign_admission();std::cout<<"PASS CUSTOM0067 unified armor bank service: owner-bound full48/3B41, same-ID whole20 swap, mixed-vault MED quantity path, sparse30, foreign instance qualification, context/lease/pending/CAS, two-way receipts, projection failure and actual mutation/late-pending trigger rollback; no schema/grants or live routing\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
