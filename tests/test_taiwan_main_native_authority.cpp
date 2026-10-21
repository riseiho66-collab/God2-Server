#include "game/TaiwanMainNativeAuthority.h"
#include <sqlite3.h>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <thread>
#include <type_traits>

// SOURCE ONLY this round. Future concentrated tests may execute this isolated
// in-memory construction fixture; no production DB, schema, Session or socket
// is used. These are not Prepare/CAS/Written/native admission acceptance.
namespace {
using namespace god2;
using Authority=TaiwanMainNativeAuthority;
void require(bool value){if(!value)throw std::runtime_error("Main native authority source contract");}
template<class F> bool rejects(F&& call){try{call();}catch(const std::invalid_argument&){return true;}return false;}
struct Memory {
    sqlite3* db{};
    Memory(){if(sqlite3_open(":memory:",&db)!=SQLITE_OK)throw std::runtime_error("Isolated authority fixture unavailable");}
    ~Memory(){sqlite3_close(db);}
};
struct Configuration {
    const std::filesystem::path root=std::filesystem::temp_directory_path()/
        ("g2-main-authority-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    Configuration(){std::filesystem::create_directories(root/"Data3");}
    ~Configuration(){std::error_code ignored;std::filesystem::remove_all(root,ignored);}
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> read(unsigned slots) {
        {std::ofstream stream(root/"Data3"/"config.ini",std::ios::binary|std::ios::trunc);
         stream<<"[Synthetic]\n";for(unsigned i=0;i<slots;++i)stream<<"Slot"<<i<<"=127.0.0.1\n";
         require(bool(stream));}
        return TaiwanNativeClientGroupConfiguration::read(root,{"127.0.0.1",0,0},4096,4096);
    }
};
}
void test_taiwan_main_native_authority() {
    using Binding=Authority::Binding;
    static_assert(!std::is_default_constructible_v<Binding>);
    static_assert(!std::is_assignable_v<decltype((std::declval<Binding&>().live)),Authority::Handoff::Live>);
    static_assert(!std::is_assignable_v<decltype((std::declval<Binding&>().authority)),Authority::Handoff::Authority>);
    static_assert(!std::is_assignable_v<decltype((std::declval<Binding&>().prepare)),Authority::Source::Prepare>);
    Memory memory;
    SqliteAccountRepository accounts(memory.db),other_accounts(memory.db);
    SqliteRecoveredCharacterRepository characters(memory.db),other_characters(memory.db);
    SqliteNativeCharacterSummarySnapshotRepository writer(memory.db,accounts,characters);
    Configuration files;const auto config=files.read(3);
    const std::array<Authority::StorageScope,3> scopes{{{7,20},{7,21},{7,22}}};
    const std::string client(TaiwanNativeClientGroupConfiguration::client_sha256);
    unsigned supply_calls=0;
    SharedTaiwanNativeCharacterOfferSource::Supply supply=[&](Session&,const Authority::Source::Scope&,
        const Authority::Source::Target&,std::span<const RecoveredCharacter>,
        const std::optional<NativeCharacterSummarySnapshot>&)->std::optional<SharedTaiwanNativeCharacterOfferSource::Offer> {
        ++supply_calls;throw std::runtime_error("Passive authority construction invoked producer");
    };
    auto owner=Authority::create(accounts,characters,writer,config,client,0,scopes,1,supply);
    require(owner->matches_sources(accounts,characters,writer));
    require(!owner->matches_sources(other_accounts,characters,writer));
    require(!owner->matches_sources(accounts,other_characters,writer));
    const auto binding=owner->binding();
    require(binding.target && binding.qualify && binding.live && binding.authority && binding.prepare);
    owner->revoke(123,0); // No publication -> no SQL and no synthetic approval.
    bool wrong_thread=false;
    std::thread other([&]{try{owner->revoke(123,0);}catch(const std::logic_error&){wrong_thread=true;}});
    other.join();require(wrong_thread);
    require(rejects([&]{Authority::create(accounts,characters,writer,config,client,0,scopes,0,supply);}));
    require(rejects([&]{Authority::create(accounts,characters,writer,config,std::string(64,'0'),0,scopes,1,supply);}));
    require(rejects([&]{Authority::create(accounts,characters,writer,config,client,0,scopes,1,{});}));
    require(rejects([&]{Authority::create(other_accounts,characters,writer,config,client,0,scopes,1,supply);}));
    auto aliases=scopes;aliases[2]=aliases[0];
    require(rejects([&]{Authority::create(accounts,characters,writer,config,client,0,aliases,1,supply);}));
    require(rejects([&]{Authority::create(accounts,characters,writer,files.read(2),client,0,scopes,1,supply);}));
    require(supply_calls==0);
}
