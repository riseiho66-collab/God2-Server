#include "handlers/OwnedGuildOfficerWorldHostDraft.h"
#include "handlers/OwnedGuildOfficerRuntimeDraft.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <random>
#include <source_location>

namespace {
using namespace god2;
using Repo=SqliteOwnedGuildMembershipRepository;
using Rows=std::vector<std::vector<std::uint8_t>>;
using Snapshot=std::map<std::string,Rows>;
using Exclusions=std::map<std::string,std::string>;
unsigned checks=0;unsigned negative_cases=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Guild officer0082 line "+std::to_string(at.line()));
}
void number(std::vector<std::uint8_t>& row,std::uint64_t value) {
    for(unsigned i=0;i<8;++i)row.push_back(static_cast<std::uint8_t>(value>>(8*i)));
}
std::string quote(const std::string& name) {
    std::string value="\"";for(const auto c:name){value+=c;if(c=='\"')value+=c;}return value+'\"';
}
// Independent oracle, including types, all bytes, duplicate rows and all schema.
// Never use the implementation's guard as its own expected result.
Snapshot snapshot(sqlite3* db,const Exclusions& exclusions={}) {
    Snapshot result;
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row()) {
        std::vector<std::uint8_t> row;
        for(int c=0;c<4;++c){const auto text=schema.text(c);number(row,text.size());row.insert(row.end(),text.begin(),text.end());}
        result[":schema"].push_back(std::move(row));
    }
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);const auto exclude=exclusions.find(name);
        const auto sql="SELECT * FROM "+quote(name)+(exclude==exclusions.end()?"":" WHERE "+exclude->second);
        sqlite3_stmt* q=nullptr;check(sqlite3_prepare_v2(db,sql.c_str(),-1,&q,nullptr)==SQLITE_OK);
        std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> query(q,sqlite3_finalize);
        auto& rows=result[name];int rc=SQLITE_OK;
        while((rc=sqlite3_step(q))==SQLITE_ROW) {
            std::vector<std::uint8_t> row;
            for(int c=0;c<sqlite3_column_count(q);++c) {
                const auto type=sqlite3_column_type(q,c);row.push_back(static_cast<std::uint8_t>(type));
                if(type==SQLITE_INTEGER)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(q,c)));
                else if(type==SQLITE_FLOAT)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(q,c)));
                else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                    const auto size=sqlite3_column_bytes(q,c);number(row,static_cast<std::uint64_t>(size));
                    const auto* data=type==SQLITE_TEXT?sqlite3_column_text(q,c):static_cast<const unsigned char*>(sqlite3_column_blob(q,c));
                    if(size)row.insert(row.end(),data,data+size);
                }
            }
            rows.push_back(std::move(row));
        }
        check(rc==SQLITE_DONE);std::sort(rows.begin(),rows.end());
    }
    return result;
}
std::int64_t scalar(sqlite3* db,const char* sql) {
    sqlite_detail::Statement q(db,sql);check(q.row());return q.integer(0);
}
struct Fixture {
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteGuildRepository> memberships;
    std::unique_ptr<SqliteTradeRepository> money;
    std::uint64_t guild{},foreign{};
    const Repo::Proof proof{[]{},[]{}}; // TEST_ONLY world readiness, no gameplay authority minted.
    explicit Fixture(const std::string& path=":memory:",bool utf16=false,bool simplified=false,bool opaque=true) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)sqlite_detail::execute(db,"PRAGMA encoding='UTF-16be'");
        auto migrations=owned_guild_announcement_migrations();check(migrations.size()==50);migrations.push_back({51,"owned_guild_officers_candidate",Repo::officer_schema()});
        SqliteMigrationManager(db,migrations).migrate();check(scalar(db,"SELECT max(version) FROM schema_migrations")==51);
        repo=std::make_unique<Repo>(db);memberships=std::make_unique<SqliteGuildRepository>(db);
        money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        for(unsigned i=1;i<=7;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_OPAQUE_HASH')");
            account.bind(1,i);account.bind(2,"DisAccount"+std::to_string(i));account.done();
            const auto name="DisPlayer"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=static_cast<std::uint8_t>(i);
            const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,?)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);character.bind_blob(4,bytes);character.bind(5,simplified?936:950);character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();money->provision_wallet(i,i);
            SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        }
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000"); // Explicit disposable funds.
        guild=create(1,"DisGuild");join(2,guild);apply(3,guild);
        foreign=create(4,"ForeignGuild");join(5,foreign);apply(6,foreign);
        SqliteOwnedGuildAnnouncementRepository announcements(db);
        announcements.save(repo->leader(1,1),announcements.load(guild),"Saved primary 100%",proof);
        announcements.save(repo->leader(4,4),announcements.load(foreign),"Saved foreign",proof);
        if(opaque)sqlite_detail::execute(db,
            "ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque_rank BLOB DEFAULT X'00F2';"
            "ALTER TABLE owned_guilds ADD COLUMN opaque_blob BLOB DEFAULT X'0002FF';"
            "ALTER TABLE owned_guilds ADD COLUMN opaque_float DEFAULT 1.25;"
            "ALTER TABLE owned_guild_members ADD COLUMN opaque_member BLOB DEFAULT X'0012';"
            "ALTER TABLE owned_guild_applications_0078 ADD COLUMN opaque_request BLOB DEFAULT X'0013';"
            "ALTER TABLE owned_guild_governance_0078 ADD COLUMN opaque_governance BLOB DEFAULT X'0014';"
            "ALTER TABLE owned_guild_announcements_0078 ADD COLUMN opaque_notice BLOB DEFAULT X'0015';"
            "CREATE TABLE unknown_save(number,bytes BLOB,label TEXT);"
            "INSERT INTO unknown_save VALUES(NULL,X'','');"
            "INSERT INTO unknown_save VALUES(1.25,X'000102FF',NULL);"
            "INSERT INTO unknown_save SELECT * FROM unknown_save;"
            "CREATE TABLE opaque_item_fixture(character_id INTEGER,instance BLOB);"
            "INSERT INTO opaque_item_fixture VALUES(2,X'00FF12'),(5,X'FF0001');"
            "CREATE INDEX unknown_save_index ON unknown_save(label);"
            "CREATE TRIGGER unknown_save_trigger AFTER UPDATE ON unknown_save BEGIN SELECT 1;END;");
    }
    ~Fixture(){money.reset();memberships.reset();repo.reset();if(db)sqlite3_close_v2(db);}
    std::uint64_t create(unsigned person,const std::string& name) {
        return repo->create(repo->nonmember(person,person),*money->load_wallet(person,person),name,{50000,30,20},proof).leader.governance.guild_id;
    }
    Repo::Application apply(unsigned person,std::uint64_t target) {
        return repo->apply(repo->nonmember(person,person),repo->guild(target),proof);
    }
    void join(unsigned person,std::uint64_t target) {
        const auto application=apply(person,target);const auto gov=repo->governance(target);
        repo->approve(repo->leader(gov.owner_account,gov.owner_character),application,proof);
    }
    struct Lease {Repo::Leader leader;std::vector<Repo::Application> applications;};
    Lease lease() {return {repo->leader(1,1),repo->applications(guild)};}
    Repo::Disbanded disband(const Lease& lease,const Repo::Proof& callbacks) {
        return repo->disband(lease.leader,lease.applications,callbacks);
    }
    Repo::Disbanded disband(const Lease& lease) {return disband(lease,proof);}
    template<class F> void failed(F action,const std::source_location at=std::source_location::current()) {
        ++negative_cases;const auto before=snapshot(db);bool rejected=false;
        try{action();}catch(const DatabaseError&){rejected=true;}
        check(rejected,at);check(snapshot(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
};

unsigned service_cases=0;
using Service=OwnedGuildOfficerServiceDraft;using Projection=OwnedGuildOfficerProjectionDraft;using Panel=OwnedGuildLeaderPanelService;
void begin_case(const char* name){++service_cases;std::cout<<"CASE "<<name<<'\n';}
struct WorldFixture:Fixture {
    std::unique_ptr<Panel> panel;std::unique_ptr<Projection> projection;std::unique_ptr<Service> service;
    std::map<std::uint64_t,Panel::Owner> owners;std::set<std::uint32_t> online;
    std::set<std::uint64_t> unready;
    std::function<void()> on_capture,on_world;
    bool deny_sql=false,deny_after_write=false,wrote=false;
    unsigned after_write_calls=0;
    WorldFixture(bool simplified=false):Fixture(":memory:",false,simplified) {
        for(unsigned i=1;i<=7;++i){owners.emplace(i,Panel::Owner{i,i,i,1,4,3,59,60,static_cast<std::uint16_t>(simplified?936:950),1,1});online.insert(i);}
        check(sqlite3_create_function_v2(db,"test_officer_written",0,SQLITE_UTF8,this,
            [](sqlite3_context* c,int,sqlite3_value**){static_cast<WorldFixture*>(sqlite3_user_data(c))->wrote=true;sqlite3_result_int(c,1);},
            nullptr,nullptr,nullptr)==SQLITE_OK);
        sqlite_detail::execute(db,"CREATE TRIGGER officer_write_witness AFTER UPDATE ON owned_guilds WHEN NEW.id=1 BEGIN SELECT test_officer_written(); END");
        panel=std::make_unique<Panel>(*repo,[this](auto session){return resolve(session);},
            [this](auto account,auto character){return memberships->load(account,character);},[this]{return online;});
        projection=std::make_unique<Projection>(*repo,*panel);
        service=std::make_unique<Service>(*repo,*projection,[this](auto session){return resolve(session);},
            [this](const auto& state){return capture(state);},[this](const auto& state,const auto& world){return current_world(state,world);});
    }
    std::optional<Panel::Owner> resolve(std::uint64_t session) {
        const auto at=owners.find(session);if(at==owners.end())return {};return at->second;
    }
    std::optional<Service::WorldLease> capture(const Panel::State& state) {
        if(auto hook=std::exchange(on_capture,{}))hook();Service::WorldLease lease;
        for(const auto& [session,owner]:owners)for(const auto& row:state.rows)
            if(row.identity.character_id==owner.character && row.identity.account_id==owner.account) {
                if(unready.contains(session))return {};lease.connected.push_back(owner);break;
            }
        return lease;
    }
    bool current_world(const Panel::State&,const Service::WorldLease& world) {
        if(auto hook=std::exchange(on_world,{}))hook();
        if(wrote)++after_write_calls;
        if(deny_sql && !sqlite3_get_autocommit(db))return false;
        if(deny_after_write && wrote && !sqlite3_get_autocommit(db))return false;
        for(const auto& owner:world.connected)if(unready.contains(owner.session) || resolve(owner.session)!=std::optional{owner})return false;
        // This callback NEVER reads SQL membership/governance/profile/resources.
        return true;
    }
    Projection::Plan open(unsigned session=1) {
        auto plan=projection->prepare(session,true);check(bool(plan));check(projection->published(*plan));return *plan;
    }
    Service::Plan action(Service::Action kind=Service::Action::Appoint,unsigned session=1,std::uint8_t slot=1) {
        open(session);const auto plan=service->prepare(session,kind,slot);check(bool(plan));return *plan;
    }
    void fail(const Service::Plan& plan) {
        ++negative_cases;const auto before=snapshot(db);check(!service->execute(plan));check(snapshot(db)==before);check(sqlite3_get_autocommit(db)==1);
    }
};
using Runtime=OwnedGuildOfficerRuntimeDraft;
using Kind=Runtime::Kind;
using WorldHost=OwnedGuildOfficerWorldHostDraft;
struct RuntimeFixture:WorldFixture {
    std::unique_ptr<OwnedGuildKickService> kick;
    std::unique_ptr<Runtime> runtime;
    std::unique_ptr<SqliteOwnedGuildAnnouncementRepository> announcement_repo;
    std::unique_ptr<OwnedGuildAnnouncementService> announcements;
    RuntimeFixture(bool simplified=false):WorldFixture(simplified) {
        kick=std::make_unique<OwnedGuildKickService>(*repo,*panel,[this](auto s){return resolve(s);},
            [this](const Repo::Identity& target){for(const auto& [s,o]:owners)
                if(o.character==target.character_id && unready.contains(s))return false;return true;});
        runtime=std::make_unique<Runtime>(*panel,*kick,*projection,*service);
        announcement_repo=std::make_unique<SqliteOwnedGuildAnnouncementRepository>(db);
        announcements=std::make_unique<OwnedGuildAnnouncementService>(*announcement_repo,*panel,[this](auto s){return resolve(s);});
    }
    std::vector<Runtime::Captured> batch(std::initializer_list<Runtime::Request> requests,std::uint64_t session=1) {
        return runtime->capture(session,std::span<const Runtime::Request>(requests.begin(),requests.size()));
    }
};
void selection() {
    begin_case("installed51-flagfalse-baseline-routes-no-rank-activation");
    check((Runtime::Selection{true,true,true,false}.valid()));
    check(!(Runtime::Selection{true,true,true,false}.instantiate_officer_runtime()));
    check((Runtime::Selection{true,true,true,true}.instantiate_officer_runtime()));
    check(!(Runtime::Selection{false,true,true,true}.valid()));
    check(!(Runtime::Selection{true,false,true,true}.valid()));
    check(!(Runtime::Selection{true,true,false,true}.valid()));
}
void mixed_batch(bool simplified) {
    begin_case("preprefix-capture-appoint-then72-cannot-be-kick");RuntimeFixture f(simplified);f.open();
    const auto plans=f.batch({{0,0x71,1},{2,0x72,1}});check(plans.size()==2);
    check(plans[0].kind==Kind::Appoint);check(plans[1].kind==Kind::KickMember);
    check(std::holds_alternative<OwnedGuildKickService::ActionPlan>(plans[1].action));
    check(f.runtime->execute(plans[0]));check(!f.runtime->execute(plans[1]));
    check(f.memberships->load(2,2).has_value());check(f.repo->officer_history(f.guild).front().role==2);
    f.open();const auto demote=f.batch({{0,0x72,1}});check(demote.front().kind==Kind::RemoveOffice);
    check(std::holds_alternative<Service::Plan>(demote.front().action));
    check(f.runtime->execute(demote.front()));check(f.memberships->load(2,2).has_value());
    check(f.repo->officer_history(f.guild).front().role==1);
}
void frozen_routes(bool simplified) {
    begin_case("frozen-founder-applicant-approve-reject-and-memberleave");RuntimeFixture f(simplified);f.open();
    const auto approval=f.batch({{0,0x71,2},{3,0x71,1}});check(approval[0].kind==Kind::Approve);
    check(std::holds_alternative<Panel::ActionPlan>(approval[0].action));
    check(f.runtime->execute(approval[0]));check(!f.runtime->execute(approval[1]));check(f.memberships->load(3,3).has_value());
    f.apply(7,f.guild);f.open();const auto rejection=f.batch({{0,0x72,3}});check(rejection.front().kind==Kind::Reject);
    check(f.runtime->execute(rejection.front()));check(f.repo->applications(f.guild).empty());
    f.open(2);const auto leave=f.batch({{0,0x73,0}},2);check(leave.front().kind==Kind::MemberLeave);
    check(f.runtime->execute(leave.front()));check(!f.memberships->load(2,2));
    const auto clear=f.panel->prepare_clear(2);check(bool(clear));check(clear->logical.back()==0);
    check(f.runtime->complete_clear(*clear));check(!f.panel->cached(2));check(!f.projection->cached_role(2,0));
}
void officer_clear(bool simplified) {
    begin_case("officer-selfslot2-native73-clears-native92-and-retains-rankhistory");RuntimeFixture f(simplified);
    const auto appoint=f.action();check(f.service->execute(appoint));f.open(2);
    check(f.projection->cached_role(2,0)==std::optional<std::uint8_t>{2});
    const auto plans=f.batch({{0,0x73,0}},2);check(plans.front().kind==Kind::OfficerLeave);
    const auto history=f.repo->officer_history(f.guild);check(f.runtime->execute(plans.front()));
    check(!f.memberships->load(2,2));check(f.repo->officer_history(f.guild)==history);
    check(!f.runtime->execute(plans.front()));const auto clear=f.panel->prepare_clear(2);check(bool(clear));
    check(f.runtime->complete_clear(*clear));check(!f.panel->cached(2));check(!f.projection->publication(2));
}
void denial_and_reopen() {
    begin_case("role3-denial-consumes-own-publication-stale-denial-protects-new-open");RuntimeFixture f;f.open();
    const auto deny=f.batch({{0,0x72,0}});check(deny.front().kind==Kind::Denied);
    check(!f.runtime->execute(deny.front()));check(!f.projection->publication(1));
    f.open();const auto old=f.batch({{0,0x71,1}});f.open();const auto fresh=f.projection->publication(1);check(bool(fresh));
    check(!f.runtime->execute(old.front()));check(f.projection->publication(1)==fresh);
    const auto invalid=f.batch({{4,0x71,1},{2,0x72,1}});check(invalid[0].kind==Kind::Denied);check(invalid[1].kind==Kind::Denied);
    const auto before=snapshot(f.db);check(!f.runtime->execute(invalid[0]));check(snapshot(f.db)==before);
}
void readiness() {
    begin_case("prefix-readiness-loss-no-SQL-and-consumed-publication");RuntimeFixture f;f.open();
    const auto plans=f.batch({{0,0x71,1}});f.unready.insert(3);const auto before=snapshot(f.db);
    check(!f.runtime->execute(plans.front()));check(snapshot(f.db)==before);check(!f.projection->publication(1));
    f.unready.clear();f.open();const auto next=f.batch({{0,0x71,1}});
    f.owners.at(3).position_revision++;check(!f.runtime->execute(next.front()));check(snapshot(f.db)==before);
}
void notices(bool simplified) {
    begin_case("announcement91plus93plus98-one-publisher-no-double-serial");RuntimeFixture f(simplified);
    check(f.service->execute(f.action()));f.open();const auto prior=f.panel->action_publication(1);check(bool(prior));
    const auto notice=f.runtime->prepare_notice(*f.announcements,1,true);check(bool(notice));
    const auto& b=notice->original.panel.logical;const auto& d=notice->decorated.logical;
    check(d.size()==b.size()+3);check(std::equal(b.begin(),b.end(),d.begin()));
    check(d[d.size()-3]==0x93 && d[d.size()-2]==1 && d.back()==2);
    check(notice->logical.size()==notice->original.logical.size()+3);
    check(std::equal(notice->original.logical.begin()+b.size(),notice->original.logical.end(),notice->logical.begin()+d.size()));
    check(notice->logical[d.size()]==0x98);
    const auto now=OwnedGuildAnnouncementService::Time{};
    check(f.runtime->published_notice(*f.announcements,*notice,now));
    const auto after=f.panel->action_publication(1);check(bool(after));check(after->serial==prior->serial+1);
    check(f.projection->cached_role(1,1)==std::optional<std::uint8_t>{2});
    check(f.announcements->prepare_action(1,now).has_value());
    const auto readonly=f.runtime->prepare_notice(*f.announcements,1,false);check(bool(readonly));
    check(readonly->decorated.logical.empty());check(f.runtime->published_notice(*f.announcements,*readonly,now));
    check(f.panel->action_publication(1)==after);
    const auto member=f.runtime->prepare_notice(*f.announcements,2,true);check(bool(member));
    check(f.runtime->published_notice(*f.announcements,*member,now));check(!f.announcements->prepare_action(2,now));
    check(f.projection->cached_role(2,0)==std::optional<std::uint8_t>{2});
    const auto forbidden=f.batch({{0,0x71,2}},2);check(forbidden.front().kind==Kind::Approve);
    check(std::holds_alternative<std::monostate>(forbidden.front().action)); // officer admission OPEN, no grant.
    check(!f.runtime->execute(forbidden.front()));
}
void complete_world_audience() {
    begin_case("host-full-accepted-pending-duplicate-worldonly-afterdelete");RuntimeFixture f;const auto opened=f.open();
    f.owners.emplace(30,Panel::Owner{30,3,3,1,4,3,59,60,950,1,1});
    unsigned sql_peer_calls=0;bool sql_forbidden=false;
    WorldHost host([&]{std::vector<WorldHost::Live> live;for(const auto& [s,o]:f.owners)
        live.push_back({s,o.account,o.character,!f.unready.contains(s)});return live;},
        [&](auto s){return f.resolve(s);},[&](const auto& o){++sql_peer_calls;check(!sql_forbidden);
            return !f.unready.contains(o.session) && f.resolve(o.session)==std::optional{o};});
    const auto world=host.capture(opened.base.next);check(bool(world));check(world->connected.size()==4);
    check(std::any_of(world->connected.begin(),world->connected.end(),[](const auto& o){return o.session==30;}));
    const auto before=sql_peer_calls;sql_forbidden=true;
    check(host.current(opened.base.next,*world));check(sql_peer_calls==before);
    // New duplicate pending session invalidates full world snapshot.
    f.owners.emplace(31,Panel::Owner{31,3,3,1,4,3,59,60,950,1,1});check(!host.current(opened.base.next,*world));
    f.owners.erase(31);f.unready.insert(30);check(!host.current(opened.base.next,*world));f.unready.clear();
    f.owners.at(30).account=7;check(!host.current(opened.base.next,*world));f.owners.at(30).account=3;
    f.owners.erase(30);check(!host.current(opened.base.next,*world));
    sql_forbidden=false;
    const auto appoint=f.action();check(f.service->execute(appoint));const auto officer=f.open(2);
    const auto selfworld=host.capture(officer.base.next);check(bool(selfworld));
    const auto leave=f.service->prepare(2,Service::Action::SelfLeave,0);check(bool(leave));check(f.service->execute(*leave));
    check(!f.memberships->load(2,2));sql_forbidden=true;
    // Real membership removal already happened; world-only proof still succeeds.
    check(host.current(officer.base.next,*selfworld));
}
}
int main() {
    try {
        selection();for(const bool simplified:{false,true}){mixed_batch(simplified);frozen_routes(simplified);officer_clear(simplified);notices(simplified);}
        denial_and_reopen();readiness();complete_world_audience();
        std::cout<<"PASS "<<service_cases<<" cases "<<checks<<" checks\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
