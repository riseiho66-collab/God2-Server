#include "game/SharedNativeWorldTransports.h"
#include <exception>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2 {
struct SharedNativeWorldTransports::Identity {};
struct SharedNativeWorldTransports::TokenStorage {
    std::shared_ptr<const Identity> identity;
    Lease lease;
    std::uint64_t generation;
    WeakTransport transport;
};
struct SharedNativeWorldTransports::SnapshotStorage {
    Token token;
    StrongTransport transport;
    std::optional<SessionState> phase;
    std::uint64_t battle_generation;
};
SharedNativeWorldTransports::Token::Token(std::shared_ptr<const TokenStorage> s):storage_(std::move(s)) {}
SharedNativeWorldTransports::Token::Token(Token&& other) noexcept:storage_(other.storage_) {}
SharedNativeWorldTransports::Token& SharedNativeWorldTransports::Token::operator=(Token&& other) noexcept {
    storage_=other.storage_;return *this;
}
const SharedNativeWorldTransports::Lease& SharedNativeWorldTransports::Token::lease() const noexcept {return storage_->lease;}
SharedNativeWorldTransports::Snapshot::Snapshot(std::shared_ptr<const SnapshotStorage> s):storage_(std::move(s)) {}
SharedNativeWorldTransports::Snapshot::Snapshot(Snapshot&& other) noexcept:storage_(other.storage_) {}
SharedNativeWorldTransports::Snapshot& SharedNativeWorldTransports::Snapshot::operator=(Snapshot&& other) noexcept {
    storage_=other.storage_;return *this;
}
const SharedNativeWorldTransports::Token& SharedNativeWorldTransports::Snapshot::token() const noexcept {return storage_->token;}
const SharedNativeWorldTransports::Lease& SharedNativeWorldTransports::Snapshot::lease() const noexcept {return storage_->token.lease();}
const SharedNativeWorldTransports::StrongTransport& SharedNativeWorldTransports::Snapshot::transport() const noexcept {return storage_->transport;}
SharedNativeWorldTransports::SharedNativeWorldTransports(std::shared_ptr<SharedWorldPresence> p)
    :presence_(std::move(p)),identity_(std::make_shared<const Identity>()) {}
