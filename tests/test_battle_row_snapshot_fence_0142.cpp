#include "db/SqliteMigrationManager.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include "game/OwnedBattleRowPreference.h"
#include <array>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace {
using namespace god2;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
// In-memory isolated repository fixture only. Never creates private Session
// receipts or claims the actual normal-entry/relogin/battle flow was tested.
struct Fixture {
    struct Close {void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
    std::unique_ptr<sqlite3,Close> db;
    std::unique_ptr<SqliteAccountRepository> accounts;
    std::unique_ptr<SqliteRecoveredCharacterRepository> characters;
    std::unique_ptr<SqliteNativeWorldEntrySnapshotRepository> repository;
    NativeWorldEntrySnapshot next;
    Fixture() {
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open fixture");db.reset(raw);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
        SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        accounts=std::make_unique<SqliteAccountRepository>(raw);
        characters=std::make_unique<SqliteRecoveredCharacterRepository>(raw);
        const auto account=accounts->create("row-fixture","fixture-hash");
        std::array<std::uint8_t,40> profile{};profile[0]='A';
        const auto root=characters->create(account.id,profile);
        const auto position=characters->commit_position(account.id,root.id,{},1,1,18,14);
        sqlite_detail::execute(raw,SqliteNativeWorldEntrySnapshotRepository::schema());
        repository=std::make_unique<SqliteNativeWorldEntrySnapshotRepository>(raw,*accounts,*characters);
        next={root,position,OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::record_kind,
            OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::source_record,{0xe8,1},1};
    }
    auto load(){return repository->load(next.root.account_id,next.root.id,next.client_sha256,next.record_kind);}
};
struct Observation {bool after_issuer=false,live=true,commit_profile=false;};
int trace(unsigned event,void* context,void* statement,void*) noexcept {
    auto& state=*static_cast<Observation*>(context);
    if(event==SQLITE_TRACE_STMT && state.after_issuer && !state.commit_profile)state.live=false;
    if(event==SQLITE_TRACE_PROFILE && state.commit_profile) {
        const auto sql=sqlite3_sql(static_cast<sqlite3_stmt*>(statement));
        if(sql && std::strcmp(sql,"COMMIT")==0)state.live=false;
    }
    return 0;
}
}
int main()try {
    using Repo=god2::SqliteNativeWorldEntrySnapshotRepository;
    Fixture final_read;
    Observation before_commit;
    sqlite3_trace_v2(final_read.db.get(),SQLITE_TRACE_STMT,trace,&before_commit);
    const auto rejected=final_read.repository->replace_from_issuer({},final_read.next,
        [&](const auto&,const auto&,auto point){
            if(point==Repo::WriteCheck::BeforeCommit)before_commit.after_issuer=true;
            return true;
        },[&]{return before_commit.live;});
    sqlite3_trace_v2(final_read.db.get(),0,nullptr,nullptr);
    require(!rejected && !final_read.load(),"Final SQL observer retirement must roll back staged choice");

    Fixture durable;
    Observation after_commit;after_commit.commit_profile=true;
    sqlite3_trace_v2(durable.db.get(),SQLITE_TRACE_PROFILE,trace,&after_commit);
    const auto saved=durable.repository->replace_from_issuer({},durable.next,
        [](const auto&,const auto&,auto){return true;},[&]{return after_commit.live;});
    sqlite3_trace_v2(durable.db.get(),0,nullptr,nullptr);
    require(saved && !after_commit.live && durable.load()==saved,"Post-COMMIT retirement is durable, never pretend rollback");
    auto changed=durable.next;changed.record={0xe8,0};changed.revision=2;
    const auto updated=durable.repository->replace_from_issuer(saved,changed,[](const auto&,const auto&,auto){return true;});
    require(updated && durable.load()==updated,"Optional fence must preserve existing caller API and exact CAS");
    bool stale_rejected=false;
    try{(void)durable.repository->replace_from_issuer(saved,changed,[](const auto&,const auto&,auto){return true;});}
    catch(const god2::DatabaseError&){stale_rejected=true;}
    require(stale_rejected && durable.load()==updated,"Stale full expected tuple must not overwrite durable choice");
    std::cout<<"Row snapshot final-fence regression source\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
