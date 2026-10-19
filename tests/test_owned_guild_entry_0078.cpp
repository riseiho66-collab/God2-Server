#include "handlers/OwnedGuildEntryService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>

using namespace god2;
namespace {
using Entry=OwnedGuildEntryService;
using Repo=Entry::Repository;
unsigned checks=0;
void check(bool value) {++checks;if(!value)throw std::runtime_error("Entry service check "+std::to_string(checks));}
struct Fixture {
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteTradeRepository> money;
    std::unique_ptr<Entry> service;
    std::map<std::uint64_t,Entry::Owner> owners;
    bool world_ready=true,fail_resolve=false,fail_read=false,foreign_snapshot=false,member_snapshot=false;
    unsigned resolves=0,vanish_at=0;
    Entry::Time now{std::chrono::seconds{100}};
    Fixture() {
        check(sqlite3_open(":memory:",&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        auto migrations=default_sqlite_migrations();check(migrations.size()==49);
        SqliteMigrationManager(db,migrations).migrate();repo=std::make_unique<Repo>(db);
        money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        for(unsigned i=1;i<=3;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'test-unchanged')");
            account.bind(1,i);account.bind(2,"EntryOwner"+std::to_string(i));account.done();
            const auto name="Entry"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=1;
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);
            character.bind_blob(4,std::span(reinterpret_cast<const std::uint8_t*>(name.data()),name.size()));character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=30;role[17]=100;role[21]=50;
            sqlite_detail::Statement level(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            level.bind(1,i);level.bind_blob(2,role);level.done();money->provision_wallet(i,i);
            owners.emplace(i,Entry::Owner{i,i,i,1,4,3,59,60,static_cast<std::uint16_t>(i==2?936:950)});
        }
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000");
        service=std::make_unique<Entry>([this](auto session)->std::optional<Entry::Owner> {
            ++resolves;if(fail_resolve)throw DatabaseError("Test resolver failure");
            if(!world_ready || (vanish_at && resolves>=vanish_at))return {};
            const auto it=owners.find(session);return it==owners.end()?std::nullopt:std::optional{it->second};
        },[this](const auto& owner)->std::optional<Repo::Identity> {
            if(fail_read)throw DatabaseError("Test eligible failure");
            if(repo->pending(owner.account,owner.character))return {};
            auto result=repo->nonmember(owner.account,owner.character);
            if(foreign_snapshot){result.account_id=2;result.character_id=2;}
            if(member_snapshot)result.membership_revision=1;
            return result;
        });
    }
    ~Fixture(){service.reset();money.reset();repo.reset();if(db)sqlite3_close(db);}
    Entry::Plan menu(unsigned session=1) {
        auto plan=service->prepare(session,now);check(bool(plan));
        check(!service->pending(session) && !service->prepare_choice(session,now));
        check(service->published(*plan,now));check(service->pending(session));return *plan;
    }
    RecoveredQuestAction::Request action(const Entry::Lease& lease,unsigned choice=0) {
        return {lease.request,static_cast<std::uint16_t>(choice),Entry::context,0xa5};
    }
};
void lifecycle() {
    Fixture f;const auto before=sqlite3_total_changes64(f.db);
    check(!f.service->prepare(0,f.now));check(!f.service->prepare(99,f.now));
    auto plan=f.menu();check(plan.lease.request==1);
    check(plan.logical[0]==0x7a && plan.logical[1]==28 && plan.logical[2]==0 && plan.logical[3]==4);
    check(plan.logical[4]==Entry::context && plan.logical[5]==1 && plan.logical[6]==0);
    check(plan.logical[7]==0xb4 && plan.logical[8]==0x0b); //2996
    check(std::all_of(plan.logical.begin()+9,plan.logical.end(),[](auto b){return b==0;}));
    check(!f.service->published(plan,f.now)); // Publication cannot repeat.
    auto lease=f.service->prepare_choice(1,f.now);check(lease && *lease==plan.lease);
    auto wrong=f.action(*lease);++wrong.request_word;
    check(!f.service->consume(*lease,wrong,f.now) && f.service->pending(1));
    wrong=f.action(*lease);++wrong.context_byte;
    check(!f.service->consume(*lease,wrong,f.now) && f.service->pending(1));
    auto forged=*lease;++forged.owner.session;check(!f.service->consume(forged,f.action(forged),f.now));
    forged=*lease;++forged.identity.character_id;check(!f.service->consume(forged,f.action(forged),f.now));
    check(f.service->consume(*lease,f.action(*lease),f.now)==Entry::Choice::Create);
    check(!f.service->pending(1) && !f.service->consume(*lease,f.action(*lease),f.now));
    for(unsigned choice:{1,2,3,4,0xffff}) {
        plan=f.menu();lease=f.service->prepare_choice(1,f.now);check(bool(lease));
        const auto result=f.service->consume(*lease,f.action(*lease,choice),f.now);
        check(result.has_value()==(choice<3));if(result)check(static_cast<unsigned>(*result)==choice);
        check(!f.service->pending(1) && !f.service->consume(*lease,f.action(*lease,0),f.now));
    }
    plan=f.menu(2);lease=f.service->prepare_choice(2,f.now);check(lease && lease->owner.name_codepage==936);
    check(f.service->consume(*lease,f.action(*lease,2),f.now)==Entry::Choice::Exit);
    check(sqlite3_total_changes64(f.db)==before && sqlite3_get_autocommit(f.db)==1); // Entry never writes SQL.
}
void recognition_scope() {
    Fixture f;
    RecoveredQuestAction::Request action{1,0,Entry::context,0};
    check(!f.service->recognizes(1,action)); // No nonce has been issued.
    const auto first=f.menu();action=f.action(first.lease);
    check(f.service->recognizes(1,action));
    check(!f.service->recognizes(2,action)); // History is session-local.
    auto foreign=action;foreign.context_byte=0x9a;
    check(!f.service->recognizes(1,foreign)); // Existing quest remains outside.
    foreign.context_byte=0x44;check(!f.service->recognizes(1,foreign));
    foreign.context_byte=0;check(!f.service->recognizes(1,foreign));
    foreign=action;foreign.request_word=0;check(!f.service->recognizes(1,foreign));
    foreign.request_word=2;check(!f.service->recognizes(1,foreign)); // Future nonce.
    f.service->invalidate(1);
    check(f.service->recognizes(1,action)); // Classify stale; this never authorizes.
    check(!f.service->prepare_choice(1,f.now));
    const auto second=f.menu();check(second.lease.request==2);
    check(f.service->recognizes(1,action));
    auto lease=f.service->prepare_choice(1,f.now);check(bool(lease));
    check(!f.service->consume(*lease,action,f.now) && f.service->pending(1));
    check(f.service->consume(*lease,f.action(*lease,2),f.now)==Entry::Choice::Exit);
    f.service->disconnect(1);check(!f.service->recognizes(1,action));
}
void publication_and_stale() {
    Fixture f;
    for(unsigned index:{0,1,3,4,5,7,9,27}) {
        auto plan=f.service->prepare(1,f.now);check(bool(plan));auto forged=*plan;forged.logical[index]^=1;
        check(!f.service->published(forged,f.now));f.service->invalidate(1);
    }
    auto first=f.service->prepare(1,f.now);auto second=f.service->prepare(1,f.now);check(first && second);
    check(!f.service->published(*first,f.now) && f.service->published(*second,f.now));
    check(!f.service->consume(first->lease,f.action(first->lease),f.now));
    auto plan=f.service->prepare(1,f.now);check(bool(plan));
    check(!f.service->published(*plan,f.now+Entry::lifetime));
    plan=f.service->prepare(1,f.now);check(bool(plan));check(!f.service->published(*plan,f.now-std::chrono::seconds{1}));
    check(!f.service->prepare(1,Entry::Time::max()));
    plan=f.menu();auto lease=f.service->prepare_choice(1,f.now);check(bool(lease));
    check(!f.service->consume(*lease,f.action(*lease),f.now+Entry::lifetime) && !f.service->pending(1));
    for(unsigned field=0;field<11;++field) {
        plan=f.menu();lease=f.service->prepare_choice(1,f.now);const auto original=f.owners[1];
        auto& owner=f.owners[1];
        switch(field){case 0:++owner.session;break;case 1:++owner.account;break;case 2:++owner.character;break;
        case 3:++owner.world_generation;break;case 4:++owner.area;break;case 5:++owner.scene;break;
        case 6:++owner.x;break;case 7:++owner.y;break;case 8:owner.name_codepage=936;break;case 9:++owner.battle_generation;break;case 10:++owner.position_revision;break;}
        check(!f.service->consume(*lease,f.action(*lease),f.now) && !f.service->pending(1));f.owners[1]=original;
    }
    for(bool published:{false,true}) {
        plan=*f.service->prepare(1,f.now);if(published)check(f.service->published(*plan,f.now));
        ++f.owners[1].x;f.service->observe_world(1,f.now);--f.owners[1].x;
        check(!f.service->published(*plan,f.now));check(!f.service->prepare_choice(1,f.now));
    }
    plan=f.menu();f.world_ready=false;f.service->observe_world(1,f.now);f.world_ready=true;
    check(!f.service->prepare_choice(1,f.now));
    plan=f.menu();f.fail_read=true;f.service->observe_world(1,f.now);f.fail_read=false;
    check(!f.service->prepare_choice(1,f.now));
    f.fail_resolve=true;check(!f.service->prepare(1,f.now));f.fail_resolve=false;
    f.fail_read=true;check(!f.service->prepare(1,f.now));f.fail_read=false;
    f.foreign_snapshot=true;check(!f.service->prepare(1,f.now));f.foreign_snapshot=false;
    f.member_snapshot=true;check(!f.service->prepare(1,f.now));f.member_snapshot=false;
    plan=f.service->prepare(1,f.now).value();f.service->disconnect(1);check(!f.service->published(*plan,f.now));
    plan=f.menu(2);lease=f.service->prepare_choice(2,f.now);f.service->disconnect(2);
    check(!f.service->consume(*lease,f.action(*lease),f.now)); // Never reuse disconnected session ID.
}
void rejected_delivery_is_exact() {
    Fixture f;
    const auto first=f.service->prepare(1,f.now);const auto successor=f.service->prepare(1,f.now);
    check(first && successor && first->lease.request!=successor->lease.request);
    f.service->reject_exact(*first); // Delayed false ACK for the replaced menu.
    check(f.service->published(*successor,f.now));
    f.service->reject_exact(*first);f.service->reject_exact(*successor);
    auto lease=f.service->prepare_choice(1,f.now);check(lease && *lease==successor->lease);
    check(f.service->consume(*lease,f.action(*lease,2),f.now)==Entry::Choice::Exit);
    const auto current=f.service->prepare(1,f.now);check(bool(current));
    auto forged=*current;forged.logical.back()^=1;f.service->reject_exact(forged);
    check(f.service->published(*current,f.now)); // Whole plan equality, not only nonce.
    f.service->invalidate(1);
    const auto rejected=f.service->prepare(1,f.now);check(bool(rejected));
    f.service->reject_exact(*rejected);f.service->reject_exact(*rejected);
    check(!f.service->published(*rejected,f.now));
    const auto next=f.service->prepare(1,f.now);check(next && next->lease.request==rejected->lease.request+1);
    f.service->reject_exact(*rejected);check(f.service->published(*next,f.now));
}
void sql_eligibility() {
    Fixture f;auto plan=f.menu(2);auto lease=f.service->prepare_choice(2,f.now);check(bool(lease));
    sqlite_detail::execute(f.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2");
    check(!f.service->consume(*lease,f.action(*lease),f.now));
    const auto created=f.repo->create(f.repo->nonmember(1,1),*f.money->load_wallet(1,1),"EntryCave",{50000,30,20},{[]{},[]{}});
    check(!f.service->prepare(1,f.now));
    plan=f.menu(2);lease=f.service->prepare_choice(2,f.now);const auto pending=f.repo->apply(f.repo->nonmember(2,2),f.repo->guild(created.leader.membership.guild_id),{[]{},[]{}});
    check(!f.service->consume(*lease,f.action(*lease),f.now) && !f.service->prepare(2,f.now));
    f.repo->cancel(pending.applicant,pending,{[]{},[]{}});check(bool(f.service->prepare(2,f.now)));
    plan=f.menu(3);lease=f.service->prepare_choice(3,f.now);
    sqlite_detail::execute(f.db,"UPDATE recovered_characters SET account_id=2,slot=1 WHERE id=3");
    check(!f.service->consume(*lease,f.action(*lease),f.now) && !f.service->prepare(3,f.now));
}
void nonce_ceiling() {
    Fixture f;const auto owner=f.owners.at(1);const auto identity=f.repo->nonmember(1,1);
    // Nonce-domain stress uses one actual immutable SQL snapshot, with no DB
    // mutations. Functional stale/eligibility cases above reread real SQL.
    Entry service([owner](auto session)->std::optional<Entry::Owner>{return session==owner.session?std::optional{owner}:std::nullopt;},
        [identity](const auto&)->std::optional<Repo::Identity>{return identity;});
    for(unsigned nonce=1;nonce<=65535;++nonce) {
        const auto plan=service.prepare(1,f.now);check(plan && plan->lease.request==nonce);
        check(service.published(*plan,f.now));const auto lease=service.prepare_choice(1,f.now);check(bool(lease));
        check(service.consume(*lease,{lease->request,2,Entry::context,0xa5},f.now)==Entry::Choice::Exit);
        service.invalidate(1); // Invalidating never resets the native WORD clock.
    }
    check(!service.prepare(1,f.now));service.invalidate(1);check(!service.prepare(1,f.now));
}
}
int main() {
    try{lifecycle();recognition_scope();publication_and_stale();rejected_delivery_is_exact();sql_eligibility();nonce_ceiling();
        std::cout<<"PASS entry service checks="<<checks<<"; actual class/full-SQL fixture, not client/UI acceptance\n";return 0;}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