SharedNativeWorldTransports::~SharedNativeWorldTransports() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    terminal_=true;busy_=true;slots_.clear();identity_.reset();presence_.reset();
}
void SharedNativeWorldTransports::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Common native transports game owner mismatch");
}
std::shared_ptr<SharedNativeWorldTransports> SharedNativeWorldTransports::create(std::shared_ptr<SharedWorldPresence> p) {
    if(!p)return {};
    return std::shared_ptr<SharedNativeWorldTransports>(new SharedNativeWorldTransports(std::move(p)));
}
bool SharedNativeWorldTransports::owns_presence(const std::shared_ptr<SharedWorldPresence>& p) const {
    owner();return !terminal_ && p && p==presence_;
}
bool SharedNativeWorldTransports::stored(const Token& token) const {
    const auto s=token.storage_;if(terminal_ || s->identity!=identity_ || !s->generation)return false;
    const auto found=slots_.find(s->lease.session);
    return found!=slots_.end() && found->second.storage_==s;
}
bool SharedNativeWorldTransports::tuple(const Lease& lease,const StrongTransport& transport) const {
    if(terminal_ || reentered_)return false;
    return std::visit([&](const auto& c) {
        if(!c || c->closing())return false;
        using Connection=typename std::decay_t<decltype(c)>::element_type;
        if constexpr(std::is_same_v<Connection,Session>)
            return c->id()==lease.session && c->account_id==lease.account && c->character_id==lease.character &&
                c->recovered_world_ready() && (c->state()==SessionState::InWorld || c->state()==SessionState::InBattle) &&
                c->common_world_delivery_current(lease.account,lease.character,lease.generation) &&
                !c->common_world_entry_current(lease.account,lease.character,lease.generation);
        else return c->role()==cn::SharedCredentialConnection::Transport::Role::World && c->world_admission_current() &&
            c->world_session_id()==lease.session && c->verified_account_id()==lease.account && c->world_character_offered(lease.character);
    },transport);
}
bool SharedNativeWorldTransports::qualified(const Token& token,const StrongTransport& transport) const {
    const auto retained=token;
    const auto same_registry=[&] {
        if(reentered_ || !stored(retained))return false;
        const auto actual=std::visit([](const auto& c)->StrongTransport{return c.lock();},retained.storage_->transport);
        return actual==transport && tuple(retained.lease(),transport);
    };
    if(!same_registry())return false;
    const auto tw=std::get_if<std::shared_ptr<Session>>(&transport);
    const auto phase=tw?std::optional{(*tw)->state()}:std::nullopt;
    const auto battle=tw?(*tw)->battle_generation():0;
    // Receiver is strong before all real repository observers. No iterator or
    // weak connection lock from an obsolete registry node survives callbacks.
    const auto ready=presence_->ready_lease(retained.lease().session,retained.lease().account,retained.lease().character);
    if(!ready || *ready!=retained.lease() || !same_registry())return false;
    const auto population=presence_->ready_characters();if(!population || !same_registry())return false;
    std::size_t matches=0;
    for(const auto& row:*population)if(row.lease==retained.lease()) {
        if(row.character.id!=row.lease.character || row.character.account_id!=row.lease.account)return false;
        ++matches;
    }
    if(matches!=1)return false;
    const auto after=presence_->ready_lease(retained.lease().session,retained.lease().account,retained.lease().character);
    return after && *after==retained.lease() && same_registry() &&
        (!tw || (phase && (*tw)->state()==*phase && (*tw)->battle_generation()==battle));
}
std::optional<SharedNativeWorldTransports::Token> SharedNativeWorldTransports::bind_owned(const Lease& lease,StrongTransport receiver) {
    if(!lease.session || !lease.account || !lease.character || !lease.generation || !tuple(lease,receiver) || slots_.contains(lease.session))
        return std::nullopt;
    const auto duplicate=[&] {
        if(slots_.contains(lease.session))return true;
        for(const auto& [id,slot]:slots_) {
            const auto actual=std::visit([](const auto& c)->StrongTransport{return c.lock();},slot.storage_->transport);
            if(actual==receiver)return true;
        }
        return false;
    };
    if(duplicate())return std::nullopt;
    const auto ready=presence_->ready_lease(lease.session,lease.account,lease.character);
    if(!ready || *ready!=lease || reentered_ || !tuple(lease,receiver) || duplicate())return std::nullopt;
    const auto population=presence_->ready_characters();if(!population || reentered_ || !tuple(lease,receiver) || duplicate())return std::nullopt;
    std::size_t matches=0;
    for(const auto& row:*population)if(row.lease==lease) {
        if(row.character.id!=lease.character || row.character.account_id!=lease.account)return std::nullopt;
        ++matches;
    }
    if(matches!=1)return std::nullopt;
    if(generation_==std::numeric_limits<std::uint64_t>::max())throw std::overflow_error("Common native transport incarnation exhausted");
    const auto weak=std::visit([](const auto& c)->WeakTransport {
        using Connection=typename std::decay_t<decltype(c)>::element_type;return std::weak_ptr<Connection>{c};
    },receiver);
    Token token(std::make_shared<const TokenStorage>(TokenStorage{identity_,lease,generation_+1,weak}));
    if(!slots_.emplace(lease.session,token).second)return std::nullopt;
    ++generation_;return token;
}
std::optional<SharedNativeWorldTransports::Token> SharedNativeWorldTransports::bind(const Lease& original,const std::shared_ptr<Session>& original_receiver) {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto lease=original;const auto receiver=original_receiver;
    return bind_owned(lease,StrongTransport{receiver});
}
std::optional<SharedNativeWorldTransports::Token> SharedNativeWorldTransports::bind(const Lease& original,const std::shared_ptr<cn::SharedCredentialConnection>& original_receiver) {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto lease=original;const auto receiver=original_receiver;
    return bind_owned(lease,StrongTransport{receiver});
}
bool SharedNativeWorldTransports::release(const Token& original) {
    owner();if(terminal_)return false;
    if(busy_)reentered_=true;
    const auto token=original;
    if(!stored(token))return false;
    slots_.erase(token.lease().session);return true; // Never calls Presence or closes any connection.
}
bool SharedNativeWorldTransports::current(const Token& original) const {
    owner();if(terminal_)return false;
    if(busy_){reentered_=true;return false;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto token=original;
    const auto receiver=std::visit([](const auto& c)->StrongTransport{return c.lock();},token.storage_->transport);
    return qualified(token,receiver);
}
std::optional<SharedNativeWorldTransports::Snapshot> SharedNativeWorldTransports::lookup(const Lease& original) const {
    owner();if(terminal_)return std::nullopt;
    if(busy_){reentered_=true;return std::nullopt;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto lease=original;
    const auto found=slots_.find(lease.session);if(found==slots_.end() || found->second.lease()!=lease)return std::nullopt;
    const auto token=found->second;
    const auto receiver=std::visit([](const auto& c)->StrongTransport{return c.lock();},token.storage_->transport);
    if(!qualified(token,receiver))return std::nullopt;
    const auto tw=std::get_if<std::shared_ptr<Session>>(&receiver);
    return Snapshot(std::make_shared<const SnapshotStorage>(SnapshotStorage{
        token,receiver,tw?std::optional{(*tw)->state()}:std::nullopt,tw?(*tw)->battle_generation():0}));
}
bool SharedNativeWorldTransports::current(const Snapshot& original) const {
    owner();if(terminal_)return false;
    if(busy_){reentered_=true;return false;}
    busy_=true;reentered_=false;
    struct EndOperation {bool& busy;~EndOperation(){busy=false;}} end{busy_};
    const auto snapshot=original.storage_;
    if(!qualified(snapshot->token,snapshot->transport))return false;
    const auto tw=std::get_if<std::shared_ptr<Session>>(&snapshot->transport);
    return !tw || (snapshot->phase && (*tw)->state()==*snapshot->phase && (*tw)->battle_generation()==snapshot->battle_generation);
}
bool SharedNativeWorldTransports::registry_current(const Snapshot& original) const {
    owner();const auto snapshot=original.storage_;
    if(terminal_ || reentered_ || !stored(snapshot->token))return false;
    const auto actual=std::visit([](const auto& c)->StrongTransport{return c.lock();},snapshot->token.storage_->transport);
    if(actual!=snapshot->transport || !tuple(snapshot->token.lease(),actual))return false;
    const auto tw=std::get_if<std::shared_ptr<Session>>(&actual);
    return !tw || (snapshot->phase && (*tw)->state()==*snapshot->phase && (*tw)->battle_generation()==snapshot->battle_generation);
}
bool SharedNativeWorldTransports::registry_current(const Token& original) const {
    owner();const auto token=original;
    if(terminal_ || reentered_ || !stored(token))return false;
    const auto actual=std::visit([](const auto& c)->StrongTransport{return c.lock();},token.storage_->transport);
    return tuple(token.lease(),actual);
}
bool SharedNativeWorldTransports::same_registration(const Token& first,const Token& second) const {
    owner();return !terminal_ && !reentered_ && first.storage_==second.storage_ && stored(first);
}
}
