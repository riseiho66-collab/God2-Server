#include "game/SharedPublishedChatNameSource.h"
#include <exception>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2 {
using Receiver=std::variant<std::shared_ptr<Session>>;
struct SharedPublishedChatNameSource::Identity {};
struct SharedPublishedChatNameSource::Observed {
    Receiver receiver;
    shared::SharedActorVisibility::ChatActorSnapshot registry;
    RecoveredPosition recipient_position;
    std::optional<SessionState> taiwan_phase;
    std::uint64_t taiwan_battle_generation;
    std::uint32_t actor;
    std::string name;
    std::uint64_t name_source_revision;
    std::uint16_t native_name_page;
    std::optional<shared::SharedActorVisibility::TaiwanReceiverTextState> taiwan_globals; // Exact profile source, including typed C1C epoch.
};
struct SharedPublishedChatNameSource::Storage {
    std::shared_ptr<const Identity> identity;
    Lookup lookup;
    Binding binding;
    std::uint16_t page;
    Observed observed;
};
SharedPublishedChatNameSource::Witness::Witness(std::shared_ptr<const Storage> s):storage_(std::move(s)) {}
SharedPublishedChatNameSource::Witness::Witness(Witness&& other) noexcept:storage_(other.storage_) {}
SharedPublishedChatNameSource::Witness& SharedPublishedChatNameSource::Witness::operator=(Witness&& other) noexcept {
    storage_=other.storage_;return *this;
}
const SharedPublishedChatNameSource::Binding& SharedPublishedChatNameSource::Witness::binding() const noexcept {return storage_->binding;}
const SharedPublishedChatNameSource::Lease& SharedPublishedChatNameSource::Witness::source() const noexcept {return storage_->binding.source();}
const SharedPublishedChatNameSource::Lease& SharedPublishedChatNameSource::Witness::recipient() const noexcept {return storage_->binding.recipient();}
std::uint32_t SharedPublishedChatNameSource::Witness::native_actor_identity() const noexcept {return storage_->observed.actor;}
std::string_view SharedPublishedChatNameSource::Witness::native_name_bytes() const noexcept {return storage_->observed.name;}
std::uint16_t SharedPublishedChatNameSource::Witness::codepage() const noexcept {return storage_->page;}
std::uint16_t SharedPublishedChatNameSource::Witness::native_name_codepage() const noexcept {return storage_->observed.native_name_page;}
const SharedPublishedChatNameSource::Lookup& SharedPublishedChatNameSource::Witness::lookup() const noexcept {return storage_->lookup;}

bool SharedPublishedChatNameSource::Witness::recipient_is(const std::shared_ptr<Session>& c) const noexcept {
    const auto retained=std::get_if<std::shared_ptr<Session>>(&storage_->observed.receiver);return c && retained && *retained==c;
}
SharedPublishedChatNameSource::SharedPublishedChatNameSource(std::shared_ptr<SharedChatIdentitySource> names,
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility)
    :identities_(std::move(names)),presence_(std::move(presence)),visibility_(std::move(visibility)),identity_(std::make_shared<const Identity>()) {}
