#include "handlers/OwnedGuildLeaderPanelService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <source_location>
using namespace god2;
namespace {
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Leader panel0078 check "+std::to_string(checks)+" line "+std::to_string(at.line()));
}
using Service=OwnedGuildLeaderPanelService;using Repo=Service::Repository;
std::string saved(sqlite3* db) {
    std::string result;
    for(const auto* sql:{"SELECT id||':'||hex(username)||':'||hex(password_hash) FROM accounts ORDER BY id",
        "SELECT id||':'||account_id||':'||slot||':'||hex(profile)||':'||hex(name_bytes)||':'||name_codepage FROM recovered_characters ORDER BY id",
        "SELECT character_id||':'||hex(logical)||':'||revision||':'||design_id FROM character_role_snapshots ORDER BY character_id",
        "SELECT character_id||':'||amount||':'||revision||':'||design_id FROM character_trade_wallets ORDER BY character_id"}) {
        sqlite_detail::Statement q(db,sql);while(q.row())result+=q.text(0)+"\n";
    }return result;
}
struct Fixture {
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteTradeRepository> money;
    std::unique_ptr<SqliteGuildRepository> guilds;
    std::map<std::uint64_t,Service::Owner> owners;
    std::set<std::uint32_t> online{1,2,3};
    std::unique_ptr<Service> service;
    unsigned resolves=0,lose_on=0;bool throw_resolve=false,throw_online=false;
    Repo::Proof proof{[]{},[]{}};
    Fixture() {
        check(sqlite3_open(":memory:",&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        auto migrations=default_sqlite_migrations();check(migrations.size()==49);
        SqliteMigrationManager(db,migrations).migrate();
        repo=std::make_unique<Repo>(db);money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        guilds=std::make_unique<SqliteGuildRepository>(db);
        for(unsigned i=1;i<=55;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'preserved-hash')");
            account.bind(1,i);account.bind(2,"Account"+std::to_string(i));account.done();
            const auto name="Player"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=static_cast<std::uint8_t>(1+i%8);
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);
            character.bind_blob(4,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(name.data()),name.size()));character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=static_cast<std::uint8_t>(30+i);role[17]=100;role[21]=50;
            sqlite_detail::Statement snapshot(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            snapshot.bind(1,i);snapshot.bind_blob(2,role);snapshot.done();money->provision_wallet(i,i);
            owners.emplace(i,Service::Owner{i,i,i,1,4,3,59,60,static_cast<std::uint16_t>(i==2?936:950)});
        }
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000"); // TEST_ONLY full-schema fixture.
        service=std::make_unique<Service>(*repo,[this](auto session)->std::optional<Service::Owner> {
            ++resolves;if(throw_resolve)throw DatabaseError("Fixture owner callback failed");
            if(lose_on && resolves>=lose_on)return {};const auto at=owners.find(session);
            return at==owners.end()?std::nullopt:std::optional{at->second};
        },[this](auto account,auto character){return guilds->load(account,character);},[this] {
            if(throw_online)throw DatabaseError("Fixture online callback failed");return online;
        });
    }
    ~Fixture(){service.reset();guilds.reset();money.reset();repo.reset();if(db)sqlite3_close(db);}
    Repo::Created create(unsigned person,const std::string& name="Cave") {
        return repo->create(repo->nonmember(person,person),*money->load_wallet(person,person),name,{50000,30,20},proof);
    }
    Repo::Application apply(unsigned person,std::uint64_t guild) {
        return repo->apply(repo->nonmember(person,person),repo->guild(guild),proof);
    }
    Service::Plan panel(unsigned session) {
        const auto plan=service->prepare(session,true);check(bool(plan));check(service->current(*plan));check(service->published(*plan));return *plan;
    }
};
}
int main() {
 try {
  Fixture f; const auto created=f.create(1);const auto id=created.leader.membership.guild_id;
  const auto pending=f.apply(2,id);f.repo->approve(f.repo->leader(1,1),pending,f.proof);const auto retained=f.apply(3,id);
  const auto protected_saved=saved(f.db);f.panel(1);
  check(!f.service->prepare_leave(1,0));check(!f.service->prepare_leave(2,0));check(!f.service->prepare_leave(3,0));
  auto member=f.panel(2);check(!f.service->prepare_leave(2,1));auto lease=f.service->prepare_leave(2,0);check(bool(lease));
  auto forged=*lease;forged.publication++;check(!f.service->leave(forged,0));forged=*lease;forged.panel.owner.account=1;check(!f.service->leave(forged,0));
  check(!f.service->leave(*lease,1));check(f.service->current(*lease));
  ++f.owners[2].x;f.service->observe_world(2);--f.owners[2].x;check(!f.service->leave(*lease,0));
  auto idle=f.service->prepare(2);check(idle && f.service->published(*idle));check(!f.service->prepare_leave(2,0));
  member=f.panel(2);lease=f.service->prepare_leave(2,0);check(bool(lease));
  f.online.erase(1);check(!f.service->leave(*lease,0));f.online.insert(1);
  member=f.panel(2);lease=f.service->prepare_leave(2,0);check(bool(lease));
  const auto before=f.repo->leader(1,1);const auto before_apps=f.repo->applications(id);
  f.lose_on=f.resolves+4;check(!f.service->leave(*lease,0));f.lose_on=0;
  check(f.repo->leader(1,1)==before && f.repo->applications(id)==before_apps && f.guilds->load(2,2));
  check(!f.service->prepare_leave(2,0));member=f.panel(2);lease=f.service->prepare_leave(2,0);check(bool(lease));
  member=f.panel(2);check(!f.service->leave(*lease,0));lease=f.service->prepare_leave(2,0);check(bool(lease));
  check(f.service->leave(*lease,0));check(!f.service->leave(*lease,0));check(!f.guilds->load(2,2));
  check(f.repo->applications(id)==before_apps && f.repo->pending(3,3)==std::optional{retained});
  const auto after=f.repo->leader(1,1);check(after.roster.size()==1 && after.roster[0].character_id==1 && after.governance==before.governance);
  check(after.membership.guild_revision>before.membership.guild_revision && saved(f.db)==protected_saved);
  check(!f.service->prepare(2));check(f.service->cached(2));auto clear=f.service->prepare_clear(2);check(bool(clear));
  check(clear->logical==std::vector<std::uint8_t>({0x92,1,0x92,2,0x92,0}));
  auto forged_clear=*clear;forged_clear.publication++;check(!f.service->cleared(forged_clear));
  ++f.owners[2].world_generation;check(!f.service->current(*clear));--f.owners[2].world_generation;
  check(f.service->current(*clear) && f.service->cleared(*clear));check(!f.service->cached(2) && !f.service->cleared(*clear));
  check(!f.service->prepare_clear(2));f.panel(1);check(!f.service->prepare_leave(1,0));
  // A caller cannot clear a currently retained membership or replay a stale
  // departure after a subsequent, independently approved rejoin.
  const auto reapply=f.apply(2,id);f.repo->approve(f.repo->leader(1,1),reapply,f.proof);member=f.panel(2);
  check(!f.service->prepare_clear(2) && !f.service->cleared(*clear));
  lease=f.service->prepare_leave(2,0);check(bool(lease));f.service->forget(2);check(!f.service->leave(*lease,0));
  check(f.guilds->load(2,2) && sqlite3_get_autocommit(f.db)==1);
  std::cout<<"PASS "<<checks<<" ordinary-member leave/publication/native cache checks; source-only, not live UI acceptance\n";return 0;
 }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
