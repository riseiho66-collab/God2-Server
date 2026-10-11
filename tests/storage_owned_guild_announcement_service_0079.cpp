#include "handlers/OwnedGuildAnnouncementService.h"
#include <memory>
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <source_location>
#include <vector>

namespace announcement_test {
using Member=god2::SqliteOwnedGuildMembershipRepository;
using Repo=god2::SqliteOwnedGuildAnnouncementRepository;
using god2::sqlite_detail::execute;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Announcement storage check "+std::to_string(checks)+" line "+std::to_string(at.line()));
}
template<class F> void rejects(F action,const std::source_location at=std::source_location::current()) {
    bool rejected=false;try{action();}catch(const god2::DatabaseError&){rejected=true;}check(rejected,at);
}
// Independent typed database oracle: retain type names, bytes, and duplicate
// rows, plus all schema. This does not rely on either repository's private guard.
std::vector<std::string> state(sqlite3* db,const std::string& skip={}) {
    std::vector<std::string> result;
    god2::sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row())for(int c=0;c<4;++c)result.push_back("schema:"+schema.text(c));
    god2::sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);if(name==skip)continue;
        std::string quoted="\"";for(const auto c:name){quoted+=c;if(c=='\"')quoted+=c;}quoted+='\"';
        sqlite3_stmt* q=nullptr;god2::sqlite_detail::check(db,sqlite3_prepare_v2(db,("SELECT * FROM "+quoted).c_str(),-1,&q,nullptr));
        struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
        std::vector<std::string> rows;int rc;
        while((rc=sqlite3_step(q))==SQLITE_ROW) {
            std::string row=name+":";
            for(int c=0;c<sqlite3_column_count(q);++c) {
                const auto type=sqlite3_column_type(q,c);row+=std::to_string(type)+":";
                if(type==SQLITE_NULL)continue;
                const auto size=sqlite3_column_bytes(q,c);const auto* data=static_cast<const char*>(sqlite3_column_blob(q,c));
                row+=std::to_string(size)+":";if(size)row.append(data,static_cast<std::size_t>(size));
            }
            rows.push_back(std::move(row));
        }
        if(rc!=SQLITE_DONE)throw std::runtime_error("Independent database oracle failed");
        std::sort(rows.begin(),rows.end());result.insert(result.end(),rows.begin(),rows.end());
    }
    return result;
}
struct Fixture {
    sqlite3* db=nullptr;
    Member::Policy policy{50000,30,20};
    Member::Proof proof{[]{},[]{}}; // TEST_ONLY world readiness, no ports/session permissions.
    Member::Leader leader;
    std::uint64_t guild{};
    explicit Fixture(const std::string& path=":memory:",bool utf16=false) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)execute(db,"PRAGMA encoding='UTF-16be'");
        auto migrations=god2::default_sqlite_migrations();check(migrations.size()==49);
        
        god2::SqliteMigrationManager(db,migrations).migrate();god2::SqliteTradeRepository(db).install_schema();
        execute(db,Repo::schema()); // Explicit test-only schema proposal, not migration50.
        for(unsigned i=1;i<=4;++i) {
            god2::sqlite_detail::Statement a(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_NOT_LOGIN')");
            a.bind(1,i);a.bind(2,"AnnAccount"+std::to_string(i));a.done();
            const auto name="AnnPlayer"+std::to_string(i);const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            std::array<std::uint8_t,40> profile{};std::copy(bytes.begin(),bytes.end(),profile.begin());profile[29]=1;
            god2::sqlite_detail::Statement c(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,bytes);c.done();
            god2::RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            god2::sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();
            god2::sqlite_detail::Statement w(db,"INSERT INTO character_trade_wallets(character_id,amount,revision,design_id) VALUES(?,100000,1,'CUSTOM-0063')");
            w.bind(1,i);w.done();
            god2::SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        }
        Member members(db);god2::SqliteTradeRepository money(db);
        guild=members.create(members.nonmember(1,1),*money.load_wallet(1,1),"AnnGuild",policy,proof).leader.governance.guild_id;
        const auto application=members.apply(members.nonmember(2,2),members.guild(guild),proof);
        members.approve(members.leader(1,1),application,proof);leader=members.leader(1,1);
        members.apply(members.nonmember(3,3),members.guild(guild),proof);
        execute(db,"CREATE TABLE unknown_save(v,blob BLOB,text TEXT);INSERT INTO unknown_save VALUES(NULL,X'00017F','unchanged');"
                   "INSERT INTO unknown_save VALUES(1.25,X'', '');INSERT INTO unknown_save SELECT * FROM unknown_save;");
    }
    ~Fixture(){if(db)sqlite3_close(db);}
    Repo repo(){return Repo(db);}
    template<class F> void failed(F action,const std::source_location at=std::source_location::current()) {
        const auto before=state(db);rejects(action,at);check(state(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
    Repo::Snapshot save(const Repo::Snapshot& before,const std::string& text) {return repo().save(leader,before,text,proof);}
};

using Service=god2::OwnedGuildAnnouncementService;
using Wire=Service::Wire;
struct Harness:Fixture {
    std::map<std::uint64_t,Service::Owner> owners;
    Member members{db};
    Repo announcements{db};
    god2::SqliteGuildRepository guilds{db};
    bool throw_resolve=false,lose_after_write=false;
    god2::OwnedGuildLeaderPanelService panels;
    Service service;
    Harness():panels(members,[this](auto id){return resolve(id);},
        [this](auto a,auto c){return guilds.load(a,c);},[]{return std::set<std::uint32_t>{1,2,3,4};}),
        service(announcements,panels,[this](auto id){return resolve(id);}) {
        for(unsigned i=1;i<=4;++i)owners.emplace(i,Service::Owner{i,i,i,1,4,3,59,60,950,1,1});
    }
    std::optional<Service::Owner> resolve(std::uint64_t id) {
        if(throw_resolve)throw god2::DatabaseError("TEST_ONLY resolver failure");
        if(lose_after_write) {
            god2::sqlite_detail::Statement q(db,"SELECT count(*) FROM owned_guild_announcements_0078");
            check(q.row());if(q.integer(0)>0)return {};
        }
        const auto at=owners.find(id);return at==owners.end()?std::nullopt:std::optional{at->second};
    }
    Service::Time now=Service::Time{}+std::chrono::seconds{1000};
    Service::ActionPlan open(unsigned id=1,Service::Time time={}) {
        if(time==Service::Time{})time=now;
        const auto plan=service.prepare(id,true);check(bool(plan));check(service.current(*plan));
        const auto update=Wire::update(Wire::text_request(plan->announcement.value?plan->announcement.value->text_utf8:"",owners.at(id).name_codepage));
        check(bool(update));check(plan->logical.size()==plan->panel.logical.size()+update->size());
        check(std::equal(update->begin(),update->end(),plan->logical.end()-update->size()));
        check(service.published(*plan,time));auto action=service.prepare_action(id,time);check(bool(action));return *action;
    }
    void fail(const Service::ActionPlan& action,const Wire::Request& req,Service::Time time={}) {
        if(time==Service::Time{})time=now;
        const auto before=state(db);check(!service.execute(action,req,time));check(state(db)==before);
        check(sqlite3_get_autocommit(db)==1);check(!service.prepare_action(action.panel.owner.session,time));
    }
};
void permissions() {
    Harness h;check(!h.service.prepare(3,true));check(!h.service.prepare(4,true));
    auto plan=h.service.prepare(1,true);check(bool(plan));check(!h.service.prepare_action(1,h.now));
    // A successfully prepared but unqueued publication grants no lease.
    auto readonly=h.service.prepare(1);check(readonly && h.service.published(*readonly,h.now));
    check(!h.service.prepare_action(1,h.now));
    auto member=h.service.prepare(2,true);check(member && h.service.published(*member,h.now));
    check(!h.service.prepare_action(2,h.now));
    auto action=h.open();auto forged=action;forged.publication++;
    check(!h.service.execute(forged,Wire::text_request("forged",950),h.now));
    check(h.service.prepare_action(1,h.now)==action);
    forged=action;forged.panel.owner.account=2;check(!h.service.execute(forged,{},h.now));
    const auto reopened=h.open();check(reopened.publication>action.publication);
    check(!h.service.execute(action,{},h.now));check(h.service.prepare_action(1,h.now)==reopened);
    h.service.invalidate(1);check(!h.service.prepare_action(1,h.now));
    action=h.open();h.service.forget(1);check(!h.service.execute(action,{},h.now));
    // Capturing before a batch prefix that opens a new panel gives no action.
    const auto captured=h.service.prepare_action(1,h.now);h.open();check(!captured);
}
void lifecycle_and_locales() {
    for(const auto cp:{950,936}) {
        Harness h;h.owners[1].name_codepage=static_cast<std::uint16_t>(cp);
        auto action=h.open();const auto preserved=state(h.db,"owned_guild_announcements_0078");
        const auto request=Wire::text_request("  公告 100%  ",static_cast<std::uint16_t>(cp));
        const auto encoded=Wire::encode_request(request);check(encoded && Wire::decode(*encoded)==request);
        const auto saved=h.service.execute(action,request,h.now);check(saved && saved->value==Repo::Value{"  公告 100%  ",1});
        check(h.announcements.load(h.guild)==saved);check(state(h.db,"owned_guild_announcements_0078")==preserved);
        check(!h.service.execute(action,request,h.now));check(!h.service.prepare_action(1,h.now));
        auto echo=h.service.prepare(1);check(echo && h.service.published(*echo,h.now));check(!h.service.prepare_action(1,h.now));
        auto clear=h.open();const auto empty=h.service.execute(clear,{},h.now);check(empty && empty->value==Repo::Value{"",2});
        auto maximum=h.open();const auto big=h.service.execute(maximum,Wire::text_request(std::string(1040,'x'),static_cast<std::uint16_t>(cp)),h.now);
        check(big && big->value->revision==3 && big->value->text_utf8.size()==1040);
        const auto member=h.service.prepare(2,true);check(member && member->announcement==big);
    }
}
void expiry_and_owner() {
    Harness h;auto action=h.open();check(!h.service.prepare_action(1,h.now-std::chrono::nanoseconds{1}));
    check(bool(h.service.prepare_action(1,h.now+Service::lifetime-std::chrono::nanoseconds{1})));
    auto idle=h.service.prepare(1);check(idle && h.service.published(*idle,h.now+std::chrono::seconds{250}));
    h.fail(action,{},h.now+Service::lifetime); // readonly publication does not renew.
    auto plan=h.service.prepare(1,true);check(plan && !h.service.published(*plan,Service::Time::max()));
    for(unsigned field=0;field<11;++field) {
        Harness f;auto a=f.open();const auto original=f.owners[1];auto& o=f.owners[1];
        switch(field){case 0:++o.session;break;case 1:++o.account;break;case 2:++o.character;break;
            case 3:++o.world_generation;break;case 4:++o.area;break;case 5:++o.scene;break;
            case 6:++o.x;break;case 7:++o.y;break;case 8:o.name_codepage=936;break;
            case 9:++o.battle_generation;break;case 10:++o.position_revision;break;}
        f.service.observe_world(1);o=original;f.fail(a,{}); // ABA cannot restore publication.
    }
    Harness absent;auto a=absent.open();absent.owners.erase(1);absent.service.observe_world(1);absent.fail(a,{});
    Harness throwing;auto b=throwing.open();throwing.throw_resolve=true;throwing.service.observe_world(1);
    throwing.throw_resolve=false;throwing.fail(b,{});
}
void stale_and_battle() {
    for(unsigned kind=0;kind<5;++kind) {
        Harness h;auto action=h.open();
        if(kind==0)h.announcements.save(h.members.leader(1,1),action.announcement,"other editor",h.proof);
        if(kind==1)execute(h.db,"UPDATE owned_guild_governance_0078 SET capacity=19");
        if(kind==2)execute(h.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2");
        if(kind==3)h.members.cancel(h.members.nonmember(3,3),*h.members.pending(3,3),h.proof);
        if(kind==4)h.members.member_leave(h.members.identity(2,2),*h.guilds.load(2,2),h.members.leader(1,1),h.members.applications(h.guild),h.proof);
        h.fail(action,{});
    }
    Harness h;auto action=h.open();god2::SqliteRecoveredCharacterRepository chars(h.db);
    const auto resources=chars.load_resources(1,1);check(bool(resources));check(chars.reserve_battle(1,1,*resources)>0);
    check(!h.service.prepare(1,true));auto member=h.service.prepare(2,true);
    check(member && h.service.published(*member,h.now));check(!h.service.prepare_action(2,h.now));
    h.fail(action,Wire::text_request("battle",950));
    // Nonfounder battle does not suppress the founder's independent authority.
    Harness ordinary;god2::SqliteRecoveredCharacterRepository c(ordinary.db);const auto r=c.load_resources(2,2);check(bool(r));
    check(c.reserve_battle(2,2,*r)>0);auto a=ordinary.open();check(ordinary.service.execute(a,{},ordinary.now).has_value());
}
void malformed_and_atomicity() {
    for(const Wire::Request& req:std::vector<Wire::Request>{{{0}},{{0xff}},{{'a','\n'}},{{0x7f}},{{'\t'}},{std::vector<std::uint8_t>(1041,'x')}}) {
        Harness h;auto a=h.open();h.fail(a,req);
    }
    Harness world;auto a=world.open();world.lose_after_write=true;
    world.fail(a,Wire::text_request("after SQL proof fails",950));world.lose_after_write=false;
    check(!world.announcements.load(world.guild).value);
    for(const std::string effect:{"UPDATE unknown_save SET blob=X'12';","UPDATE accounts SET password_hash='changed' WHERE id=4;",
        "UPDATE owned_guild_announcements_0078 SET text_utf8='rewrite';","SELECT RAISE(IGNORE);"}) {
        Harness h;execute(h.db,"CREATE TRIGGER fault "+std::string(effect=="SELECT RAISE(IGNORE);"?"BEFORE":"AFTER")+" INSERT ON owned_guild_announcements_0078 BEGIN "+effect+" END");
        auto action=h.open();h.fail(action,Wire::text_request("original",950));
    }
    Harness extended;execute(extended.db,"ALTER TABLE owned_guild_announcements_0078 ADD COLUMN future_blob BLOB DEFAULT X'00127F'");
    auto action=extended.open();auto saved=extended.service.execute(action,Wire::text_request("one",950),extended.now);check(bool(saved));
    god2::sqlite_detail::Statement q(extended.db,"SELECT hex(future_blob) FROM owned_guild_announcements_0078");check(q.row() && q.text(0)=="00127F");
    execute(extended.db,"CREATE TRIGGER fault AFTER UPDATE ON owned_guild_announcements_0078 BEGIN UPDATE owned_guild_announcements_0078 SET future_blob=X'12'; END");
    auto update=extended.open();extended.fail(update,Wire::text_request("two",950));
}
}
int main(){try{announcement_test::permissions();announcement_test::lifecycle_and_locales();announcement_test::expiry_and_owner();
    announcement_test::stale_and_battle();announcement_test::malformed_and_atomicity();
    std::cout<<"TEST_ONLY announcement service: "<<announcement_test::checks<<" checks passed; no native UI qualification\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
