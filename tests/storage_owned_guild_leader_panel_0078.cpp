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
        Fixture f;check(!f.service->prepare(1));const auto created=f.create(1);const auto id=created.leader.membership.guild_id;
        const auto other=f.create(4,"Other");const auto invariant=saved(f.db);
        const auto a2=f.apply(2,id);const auto a3=f.apply(3,id);
        check(!f.service->prepare(2));auto panel=f.panel(1);
        check(panel.next.rows.size()==3 && panel.next.rows[0].identity.character_id==1 && panel.next.rows[0].role==3);
        check(panel.next.rows[1].role==0 && panel.next.rows[1].application==std::optional{a2});
        check(panel.next.rows[2].role==0 && panel.next.rows[2].application==std::optional{a3});
        check(panel.logical.size()==3*22+53 && panel.logical[0]==0x91 && panel.logical[1]==0 && panel.logical[2]==3);
        check(panel.logical[3]==31 && panel.logical[4]==2 && panel.logical[5]==1);
        check(panel.logical[66]==0x8e && panel.logical[66+1+0x0d]==6 && panel.logical[66+1+0x13]==1 && panel.logical[66+1+0x17]==20);
        check(!f.service->prepare_action(1,Service::Action::Approve,0));
        check(!f.service->prepare_action(1,Service::Action::Reject,49));
        check(!f.service->prepare_action(4,Service::Action::Approve,1));
        auto approve=f.service->prepare_action(1,Service::Action::Approve,1);check(bool(approve));
        auto forged=*approve;forged.panel.owner.account=2;check(!f.service->execute(forged));
        forged=*approve;forged.slot=2;check(!f.service->execute(forged));
        const auto revision=created.leader.membership.guild_revision;
        check(f.service->execute(*approve));check(!f.service->execute(*approve));
        check(f.guilds->load(2,2)->guild_id==id && f.repo->guild(id).revision>revision && !f.repo->pending(2,2));
        check(!f.service->current(panel) && saved(f.db)==invariant);
        auto refresh=f.service->prepare(1);check(refresh && !refresh->open_panel && refresh->logical.size()==2*2+3*22);
        check(f.service->published(*refresh) && !f.service->prepare_action(1,Service::Action::Approve,2));
        const auto idle=f.service->prepare(1);check(idle && idle->logical.empty() && f.service->published(*idle));
        auto member=f.panel(2);check(member.next.rows[0].identity.character_id==2 && member.next.rows[0].role==1);
        check(member.next.rows[1].identity.character_id==1 && member.next.rows[1].role==3 && member.next.rows[2].role==0);
        check(member.logical[3*22+1+0x13]==2);
        check(!f.service->prepare_action(2,Service::Action::Reject,2));
        panel=f.panel(1);check(panel.logical[0]==0x92 && panel.logical[1]==1 && panel.logical[2]==0x92 && panel.logical[3]==2);
        check(panel.next.rows[1].identity.character_id==2 && panel.next.rows[1].role==1);
        auto reject=f.service->prepare_action(1,Service::Action::Reject,2);check(bool(reject));
        check(f.service->execute(*reject) && !f.repo->pending(3,3) && !f.guilds->load(3,3));
        check(f.repo->guild(id).revision==f.guilds->load(2,2)->guild_revision && saved(f.db)==invariant);
        check(f.repo->leader(4,4)==other.leader);
        // A captured action must survive neither a prior mutation nor ABA in
        // the same coalesced batch. Root captures it before prefix dispatch.
        f.apply(3,id);panel=f.panel(1);auto stale=f.service->prepare_action(1,Service::Action::Approve,2);check(bool(stale));
        ++f.owners[1].x;f.service->observe_world(1);--f.owners[1].x;
        check(!f.service->execute(*stale));
        auto tick=f.service->prepare(1);check(tick && tick->logical.empty() && !tick->open_panel && f.service->published(*tick));
        check(!f.service->prepare_action(1,Service::Action::Approve,2));panel=f.panel(1);
        check(panel.logical[0]==0x92); // invalidation preserved old slot cache.
        stale=f.service->prepare_action(1,Service::Action::Approve,2);check(bool(stale));f.service->invalidate(1);
        check(!f.service->execute(*stale));panel=f.panel(1);
        stale=f.service->prepare_action(1,Service::Action::Approve,2);check(bool(stale));
        f.online.erase(2);check(!f.service->execute(*stale));f.online.insert(2);panel=f.panel(1);
        const auto old_publication=*f.service->prepare_action(1,Service::Action::Approve,2);
        panel=f.panel(1);check(!f.service->execute(old_publication)); // explicit reopen supersedes captured action.
        stale=f.service->prepare_action(1,Service::Action::Approve,2);check(bool(stale));
        sqlite_detail::execute(f.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2");
        check(!f.service->execute(*stale));panel=f.panel(1);
        stale=f.service->prepare_action(1,Service::Action::Approve,2);check(bool(stale));
        // Lose authenticated world in the repository's after_write callback.
        // Approval generation/member/application must all roll back atomically.
        const auto before=f.repo->leader(1,1);const auto pending=f.repo->pending(3,3);
        f.lose_on=f.resolves+4;
        check(!f.service->execute(*stale));f.lose_on=0;
        check(f.repo->leader(1,1)==before && f.repo->pending(3,3)==pending && !f.guilds->load(3,3));
        check(sqlite3_get_autocommit(f.db)==1);panel=f.panel(1);
        reject=f.service->prepare_action(1,Service::Action::Reject,2);check(bool(reject));
        f.throw_resolve=true;check(!f.service->execute(*reject) && !f.service->prepare(1));f.throw_resolve=false;
        f.throw_online=true;check(!f.service->prepare(1));f.throw_online=false;
        panel=f.panel(1);reject=f.service->prepare_action(1,Service::Action::Reject,2);check(bool(reject));
        f.service->forget(1);check(!f.service->execute(*reject));
        // Native50 admission is atomic: reject a 51st row without stranding
        // any existing application or invalidating the published lease.
        Fixture overflow;const auto over=overflow.create(1);for(unsigned person=2;person<=50;++person)overflow.apply(person,over.leader.membership.guild_id);
        auto full=overflow.panel(1);check(full.next.rows.size()==50 && full.logical.size()==50*22+53);
        auto repeat=overflow.panel(1);check(repeat.logical.size()==49*2+50*22+53 && repeat.logical[0]==0x92);
        auto old=overflow.service->prepare_action(1,Service::Action::Approve,49);check(bool(old));
        bool refused=false;
        try{overflow.apply(51,over.leader.membership.guild_id);}catch(const DatabaseError&){refused=true;}
        check(refused && !overflow.repo->pending(51,51));
        check(overflow.repo->applications(over.leader.membership.guild_id).size()==49 && !overflow.guilds->load(51,51));
        check(overflow.service->current(repeat) && overflow.service->execute(*old));
        check(overflow.guilds->load(50,50).has_value() && overflow.repo->applications(over.leader.membership.guild_id).size()==48);
        check(overflow.panel(1).next.rows.size()==50);
        Fixture cap;const auto limited=cap.create(1);const auto capid=limited.leader.membership.guild_id;
        for(unsigned person=2;person<=21;++person)cap.apply(person,capid);
        for(unsigned person=2;person<=20;++person) {
            auto p=cap.panel(1);check(p.next.rows[person-1].identity.character_id==person);
            auto a=cap.service->prepare_action(1,Service::Action::Approve,static_cast<std::uint8_t>(person-1));check(bool(a));
            check(cap.service->execute(*a));
        }
        const auto maxed=cap.panel(1);check(maxed.next.leader.roster.size()==20 && maxed.next.rows.size()==21);
        auto excess=cap.service->prepare_action(1,Service::Action::Approve,20);check(bool(excess));
        const auto maxed_leader=cap.repo->leader(1,1);const auto maxed_app=cap.repo->pending(21,21);
        check(!cap.service->execute(*excess) && cap.repo->leader(1,1)==maxed_leader && cap.repo->pending(21,21)==maxed_app);
        check(!cap.guilds->load(21,21));
        // Projection does not itself grant SQL authority after forged ownership.
        ++f.owners[2].account;check(!f.service->prepare(2));--f.owners[2].account;
        check(sqlite3_get_autocommit(f.db)==1);
        std::cout<<"PASS "<<checks<<" full-schema leader panel/CAS checks; source-only, not live UI acceptance\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
