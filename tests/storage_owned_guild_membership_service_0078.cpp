#include "handlers/OwnedGuildMembershipService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "scripting/LuaEngine.h"
#include <iostream>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value) {++checks;if(!value)throw std::runtime_error("Guild membership service check failed");}
using Service=OwnedGuildMembershipService;
using Repo=Service::Repository;
using Wire=Service::Wire;
struct Fixture {
    sqlite3* db=nullptr;
    LuaEngine lua{std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false};
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteTradeRepository> money;
    std::map<std::uint64_t,Service::Owner> owners;
    std::unique_ptr<Service> service;
    bool world_available=true,rule_available=true;
    unsigned resolve_calls=0,disappear_on=0;
    Fixture() {
        check(sqlite3_open(":memory:",&db)==SQLITE_OK);
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        auto migrations=default_sqlite_migrations();check(migrations.size()==49);
        // CANDIDATE_ONLY: production defaults remain48; no formal DB mutation.
        
        SqliteMigrationManager(db,migrations).migrate();
        repo=std::make_unique<Repo>(db);money=std::make_unique<SqliteTradeRepository>(db);
        money->install_schema(); // Same explicit ancillary install used by Application.
        for(unsigned i=1;i<=5;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'unchanged-test-hash')");
            account.bind(1,i);account.bind(2,"Owner"+std::to_string(i));account.done();
            const auto name="Player"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=1;
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);
            character.bind_blob(4,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(name.data()),name.size()));character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=30;role[17]=100;role[21]=50;
            sqlite_detail::Statement snapshot(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            snapshot.bind(1,i);snapshot.bind_blob(2,role);snapshot.done();
            money->provision_wallet(i,i);
            owners.emplace(i,Service::Owner{i,i,i,1,1,2,59,60,static_cast<std::uint16_t>(i==2?936:950)});
        }
        // TEST_ONLY balances in a disposable full-schema database, never grants.
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000");
        check(lua.initialize());
        service=std::make_unique<Service>(*repo,[this](auto session)->std::optional<Service::Owner> {
            ++resolve_calls;if(!world_available || (disappear_on && resolve_calls>=disappear_on))return {};
            const auto it=owners.find(session);return it==owners.end()?std::nullopt:std::optional{it->second};
        },[this](auto account,auto character){return money->load_wallet(account,character);},
        [this](const auto& input){if(!rule_available)throw std::runtime_error("Test rule unavailable");return lua.owned_guild_membership(input);});
    }
    ~Fixture(){service.reset();money.reset();repo.reset();if(db)sqlite3_close(db);}
    Wire::Request request(const Wire::Prompt& prompt,const std::string& utf8,bool simplified=false) {
        const auto bytes=LegacyChineseCodec::encode(utf8,simplified);check(bytes.size()<16);
        Wire::Request request;request.context=static_cast<std::uint16_t>(prompt[1]|(std::uint16_t{prompt[2]}<<8));
        request.operation=static_cast<Wire::Operation>(prompt[3]);request.selected_actor_hint=0xffff; // never authority.
        std::copy(bytes.begin(),bytes.end(),request.raw_name.begin());request.opaque_stack_byte=0xa5;return request;
    }
};
}
int main() {
    try {
        Fixture f;const auto now=Service::Conversation::Clock::now();
        for(auto level:{29,30})for(auto wallet:{49999u,50000u}) {
            const auto policy=f.lua.owned_guild_membership({static_cast<std::uint8_t>(level),wallet});
            check(policy.creation_fee==50000 && policy.minimum_level==30 && policy.initial_capacity==20);
            check(policy.may_create==(level==30 && wallet==50000));
        }
        check(!f.service->open(1,Wire::Operation::Create,now,false));
        const auto prompt=f.service->open(1,Wire::Operation::Create,now,true);check(bool(prompt));
        check(!f.service->open(1,Wire::Operation::Join,now,true));
        auto request=f.request(*prompt,"仙界");auto wrong=request;++wrong.context;
        check(!f.service->submit(1,wrong,now) && f.service->pending(1));
        check(!f.service->submit(2,request,now));
        const auto result=f.service->submit(1,request,now);check(result && std::holds_alternative<Repo::Created>(*result));
        const auto created=std::get<Repo::Created>(*result);
        check(created.wallet.amount==50000 && created.leader.governance.capacity==20);
        check(!f.service->submit(1,request,now) && f.money->load_wallet(1,1)->amount==50000);
        check(!f.service->open(1,Wire::Operation::Create,now,true));
        const auto join=f.service->open(2,Wire::Operation::Join,now,true);check(bool(join));
        const auto joined=f.service->submit(2,f.request(*join,"仙界",true),now);check(joined && std::holds_alternative<Repo::Application>(*joined));
        check(!SqliteGuildRepository(f.db).load(2,2)); // Pending never pretends to be membership.
        check(f.money->load_wallet(2,2)->amount==100000 && f.repo->applications(created.leader.membership.guild_id).size()==1);
        check(!f.service->open(2,Wire::Operation::Create,now,true));
        const auto approved=f.repo->approve(f.repo->leader(1,1),std::get<Repo::Application>(*joined),{[]{},[]{}});
        check(approved.joined.guild_id==created.leader.membership.guild_id && !f.repo->pending(2,2));
        const auto stale=f.service->open(3,Wire::Operation::Create,now,true);check(bool(stale));
        sqlite_detail::execute(f.db,"UPDATE character_trade_wallets SET amount=90000,revision=revision+1 WHERE character_id=3");
        check(!f.service->submit(3,f.request(*stale,"Stale"),now));
        check(f.money->load_wallet(3,3)->amount==90000 && !f.service->pending(3));
        const auto moved=f.service->open(3,Wire::Operation::Create,now,true);check(bool(moved));++f.owners[3].x;
        check(!f.service->submit(3,f.request(*moved,"Moved"),now) && !f.service->pending(3));
        const auto expired=f.service->open(3,Wire::Operation::Create,now,true);check(bool(expired));
        check(!f.service->submit(3,f.request(*expired,"Expired"),now+Service::Conversation::lifetime));
        const auto invalid=f.service->open(3,Wire::Operation::Create,now,true);check(bool(invalid));
        check(!f.service->submit(3,f.request(*invalid,"100%"),now) && !f.service->pending(3));
        check(!f.service->submit(3,f.request(*invalid,"Valid"),now));
        const auto changed=f.service->open(3,Wire::Operation::Create,now,true);check(bool(changed));f.rule_available=false;
        check(!f.service->submit(3,f.request(*changed,"Changed"),now) && f.money->load_wallet(3,3)->amount==90000);f.rule_available=true;
        const auto lost=f.service->open(4,Wire::Operation::Create,now,true);check(bool(lost));
        // submit resolves once, then SQL before and after proof. Lose the world
        // only after writes: the entire debit/guild/member/governance rolls back.
        f.disappear_on=f.resolve_calls+3;
        check(!f.service->submit(4,f.request(*lost,"Lost"),now));f.disappear_on=0;
        check(f.money->load_wallet(4,4)->amount==100000 && !f.repo->find_by_name("Lost"));
        const auto goodbye=f.service->open(5,Wire::Operation::Create,now,true);check(bool(goodbye));
        f.service->disconnect(5);check(!f.service->submit(5,f.request(*goodbye,"Gone"),now));
        const auto away=f.service->open(5,Wire::Operation::Create,now,true);check(bool(away));
        ++f.owners[5].x;f.service->observe_world(5);--f.owners[5].x;
        check(!f.service->submit(5,f.request(*away,"Return"),now));
        const auto battle=f.service->open(5,Wire::Operation::Create,now,true);check(bool(battle));
        f.world_available=false;f.service->observe_world(5);f.world_available=true;
        check(!f.service->submit(5,f.request(*battle,"Battle"),now));
        Wire::Name name{};name.fill('A');name[15]=0;check(OwnedGuildMembershipName::valid(name,950));
        name[15]='A';check(!OwnedGuildMembershipName::valid(name,950));name[15]=0;
        check(!OwnedGuildMembershipName::valid(name,0));name[0]=0x1f;check(!OwnedGuildMembershipName::valid(name,950));
        check(sqlite3_get_autocommit(f.db)==1);
        std::cout<<"PASS "<<checks<<" full-schema/Lua/service checks; not current-client acceptance\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
