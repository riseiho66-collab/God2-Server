#include "game/TaiwanActorStatusProfileScope.h"
#include <atomic>

namespace god2 {
namespace {
template<class T>bool same_owner(const std::shared_ptr<T>& a,const std::shared_ptr<T>& b) noexcept {
    return a&&b&&a.get()==b.get()&&!a.owner_before(b)&&!b.owner_before(a);
}
}
struct TaiwanActorStatusProfileScope::Identity {std::atomic<bool> stopped{false};};
struct TaiwanActorStatusProfileScope::Data {
    const std::shared_ptr<Identity> identity;
    const std::shared_ptr<const Input> input;
    const std::size_t row;
    const Equipment equipment;
    const Lease source,recipient;
    const Incarnation source_incarnation,recipient_incarnation;
    Data(std::shared_ptr<Identity> issuer,std::shared_ptr<const Input> saved,std::size_t index,
         Equipment eq,Lease actor,Lease receiver,Incarnation a,Incarnation b)
        :identity(std::move(issuer)),input(std::move(saved)),row(index),equipment(std::move(eq)),
         source(std::move(actor)),recipient(std::move(receiver)),source_incarnation(std::move(a)),
         recipient_incarnation(std::move(b)){}
};
class TaiwanActorStatusProfileScope::Operation final {
public:
    explicit Operation(const TaiwanActorStatusProfileScope& source) noexcept:source_(source) {
        if(source.thread_!=std::this_thread::get_id()||source.identity_->stopped.load(std::memory_order_acquire))return;
        if(source.busy_){source.identity_->stopped.store(true,std::memory_order_release);return;}
        source.busy_=true;active_=true;
    }
    ~Operation(){if(active_)source_.busy_=false;}
    explicit operator bool() const noexcept{return active_;}
    Operation(const Operation&)=delete;
private:
    const TaiwanActorStatusProfileScope& source_;
    bool active_=false;
};
const std::shared_ptr<const TaiwanActorStatusProfileScope::Input>& TaiwanActorStatusProfileScope::Observation::saved_input() const noexcept{return data_->input;}
std::size_t TaiwanActorStatusProfileScope::Observation::row_index() const noexcept{return data_->row;}
const TaiwanActorStatusProfileScope::Equipment& TaiwanActorStatusProfileScope::Observation::equipment() const noexcept{return data_->equipment;}
const TaiwanActorStatusProfileScope::Lease& TaiwanActorStatusProfileScope::Observation::source() const noexcept{return data_->source;}
const TaiwanActorStatusProfileScope::Lease& TaiwanActorStatusProfileScope::Observation::recipient() const noexcept{return data_->recipient;}
const TaiwanActorStatusProfileScope::Incarnation& TaiwanActorStatusProfileScope::Observation::source_incarnation() const noexcept{return data_->source_incarnation;}
const TaiwanActorStatusProfileScope::Incarnation& TaiwanActorStatusProfileScope::Observation::recipient_incarnation() const noexcept{return data_->recipient_incarnation;}
TaiwanActorStatusProfileScope::TaiwanActorStatusProfileScope(const std::shared_ptr<SharedWorldPresence>& presence,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations)
    :presence_(presence),presence_address_(presence.get()),incarnations_(std::move(incarnations)),identity_(std::make_shared<Identity>()){}
std::shared_ptr<TaiwanActorStatusProfileScope> TaiwanActorStatusProfileScope::create(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations) {
    if(!presence||!incarnations||!incarnations->owns_presence(presence))return {};
    return std::shared_ptr<TaiwanActorStatusProfileScope>(new TaiwanActorStatusProfileScope(presence,std::move(incarnations)));
}
TaiwanActorStatusProfileScope::~TaiwanActorStatusProfileScope() noexcept{stop();}
bool TaiwanActorStatusProfileScope::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    return presence&&presence.get()==presence_address_&&!presence_.expired()&&
        !presence_.owner_before(presence)&&!presence.owner_before(presence_);
}
bool TaiwanActorStatusProfileScope::owns_incarnations(const std::shared_ptr<TaiwanActorStatusIncarnationSource>& source) const noexcept {
    return same_owner(source,incarnations_);
}
bool TaiwanActorStatusProfileScope::shape(const Data& data) const noexcept {
    if(data.identity!=identity_||!data.input||identity_->stopped.load(std::memory_order_acquire)||
       data.source.session==data.recipient.session)return false;
    const auto& saved=data.input->readset();const auto& rows=saved.materials();
    if(data.row>=rows.size()||rows[data.row].actor.lease!=data.source||
       data.source_incarnation.lease()!=data.source||data.recipient_incarnation.lease()!=data.recipient||
       !data.input->source()||!data.input->source()->owns_readset(saved)||
       !data.input->source()->profile_equipment_matches(data.equipment,saved,data.row)||
       !saved.matches_population(data.input->population().characters()))return false;
    std::size_t recipients=0;
    for(const auto& actor:rows)if(actor.actor.lease==data.recipient)++recipients;
    return recipients==1;
}
bool TaiwanActorStatusProfileScope::retained_data(const Data& data) const {
    if(!shape(data))return false;
    const auto presence=presence_.lock();
    if(!presence||!owns_presence(presence)||!data.input->source()->owns_presence(presence)||
       !incarnations_->owns_presence(presence)||!presence->retained_population_current(data.input->population())||
       !incarnations_->retained(data.source_incarnation)||!incarnations_->retained(data.recipient_incarnation))return false;
    return !identity_->stopped.load(std::memory_order_acquire);
}
std::optional<TaiwanActorStatusProfileScope::Observation> TaiwanActorStatusProfileScope::observe(
        std::shared_ptr<const Input> input,std::size_t row,Equipment equipment,Lease recipient) const noexcept {
    Operation operation(*this);if(!operation)return {};
    try {
        const auto presence=presence_.lock();
        if(!presence||!input||!owns_presence(presence)||!input->source()||
           !input->source()->owns_presence(presence)||!input->source()->owns_readset(input->readset())||
           !input->source()->profile_equipment_matches(equipment,input->readset(),row)||
           !input->readset().matches_population(input->population().characters())||
           !presence->retained_population_current(input->population())||row>=input->readset().materials().size())return {};
        const auto source=input->readset().materials()[row].actor.lease;
        if(source.session==recipient.session)return {};
        std::size_t recipients=0;for(const auto& actor:input->readset().materials())if(actor.actor.lease==recipient)++recipients;
        if(recipients!=1)return {};
        const auto a=incarnations_->observe(source),b=incarnations_->observe(recipient);
        if(!a||!b)return {};
        const auto data=std::make_shared<const Data>(identity_,std::move(input),row,std::move(equipment),source,recipient,*a,*b);
        // Allocation/new_handler precedes the final lifetime/whole-population
        // cut. No SQL, provider or wire authoring occurs in this component.
        if(!retained_data(*data)||!incarnations_->current(data->source_incarnation)||
           !incarnations_->current(data->recipient_incarnation)||!retained_data(*data))return {};
        return Observation(data);
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return {};}
}
bool TaiwanActorStatusProfileScope::matches_inputs(const Observation& value,const std::shared_ptr<const Input>& input,
        std::size_t row,const Equipment& equipment,const Lease& recipient) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){identity_->stopped.store(true,std::memory_order_release);return false;}
    const auto& data=*value.data_;
    return shape(data)&&same_owner(data.input,input)&&data.row==row&&data.equipment==equipment&&data.recipient==recipient;
}
bool TaiwanActorStatusProfileScope::retained(const Observation& value) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){identity_->stopped.store(true,std::memory_order_release);return false;}
    try {const auto data=value.data_;return retained_data(*data);}
    catch(...){identity_->stopped.store(true,std::memory_order_release);return false;}
}
bool TaiwanActorStatusProfileScope::current(const Observation& value) const noexcept {
    Operation operation(*this);if(!operation)return false;
    try {
        const auto data=value.data_;
        return retained_data(*data)&&incarnations_->current(data->source_incarnation)&&
            incarnations_->current(data->recipient_incarnation)&&retained_data(*data);
    }catch(...){identity_->stopped.store(true,std::memory_order_release);return false;}
}
void TaiwanActorStatusProfileScope::stop() noexcept{identity_->stopped.store(true,std::memory_order_release);}
}
