#include "game/SharedNativeActorNameSource.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
bool same_row(const SharedWorldPresence::ReadyCharacter& a,const SharedWorldPresence::ReadyCharacter& b) {
    const auto& x=a.character;const auto& y=b.character;
    return a.lease==b.lease && a.position==b.position && x.id==y.id && x.account_id==y.account_id &&
        x.slot==y.slot && x.profile==y.profile && x.created_at==y.created_at &&
        x.name_codepage==y.name_codepage && x.streamer_privilege==y.streamer_privilege;
}
}
SharedNativeActorNameSource::SharedNativeActorNameSource(std::shared_ptr<SharedWorldPresence> p):presence_(std::move(p)) {}
SharedNativeActorNameSource::~SharedNativeActorNameSource() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    terminal_=true;busy_=true;presence_.reset();
}
void SharedNativeActorNameSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Common native actor name game owner mismatch");
}
std::shared_ptr<SharedNativeActorNameSource> SharedNativeActorNameSource::create(std::shared_ptr<SharedWorldPresence> p) {
    if(!p)return {};
    return std::shared_ptr<SharedNativeActorNameSource>(new SharedNativeActorNameSource(std::move(p)));
}
bool SharedNativeActorNameSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& p) const {
    owner();return !terminal_ && p && p==presence_;
}
std::optional<SharedNativeActorNameSource::Native> SharedNativeActorNameSource::project_owned(
    const Lease& source,const Lease& recipient,Native supplied) const {
    if(terminal_ || reentered_ || source.actor_handle>0xfff || source.session==recipient.session)return std::nullopt;
    // Own complete model and real receiver before any repository/issuer reads.
    return std::visit([&](auto native)->std::optional<Native> {
        if(native.common_name_source.get()!=this)return std::nullopt;
        const auto receiver=native.connection.lock();
        if(!receiver || !native.raw_name_state || native.spawn.identity()!=source.actor_handle)return std::nullopt;
        const auto state=*native.raw_name_state;
        const auto page=state.wire_codepage();
        const bool available=state.available();
        if(!available)return std::nullopt;
        const auto original=RecoveredRemoteActor::encode_logical(native.spawn);
        const auto word=std::uint32_t(original[1])|(std::uint32_t(original[2])<<8)|
            (std::uint32_t(original[3])<<16)|(std::uint32_t(original[4])<<24);
        if(bool((word>>25)&1)!=state.simplified())
            return std::nullopt; // Different-selector postadapted name source remains OPEN.
        const auto receiver_tuple=[&] {
            if(terminal_ || reentered_ || receiver->closing())return false;
            return receiver->id()==recipient.session && receiver->account_id==recipient.account && receiver->character_id==recipient.character;
        };
        const auto receiver_bound=[&] {
            if(!receiver_tuple())return false;
            const bool bound=presence_->current(recipient);
            return bound && receiver_tuple(); // Prepared recipients are allowed; no fabricated ready state.
        };
        const auto actual_current=[&] {
            if(!receiver_tuple())return false;
            const bool actual=state.current(*receiver);
            return actual && receiver_tuple();
        };
        const auto root=[&]()->std::optional<SharedWorldPresence::ReadyCharacter> {
            if(reentered_)return std::nullopt;
            const auto population=presence_->ready_characters();if(!population || reentered_)return std::nullopt;
            std::optional<SharedWorldPresence::ReadyCharacter> selected;
            for(const auto& row:*population)if(row.lease==source) {
                if(selected || row.character.id!=source.character || row.character.account_id!=source.account)return std::nullopt;
                selected=row;
            }
            return selected;
        };
        if(!receiver_bound() || !actual_current())return std::nullopt;
        const auto before=root();if(!before || !receiver_bound())return std::nullopt;
        const auto stable=root();if(!stable || !same_row(*before,*stable) || !receiver_tuple())return std::nullopt;
        // Common stored profile first15 is an existing14-byte identity domain.
        // Decode its actual stored page strictly (0 only unchanged ASCII), then
        // encode the same original Unicode in the actual receiving wire page.
        const auto& profile=before->character.profile;
        const auto end=std::find(profile.begin(),profile.begin()+15,0);
        if(end==profile.begin() || end==profile.begin()+15)return std::nullopt;
        const auto stored=OwnedCharacterNameText::from_encoded(std::string_view(
            reinterpret_cast<const char*>(profile.data()),static_cast<std::size_t>(end-profile.begin())),before->character.name_codepage);
        if(!stored)return std::nullopt;
        const auto encoded=OwnedCharacterNameText::from_utf8(stored->original_utf8(),page);
        if(!encoded || encoded->original_utf8()!=stored->original_utf8())return std::nullopt;
        auto projected=original;
        // Only the proven first logical16-byte field; every other byte remains
        // the supplied full model, including second/third text and opaque bits.
        std::fill_n(projected.begin()+29,16,0);
        std::copy(encoded->encoded_bytes().begin(),encoded->encoded_bytes().end(),projected.begin()+29);
        const auto record=RecoveredRemoteActor::parse_logical(projected);if(!record)return std::nullopt;native.spawn=*record;
        if(!actual_current() || !receiver_bound())return std::nullopt;
        const auto after=root();
        if(!after || !same_row(*before,*after) || !actual_current() || !receiver_tuple())return std::nullopt;
        return Native{std::move(native)};
    },std::move(supplied));
}
std::optional<SharedNativeActorNameSource::Native> SharedNativeActorNameSource::project(
    const Lease& original_source,const Lease& original_recipient,Native supplied) const {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto source=original_source;const auto recipient=original_recipient;
    auto result=project_owned(source,recipient,std::move(supplied));return !reentered_?result:std::nullopt;
}
bool SharedNativeActorNameSource::current(const Lease& original_source,const Lease& original_recipient,const Native& original) const {
    owner();if(terminal_)return false;
    if(busy_){reentered_=true;return false;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto source=original_source;const auto recipient=original_recipient;const auto retained=original;
    const auto projected=project_owned(source,recipient,retained);
    if(!projected || reentered_ || projected->index()!=retained.index())return false;
    return std::visit([&](const auto& before) {
        using Output=std::decay_t<decltype(before)>;const auto after=std::get_if<Output>(&*projected);if(!after)return false;
        return RecoveredRemoteActor::encode_logical(before.spawn)==RecoveredRemoteActor::encode_logical(after->spawn);
    },retained);
}
}
