#include "handlers/RecoveredBankService.h"
#include "db/SqliteBankAccessRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <memory>
#include <stdexcept>
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
    RecoveredBankService service(bank,[&](std::uint64_t s)->std::optional<RecoveredBankService::Peer>{if(s==7)return peer;return {};},
        [&](const auto& p,std::uint16_t target){return allowed && p.area==4 && p.scene==3 && access.lookup(p.area,p.scene,target,true).has_value();},
        [&]{return std::string(64,static_cast<char>('a'+receipts++));});
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
    const std::array duplicate{deposit,deposit};result=service.handle(7,duplicate,now);
    require(result.rejected && !result.committed && bank.load(1,role.id)==current,"Duplicated batch spent money");
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
    std::cout<<"Bank typed native framing, lease/access, test isolation, cancel and canonical sync passed\n";
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
