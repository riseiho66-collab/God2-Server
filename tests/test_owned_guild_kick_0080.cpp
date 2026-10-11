#include "handlers/OwnedGuildKickService.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <iostream>
#include <memory>
#include <source_location>
using namespace god2;
namespace {
using Service=OwnedGuildKickService;using Repo=Service::Repository;using Panel=Service::Panel;
using sqlite_detail::execute;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Kick0080 check "+std::to_string(checks)+" line "+std::to_string(at.line()));
}
// Independent whole-save typed oracle, including schema, unknown columns,
// duplicate rows and NULL/BLOB/TEXT distinctions; no repository guard reuse.
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
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteTradeRepository> money;
    std::unique_ptr<SqliteGuildRepository> guilds;
    std::unique_ptr<Panel> panels;
    std::unique_ptr<Service> service;
    std::map<std::uint64_t,Service::Owner> owners;
    std::set<std::uint32_t> online{1,2,3,4,5,6,7,8};
    Repo::Proof seed_proof{[]{},[]{}}; // TEST_ONLY provisioning, never runtime authority.
    std::uint64_t guild{},foreign{};
    bool target_ready=true,throw_ready=false,throw_resolve=false,lose_owner_after_write=false,lose_target_after_write=false;
    bool lose_owner_in_transaction=false,lose_target_in_transaction=false;
    Fixture() {
        check(sqlite3_open(":memory:",&db)==SQLITE_OK);execute(db,"PRAGMA foreign_keys=ON");
        SqliteMigrationManager(db,owned_guild_announcement_migrations()).migrate();
        repo=std::make_unique<Repo>(db);money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        guilds=std::make_unique<SqliteGuildRepository>(db);
        for(unsigned i=1;i<=8;++i) {
            sqlite_detail::Statement a(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY-preserved-hash')");
            a.bind(1,i);a.bind(2,"KickAccount"+std::to_string(i));a.done();
            const auto name="KickPlayer"+std::to_string(i);const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            std::array<std::uint8_t,40> profile{};std::copy(bytes.begin(),bytes.end(),profile.begin());profile[29]=1;
            sqlite_detail::Statement c(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,bytes);c.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();money->provision_wallet(i,i);
            SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
            owners.emplace(i,Service::Owner{i,i,i,1,4,3,59,60,950,1,1});
        }
        execute(db,"UPDATE character_trade_wallets SET amount=100000"); // TEST_ONLY fee fixture.
        guild=create(1,"KickGuild");foreign=create(4,"OtherGuild");
        join(2,guild);join(6,guild);join(5,foreign);
        repo->apply(repo->nonmember(3,3),repo->guild(guild),seed_proof);
        repo->apply(repo->nonmember(7,7),repo->guild(foreign),seed_proof);
        execute(db,"CREATE TABLE unknown_save(v,blob BLOB,text TEXT);INSERT INTO unknown_save VALUES(NULL,X'00017F','unchanged');"
                   "INSERT INTO unknown_save VALUES(1.25,X'', '');INSERT INTO unknown_save SELECT * FROM unknown_save;");
        panels=std::make_unique<Panel>(*repo,[this](auto id){return resolve(id);},
            [this](auto account,auto character){return guilds->load(account,character);},[this]{return online;});
        service=std::make_unique<Service>(*repo,*panels,[this](auto id){return resolve(id);},[this](const auto& identity){
            check(identity.membership_revision==0);
            if(throw_ready)throw DatabaseError("TEST_ONLY target readiness failure");
            if(lose_target_in_transaction && !sqlite3_get_autocommit(db))return false;
            if(lose_target_after_write && !guilds->load(identity.account_id,identity.character_id))return false;
            return target_ready;
        });
    }
    ~Fixture(){service.reset();panels.reset();guilds.reset();money.reset();repo.reset();if(db)sqlite3_close(db);}
    std::optional<Service::Owner> resolve(std::uint64_t id) {
        if(throw_resolve)throw DatabaseError("TEST_ONLY resolver failure");
        if(lose_owner_in_transaction && !sqlite3_get_autocommit(db))return {};
        if(lose_owner_after_write && !guilds->load(2,2))return {};
        const auto at=owners.find(id);return at==owners.end()?std::nullopt:std::optional{at->second};
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
    Service::ActionPlan action(unsigned id=1,std::uint8_t slot=1) {
        open(id);const auto action=service->prepare_action(id,slot);check(bool(action));return *action;
    }
    void fail(const Service::ActionPlan& action,bool consumed=true) {
        const auto before=state(db);check(!service->execute(action));check(state(db)==before);check(sqlite3_get_autocommit(db)==1);
        if(consumed)check(!panels->action_publication(action.panel.owner.session));
    }
};
void publication_and_permissions() {
    Fixture f;check(!f.service->prepare_action(1,1));const auto prepared=f.panels->prepare(1,true);check(bool(prepared));
    check(!f.service->prepare_action(1,1));auto readonly=f.panels->prepare(1);check(readonly && f.panels->published(*readonly));
    check(!f.service->prepare_action(1,1));const auto founder=f.open();
    check(founder.next.rows.size()==4 && founder.next.rows[0].role==3 && founder.next.rows[1].identity.character_id==2 &&
          founder.next.rows[2].identity.character_id==6 && founder.next.rows[3].role==0);
    check(!f.service->prepare_action(1,0));check(!f.service->prepare_action(1,3));check(!f.service->prepare_action(1,255));
    const auto action=f.service->prepare_action(1,1);check(bool(action));check(action->target.membership_revision==0);
    check(action->target_membership==*f.guilds->load(2,2));
    f.open(2);check(!f.service->prepare_action(2,1)); // Ordinary member cannot remove founder/others.
    f.open(4);check(!f.service->prepare_action(4,2)); // Pending applicant is not an accepted member.
    check(!f.service->prepare_action(3,1));check(!f.service->prepare_action(8,1));
    auto forged=*action;forged.publication++;f.fail(forged,false);check(f.service->current(*action));
    forged=*action;forged.panel.owner.account=4;f.fail(forged,false);check(f.service->current(*action));
    forged=*action;forged.target=f.repo->identity(5,5);f.fail(forged); // Full plan equality denies foreign identity.
    check(!f.service->prepare_action(1,1));
    Service absent(*f.repo,*f.panels,[&](auto id){return f.resolve(id);},{});f.open();check(!absent.prepare_action(1,1));
}
void lifecycle_and_persistence() {
    for(const auto cp:{950,936}) {
        Fixture f;f.owners[1].name_codepage=static_cast<std::uint16_t>(cp);const auto action=f.action();
        const auto preserve=state(f.db,{"owned_guilds","owned_guild_members"});
        const auto pending=f.repo->applications(f.guild);const auto other=f.repo->leader(4,4);
        const auto before=f.repo->guild(f.guild);check(f.service->execute(action));
        check(!f.guilds->load(2,2));check(f.repo->nonmember(2,2).character_id==2);
        check(f.repo->guild(f.guild).revision>before.revision && f.repo->leader(1,1).roster.size()==2);
        check(f.repo->applications(f.guild)==pending && f.repo->leader(4,4)==other && state(f.db,{"owned_guilds","owned_guild_members"})==preserve);
        check(!f.service->execute(action));check(!f.service->prepare_action(1,1));
        const auto refresh=f.panels->prepare(1);check(refresh && f.panels->published(*refresh));check(!f.service->prepare_action(1,1));
        const auto next=f.action();check(next.target.character_id==6 && next.publication>action.publication);
        check(f.service->execute(next));check(f.repo->leader(1,1).roster.size()==1);
    }
    Fixture offline;offline.online.erase(2);check(offline.service->execute(offline.action())); // Offline target allowed by custom policy.
}
void stale_serial_and_batch() {
    Fixture f;const auto old=f.action();const auto fresh=f.action();check(fresh.publication>old.publication);
    f.fail(old,false);check(f.service->current(fresh));
    f.service->invalidate(1);f.fail(fresh); // Mixed/unqualified batch revokes publication before prefix work.
    auto tick=f.panels->prepare(1);check(tick && tick->logical.empty() && f.panels->published(*tick));check(!f.service->prepare_action(1,1));
    const auto absent=f.service->prepare_action(1,1);f.open();check(!absent); // Prefix help cannot manufacture a captured action.
    const auto captured=f.service->prepare_action(1,1);check(bool(captured));f.open();f.fail(*captured,false);
    const auto new_action=f.service->prepare_action(1,1);check(bool(new_action));f.service->forget(1);f.fail(*new_action);
    check(f.panels->cached(1)); // Retain native92 debt despite authority loss.
}
void owner_and_target_readiness() {
    for(unsigned field=0;field<11;++field) {
        Fixture f;auto action=f.action();const auto saved=f.owners[1];auto& o=f.owners[1];
        switch(field){case 0:++o.session;break;case 1:++o.account;break;case 2:++o.character;break;case 3:++o.world_generation;break;
            case 4:++o.area;break;case 5:++o.scene;break;case 6:++o.x;break;case 7:++o.y;break;case 8:o.name_codepage=936;break;
            case 9:++o.battle_generation;break;case 10:++o.position_revision;break;}
        f.service->observe_world(1);o=saved;f.fail(action); // Monotonic founder ABA evidence survives restored coordinates.
    }
    Fixture f;auto action=f.action();f.target_ready=false;f.fail(action);f.target_ready=true;check(!f.service->prepare_action(1,1));
    action=f.action();f.throw_ready=true;f.fail(action);f.throw_ready=false;check(!f.service->prepare_action(1,1));
    action=f.action();f.throw_resolve=true;f.fail(action);f.throw_resolve=false;check(!f.service->prepare_action(1,1));
    action=f.action();f.owners.erase(1);f.fail(action);
}
void sql_staleness_and_battle() {
    for(unsigned kind=0;kind<5;++kind) {
        Fixture f;const auto action=f.action();
        if(kind==0)execute(f.db,"UPDATE owned_guild_governance_0078 SET capacity=19");
        if(kind==1)execute(f.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2");
        if(kind==2)f.repo->cancel(f.repo->nonmember(3,3),*f.repo->pending(3,3),f.seed_proof);
        if(kind==3)f.repo->member_leave(f.repo->identity(6,6),*f.guilds->load(6,6),f.repo->leader(1,1),f.repo->applications(f.guild),f.seed_proof);
        if(kind==4)f.online.erase(6);
        f.fail(action);
    }
    for(const unsigned id:{1u,2u}) {
        Fixture f;const auto action=f.action();SqliteRecoveredCharacterRepository chars(f.db);
        const auto resources=chars.load_resources(id,id);check(bool(resources));check(chars.reserve_battle(id,id,*resources)>0);
        f.fail(action);check(!f.service->prepare_action(1,1));
    }
}
void rollback_requires_reopen() {
    for(const bool owner:{true,false}) {
        Fixture f;const auto action=f.action();f.lose_owner_in_transaction=owner;f.lose_target_in_transaction=!owner;
        f.fail(action);f.lose_owner_in_transaction=f.lose_target_in_transaction=false;check(f.guilds->load(2,2).has_value());
        check(!f.service->prepare_action(1,1));check(f.service->execute(f.action()));
    }
    for(const bool owner:{true,false}) {
        Fixture f;const auto action=f.action();f.lose_owner_after_write=owner;f.lose_target_after_write=!owner;
        f.fail(action);f.lose_owner_after_write=f.lose_target_after_write=false;check(f.guilds->load(2,2).has_value());
        check(!f.service->prepare_action(1,1));const auto next=f.action();check(f.service->execute(next));
    }
    for(const std::string effect:{"UPDATE unknown_save SET blob=X'12';", "UPDATE accounts SET password_hash='changed' WHERE id=8;",
                                   "SELECT RAISE(IGNORE);"}) {
        Fixture f;execute(f.db,"CREATE TRIGGER fault "+std::string(effect=="SELECT RAISE(IGNORE);"?"BEFORE":"AFTER")+
            " DELETE ON owned_guild_members BEGIN "+effect+" END");
        const auto action=f.action();f.fail(action);check(f.guilds->load(2,2).has_value());
    }
}
}
int main(){try{publication_and_permissions();lifecycle_and_persistence();stale_serial_and_batch();owner_and_target_readiness();
    sql_staleness_and_battle();rollback_requires_reopen();
    std::cout<<"TEST_ONLY kick0080 service: "<<checks<<" checks passed; no native UI qualification\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
