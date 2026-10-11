#include "game/SharedChatIdentitySource.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2 {
struct SharedChatIdentitySource::Identity {};
struct SharedChatIdentitySource::Storage {
    std::shared_ptr<const Identity> identity;
    std::string target;
    std::uint16_t page;
    std::optional<OwnedCharacterNameText> qualified_target;
    std::vector<SharedWorldPresence::ReadyCharacter> population;
    std::vector<OwnedCharacterNameText> names;
    Result result;
    std::optional<std::size_t> matched_index;
};
namespace {
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool same_population(const std::vector<SharedWorldPresence::ReadyCharacter>& a,
    const std::vector<SharedWorldPresence::ReadyCharacter>& b) {
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)
        if(a[i].lease!=b[i].lease || a[i].position!=b[i].position || !same_root(a[i].character,b[i].character))return false;
    return true;
}
std::optional<std::vector<OwnedCharacterNameText>> strict_names(
    const std::vector<SharedWorldPresence::ReadyCharacter>& population) {
    std::vector<OwnedCharacterNameText> names;names.reserve(population.size());
    for(const auto& row:population) {
        // Existing common profile stores a NUL-terminated name in its first15
        // bytes (up to14 encoded bytes); retain all remaining root fields too.
        const auto end=std::find(row.character.profile.begin(),row.character.profile.begin()+15,0);
        if(end==row.character.profile.begin() || end==row.character.profile.begin()+15)return std::nullopt;
        const auto size=static_cast<std::size_t>(end-row.character.profile.begin());
        const auto name=OwnedCharacterNameText::from_encoded(
            std::string_view(reinterpret_cast<const char*>(row.character.profile.data()),size),row.character.name_codepage);
        if(!name)return std::nullopt;
        names.push_back(*name);
    }
    return names;
}
}
SharedChatIdentitySource::Lookup::Lookup(std::shared_ptr<const Storage> storage):storage_(std::move(storage)) {}
SharedChatIdentitySource::Lookup::Lookup(Lookup&& other) noexcept:storage_(other.storage_) {}
SharedChatIdentitySource::Lookup& SharedChatIdentitySource::Lookup::operator=(Lookup&& other) noexcept {
    storage_=other.storage_;return *this;
}
SharedChatIdentitySource::Result SharedChatIdentitySource::Lookup::result() const noexcept {return storage_->result;}
std::string_view SharedChatIdentitySource::Lookup::raw_target() const noexcept {return storage_->target;}
std::uint16_t SharedChatIdentitySource::Lookup::codepage() const noexcept {return storage_->page;}
std::optional<std::string_view> SharedChatIdentitySource::Lookup::original_utf8() const noexcept {
    if(!storage_->qualified_target)return std::nullopt;
    return storage_->qualified_target->original_utf8();
}
const std::vector<SharedWorldPresence::ReadyCharacter>& SharedChatIdentitySource::Lookup::population() const noexcept {
    return storage_->population;
}
const std::vector<OwnedCharacterNameText>& SharedChatIdentitySource::Lookup::names() const noexcept {return storage_->names;}
const SharedWorldPresence::ReadyCharacter* SharedChatIdentitySource::Lookup::matched() const noexcept {
    return storage_->matched_index?&storage_->population[*storage_->matched_index]:nullptr;
}
const OwnedCharacterNameText* SharedChatIdentitySource::Lookup::matched_name() const noexcept {
    return storage_->matched_index?&storage_->names[*storage_->matched_index]:nullptr;
}
SharedChatIdentitySource::SharedChatIdentitySource(std::shared_ptr<SharedWorldPresence> presence)
    :presence_(std::move(presence)),identity_(std::make_shared<const Identity>()) {}
SharedChatIdentitySource::~SharedChatIdentitySource() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    terminal_=true;busy_=true;presence_.reset();identity_.reset();
}
void SharedChatIdentitySource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Chat identity game owner mismatch");
}
std::shared_ptr<SharedChatIdentitySource> SharedChatIdentitySource::create(std::shared_ptr<SharedWorldPresence> presence) {
    if(!presence)return {};
    return std::shared_ptr<SharedChatIdentitySource>(new SharedChatIdentitySource(std::move(presence)));
}
bool SharedChatIdentitySource::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const {
    owner();return !terminal_ && presence && presence==presence_;
}
std::optional<SharedChatIdentitySource::Lookup> SharedChatIdentitySource::lookup(
    std::string_view raw_target,std::uint16_t page) const {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    // Own the original argument before virtual repository reads; no caller
    // string_view/mutable buffer survives as target identity authority.
    const std::string target_bytes(raw_target);
    const auto population=presence_->ready_characters();if(!population || reentered_)return std::nullopt;
    const auto names=strict_names(*population);if(!names || reentered_)return std::nullopt;
    const auto target=(page==936 || page==950)?OwnedCharacterNameText::from_encoded(target_bytes,page):std::nullopt;
    Result result=Result::UnqualifiedTarget;std::optional<std::size_t> matched;
    if(target) {
        std::size_t matches=0;
        for(std::size_t i=0;i<names->size();++i)
            if((*names)[i].original_utf8()==target->original_utf8()){++matches;matched=i;}
        result=matches==0?Result::NoReadyMatch:matches==1?Result::Matched:Result::Ambiguous;
        if(matches!=1)matched.reset();
    }
    if(reentered_)return std::nullopt;
    // Allocate const storage directly: caller has no mutable alias to roots,
    // strict names, source identity capability, raw target or match decision.
    return Lookup(std::make_shared<const Storage>(Storage{
        identity_,target_bytes,page,target,*population,*names,result,matched}));
}
bool SharedChatIdentitySource::current(const Lookup& lookup) const {
    owner();if(terminal_)return false;
    if(busy_){reentered_=true;return false;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    if(lookup.storage_->identity!=identity_)return false;
    const auto population=presence_->ready_characters();
    if(!population || reentered_ || !same_population(*population,lookup.storage_->population))return false;
    const auto names=strict_names(*population);
    if(!names || reentered_ || names->size()!=lookup.storage_->names.size())return false;
    for(std::size_t i=0;i<names->size();++i) {
        const auto& a=(*names)[i];const auto& b=lookup.storage_->names[i];
        if(a.codepage()!=b.codepage() || a.encoded_bytes()!=b.encoded_bytes() || a.original_utf8()!=b.original_utf8())return false;
    }
    return !reentered_;
}
}
