#include "handlers/OwnedGuildDisbandService.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <iostream>
#include <memory>
#include <source_location>
#include <utility>
using namespace god2;
namespace {
using Service=OwnedGuildDisbandService;using Repo=Service::Repository;using Panel=Service::Panel;
using sqlite_detail::execute;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("DisbandService0081 check "+std::to_string(checks)+" line "+std::to_string(at.line()));
}
// Independent whole-save typed oracle copied from the frozen kick test:
// schema + unknown columns + duplicate rows + NULL/BLOB/TEXT type distinctions.
std::vector<std::string> state(sqlite3* db,const std::set<std::string>& skip={}) {
    std::vector<std::string> result;
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row())for(int c=0;c<4;++c)result.push_back("schema:"+schema.text(c));
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);if(skip.contains(name))continue;
        std::string quoted="\"";for(const auto c:name){quoted+=c;if(c=='\"')quoted+=c;}quoted+='\"';
        sqlite3_stmt* query=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,("SELECT * FROM "+quoted).c_str(),-1,&query,nullptr));
        struct Done {sqlite3_stmt* query;~Done(){sqlite3_finalize(query);}} done{query};
        std::vector<std::string> rows;int rc;
        while((rc=sqlite3_step(query))==SQLITE_ROW) {
            std::string row=name+":";
            for(int c=0;c<sqlite3_column_count(query);++c) {
                const auto type=sqlite3_column_type(query,c);row+=std::to_string(type)+":";
                if(type==SQLITE_NULL)continue;
                const auto size=sqlite3_column_bytes(query,c);const auto* data=static_cast<const char*>(sqlite3_column_blob(query,c));
                row+=std::to_string(size)+":";if(size)row.append(data,static_cast<std::size_t>(size));
            }
            rows.push_back(std::move(row));
        }
        check(rc==SQLITE_DONE);std::sort(rows.begin(),rows.end());result.insert(result.end(),rows.begin(),rows.end());
    }
    return result;
}
struct Fixture {
    struct Peer {std::uint64_t account,character;bool ready=true;};
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteTradeRepository> money;
    std::unique_ptr<SqliteGuildRepository> guilds;
    std::unique_ptr<Panel> panels;
    std::unique_ptr<Service> service;
    std::map<std::uint64_t,Service::Owner> owners;
    std::vector<Peer> peers;
    std::set<std::uint32_t> online{1,2,3,4,5,6,7,8};
    Repo::Proof seed_proof{[]{},[]{}}; // TEST_ONLY private fixture, never client authority.
    std::uint64_t guild{},foreign{};
    bool throw_ready=false,throw_resolve=false,retired=false;
    bool deny_inside_transaction=false,deny_after_retirement=false,lose_owner_inside_transaction=false;
    bool lose_owner_after_retirement=false;
    unsigned readiness_calls=0,after_retirement_calls=0;
    std::vector<std::set<std::uint64_t>> observed_audiences;
    std::set<std::uint64_t> expected_audience{1,2,3,6};
    std::function<void()> on_ready;
    Fixture(bool maximum=false) {
        check(sqlite3_open(":memory:",&db)==SQLITE_OK);execute(db,"PRAGMA foreign_keys=ON");
        SqliteMigrationManager(db,owned_guild_announcement_migrations()).migrate();
        repo=std::make_unique<Repo>(db);money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        guilds=std::make_unique<SqliteGuildRepository>(db);
        if(maximum) {online.clear();expected_audience.clear();for(unsigned i=1;i<=50;++i)expected_audience.insert(i);}
        for(unsigned i=1;i<=(maximum?54u:8u);++i) {
            sqlite_detail::Statement a(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY-preserved-hash')");
            a.bind(1,i);a.bind(2,"DisbandAcct"+std::to_string(i));a.done();
            const auto name="DisbandP"+std::to_string(i);const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            std::array<std::uint8_t,40> profile{};std::copy(bytes.begin(),bytes.end(),profile.begin());profile[29]=1;
            sqlite_detail::Statement c(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,bytes);c.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();money->provision_wallet(i,i);
            SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
            owners.emplace(i,Service::Owner{i,i,i,1,4,3,59,60,950,1,1});peers.push_back({i,i,true});online.insert(i);
        }
        execute(db,"UPDATE character_trade_wallets SET amount=100000"); // TEST_ONLY.
        guild=create(1,"DisbandGuild");foreign=create(maximum?52:4,"OtherGuild");
        if(maximum) {
            execute(db,"UPDATE owned_guild_governance_0078 SET capacity=50 WHERE guild_id="+std::to_string(guild));
            for(unsigned i=2;i<=26;++i)join(i,guild);
            for(unsigned i=27;i<=50;++i)repo->apply(repo->nonmember(i,i),repo->guild(guild),seed_proof);
            join(53,foreign);repo->apply(repo->nonmember(54,54),repo->guild(foreign),seed_proof);
        }else {
            join(2,guild);join(6,guild);join(5,foreign);
            repo->apply(repo->nonmember(3,3),repo->guild(guild),seed_proof);
            repo->apply(repo->nonmember(7,7),repo->guild(foreign),seed_proof);
        }
        execute(db,"CREATE TABLE unknown_save(v,blob BLOB,text TEXT);INSERT INTO unknown_save VALUES(NULL,X'00017F','unchanged');"
                   "INSERT INTO unknown_save VALUES(1.25,X'', '');INSERT INTO unknown_save SELECT * FROM unknown_save;");
        // SQL execution witness only, NEVER permission. It marks the post-delete
        // phase without our world callback reloading now-deleted membership/gov.
        check(sqlite3_create_function_v2(db,"test_disband_retired",0,SQLITE_UTF8,this,
            [](sqlite3_context* context,int,sqlite3_value**) {
                auto* fixture=static_cast<Fixture*>(sqlite3_user_data(context));fixture->retired=true;
                sqlite3_result_int(context,1);
            },nullptr,nullptr,nullptr)==SQLITE_OK);
        execute(db,"CREATE TRIGGER test_retired_witness AFTER DELETE ON owned_guild_governance_0078 WHEN OLD.guild_id="+
                   std::to_string(guild)+" BEGIN SELECT test_disband_retired(); END");
        panels=std::make_unique<Panel>(*repo,[this](auto id){return resolve(id);},
            [this](auto account,auto character){return guilds->load(account,character);},[this]{return online;});
        service=std::make_unique<Service>(*repo,*panels,[this](auto id){return resolve(id);},
            [this](const auto& panel){return alive(panel);});
    }
    ~Fixture(){service.reset();panels.reset();guilds.reset();money.reset();repo.reset();if(db)sqlite3_close(db);}
    std::optional<Service::Owner> resolve(std::uint64_t id) {
        if(throw_resolve)throw DatabaseError("TEST_ONLY resolver failure");
        if(lose_owner_inside_transaction && !sqlite3_get_autocommit(db))return {};
        if(lose_owner_after_retirement && retired)return {};
        const auto at=owners.find(id);return at==owners.end()?std::nullopt:std::optional{at->second};
    }
    bool alive(const Panel::State& panel) {
        ++readiness_calls;if(retired)++after_retirement_calls;
        // World-only captured identities; NO membership/governance/panel reread.
        std::set<std::uint64_t> audience;
        for(const auto& member:panel.leader.roster)check(audience.insert(member.character_id).second);
        for(const auto& app:panel.applications)check(audience.insert(app.applicant.character_id).second);
        check(audience==expected_audience);observed_audiences.push_back(audience);
        const auto check_peer=[&](const Repo::Identity& identity) {
            for(const auto& peer:peers)if(peer.character==identity.character_id &&
                (peer.account!=identity.account_id || !peer.ready))return false;
            return true; // Offline allowed by world policy, SQL proof still required.
        };
        if(throw_ready)throw DatabaseError("TEST_ONLY complete audience callback failure");
        if(auto hook=std::exchange(on_ready,{}))hook(); // TEST_ONLY hostile side-effect guard.
        if(deny_inside_transaction && !sqlite3_get_autocommit(db))return false;
        if(deny_after_retirement && retired)return false;
        for(const auto& member:panel.leader.roster)if(!check_peer(member))return false;
        for(const auto& app:panel.applications)if(!check_peer(app.applicant))return false;
        return true;
    }
    std::uint64_t create(unsigned id,const std::string& name) {
        return repo->create(repo->nonmember(id,id),*money->load_wallet(id,id),name,{50000,30,20},seed_proof).leader.governance.guild_id;
    }
    void join(unsigned id,std::uint64_t target) {
        const auto app=repo->apply(repo->nonmember(id,id),repo->guild(target),seed_proof);
        const auto gov=repo->governance(target);repo->approve(repo->leader(gov.owner_account,gov.owner_character),app,seed_proof);
    }
    Panel::Plan open(unsigned id=1) {
        const auto plan=panels->prepare(id,true);check(bool(plan));check(panels->current(*plan));check(panels->published(*plan));return *plan;
    }
    Service::ActionPlan action() {
        open();const auto action=service->prepare_action(1,0);check(bool(action));return *action;
    }
    void fail(const Service::ActionPlan& action,bool consumed=true) {
        const auto before=state(db);check(!service->execute(action));check(state(db)==before);check(sqlite3_get_autocommit(db)==1);
        if(consumed)check(!panels->action_publication(action.panel.owner.session));
    }
    void unready(unsigned character) {for(auto& peer:peers)if(peer.character==character)peer.ready=false;}
};
void permissions() {
    Fixture f;check(!f.service->prepare_action(1,0));
    const auto prepared=f.panels->prepare(1,true);check(bool(prepared));check(!f.service->prepare_action(1,0));
    const auto readonly=f.panels->prepare(1);check(readonly && f.panels->published(*readonly));check(!f.service->prepare_action(1,0));
    f.open();const auto plan=f.service->prepare_action(1,0);check(bool(plan));
    for(unsigned slot=1;slot<256;++slot)check(!f.service->prepare_action(1,static_cast<std::uint8_t>(slot)));
    f.open(2);check(!f.service->prepare_action(2,0));check(!f.service->prepare_action(3,0));check(!f.service->prepare_action(8,0));
    Service no_resolve(*f.repo,*f.panels,{},[&](const auto& p){return f.alive(p);});check(!no_resolve.prepare_action(1,0));
    Service no_ready(*f.repo,*f.panels,[&](auto id){return f.resolve(id);},{});check(!no_ready.prepare_action(1,0));
    for(unsigned variant=0;variant<8;++variant) {
        const auto valid=f.action();auto forged=valid;
        if(variant==0)forged.slot=1;if(variant==1)forged.publication++;
        if(variant==2)forged.panel.rows[0].role=1;if(variant==3)forged.panel.owner.account=4;
        if(variant==4)forged.panel.leader.governance.owner_character=2;
        if(variant==5)forged.panel.membership.guild_revision++;
        if(variant==6)forged.panel.rows[0].application=forged.panel.applications.front();
        if(variant==7)forged.panel.leader.identity.character_id=2;
        f.fail(forged,variant==0);if(variant!=0)check(f.service->current(valid));
    }
}
void success_world_only_after_delete() {
    for(const auto cp:{950,936}) {
        Fixture f;f.owners[1].name_codepage=static_cast<std::uint16_t>(cp);const auto action=f.action();
        const auto before=f.repo->guild(f.guild);const auto foreign=f.repo->leader(4,4);
        const auto preserved=state(f.db,{"owned_guilds","owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"});
        check(f.service->execute(action));check(f.retired && f.after_retirement_calls>=1);
        check(f.repo->guild(f.guild).name_utf8==before.name_utf8 && f.repo->guild(f.guild).revision>before.revision);
        for(const unsigned id:{1u,2u,6u})check(!f.guilds->load(id,id));
        check(!f.repo->pending(3,3));check(!f.repo->player_created(f.guild));check(!f.repo->find_by_name(before.name_utf8));
        check(f.repo->leader(4,4)==foreign && f.repo->pending(7,7).has_value());
        check(state(f.db,{"owned_guilds","owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"})==preserved);
        check(!f.service->execute(action));check(!f.service->prepare_action(1,0));check(f.panels->cached(1));
        check(std::all_of(f.observed_audiences.begin(),f.observed_audiences.end(),[](const auto& s){return s==std::set<std::uint64_t>({1,2,3,6});}));
    }
    Fixture offline;offline.peers.erase(std::remove_if(offline.peers.begin(),offline.peers.end(),[](const auto& p){return p.character!=1;}),offline.peers.end());
    offline.online={1,4,5,7,8};check(offline.service->execute(offline.action()));
    for(const auto cp:{950,936}) {
        Fixture full(true);full.owners[1].name_codepage=static_cast<std::uint16_t>(cp);const auto plan=full.action();
        check(plan.panel.rows.size()==50 && plan.panel.leader.roster.size()==26 && plan.panel.applications.size()==24);
        const auto other=full.repo->leader(52,52);check(full.service->execute(plan));check(full.repo->leader(52,52)==other);
        check(full.after_retirement_calls>=1 && full.observed_audiences.back().size()==50);
        for(unsigned i=1;i<=26;++i)check(!full.guilds->load(i,i));for(unsigned i=27;i<=50;++i)check(!full.repo->pending(i,i));
    }
}
void publication_and_batch() {
    Fixture f;const auto old=f.action();const auto fresh=f.action();check(fresh.publication>old.publication);
    f.fail(old,false);check(f.service->current(fresh));
    f.service->invalidate(1);f.fail(fresh);
    const auto tick=f.panels->prepare(1);check(tick && f.panels->published(*tick));check(!f.service->prepare_action(1,0));
    const auto initially_absent=f.service->prepare_action(1,0);f.open();check(!initially_absent);
    const auto captured=f.service->prepare_action(1,0);check(bool(captured));f.open();f.fail(*captured,false);
    const auto next=f.service->prepare_action(1,0);check(bool(next));f.service->forget(1);f.fail(*next);check(f.panels->cached(1));
    Fixture two;const auto a=two.action();const auto b=two.service->prepare_action(1,0);check(b && *b==a);
    check(two.service->execute(a));two.fail(*b);
}
void world_aba_and_audience() {
    for(unsigned field=0;field<11;++field) {
        Fixture f;const auto action=f.action();const auto saved=f.owners[1];auto& o=f.owners[1];
        switch(field){case 0:++o.session;break;case 1:++o.account;break;case 2:++o.character;break;case 3:++o.world_generation;break;
            case 4:++o.area;break;case 5:++o.scene;break;case 6:++o.x;break;case 7:++o.y;break;case 8:o.name_codepage=936;break;
            case 9:++o.battle_generation;break;case 10:++o.position_revision;break;}
        f.service->observe_world(1);o=saved;f.fail(action);
    }
    for(const unsigned id:{1u,2u,3u,6u}) {Fixture f;const auto action=f.action();f.unready(id);f.fail(action);}
    for(const unsigned id:{2u,3u}) {
        Fixture f;const auto action=f.action();f.peers.push_back({id,id,false});f.fail(action);
        Fixture wrong;const auto a=wrong.action();wrong.peers.push_back({8,id,true});wrong.fail(a);
    }
    Fixture foreign;const auto good=foreign.action();foreign.unready(4);foreign.unready(7);check(foreign.service->execute(good));
    for(const bool ready:{false,true}) {
        Fixture f;const auto action=f.action();f.throw_ready=ready;f.throw_resolve=!ready;f.fail(action);
        f.throw_ready=f.throw_resolve=false;check(!f.service->prepare_action(1,0));
    }
    Fixture no_owner;const auto action=no_owner.action();no_owner.owners.erase(1);no_owner.fail(action);
}
void hostile_callback_republication() {
    Fixture invalidate;invalidate.open();invalidate.on_ready=[&]{invalidate.panels->invalidate(1);};check(!invalidate.service->prepare_action(1,0));
    Fixture reopen;const auto action=reopen.action();reopen.on_ready=[&]{reopen.open();};reopen.fail(action,false);
    const auto fresh=reopen.service->prepare_action(1,0);check(fresh && fresh->publication>action.publication);check(reopen.service->current(*fresh));
    // SQL-proof reopen is deliberately an invalid callback. Re-arm only when
    // inside the transaction; the proof rejects new authority and rolls back.
    Fixture sql;const auto a=sql.action();
    sql.on_ready=[&]{sql.on_ready=[&]{if(!sqlite3_get_autocommit(sql.db))sql.open();};};
    sql.fail(a,false);check(sql.panels->action_publication(1).has_value());
    sql.service->invalidate(1); // REQUIRED runtime EACH75 boundary, before suffix.
    check(!sql.service->prepare_action(1,0));
}
void sql_staleness_and_nonbattle() {
    for(unsigned kind=0;kind<5;++kind) {
        Fixture f;const auto action=f.action();
        if(kind==0)execute(f.db,"UPDATE owned_guild_governance_0078 SET capacity=19");
        if(kind==1)execute(f.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2");
        if(kind==2)f.repo->cancel(f.repo->nonmember(3,3),*f.repo->pending(3,3),f.seed_proof);
        if(kind==3)f.repo->member_leave(f.repo->identity(6,6),*f.guilds->load(6,6),f.repo->leader(1,1),f.repo->applications(f.guild),f.seed_proof);
        if(kind==4)f.online.erase(6);f.fail(action);
    }
    for(const unsigned id:{1u,2u,3u,6u}) {
        Fixture f;const auto action=f.action();SqliteRecoveredCharacterRepository chars(f.db);
        const auto resources=chars.load_resources(id,id);check(bool(resources));check(chars.reserve_battle(id,id,*resources)>0);f.fail(action);
    }
}
void rollback_consumes_and_reopen() {
    for(unsigned phase=0;phase<4;++phase) {
        Fixture f;const auto action=f.action();f.deny_inside_transaction=phase==0;f.deny_after_retirement=phase==1;
        f.lose_owner_inside_transaction=phase==2;f.lose_owner_after_retirement=phase==3;
        f.fail(action);check(f.guilds->load(1,1).has_value());check(f.repo->pending(3,3).has_value());
        f.deny_inside_transaction=f.deny_after_retirement=f.lose_owner_inside_transaction=f.lose_owner_after_retirement=false;
        f.retired=false;check(!f.service->prepare_action(1,0));check(f.service->execute(f.action()));
    }
    for(const std::string effect:{"UPDATE unknown_save SET blob=X'12';", "UPDATE accounts SET password_hash='changed' WHERE id=8;", "SELECT RAISE(IGNORE);"}) {
        Fixture f;execute(f.db,"CREATE TRIGGER fault "+std::string(effect=="SELECT RAISE(IGNORE);"?"BEFORE":"AFTER")+
            " DELETE ON owned_guild_members BEGIN "+effect+" END");const auto action=f.action();f.fail(action);
    }
}
}
int main(){try{permissions();success_world_only_after_delete();publication_and_batch();world_aba_and_audience();
    hostile_callback_republication();sql_staleness_and_nonbattle();rollback_consumes_and_reopen();
    std::cout<<"DisbandService0081 "<<checks<<" checks passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