SharedPublishedChatNameSource::~SharedPublishedChatNameSource() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    terminal_=true;busy_=true;visibility_.reset();identities_.reset();presence_.reset();identity_.reset();
}
void SharedPublishedChatNameSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Published chat name game owner mismatch");
}
std::shared_ptr<SharedPublishedChatNameSource> SharedPublishedChatNameSource::create(
    std::shared_ptr<SharedChatIdentitySource> names,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<shared::SharedActorVisibility> visibility) {
    if(!names || !presence || !visibility || !names->owns_presence(presence) || !visibility->owns_presence(presence))return {};
    return std::shared_ptr<SharedPublishedChatNameSource>(new SharedPublishedChatNameSource(std::move(names),std::move(presence),std::move(visibility)));
}
std::optional<SharedPublishedChatNameSource::Observed> SharedPublishedChatNameSource::observe(
    const Lookup& lookup,const Binding& binding,std::uint16_t page) const {
    if(reentered_ || terminal_ || (page!=936 && page!=950) || lookup.codepage()!=page ||
       lookup.result()!=SharedChatIdentitySource::Result::Matched || !lookup.matched() || !lookup.matched_name() ||
       lookup.matched()->lease!=binding.source())return std::nullopt;
    const auto& source=*lookup.matched();
    const SharedWorldPresence::ReadyCharacter* recipient=nullptr;
    for(const auto& row:lookup.population())if(row.lease==binding.recipient()) {
        if(recipient)return std::nullopt;recipient=&row;
    }
    if(!recipient || !identities_->current(lookup) || reentered_)return std::nullopt;
    const auto retained=visibility_->chat_actor_snapshot(binding,source.position);if(!retained)return std::nullopt;
    // The native name must encode the identical stored original Unicode. This
    // performs no script/display conversion, case/space normalization or alias.
    const auto encoded=OwnedCharacterNameText::from_utf8(lookup.matched_name()->original_utf8(),page);
    if(!encoded || encoded->encoded_bytes()!=lookup.raw_target())return std::nullopt;
    const auto tw=visibility_->taiwan_chat_actor(binding,source.position);
    if(reentered_ || !identities_->current(lookup) || reentered_)return std::nullopt;
    Receiver receiver;std::uint32_t actor=0;std::string name;std::uint64_t revision=0;std::uint16_t native_page=0;
    std::optional<shared::SharedActorVisibility::TaiwanReceiverTextState> globals;
    if(!tw)return std::nullopt;
    const auto connection=tw->connection.lock();
    if(!connection || !tw->raw_name_state.available())return std::nullopt;
    native_page=tw->raw_name_state.wire_codepage();
    receiver=connection;actor=tw->native_actor_identity;name=tw->native_name_bytes;
    revision=tw->raw_name_state.source_revision();globals=tw->raw_name_state;
    // Same original Unicode, not equal bytes across distinct936/950 domains.
    // No display conversion, alias or forced page/tag change is introduced.
    const auto native_encoded=OwnedCharacterNameText::from_utf8(lookup.matched_name()->original_utf8(),native_page);
    if(!revision || actor!=binding.source().actor_handle || !native_encoded ||
       native_encoded->original_utf8()!=encoded->original_utf8() || name!=native_encoded->encoded_bytes())return std::nullopt;
    const auto receiver_current=[&] {
        if(reentered_ || terminal_ || !identities_->current(lookup) || reentered_)return false;
        const auto actual=presence_->ready_lease(binding.recipient().session,binding.recipient().account,binding.recipient().character);
        if(reentered_ || !actual || *actual!=binding.recipient())return false;
        const auto position=presence_->saved_position(binding.recipient());
        if(reentered_ || !position || *position!=recipient->position)return false;
        return std::visit([&](const auto& c) {
            if(!c || c->closing())return false;
            return c->id()==binding.recipient().session && c->account_id==binding.recipient().account &&
                c->character_id==binding.recipient().character && c->recovered_world_ready() &&
                (c->state()==SessionState::InWorld || c->state()==SessionState::InBattle) &&
                c->common_world_delivery_current(binding.recipient().account,binding.recipient().character,binding.recipient().generation) &&
                !c->common_world_entry_current(binding.recipient().account,binding.recipient().character,binding.recipient().generation);
        },receiver);
    };
    if(!receiver_current())return std::nullopt;
    std::optional<SessionState> phase;std::uint64_t battle=0;
    if(const auto c=std::get_if<std::shared_ptr<Session>>(&receiver)){phase=(*c)->state();battle=(*c)->battle_generation();}
    const auto same_receiver=[&] {
        if(!receiver_current())return false;
        const auto c=std::get_if<std::shared_ptr<Session>>(&receiver);
        return !c || (phase && (*c)->state()==*phase && (*c)->battle_generation()==battle);
    };
    // Obtain a second current private publication after all real receiver/NLS
    // callbacks, not a name-only join. The incarnation is checked by visibility.
    const auto again=visibility_->taiwan_chat_actor(binding,source.position);
    if(!again || again->connection.lock()!=std::get<std::shared_ptr<Session>>(receiver) ||
       again->native_actor_identity!=actor || again->native_name_bytes!=name ||
       again->raw_name_state.source_revision()!=revision || again->raw_name_state.wire_codepage()!=native_page ||
       !globals || !again->raw_name_state.same_source(*globals))return std::nullopt;
    if(!same_receiver() || !visibility_->chat_actor_snapshot_current(*retained))return std::nullopt;
    return Observed{receiver,*retained,recipient->position,phase,battle,actor,std::move(name),revision,native_page,globals};
}
std::optional<SharedPublishedChatNameSource::Witness> SharedPublishedChatNameSource::qualify(
    const Lookup& original_lookup,const Binding& original_binding,std::uint16_t page) const {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    // Copy all external identity/token inputs before any actual observers.
    const auto lookup=original_lookup;const auto binding=original_binding;
    auto observed=observe(lookup,binding,page);if(!observed || reentered_)return std::nullopt;
    return Witness(std::make_shared<const Storage>(Storage{identity_,lookup,binding,page,std::move(*observed)}));
}
bool SharedPublishedChatNameSource::current(const Witness& witness) const {
    owner();if(terminal_)return false;
    if(busy_){reentered_=true;return false;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto storage=witness.storage_;if(storage->identity!=identity_)return false;
    const auto actual=observe(storage->lookup,storage->binding,storage->page);
    if(!actual || reentered_)return false;
    const auto& before=storage->observed;
    return actual->receiver==before.receiver && actual->recipient_position==before.recipient_position &&
        actual->taiwan_phase==before.taiwan_phase && actual->taiwan_battle_generation==before.taiwan_battle_generation &&
        actual->actor==before.actor && actual->name==before.name && actual->name_source_revision==before.name_source_revision &&
        actual->native_name_page==before.native_name_page && actual->taiwan_globals==before.taiwan_globals && !reentered_ && registry_current(witness);
}
bool SharedPublishedChatNameSource::registry_current(const Witness& witness) const {
    owner();const auto storage=witness.storage_;
    return !terminal_ && !reentered_ && storage->identity==identity_ &&
        visibility_->chat_actor_snapshot_current(storage->observed.registry);
}
}
