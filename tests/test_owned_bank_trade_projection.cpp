#include "handlers/OwnedBagProjectionService.h"
#include "handlers/RecoveredTradeService.h"
#include "handlers/RecoveredBankItemsService.h"
#include "db/SqliteMigrationManager.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
namespace {
void require(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
template<class F>void rejects(F&& run){try{run();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected rejection");}
// Synthetic owned instances exercise routes/CAS only, not native grants/maps.
std::optional<std::uint8_t> armor(std::uint16_t item){return item==60011?std::optional<std::uint8_t>(30):std::nullopt;}
bool weapon(std::uint16_t item){return item==60010;}
bool eligible(const StoredInventorySlot& item){return item.item_id==3107&&item.count&&item.source_sha256==SqliteArmorSlotRepository::source_sha256;}
std::vector<std::uint8_t> plain(std::uint8_t slot,const StoredInventorySlot& item){
    if(item.count&&!eligible(item))throw DatabaseError("Original scalar projection category denied");
    RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(item.item_id);bytes[1]=static_cast<std::uint8_t>(item.item_id>>8);return RecoveredInventoryProjection::encode({slot,item.count,bytes}).value();
}
bool contains(const std::vector<std::uint8_t>& bytes,const std::vector<std::uint8_t>& expected){return std::search(bytes.begin(),bytes.end(),expected.begin(),expected.end())!=bytes.end();}
struct Fixture {
    sqlite3* raw{};std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db{nullptr,sqlite3_close_v2};std::array<std::uint64_t,2> ids{};
    std::unique_ptr<SqliteTradeRepository> trades;std::unique_ptr<SqliteBankItemsRepository> banks;std::unique_ptr<OwnedBagProjectionService> projector;
    std::vector<std::string> trace;unsigned receipt{};
    Fixture(){require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);sql("PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'adapter-a','hash'),(2,'adapter-b','hash')");SqliteRecoveredCharacterRepository characters(raw);
        trades=std::make_unique<SqliteTradeRepository>(raw);trades->install_schema();banks=std::make_unique<SqliteBankItemsRepository>(raw);banks->install_schema();
        for(unsigned n=0;n<2;++n){std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);ids[n]=characters.create(n+1,profile).id;
            for(unsigned slot=0;slot<50;++slot){sqlite_detail::Statement insert(raw,"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,ids[n]);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}
            scalar(n,5,3107,7,3);instance(n,10,60010,static_cast<std::uint8_t>(0xa1+n));instance(n,11,60011,static_cast<std::uint8_t>(0xb1+n));instance(n,12,16055,static_cast<std::uint8_t>(0xc1+n));instance(n,34,60010,static_cast<std::uint8_t>(0xd1+n));trades->provision_wallet(n+1,ids[n]);banks->provision_empty(n+1,ids[n]);}
        sql("UPDATE character_trade_wallets SET amount=500");projector=std::make_unique<OwnedBagProjectionService>(raw,armor,weapon,plain);
    }
    void sql(const std::string& query){sqlite_detail::execute(raw,query);}
    void scalar(unsigned owner,unsigned slot,std::uint16_t item,unsigned count,std::uint64_t revision){sqlite_detail::Statement write(raw,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=?");write.bind(1,item);write.bind(2,count);write.bind_id(3,revision);write.bind_id(4,ids[owner]);write.bind(5,slot);write.done();}
    void instance(unsigned owner,unsigned slot,std::uint16_t item,std::uint8_t fill){
        scalar(owner,slot,item,1,7);RecoveredInventoryProjection::Metadata bytes;bytes.fill(fill);bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);const bool a=item==60011,g=item==16055;bytes[2]=static_cast<std::uint8_t>((bytes[2]&0xc0u)|(a?2u:g?8u:1u));if(g)bytes[3]=6;
        sqlite_detail::Statement insert(raw,g?"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter',?,'CUSTOM-0057')":a?"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter',?,?,'CUSTOM-0066')":"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter',?,?,'CUSTOM-0046')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind(4,SqliteArmorSlotRepository::source_sha256);if(!g)insert.bind(5,a?SqliteArmorSlotRepository::client_sha256:SqliteWeaponSlotRepository::client_sha256);insert.done();
    }
    std::string next_receipt(){return std::string(63,'0')+"123456789abcdef"[receipt++];}
    auto owned(){return [this](std::uint64_t account,std::uint64_t character,std::uint8_t slot,const StoredInventorySlot& before,const StoredInventorySlot& after){trace.push_back("projection");return before==after?projector->project(account,character,slot,before):projector->project_planned(account,character,slot,before,after);};}
    static auto changes(const auto& before,const auto& after){std::vector<OwnedBagProjectionService::ScalarChange> changed;for(std::uint8_t slot=0;slot<30;++slot)if(before.bag[slot]!=after.bag[slot])changed.push_back({slot,before.bag[slot],after.bag[slot]});return changed;}
    SqliteTradeRepository::PrepareProof trade_proof(){return [this](const auto& before,const auto& after){require(sqlite3_get_autocommit(raw)!=0,"Proof factory was not before BEGIN");trace.push_back("capture");
        const auto a=projector->capture_proof(before[0].account,before[0].character),b=projector->capture_proof(before[1].account,before[1].character);const auto ca=changes(before[0],after.sides[0]),cb=changes(before[1],after.sides[1]);
        return SqliteTradeRepository::CommitProof{[this,a,b]{trace.push_back("pre");projector->verify_proof_in_transaction(a);projector->verify_proof_in_transaction(b);},[this,a,b,ca,cb]{trace.push_back("post");projector->verify_planned_in_transaction(a,ca);projector->verify_planned_in_transaction(b,cb);}};};}
    SqliteBankItemsRepository::PrepareProof bank_proof(){return [this](const auto& before,const auto& after){require(sqlite3_get_autocommit(raw)!=0,"Proof factory was not before BEGIN");trace.push_back("capture");const auto proof=projector->capture_proof(before.account,before.character);const auto changed=changes(before,after);
        return SqliteBankItemsRepository::CommitProof{[this,proof]{trace.push_back("pre");projector->verify_proof_in_transaction(proof);},[this,proof,changed]{trace.push_back("post");projector->verify_planned_in_transaction(proof,changed);}};};}
    std::unique_ptr<RecoveredTradeService> trade_service(){return std::make_unique<RecoveredTradeService>(*trades,[this](auto session)->std::optional<RecoveredTradeService::Peer>{if(session<1||session>2)return {};return RecoveredTradeService::Peer{session,session,ids[session-1],4,3,true};},[this](std::uint16_t character)->std::optional<RecoveredTradeService::Peer>{for(unsigned n=0;n<2;++n)if(ids[n]==character)return RecoveredTradeService::Peer{n+1,n+1,ids[n],4,3,true};return {};},[](const auto&,const auto& actor){RecoveredTrade::Name name{};name[0]=static_cast<std::uint8_t>('A'+actor.account);return name;},eligible,plain,[this]{return next_receipt();},owned(),trade_proof());}
    std::unique_ptr<RecoveredBankItemsService> bank_service(){return std::make_unique<RecoveredBankItemsService>(*banks,[this](auto session)->std::optional<RecoveredBankService::Peer>{if(session<1||session>2)return {};return RecoveredBankService::Peer{session,session,ids[session-1],4,3,50,50,true};},[](auto,std::uint16_t target,auto){return target==531;},[](auto,auto){},eligible,plain,[this]{return next_receipt();},owned(),bank_proof());}
    auto proof(unsigned n){return projector->capture_proof(n+1,ids[n]);}
    void check_render(unsigned n,const std::vector<std::uint8_t>& logical){const auto saved=trades->load(n+1,ids[n]);for(std::uint8_t slot=10;slot<=12;++slot)require(contains(logical,projector->project(n+1,ids[n],slot,saved.bag[slot])),"Actual service reply flattened/lost another owner's full instance");}
    std::uint64_t receipts(const char* table){sqlite_detail::Statement read(raw,(std::string("SELECT count(*) FROM ")+table).c_str());require(read.row(),"Count missing");return read.number<std::uint64_t>(0);}
};
using K=RecoveredTrade::Kind;using R=RecoveredTrade::Request;
RecoveredTradeService::Result act(RecoveredTradeService& service,std::uint64_t session,std::initializer_list<R> records){const std::vector<R> copied(records);return service.handle(session,copied,RecoveredTradeService::Clock::now());}
R open(std::uint64_t target){R r{K::Open};r.target=static_cast<std::uint16_t>(target);return r;}
R item(std::uint64_t target,std::uint8_t quantity=3,std::uint8_t slot=5,std::uint16_t key=3107){R r{K::OfferItem};r.target=static_cast<std::uint16_t>(target);r.quantity=quantity;r.slot=slot;r.item=key;return r;}
R money(std::uint64_t target,std::uint32_t amount){R r{K::OfferMoney};r.target=static_cast<std::uint16_t>(target);r.money=amount;return r;}
void start_exchange(Fixture& f,RecoveredTradeService& service){require(!act(service,1,{open(f.ids[1])}).rejected,"Owner-aware trade did not open");require(!act(service,1,{item(f.ids[1])}).rejected,"MED offer denied");require(!act(service,2,{item(f.ids[0],2)}).rejected,"Other MED offer denied");require(!act(service,1,{money(f.ids[1],100),R{K::Confirm}}).rejected,"Money+confirm denied");}
void trade_routes(){Fixture f;auto service=f.trade_service();const auto initial0=f.proof(0),initial1=f.proof(1);
    require(!act(*service,1,{open(f.ids[1])}).rejected,"Open failed with full weapon/armor/gem");const auto cancelled=act(*service,2,{R{K::Cancel}});require(cancelled.deliveries.size()==2,"Cancel did not restore both owners");f.check_render(0,cancelled.deliveries.at(1));f.check_render(1,cancelled.deliveries.at(2));
    require(f.proof(0).snapshot()==initial0.snapshot()&&f.proof(1).snapshot()==initial1.snapshot(),"Read/open/cancel mutated instances");
    require(!act(*service,1,{open(f.ids[1])}).rejected,"Second open failed");const auto denied=act(*service,1,{item(f.ids[1],1,11,60011)});require(denied.rejected,"Rendering armor broadened trade eligibility");f.check_render(0,denied.deliveries.at(1));f.check_render(1,denied.deliveries.at(2));
    f.trace.clear();start_exchange(f,*service);const auto committed=act(*service,2,{money(f.ids[0],20),R{K::Confirm}});require(committed.committed&&!committed.rejected,"Actual MED+money settlement failed");f.check_render(0,committed.deliveries.at(1));f.check_render(1,committed.deliveries.at(2));
    const auto a=f.trades->load(1,f.ids[0]),b=f.trades->load(2,f.ids[1]);require(a.wallet.amount==420&&b.wallet.amount==580&&a.bag[5].count==4&&b.bag[5].count==5&&a.bag[0].count==2&&b.bag[0].count==3,"Settlement changed original scalar/money rules");
    const auto after0=f.proof(0),after1=f.proof(1);require(after0.snapshot().armor==initial0.snapshot().armor&&after0.snapshot().weapons==initial0.snapshot().weapons&&after0.snapshot().gems==initial0.snapshot().gems&&after1.snapshot().armor==initial1.snapshot().armor&&after1.snapshot().weapons==initial1.snapshot().weapons&&after1.snapshot().gems==initial1.snapshot().gems,"Trade moved/changed unoffered full instances");
    const auto capture=std::find(f.trace.begin(),f.trace.end(),"capture"),pre=std::find(f.trace.begin(),f.trace.end(),"pre"),post=std::find(f.trace.begin(),f.trace.end(),"post");require(capture<pre&&pre<post&&std::find(capture,pre,"projection")!=pre,"Immutable proof was not captured before planned reply/BEGIN");
}
void bank_routes(){Fixture f;auto service=f.bank_service();const auto initial0=f.proof(0),initial1=f.proof(1);const auto now=RecoveredBankItemsService::Clock::now();
    for(std::uint64_t session=1;session<=2;++session){service->open(session,531,now);const std::array<RecoveredBankItems::Request,1> bad{{{RecoveredBankItems::Kind::Deposit,531,0,11,2,1}}};const auto rejected=service->handle(session,bad,now);require(rejected.rejected&&!rejected.committed,"Armor became bank eligible");std::vector<std::uint8_t> logical;for(const auto& batch:rejected.batches)logical.insert(logical.end(),batch.begin(),batch.end());f.check_render(static_cast<unsigned>(session-1),logical);}
    require(f.proof(0).snapshot()==initial0.snapshot()&&f.proof(1).snapshot()==initial1.snapshot(),"Bank rejection changed either full owner");
    service->open(1,531,now);const std::array<RecoveredBankItems::Request,1> deposit{{{RecoveredBankItems::Kind::Deposit,531,0,5,2,3}}};require(service->handle(1,deposit,now).committed,"Owned adapter blocked normal scalar deposit");
    const std::array<RecoveredBankItems::Request,1> withdrawal{{{RecoveredBankItems::Kind::Withdraw,531,0,2,1,1}}};require(service->handle(1,withdrawal,now).committed,"Owned adapter blocked normal scalar withdrawal");const auto saved=f.banks->load(1,f.ids[0]);require(saved.bag[5].count==4&&saved.bag[1].count==1&&saved.vault[2].count==2,"Bank scalar quantities changed");require(f.proof(1).snapshot()==initial1.snapshot(),"Bank changed another player");
}
void trade_trigger_rollback(){Fixture f;auto service=f.trade_service();const auto owner0=f.proof(0),owner1=f.proof(1);const auto before0=f.trades->load(1,f.ids[0]),before1=f.trades->load(2,f.ids[1]);
    f.sql("CREATE TRIGGER corrupt AFTER INSERT ON character_trade_receipts BEGIN UPDATE character_weapon_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE slot=34;END");start_exchange(f,*service);const auto changes=sqlite3_total_changes(f.raw);const auto failed=act(*service,2,{money(f.ids[0],20),R{K::Confirm}});
    require(failed.rejected&&!failed.committed&&sqlite3_total_changes(f.raw)>changes+2&&f.receipts("character_trade_receipts")==0,"Trade receipt trigger was not rejected inside transaction");require(f.trades->load(1,f.ids[0])==before0&&f.trades->load(2,f.ids[1])==before1&&f.proof(0).snapshot()==owner0.snapshot()&&f.proof(1).snapshot()==owner1.snapshot(),"Postwrite proof failed to rollback both wallets/bags/full instances");f.check_render(0,failed.deliveries.at(1));f.check_render(1,failed.deliveries.at(2));require(std::find(f.trace.begin(),f.trace.end(),"post")!=f.trace.end(),"Trade postwrite check was not executed");
}
void bank_vault_trigger_rollback(){Fixture f;const auto owner0=f.proof(0),owner1=f.proof(1);f.sql("UPDATE character_bank_item_slots SET item_id=3107,count=slot+1,revision=slot+1,source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731' WHERE character_id=1 AND slot IN (2,3)");const auto bank_before=f.banks->load(1,f.ids[0]);auto service=f.bank_service();const auto now=RecoveredBankItemsService::Clock::now();service->open(1,531,now);
    f.sql("CREATE TRIGGER corrupt AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_weapon_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE slot=34;END");const auto changes=sqlite3_total_changes(f.raw);const std::array<RecoveredBankItems::Request,1> move{{{RecoveredBankItems::Kind::Move,531,0,2,3,1}}};const auto failed=service->handle(1,move,now);
    require(failed.rejected&&!failed.committed&&sqlite3_total_changes(f.raw)>changes+2&&f.receipts("character_bank_item_receipts")==0,"Vault-only65 did not enforce postwrite full-instance proof");require(f.banks->load(1,f.ids[0])==bank_before&&f.proof(0).snapshot()==owner0.snapshot()&&f.proof(1).snapshot()==owner1.snapshot(),"Bank trigger did not rollback both full owners plus vault/receipt");
}
void final_readback_after_callback(){Fixture f;const auto a=f.trades->load(1,f.ids[0]),b=f.trades->load(2,f.ids[1]);bool post=false;
    const std::array<SqliteTradeRepository::Side,2> sides{{{a,{},10},{b,{},20}}};const SqliteTradeRepository::CommitProof proof{[&]{require(sqlite3_get_autocommit(f.raw)==0,"Trade precheck was outside transaction");},[&]{f.sql("UPDATE character_trade_receipts SET first_character=2,second_character=1");post=true;}};
    rejects([&]{f.trades->commit(std::string(64,'a'),sides,proof);});require(post&&f.trades->load(1,f.ids[0])==a&&f.trades->load(2,f.ids[1])==b&&f.receipts("character_trade_receipts")==0,"Trade failed to reread receipt after post callback or rollback wallets");
    const auto bank=f.banks->load(1,f.ids[0]);const SqliteBankItemsRepository::Request deposit{bank,SqliteBankItemsRepository::Operation::Deposit,0,5,2,3};post=false;const SqliteBankItemsRepository::CommitProof bank_proof{[&]{require(sqlite3_get_autocommit(f.raw)==0,"Bank precheck was outside transaction");},[&]{f.sql("UPDATE character_bank_item_receipts SET quantity=1");post=true;}};
    rejects([&]{f.banks->commit(std::string(64,'b'),deposit,bank_proof);});require(post&&f.banks->load(1,f.ids[0])==bank&&f.receipts("character_bank_item_receipts")==0,"Bank failed to reread receipt after post callback or rollback330 cells");
    rejects([&]{f.trades->prepare_proof({a,b},SqliteTradeRepository::plan(sides),[](const auto&,const auto&){return SqliteTradeRepository::CommitProof{};});});
}
// Source regressions only in PHASE1: no fixture/test was executed.
void bank_callback_lifecycle(){
    using B=RecoveredBankItemsService;using Q=RecoveredBankItems::Request;
    const auto now=B::Clock::now();
    // Every adapter is tested against explicit retirement and caught nested
    // open/handle. A caught inner exception must still poison the outer call.
    for(unsigned lane=0;lane<8;++lane)for(unsigned mode=0;mode<3;++mode){
        Fixture f;std::unique_ptr<B> service;bool armed=false,fired=false;
        const std::array<Q,1> deposit{{{RecoveredBankItems::Kind::Deposit,531,0,5,2,3}}};
        const auto interrupt=[&](unsigned at){if(!armed||fired||at!=lane)return;fired=true;
            if(mode==0)service->disconnect(1);
            else if(mode==1){try{service->open(1,531,now);}catch(const DatabaseError&){}}
            else {try{service->handle(1,deposit,now);}catch(const DatabaseError&){}}
        };
        const auto owned=f.owned();const auto factory=f.bank_proof();
        service=std::make_unique<B>(*f.banks,[&](auto session)->std::optional<RecoveredBankService::Peer>{interrupt(0);return RecoveredBankService::Peer{session,1,f.ids[0],4,3,50,50,true};},
            [&](auto,auto,auto){interrupt(1);return true;},[](auto,auto){},
            [&](const auto& slot){interrupt(2);return eligible(slot);},plain,
            [&]{interrupt(4);return f.next_receipt();},
            [&](auto a,auto c,auto slot,const auto& before,const auto& after){interrupt(3);return owned(a,c,slot,before,after);},
            [&](const auto& before,const auto& after){interrupt(5);auto proof=factory(before,after);
                return SqliteBankItemsRepository::CommitProof{
                    [&,check=proof.before_write]{interrupt(6);check();},
                    [&,check=proof.after_write]{interrupt(7);check();}};});
        service->open(1,531,now);const auto before=f.banks->load(1,f.ids[0]),other=f.banks->load(2,f.ids[1]);
        const auto owner=f.proof(0).snapshot();armed=true;const auto rejected=service->handle(1,deposit,now);armed=false;
        require(fired&&rejected.rejected&&!rejected.committed&&rejected.batches.empty(),"Revoked bank callback continued transfer/reply");
        require(f.banks->load(1,f.ids[0])==before&&f.banks->load(2,f.ids[1])==other&&f.proof(0).snapshot()==owner&&f.receipts("character_bank_item_receipts")==0,
            "Bank callback rejection did not rollback cells/receipt/full metadata");
        require(service->handle(1,deposit,now).rejected,"Revoked bank lease survived");
        service->open(1,531,now);require(service->handle(1,deposit,now).committed,"Fresh explicit open failed after callback retirement");
    }
    // Renewal occurs after durable commit. Its exception cannot reverse the
    // receipt result or retain the previous lease; response was prepared first.
    {Fixture f;B service(*f.banks,[&](auto session)->std::optional<RecoveredBankService::Peer>{return RecoveredBankService::Peer{session,1,f.ids[0],4,3,50,50,true};},
        [](auto,auto,auto){return true;},[](auto,auto){throw std::runtime_error("renew failed");},eligible,plain,[&]{return f.next_receipt();},f.owned(),f.bank_proof());
        service.open(1,531,now);const std::array<Q,1> deposit{{{RecoveredBankItems::Kind::Deposit,531,0,5,2,3}}};const auto done=service.handle(1,deposit,now);
        require(done.committed&&!done.rejected&&!done.batches.empty()&&f.receipts("character_bank_item_receipts")==1&&f.banks->load(1,f.ids[0]).vault[2].count==3,
            "Renewal exception falsely rejected committed transfer");require(service.handle(1,deposit,now).rejected,"Failed renewal retained bank lease");}
    for(unsigned nested=0;nested<2;++nested){Fixture f;std::unique_ptr<B> service;
        service=std::make_unique<B>(*f.banks,[&](auto session)->std::optional<RecoveredBankService::Peer>{return RecoveredBankService::Peer{session,1,f.ids[0],4,3,50,50,true};},
            [](auto,auto,auto){return true;},[&](auto,auto){
                if(!nested)service->disconnect(1);else {try{service->open(1,531,now);}catch(const DatabaseError&){}}
                throw std::runtime_error("renew revoked and failed");},eligible,plain,[&]{return f.next_receipt();},f.owned(),f.bank_proof());
        service->open(1,531,now);const std::array<Q,1> deposit{{{RecoveredBankItems::Kind::Deposit,531,0,5,2,3}}};const auto done=service->handle(1,deposit,now);
        require(done.committed&&!done.rejected&&done.batches.empty()&&f.receipts("character_bank_item_receipts")==1&&f.banks->load(1,f.ids[0]).vault[2].count==3,
            "Revoked renewal published stale owner output or denied committed transfer");require(service->handle(1,deposit,now).rejected,"Revoked renewal retained lease");}
    // The last pure fence follows postproof rereads; no partial write escapes.
    {Fixture f;const auto before=f.banks->load(1,f.ids[0]);bool reached=false;
        const SqliteBankItemsRepository::CommitProof proof{[]{},[]{},[&]{reached=true;throw DatabaseError("late revoke");}};
        rejects([&]{f.banks->commit(std::string(64,'d'),{before,SqliteBankItemsRepository::Operation::Deposit,0,5,2,3},proof);});
        require(reached&&f.banks->load(1,f.ids[0])==before&&f.receipts("character_bank_item_receipts")==0,"Final bank revocation did not rollback durable cells");}
    // Provision is also fenced, including its existing-vault fast path.
    {Fixture f;const auto before=f.banks->load(1,f.ids[0]);bool reached=false;
        rejects([&]{f.banks->provision_empty(1,f.ids[0],[&]{reached=true;throw DatabaseError("provision revoked");});});
        require(reached&&f.banks->load(1,f.ids[0])==before,"Provision bypassed final current check");}
}
}
int main(){try{bank_callback_lifecycle();trade_routes();bank_routes();trade_trigger_rollback();bank_vault_trigger_rollback();final_readback_after_callback();std::cout<<"Actual owner-aware trade/bank full-instance restoration, unchanged scalar eligibility, pre-projection immutable proofs, in-transaction dual-owner trigger rollback and postcallback receipt/scalar readback passed\n";}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
