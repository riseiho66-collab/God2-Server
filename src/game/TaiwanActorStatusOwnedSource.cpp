#include "game/TaiwanActorStatusOwnedSource.h"
#include "net/Session.h"
#include "protocol/RecoveredRemoteActor.h"
#include <algorithm>
#include <atomic>
#include <limits>
#include <stdexcept>

namespace god2 {
namespace {
template<class T>bool same_owner(const std::shared_ptr<T>& a,const std::shared_ptr<T>& b) noexcept {
    return a&&b&&a.get()==b.get()&&!a.owner_before(b)&&!b.owner_before(a);
}
}
struct TaiwanActorStatusOwnedSource::Identity {std::atomic<bool> stopped{false};};
struct TaiwanActorStatusOwnedSource::Entry {
    const std::shared_ptr<Identity> identity;
    const Lease lease;
    const Incarnation incarnation;
    const std::weak_ptr<Session> session;
    const std::uint64_t revision;
    const std::shared_ptr<const Override> actor_override;
    // No implicit ordinary state: Unknown until the real install succeeds.
    std::atomic<bool> known_clear{false},retired{false};
    Entry(std::shared_ptr<Identity> issuer,Lease actor,Incarnation token,
          const std::shared_ptr<Session>& connection,std::uint64_t serial,std::shared_ptr<const Override> value)
        :identity(std::move(issuer)),lease(std::move(actor)),incarnation(std::move(token)),session(connection),
         revision(serial),actor_override(std::move(value)){}
};
struct TaiwanActorStatusOwnedSource::InstallData {
    const std::shared_ptr<Entry> entry;
    std::atomic<bool> committed{false};
    explicit InstallData(std::shared_ptr<Entry> value) noexcept:entry(std::move(value)){}
    ~InstallData() noexcept {
        if(!committed.load(std::memory_order_acquire))entry->retired.store(true,std::memory_order_release);
    }
};
struct TaiwanActorStatusPublication::UnitData {
    // Entry contains immutable revision/override, pure atomic state identity,
    // source incarnation and only a WEAK Session. No game owner is retained.
    const std::shared_ptr<TaiwanActorStatusOwnedSource::Entry> entry;
    const TaiwanActorStatusIncarnationSource::Token recipient_incarnation;
    const std::vector<std::uint8_t> logical;
    UnitData(std::shared_ptr<TaiwanActorStatusOwnedSource::Entry> state,
             TaiwanActorStatusIncarnationSource::Token receiver,std::span<const std::uint8_t> bytes)
        :entry(std::move(state)),recipient_incarnation(std::move(receiver)),logical(bytes.begin(),bytes.end()){}
};
bool TaiwanActorStatusPublication::retained_impl(const std::shared_ptr<const UnitData>& data) noexcept {
    if(!data||!data->entry)return false;
    const auto& entry=*data->entry;
    return !entry.identity->stopped.load(std::memory_order_acquire)&&
        !entry.retired.load(std::memory_order_acquire)&&entry.known_clear.load(std::memory_order_acquire)&&
        entry.incarnation.live()&&data->recipient_incarnation.live();
}
const SharedWorldPresence::Lease& TaiwanActorStatusPublication::ActorUnit::source() const noexcept{return data_->entry->lease;}
const SharedWorldPresence::Lease& TaiwanActorStatusPublication::ActorUnit::recipient() const noexcept{return data_->recipient_incarnation.lease();}
const std::vector<std::uint8_t>& TaiwanActorStatusPublication::ActorUnit::logical() const noexcept{return data_->logical;}
bool TaiwanActorStatusPublication::ActorUnit::retained() const noexcept{return retained_impl(data_);}
struct TaiwanActorStatusOwnedSource::Data {
    const std::shared_ptr<Identity> identity;
    const std::shared_ptr<Entry> entry;
    const std::shared_ptr<const Input> input;
    const std::size_t row;
    const Equipment equipment;
    const Lease source,recipient;
    const Incarnation recipient_incarnation;
    Data(std::shared_ptr<Identity> issuer,std::shared_ptr<Entry> state,std::shared_ptr<const Input> saved,
         std::size_t index,Equipment eq,Lease receiver,Incarnation token)
        :identity(std::move(issuer)),entry(std::move(state)),input(std::move(saved)),row(index),
         equipment(std::move(eq)),source(entry->lease),recipient(std::move(receiver)),recipient_incarnation(std::move(token)){}
};
class TaiwanActorStatusOwnedSource::Operation final {
public:
    explicit Operation(const TaiwanActorStatusOwnedSource& source) noexcept:source_(source) {
        if(source.thread_!=std::this_thread::get_id()||source.identity_->stopped.load(std::memory_order_acquire))return;
        if(source.busy_){source.identity_->stopped.store(true,std::memory_order_release);return;}
        source.busy_=true;active_=true;
    }
    ~Operation(){if(active_)source_.busy_=false;}
    explicit operator bool() const noexcept{return active_;}
    Operation(const Operation&)=delete;
private:
    const TaiwanActorStatusOwnedSource& source_;
    bool active_=false;
};
TaiwanActorStatusOwnedSource::Policy::Policy(Version value,std::uint32_t raw)
    :version(value),raw_clear_index(raw) {
    if(value!=Version::Custom0133OrdinaryInitialClearV1||raw>255)
        throw std::invalid_argument("CUSTOM0133 initial clear requires explicit version/raw byte index");
}
TaiwanActorStatusOwnedSource::TaiwanActorStatusOwnedSource(const std::shared_ptr<SharedWorldPresence>& presence,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations,Policy policy)
    :presence_(presence),presence_address_(presence.get()),incarnations_(std::move(incarnations)),
     policy_(std::move(policy)),identity_(std::make_shared<Identity>()){}
std::shared_ptr<TaiwanActorStatusOwnedSource> TaiwanActorStatusOwnedSource::create(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations,Policy policy) {
    if(!presence||!incarnations||!incarnations->owns_presence(presence))return {};
    return std::shared_ptr<TaiwanActorStatusOwnedSource>(new TaiwanActorStatusOwnedSource(presence,std::move(incarnations),std::move(policy)));
}
TaiwanActorStatusOwnedSource::~TaiwanActorStatusOwnedSource() noexcept{stop();}
bool TaiwanActorStatusOwnedSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    return presence&&presence.get()==presence_address_&&!presence_.expired()&&
        !presence_.owner_before(presence)&&!presence.owner_before(presence_);
}
bool TaiwanActorStatusOwnedSource::owns_incarnations(const std::shared_ptr<TaiwanActorStatusIncarnationSource>& value) const noexcept {
    return same_owner(value,incarnations_);
}
bool TaiwanActorStatusOwnedSource::entry_retained(const Entry& entry) const noexcept {
    return entry.identity==identity_&&!identity_->stopped.load(std::memory_order_acquire)&&
        !entry.retired.load(std::memory_order_acquire)&&incarnations_->retained(entry.incarnation);
}
bool TaiwanActorStatusOwnedSource::entry_current(const std::shared_ptr<Entry>& entry) const {
    if(!entry||!entry_retained(*entry))return false;
    const auto found=entries_.find(entry->lease.session);
    if(found==entries_.end()||found->second!=entry)return false;
    const auto session=entry->session.lock();
    return session&&!session->closing()&&session->id()==entry->lease.session&&
        session->account_id==entry->lease.account&&session->character_id==entry->lease.character&&
        incarnations_->current(entry->incarnation)&&entry_retained(*entry);
}
std::optional<TaiwanActorStatusOwnedSource::InitialInstall> TaiwanActorStatusOwnedSource::begin_initial_install(
        Session& session,const Lease& supplied) noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        const auto lease=supplied;const auto presence=presence_.lock();
        if(!presence||!owns_presence(presence)||!lease.actor_handle||lease.actor_handle>0xfff||
           session.closing()||session.id()!=lease.session||session.account_id!=lease.account||session.character_id!=lease.character)return {};
        const auto token=incarnations_->observe(lease);if(!token)return {};
        // Keep failed attempts while that incarnation is live, but do not retain
        // every disconnected Session's entry for the lifetime of the host.
        for(auto i=entries_.begin();i!=entries_.end();) {
            if(!incarnations_->retained(i->second->incarnation)) {
                i->second->retired.store(true,std::memory_order_release);i=entries_.erase(i);
            }else ++i;
        }
        const auto old=entries_.find(lease.session);
        // Even an abandoned/failed attempt is remembered for this incarnation.
        if(old!=entries_.end()) {
            if(old->second->incarnation==*token)return {};
            old->second->retired.store(true,std::memory_order_release);
        }
        if(revision_==std::numeric_limits<std::uint64_t>::max()){stop();return {};}
        const auto connection=session.shared_from_this();
        RecoveredTaiwanActorOverride::LogicalRecord raw{0xea,static_cast<std::uint8_t>(lease.actor_handle),
            static_cast<std::uint8_t>(lease.actor_handle>>8),0,static_cast<std::uint8_t>(policy_.raw_clear_index)};
        const auto record=RecoveredTaiwanActorOverride::parse_logical(raw);if(!record){stop();return {};}
        auto replay=std::make_shared<const Override>(*record);
        auto entry=std::make_shared<Entry>(identity_,lease,*token,connection,++revision_,std::move(replay));
        // InstallData and map allocation all precede the real install callback.
        auto ticket=std::make_shared<InstallData>(entry);
        entries_.insert_or_assign(lease.session,entry);
        if(!entry_current(entry))return {};
        return InitialInstall(std::move(ticket));
    }catch(...){stop();return {};}
}
bool TaiwanActorStatusOwnedSource::commit_initial_clear(const InitialInstall& value) noexcept {
    Operation operation(*this);if(!operation)return false;
    try {
        const auto ticket=value.data_;const auto entry=ticket->entry;
        if(ticket->committed.load(std::memory_order_acquire)||entry->known_clear.load(std::memory_order_acquire)||
           !entry_current(entry))return false;
        // No allocations/providers/SQL after this final actual token/session cut.
        entry->known_clear.store(true,std::memory_order_release);
        ticket->committed.store(true,std::memory_order_release);
        return entry_retained(*entry);
    }catch(...){stop();return false;}
}
void TaiwanActorStatusOwnedSource::retire_initial_install(const InitialInstall& value) noexcept {
    const auto entry=value.data_->entry;
    if(entry->identity==identity_)entry->retired.store(true,std::memory_order_release);
}
bool TaiwanActorStatusOwnedSource::retained_data(const Data& data) const {
    if(data.identity!=identity_||!entry_retained(*data.entry)||!data.entry->known_clear.load(std::memory_order_acquire)||
       !data.input||data.source!=data.entry->lease||data.source.session==data.recipient.session||
       data.recipient_incarnation.lease()!=data.recipient||!incarnations_->retained(data.recipient_incarnation))return false;
    const auto& saved=data.input->readset();const auto& rows=saved.materials();
    if(data.row>=rows.size()||rows[data.row].actor.lease!=data.source||!data.input->source()||
       !data.input->source()->owns_readset(saved)||!data.input->source()->profile_equipment_matches(data.equipment,saved,data.row)||
       !saved.matches_population(data.input->characters()))return false;
    const auto presence=presence_.lock();
    if(!presence||!owns_presence(presence)||!data.input->source()->owns_presence(presence)||
       !data.input->population_current(presence))return false;
    std::size_t receivers=0;for(const auto& row:rows)if(row.actor.lease==data.recipient)++receivers;
    return receivers==1&&entry_retained(*data.entry)&&incarnations_->retained(data.recipient_incarnation);
}
std::optional<TaiwanActorStatusOwnedSource::Observation> TaiwanActorStatusOwnedSource::observe(
        std::shared_ptr<const Input> input,std::size_t row,Equipment equipment,Lease recipient) const noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        if(!input||row>=input->readset().materials().size())return {};
        const auto lease=input->readset().materials()[row].actor.lease;
        const auto found=entries_.find(lease.session);if(found==entries_.end())return {};
        const auto entry=found->second;
        if(entry->lease!=lease||!entry->known_clear.load(std::memory_order_acquire)||!entry_current(entry))return {};
        const auto token=incarnations_->observe(recipient);if(!token)return {};
        auto data=std::make_shared<const Data>(identity_,entry,std::move(input),row,std::move(equipment),recipient,*token);
        if(!retained_data(*data)||!entry_current(entry)||!incarnations_->current(*token)||!retained_data(*data))return {};
        return Observation(std::move(data));
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return {};}
}
bool TaiwanActorStatusOwnedSource::matches_inputs(const Observation& value,const std::shared_ptr<const Input>& input,
        std::size_t row,const Equipment& equipment,const Lease& recipient) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){identity_->stopped.store(true,std::memory_order_release);return false;}
    const auto& data=*value.data_;
    return data.identity==identity_&&same_owner(data.input,input)&&data.row==row&&data.equipment==equipment&&data.recipient==recipient;
}
bool TaiwanActorStatusOwnedSource::retained(const Observation& value) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){identity_->stopped.store(true,std::memory_order_release);return false;}
    try {return retained_data(*value.data_);}catch(...){identity_->stopped.store(true,std::memory_order_release);return false;}
}
bool TaiwanActorStatusOwnedSource::current(const Observation& value) const noexcept {
    Operation operation(*this);if(!operation)return false;
    try {
        const auto data=value.data_;
        return retained_data(*data)&&entry_current(data->entry)&&incarnations_->current(data->recipient_incarnation)&&retained_data(*data);
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return false;}
}
std::optional<TaiwanActorStatusPublication::ActorUnit> TaiwanActorStatusOwnedSource::prepare_publication(
        const Observation& value,std::span<const std::uint8_t> whole_unit) const noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        const auto data=value.data_;
        if(!retained_data(*data)||!entry_current(data->entry)||
           !incarnations_->current(data->recipient_incarnation)||!retained_data(*data))return {};
        constexpr auto actor_size=RecoveredRemoteActor::logical_size;
        constexpr auto override_size=RecoveredTaiwanActorOverride::logical_size;
        if(whole_unit.size()!=actor_size+override_size)return {};
        const auto actor=RecoveredRemoteActor::parse_logical(whole_unit.first(actor_size));
        const auto& replay=data->entry->actor_override->replay();
        if(!actor||actor->identity()!=data->source.actor_handle||!replay||replay->type()!=0||
           replay->identity()!=data->source.actor_handle||replay->is_self(data->recipient.actor_handle))return {};
        const auto expected=RecoveredTaiwanActorOverride::encode_logical(*replay);
        if(!std::equal(expected.begin(),expected.end(),whole_unit.begin()+actor_size))return {};
        auto unit=std::make_shared<const TaiwanActorStatusPublication::UnitData>(
            data->entry,data->recipient_incarnation,whole_unit);
        // Byte copies/allocations precede the final actual status/lifetime cuts.
        // The returned unit never captures this Observation or its saved input.
        if(!retained_data(*data)||!entry_current(data->entry)||
           !incarnations_->current(data->recipient_incarnation)||!retained_data(*data)||
           !TaiwanActorStatusPublication::retained_impl(unit))return {};
        return TaiwanActorStatusPublication::ActorUnit(std::move(unit));
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return {};}
}
std::uint64_t TaiwanActorStatusOwnedSource::Observation::revision() const noexcept{return data_->entry->revision;}
const std::shared_ptr<const TaiwanActorStatusOwnedSource::Override>& TaiwanActorStatusOwnedSource::Observation::actor_override() const noexcept{return data_->entry->actor_override;}
const std::shared_ptr<const TaiwanActorStatusOwnedSource::Input>& TaiwanActorStatusOwnedSource::Observation::saved_input() const noexcept{return data_->input;}
std::size_t TaiwanActorStatusOwnedSource::Observation::row_index() const noexcept{return data_->row;}
const TaiwanActorStatusOwnedSource::Equipment& TaiwanActorStatusOwnedSource::Observation::equipment() const noexcept{return data_->equipment;}
const TaiwanActorStatusOwnedSource::Lease& TaiwanActorStatusOwnedSource::Observation::source() const noexcept{return data_->source;}
const TaiwanActorStatusOwnedSource::Lease& TaiwanActorStatusOwnedSource::Observation::recipient() const noexcept{return data_->recipient;}
const TaiwanActorStatusOwnedSource::Incarnation& TaiwanActorStatusOwnedSource::Observation::source_incarnation() const noexcept{return data_->entry->incarnation;}
const TaiwanActorStatusOwnedSource::Incarnation& TaiwanActorStatusOwnedSource::Observation::recipient_incarnation() const noexcept{return data_->recipient_incarnation;}
void TaiwanActorStatusOwnedSource::stop() noexcept{identity_->stopped.store(true,std::memory_order_release);}
}
