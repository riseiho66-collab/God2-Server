#include "game/SharedTaiwanCharacterListHandoff.h"
#include <filesystem>
#include <fstream>
#include <random>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

// SOURCE ONLY. Construction/extraction cases use no Session/socket/database,
// native codec, login or admission. All repository/provider access is a failure.
namespace {
using namespace god2;
using Source=SharedTaiwanNativeCharacterListSource;
using Handoff=SharedTaiwanCharacterListHandoff;
void need(bool value){if(!value)throw std::runtime_error("Handoff canonical source regression");}
[[noreturn]] void unused(){throw std::runtime_error("Unexpected repository or provider use");}
struct Accounts final:AccountRepository {
    Account create(const std::string&,const std::string&) override{unused();}
    std::optional<Account> find_by_username(const std::string&) override{unused();}
    std::optional<Account> find_by_id(std::uint64_t) override{unused();}
};
struct Characters final:RecoveredCharacterRepository {
    std::optional<CharacterRoleSnapshot> load_role(std::uint64_t,std::uint64_t) override{unused();}
    RoleResourceCommit commit_role_resources(std::uint64_t,std::uint64_t,
        const std::optional<CharacterRoleSnapshot>&,const CharacterResources&,
        CharacterRoleSnapshot,CharacterResources) override{unused();}
    std::optional<CharacterExperience> load_experience(std::uint64_t,std::uint64_t) override{unused();}
    BattleSettlement settle_battle(std::uint64_t,std::uint64_t,std::uint64_t,
        const CharacterResources&,CharacterResources,bool,std::uint64_t,
        const std::optional<BattleProgressionCommit>&) override{unused();}
    std::uint64_t reserve_battle(std::uint64_t,std::uint64_t,const CharacterResources&) override{unused();}
    std::optional<CharacterResources> load_resources(std::uint64_t,std::uint64_t) override{unused();}
    CharacterResources commit_resources(std::uint64_t,std::uint64_t,
        const std::optional<CharacterResources>&,CharacterResources) override{unused();}
    RecoveredCharacter create(std::uint64_t,const std::array<std::uint8_t,40>&) override{unused();}
    std::vector<RecoveredCharacter> list_for_account(std::uint64_t) override{unused();}
    std::optional<RecoveredPosition> load_position(std::uint64_t,std::uint64_t) override{unused();}
    RecoveredPosition commit_position(std::uint64_t,std::uint64_t,const std::optional<RecoveredPosition>&,
        std::uint16_t,std::uint16_t,std::uint16_t,std::uint16_t) override{unused();}
};
struct Summaries final:NativeCharacterSummarySnapshotRepository {
    const Accounts& accounts;const Characters& characters;
    Summaries(const Accounts& a,const Characters& c):accounts(a),characters(c){}
    bool owns_sources(const AccountRepository& a,const RecoveredCharacterRepository& c) const noexcept override{
        return &a==&accounts&&&c==&characters;
    }
    std::optional<NativeCharacterSummarySnapshot> load(std::uint64_t,std::uint16_t,std::uint16_t,std::string_view) override{unused();}
};
struct Configuration {
    std::filesystem::path root;
    Configuration(){
        const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());std::random_device random;
        for(unsigned attempt=0;attempt<100;++attempt){
            const auto candidate=temp/("god2-handoff-binding-"+std::to_string(random()));
            if(std::filesystem::create_directory(candidate)){root=candidate;break;}
        }
        if(root.empty())unused();
        if(!std::filesystem::create_directory(root/"Data3"))unused();
        std::ofstream out(root/"Data3"/"config.ini",std::ios::binary);
        out<<"$1\n[Group]\nChannel0=127.0.0.1\nChannel1=127.0.0.1\nChannel2=127.0.0.1\n";
        out.close();if(!out)unused();
    }
    ~Configuration(){std::error_code ec;std::filesystem::remove_all(root,ec);}
    auto read(){return TaiwanNativeClientGroupConfiguration::read(root,{"127.0.0.1",0,0},4096,4096);}
};
template<class Call>bool rejects(Call&& call){try{call();}catch(const std::invalid_argument&){return true;}return false;}
bool same_callbacks(const Source::Binding& a,const Source::Binding& b){
    // Test observation only. Production qualification never trusts target_type.
    return a.list.target_type()==b.list.target_type()&&a.select.target_type()==b.select.target_type()&&
        a.invalidate_active.target_type()==b.invalidate_active.target_type()&&a.current.target_type()==b.current.target_type()&&
        a.complete.target_type()==b.complete.target_type()&&a.selected.target_type()==b.selected.target_type()&&
        a.invalidate_selection.target_type()==b.invalidate_selection.target_type();
}
void canonical_owner_and_facade_replacement(){
    Accounts accounts;Characters characters;Summaries summaries(accounts,characters);Configuration files;
    const auto config=files.read();
    const auto live=[](const Source::Issued&,const Handoff::Auth&)->bool{unused();};
    const auto authority=[](Session&,const Source::Scope&,const Source::Issued&,
        const Handoff::Auth&,const Handoff::Auth&)->std::optional<Handoff::DestinationAuthority>{unused();};
    auto owner=Handoff::create(accounts,characters,summaries,std::string(TaiwanNativeClientGroupConfiguration::client_sha256),4,config,live,authority);
    const auto second=Handoff::create(accounts,characters,summaries,std::string(TaiwanNativeClientGroupConfiguration::client_sha256),4,config,live,authority);
    const auto target=[](Session&,const Source::Scope&)->std::optional<Source::Target>{unused();};
    const auto qualify=[](Session&,const Source::Scope&,const Source::Target&,
        const NativeCharacterSummarySnapshot&,std::span<const RecoveredCharacter>,Source::Check)->bool{unused();};
    const auto create=[&](std::shared_ptr<Handoff> input){return Source::create_with_handoff(accounts,characters,summaries,
        std::string(TaiwanNativeClientGroupConfiguration::client_sha256),target,qualify,4,std::move(input));};
    auto binding=create(owner);const auto canonical=binding.for_handoff(owner);
    need(bool(canonical)&&same_callbacks(*canonical,binding));
    unsigned replaced_calls=0;
    binding.list=[&](Session&)->Session::NativeCharacterList{++replaced_calls;unused();};
    binding.select=[&](Session&,const RecoveredPostCreateSelect::Selection&,std::optional<std::uint64_t>)->std::uint64_t{++replaced_calls;unused();};
    binding.invalidate_active=[&]{++replaced_calls;};
    binding.current=[&](Session&,const Session::NativeCharacterList&){++replaced_calls;return true;};
    binding.complete=[&](Session&,const Session::NativeCharacterList&,bool){++replaced_calls;return true;};
    binding.selected=[&](std::uint64_t,std::uint64_t,std::uint64_t)->std::optional<Source::SelectedLink>{++replaced_calls;unused();};
    binding.invalidate_selection=[&](std::uint64_t){++replaced_calls;};
    const auto restored=binding.for_handoff(owner);need(bool(restored)&&same_callbacks(*canonical,*restored));
    restored->invalidate_active();restored->invalidate_selection(1);need(replaced_calls==0);
    const auto repeated=restored->for_handoff(owner);need(bool(repeated)&&same_callbacks(*repeated,*canonical));
    need(!binding.for_handoff({})&&!binding.for_handoff(second));
    // Same raw pointer with a foreign control block does not own this handoff.
    const std::shared_ptr<Handoff> impostor(owner.get(),[](Handoff*){});
    need(!binding.for_handoff(impostor));
    bool wrong_thread=false;std::thread foreign([&]{wrong_thread=!binding.for_handoff(owner);});foreign.join();need(wrong_thread);
    Source::Binding generic=*canonical;
    // Reconstructing all seven callbacks strips the private proof completely.
    Source::Binding forged{generic.list,generic.select,generic.invalidate_active,generic.current,generic.complete,generic.selected,generic.invalidate_selection};
    need(!forged.for_handoff(owner));
    auto callbacks=owner->binding();
    const auto legacy=Source::create(accounts,characters,summaries,std::string(TaiwanNativeClientGroupConfiguration::client_sha256),
        target,qualify,4,callbacks.publish,callbacks.link);
    need(!legacy.for_handoff(owner));
    need(rejects([&]{(void)create({});}));
    Accounts unrelated;need(rejects([&]{(void)Source::create_with_handoff(unrelated,characters,summaries,
        std::string(TaiwanNativeClientGroupConfiguration::client_sha256),target,qualify,4,owner);}));
    need(rejects([&]{(void)Source::create_with_handoff(accounts,characters,summaries,
        std::string(TaiwanNativeClientGroupConfiguration::client_sha256),target,qualify,5,owner);}));
    const std::weak_ptr<Handoff> retired=owner;owner.reset();need(retired.expired());
    need(!binding.for_handoff(retired.lock()));
}
}
void test_taiwan_handoff_binding(){canonical_owner_and_facade_replacement();}
