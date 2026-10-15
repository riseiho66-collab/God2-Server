#include "game/TaiwanActorStatusIncarnationSource.h"
#include "net/Session.h"
#include <atomic>
#include <limits>

namespace god2 {
struct TaiwanActorStatusIncarnationSource::Identity {
    std::atomic<bool> stopped{false};
};
struct TaiwanActorStatusIncarnationSource::Entry {
    const std::shared_ptr<Identity> identity;
    const Lease lease;
    const std::uint64_t sequence;
    const std::weak_ptr<Session> session;
    const std::thread::id thread=std::this_thread::get_id();
    std::atomic<bool> retired{false};
    Entry(std::shared_ptr<Identity> issuer,Lease value,std::uint64_t serial,
          const std::shared_ptr<Session>& connection)
        :identity(std::move(issuer)),lease(std::move(value)),sequence(serial),session(connection){}
};
class TaiwanActorStatusIncarnationSource::Operation final {
public:
    explicit Operation(const TaiwanActorStatusIncarnationSource& source) noexcept:source_(source) {
        if(source.thread_!=std::this_thread::get_id()||source.identity_->stopped.load(std::memory_order_acquire))return;
        if(source.busy_){source.identity_->stopped.store(true,std::memory_order_release);return;}
        source.busy_=true;active_=true;
    }
    ~Operation(){if(active_)source_.busy_=false;}
    explicit operator bool() const noexcept{return active_;}
    Operation(const Operation&)=delete;
private:
    const TaiwanActorStatusIncarnationSource& source_;
    bool active_=false;
};
const TaiwanActorStatusIncarnationSource::Lease& TaiwanActorStatusIncarnationSource::Token::lease() const noexcept {
    return entry_->lease;
}
std::uint64_t TaiwanActorStatusIncarnationSource::Token::sequence() const noexcept{return entry_->sequence;}
void TaiwanActorStatusIncarnationSource::Token::retire() const noexcept{entry_->retired.store(true,std::memory_order_release);}
bool TaiwanActorStatusIncarnationSource::Token::live() const noexcept {
    return !entry_->identity->stopped.load(std::memory_order_acquire)&&!entry_->retired.load(std::memory_order_acquire);
}
bool TaiwanActorStatusIncarnationSource::Token::can_bind(Session& session) const noexcept {
    if(entry_->thread!=std::this_thread::get_id()||!live())return false;
    const auto connection=entry_->session.lock();
    return connection.get()==&session&&!session.closing()&&session.id()==entry_->lease.session&&
        session.account_id==entry_->lease.account&&session.character_id==entry_->lease.character&&live();
}
TaiwanActorStatusIncarnationSource::TaiwanActorStatusIncarnationSource(const std::shared_ptr<SharedWorldPresence>& presence)
    :presence_(presence),presence_address_(presence.get()),identity_(std::make_shared<Identity>()){}
std::shared_ptr<TaiwanActorStatusIncarnationSource> TaiwanActorStatusIncarnationSource::create(
    std::shared_ptr<SharedWorldPresence> presence) {
    if(!presence)return {};
    return std::shared_ptr<TaiwanActorStatusIncarnationSource>(new TaiwanActorStatusIncarnationSource(presence));
}
TaiwanActorStatusIncarnationSource::~TaiwanActorStatusIncarnationSource() noexcept{stop();}
bool TaiwanActorStatusIncarnationSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    return presence&&presence.get()==presence_address_&&!presence_.expired()&&
        !presence_.owner_before(presence)&&!presence.owner_before(presence_);
}
bool TaiwanActorStatusIncarnationSource::retained(const Token& token) const noexcept {
    return token.entry_->identity==identity_&&token.live();
}
bool TaiwanActorStatusIncarnationSource::current_entry(const std::shared_ptr<Entry>& entry,bool require_bound) const {
    if(entry->identity!=identity_||identity_->stopped.load(std::memory_order_acquire)||
       entry->retired.load(std::memory_order_acquire))return false;
    const auto found=entries_.find(entry->lease.session);
    if(found==entries_.end()||found->second.lock()!=entry)return false;
    const auto presence=presence_.lock();const auto session=entry->session.lock();
    if(!presence||!session||!owns_presence(presence)||session->closing()||
       session->id()!=entry->lease.session||session->account_id!=entry->lease.account||
       session->character_id!=entry->lease.character)return false;
    if(require_bound&&!session->actor_status_incarnation_matches(Token(entry)))return false;
    // Activation does not replace an incarnation. Both checks are retained
    // registry-only; do not consult saved-position or normal-output Current.
    if(!presence->retained_preparation_current(entry->lease)&&!presence->retained_ready_current(entry->lease))return false;
    return !identity_->stopped.load(std::memory_order_acquire)&&!entry->retired.load(std::memory_order_acquire);
}
std::optional<TaiwanActorStatusIncarnationSource::Token> TaiwanActorStatusIncarnationSource::observe(const Lease& input) const noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        const auto lease=input;const auto found=entries_.find(lease.session);
        if(found==entries_.end())return {};
        const auto entry=found->second.lock();
        if(!entry||entry->lease!=lease||!current_entry(entry))return {};
        return Token(entry);
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return {};}
}
bool TaiwanActorStatusIncarnationSource::current(const Token& input) const noexcept {
    Operation operation(*this);if(!operation)return false;
    try {const auto entry=input.entry_;return current_entry(entry);}
    catch(...){identity_->stopped.store(true,std::memory_order_release);return false;}
}
std::optional<TaiwanActorStatusIncarnationSource::Token> TaiwanActorStatusIncarnationSource::prepare(
    Session& session,const Lease& input) noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        const auto lease=input;const auto presence=presence_.lock();
        if(!presence||!owns_presence(presence)||!lease.session||!lease.account||!lease.character||!lease.generation||
           session.closing()||session.id()!=lease.session||session.account_id!=lease.account||
           session.character_id!=lease.character||!presence->retained_preparation_current(lease))return {};
        const auto connection=session.shared_from_this();
        if(sequence_==std::numeric_limits<std::uint64_t>::max()){stop();return {};}
        // An actual replacement retires the predecessor before any allocation
        // or registry replacement. Failure permanently disables all old tokens.
        const auto previous=entries_.find(lease.session);
        if(previous!=entries_.end())if(const auto old=previous->second.lock())old->retired.store(true,std::memory_order_release);
        const auto entry=std::make_shared<Entry>(identity_,lease,++sequence_,connection);
        entries_.insert_or_assign(lease.session,entry);
        // All allocation/map-node work precedes this final retained cut.
        // Actual lifecycle binds the Session slot immediately after this mint.
        if(!current_entry(entry,false)||!presence->retained_preparation_current(lease)){stop();return {};}
        return Token(entry);
    }catch(...){stop();return {};}
}
void TaiwanActorStatusIncarnationSource::retire(const Token& input) noexcept {
    const auto entry=input.entry_;
    if(entry->identity!=identity_)return;
    // First atomic retire is safe even during exceptional/off-thread cleanup.
    // Never read mutable registry/game fields from a foreign thread.
    entry->retired.store(true,std::memory_order_release);
    if(thread_!=std::this_thread::get_id())return;
    Operation operation(*this);if(!operation)return;
    const auto found=entries_.find(entry->lease.session);
    if(found!=entries_.end()&&found->second.lock()==entry)entries_.erase(found);
}
void TaiwanActorStatusIncarnationSource::stop() noexcept{identity_->stopped.store(true,std::memory_order_release);}
}
