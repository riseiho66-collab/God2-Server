#include "handlers/RecoveredBankService.h"
#include "db/SqliteBankAccessRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>
#include "BankCallbackRegression.h"
using namespace god2;
void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
int main(){try {
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'a','hash'),(2,'b','hash')");
    SqliteRecoveredCharacterRepository characters(raw);std::array<std::uint8_t,40> profile{};profile[0]='A';
    const auto role=characters.create(1,profile);profile[0]='B';const auto other=characters.create(2,profile);
    SqliteTradeRepository trade(raw);trade.install_schema();trade.provision_wallet(1,role.id);trade.provision_wallet(2,other.id);
    SqliteBankRepository bank(raw);bank.install_schema();bank.provision_bank(2,other.id);
    sqlite_detail::execute(raw,"UPDATE character_trade_wallets SET amount=1000 WHERE character_id=1");
    SqliteBankAccessRepository access(raw);access.install_schema();
    const auto row=StoredWorldDisplay{4,3,{0x72,0x13,0x02,0,0,21,0x60,0,0,1,0,0,0,0,0,0,0,0xf8,1,0xfc,0},"ISOLATED_TEST_ONLY","Explicit test fixture, not official banker"};
    SqliteWorldDisplayRepository(raw).insert(row);
    require(!access.lookup(4,3,531,true),"Placement alone granted bank role");
    sqlite_detail::execute(raw,"INSERT INTO world_bank_service_points VALUES(4,3,114,531,'ISOLATED_TEST_ONLY','explicit test banker','CUSTOM-0064')");
    require(!access.lookup(4,3,531) && access.lookup(4,3,531,true).has_value(),"Test banker escaped lab or missing role");
    RecoveredBankService::Peer peer{7,1,role.id,4,3,126,126,true};unsigned receipts=0;bool allowed=true;
    std::function<void(std::string_view)> callback;
    const auto observe=[&](std::string_view stage){const auto hook=callback;if(hook)hook(stage);};
    RecoveredBankService service(bank,[&](std::uint64_t s)->std::optional<RecoveredBankService::Peer>{observe("lookup");if(s==7)return peer;return {};},
        [&](const auto& p,std::uint16_t target){observe("access");return allowed && p.area==4 && p.scene==3 && access.lookup(p.area,p.scene,target,true).has_value();},
        [&]{observe("receipt");return std::string(64,static_cast<char>('a'+receipts++));});
    const auto now=RecoveredBankService::Clock::now();
    require(!service.open(7,999,now) && !bank.load_bank(1,role.id),"Unknown banker created a balance");
    const auto opened=service.open(7,531,now);require(opened && opened->size()==27 && (*opened)[0]==0x46 && (*opened)[13]==0x47 && (*opened)[22]==0x27,"Native bank projection layout");
    const auto initial=bank.load(1,role.id),unrelated=bank.load(2,other.id);
    const RecoveredBank::Request deposit{RecoveredBank::Kind::Deposit,100,531,0xa5a5};
    const auto decoded=RecoveredWorldRecords::decode(RecoveredBank::encode(deposit));
    require(decoded && std::get<RecoveredBank::Request>(decoded->front())==deposit,"Bank raw opcode/opaque fields lost");
    auto result=service.handle(7,std::span(&deposit,1),now);
    require(result.committed && result.logical==std::vector<std::uint8_t>{0x47,100,0,0,0,0,0,0,0,0x27,0x84,3,0,0},"Native bank/purse commit projection");
    auto current=bank.load(1,role.id);require(current.wallet.amount==900 && current.bank.amount==100,"Bank money not conserved");
    const auto absolute=result.logical;
    const std::array duplicate{deposit,deposit};result=service.handle(7,duplicate,now);
    require(result.rejected && !result.committed && result.logical==absolute && bank.load(1,role.id)==current,"Duplicated batch spent money or lost absolute rollback sync");
    service.open(7,531,now);peer.scene=2;result=service.handle(7,std::span(&deposit,1),now);
    require(result.rejected && bank.load(1,role.id)==current,"Cross-scene lease spent money");peer.scene=3;
    service.open(7,531,now);result=service.handle(7,std::span(&deposit,1),now+std::chrono::seconds(61));
    require(result.rejected && bank.load(1,role.id)==current,"Expired lease spent money");
    service.open(7,531,now);service.disconnect(7);result=service.handle(7,std::span(&deposit,1),now);
    require(result.rejected && bank.load(1,role.id)==current,"Disconnected lease spent money");
    service.open(7,531,now);const RecoveredBank::Request close{RecoveredBank::Kind::Close,0,531,0,1};
    result=service.handle(7,std::span(&close,1),now);require(!result.rejected && result.logical.empty(),"Native local close needs no response");
    result=service.handle(7,std::span(&deposit,1),now);require(result.rejected && bank.load(1,role.id)==current,"Close retained bank authority");
    service.open(7,531,now);const RecoveredBank::Request withdraw{RecoveredBank::Kind::Withdraw,100,531,0xffff};
    result=service.handle(7,std::span(&withdraw,1),now);require(result.committed,"Native withdrawal failed");
    current=bank.load(1,role.id);require(current.wallet.amount==initial.wallet.amount && current.bank.amount==initial.bank.amount && bank.load(2,other.id)==unrelated,"Withdrawal or unrelated save changed");
    {
        service.open(7,531,now);const auto before=bank.load(1,role.id);
        const auto denied=god2_test::bank_revoke_on_receipt(raw,service,[&]{return service.handle(7,std::span(&deposit,1),now);},7);
        require(denied.rejected&&!denied.committed&&denied.logical.empty()&&bank.load(1,role.id)==before,"Money postwrite observer escaped rollback");
    }
    // PHASE1 source-only regression: caught nested entry still poisons the outer lease.
    for(const auto stage:{"lookup","access","receipt"})for(unsigned failure=0;failure<5;++failure){
        service.open(7,531,now);const auto before=bank.load(1,role.id);unsigned hits=0;
        callback=[&](std::string_view at){if(at!=stage)return;++hits;callback={};
            if(failure==0)service.disconnect(7);
            else if(failure==1){try{service.open(7,531,now);}catch(...){} }
            else if(failure==2){try{service.permits_items(7,531,now);}catch(...){} }
            else if(failure==3){try{service.renew_items(7,now);}catch(...){} }
            else throw 7;
        };
        const auto denied=service.handle(7,std::span(&deposit,1),now);callback={};
        require(hits==1&&denied.rejected&&!denied.committed&&bank.load(1,role.id)==before,"Money callback spent after retirement");
        if(failure!=4)require(denied.logical.empty(),"Poisoned money callback emitted stale rows");
        require(service.handle(7,std::span(&deposit,1),now).rejected,"Money callback retained lease");
    }
    for(const auto stage:{"lookup","access"}){
        unsigned hits=0;bool refused=false;const auto before=bank.load(1,role.id);
        callback=[&](std::string_view at){if(at!=stage)return;++hits;callback={};service.disconnect(7);};
        try{service.open(7,531,now);}catch(...){refused=true;}callback={};
        require(refused&&hits==1&&bank.load(1,role.id)==before&&service.handle(7,std::span(&deposit,1),now).rejected,"Money open revived revoked lease");
        service.open(7,531,now);hits=0;
        callback=[&](std::string_view at){if(at!=stage)return;++hits;callback={};service.disconnect(7);};
        require(!service.permits_items(7,531,now),"Money permit survived callback revocation");callback={};
        require(hits==1&&service.handle(7,std::span(&deposit,1),now).rejected,"Money permit retained revoked lease");
    }
    service.open(7,531,now);++peer.session;require(!service.open(7,531,now),"Money open accepted mismatching returned session");--peer.session;
    require(service.handle(7,std::span(&deposit,1),now).rejected,"Rejected replacement open retained old lease");
    {
        const auto before=bank.load(1,role.id);unsigned cuts=0;bool refused=false;
        try{bank.commit(std::string(64,'f'),{before,SqliteBankRepository::Operation::Deposit,1},[&]{if(++cuts==2)throw DatabaseError("final lifecycle cut");});}catch(const DatabaseError&){refused=true;}
        require(refused&&cuts==2&&bank.load(1,role.id)==before,"Money final readback lifecycle cut failed rollback");
        profile[0]='C';const auto fresh=characters.create(1,profile);
        for(bool existing:{false,true}){
            if(existing)bank.provision_bank(1,fresh.id);cuts=0;refused=false;const auto original=bank.load_bank(1,fresh.id);
            try{bank.provision_bank(1,fresh.id,[&]{if(++cuts==2)throw DatabaseError("final provision cut");});}catch(const DatabaseError&){refused=true;}
            require(refused&&cuts==2&&bank.load_bank(1,fresh.id)==original,"Money new/existing provision escaped final lifecycle cut");
        }
    }
    {
        unsigned receipts_seen=0;
        RecoveredBankService expiring(bank,[&](auto session)->std::optional<RecoveredBankService::Peer>{return session==7?std::optional{peer}:std::nullopt;},
            [](const auto&,auto target){return target==531;},[&]{++receipts_seen;return std::string(64,'e');});
        require(expiring.open(7,531,now).has_value(),"Expiry pure-current fixture open failed");
        const auto source=expiring.capture_lease(7,531,now);expiring.renew_items(7,now-std::chrono::seconds(61));
        require(!source.current(),"Backdated renewal did not expire its source");const auto before=bank.load(1,role.id);
        // Admission time is intentionally before expiry; real current() must
        // still reject at the repository cut without sleeping or private access.
        const auto denied=expiring.handle(7,std::span(&deposit,1),now-std::chrono::seconds(62));
        require(receipts_seen==1&&denied.rejected&&!denied.committed&&bank.load(1,role.id)==before,
            "Money pure current accepted an expired lease through stale admission time");
    }
    // Opaque shared identity survives copies only until its exact money lease
    // retires. Reopening the same peer/target is a NEW source, never ABA revival.
    {
        service.open(7,531,now);const auto old=service.capture_lease(7,531,now),copy=old;
        require(old.current()&&old.matches(peer,531)&&old.owns(7,1,role.id,531),"Qualified shared bank source missing");
        auto wrong=peer;++wrong.character;require(!old.matches(wrong,531)&&!old.owns(7,1,role.id,999),"Bank source accepted another owner/target");
        service.disconnect(7);require(!old.current()&&!copy.current(),"Retirement left copied bank source valid");
        service.open(7,531,now);const auto fresh=service.capture_lease(7,531,now);
        require(fresh.current()&&!old.current()&&!copy.current(),"Identical owner reopen revived old bank source");
        service.renew_items(7,now-std::chrono::seconds(61));require(!fresh.current(),"Expired source remained current");
        service.renew_items(7,now);require(!fresh.current()&&!service.permits_items(7,531,now),"Renew resurrected expired bank source");
        service.open(7,531,now);const auto denied_source=service.capture_lease(7,531,now);
        require(!service.permits_items(7,999,now)&&!denied_source.current(),"Rejected access observation retained source");
    }
    std::cout<<"Bank typed native framing, lease/access, test isolation, cancel and canonical sync passed\n";
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
