#include "game/SharedNativeSpectatorTargets.h"
#include "protocol/RecoveredSpectatorTargetsD0.h"
#include <exception>
#include <limits>
#include <map>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
using Source=SharedNativeSpectatorTargets;
using Pub=Source::Publication;
using Strong=SharedNativeWorldTransports::StrongTransport;
struct Identity {};
struct Entry {
    const Source::Token token;
    const Pub::Observation issued_ui; // Immutable view; actual receiver/core remain weak.
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    const std::vector<Source::BindingView> bindings;
    const std::weak_ptr<Source::Issuer> issuer;
    const std::uint64_t generation,epoch;
    bool retired=false,terminal=false;
    Entry(const Pub::Observation& ui,std::vector<Source::BindingView> values,
        const std::shared_ptr<Source::Issuer>& owner,std::uint64_t g,std::uint64_t e)
        :token(ui.token()),issued_ui(ui),bindings(std::move(values)),issuer(owner),generation(g),epoch(e) {}
};
struct D0 {
    std::uint64_t revision;
    std::size_t ordinal;
    std::uint8_t slot;
    std::uint16_t first,second;
};
bool same_character(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool same_scope(const Source::Scope& a,const Source::Scope& b) {
    return a.recipient==b.recipient && same_character(a.character,b.character) && a.saved_position==b.saved_position &&
        a.protocol==b.protocol && a.taiwan_phase==b.taiwan_phase && a.taiwan_battle_generation==b.taiwan_battle_generation;
}
template<class T> bool same_weak(const std::weak_ptr<T>& a,const std::weak_ptr<T>& b) {
    return !a.owner_before(b) && !b.owner_before(a);
}
std::optional<std::map<std::uint8_t,D0>> last_d0(const Pub::Observation& ui) {
    std::map<std::uint8_t,D0> result;
    for(const auto& event:ui.history()) {
        if(event.recipient!=ui.lease() || event.ui_epoch!=ui.ui_epoch())return std::nullopt;
        std::size_t ordinal=0;
        for(std::size_t at=0;at<event.logical.size();++ordinal) {
            const auto opcode=event.logical[at];
            const std::size_t length=opcode==0xcd?65:opcode==0xd0?7:0;
            if(!length || length>event.logical.size()-at)return std::nullopt;
            if(opcode==0xd0) {
                const std::span<const std::uint8_t> raw(event.logical.data()+at,length);
                if(event.protocol==Pub::Protocol::Taiwan) {
                    const auto view=RecoveredSpectatorTargetsD0::read(raw);if(!view)return std::nullopt;
                    result.insert_or_assign(view->slot(),D0{event.revision,ordinal,view->slot(),view->first_target(),view->second_target()});
                }else return std::nullopt;
            }
            at+=length;
        }
    }
    return result;
}
bool binding_current(const Source::BindingView& binding,const std::map<std::uint8_t,D0>& latest) {
    const auto found=latest.find(binding.slot);if(found==latest.end())return false;
    const auto& raw=found->second;
    if(raw.revision!=binding.event_revision || raw.ordinal!=binding.record_ordinal)return false;
    if(binding.operand!=Source::Operand::First && binding.operand!=Source::Operand::Second)return false;
    return binding.raw_context==(binding.operand==Source::Operand::First?raw.first:raw.second);
}
}
struct SharedNativeSpectatorTargets::Observed {
    const std::shared_ptr<const Identity> source;
    const Token token;
    const std::uint32_t context;
    std::shared_ptr<const Identity> entry;
    std::shared_ptr<const std::vector<BindingView>> bindings=std::make_shared<const std::vector<BindingView>>();
    std::optional<Publication::Observation> ui;
    std::weak_ptr<Target> target;
    std::uint64_t target_generation=0,issuer_generation=0,absence_generation=0;
    Status status=Status::Unavailable;
    bool ready=false,blocked=false,retired=false,terminal=false;
    Observed(std::shared_ptr<const Identity> owner,const Token& t,std::uint32_t raw):source(std::move(owner)),token(t),context(raw) {}
};
struct SharedNativeSpectatorTargets::Retirement {
    const std::shared_ptr<const Identity> source,entry;
    const Token token;
    const Publication::Observation issued_ui;
    const std::uint64_t epoch,generation;
    Retirement(std::shared_ptr<const Identity> owner,const Entry& actual)
        :source(std::move(owner)),entry(actual.identity),token(actual.token),issued_ui(actual.issued_ui),
         epoch(actual.epoch),generation(actual.generation) {}
};
struct SharedNativeSpectatorTargets::State:std::enable_shared_from_this<State> {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const std::shared_ptr<Publication> publication;
    const Budgets budgets;
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    std::map<std::uint64_t,std::shared_ptr<Entry>> slots;
    std::uint64_t absence_generation=0; // Private view fence, never issuer/native generation.
    bool operating=false,reentered=false,terminal=false;
    std::shared_ptr<Entry> active;
    State(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Publication> u,Budgets b):presence(std::move(p)),transports(std::move(t)),publication(std::move(u)),budgets(b) {}
    ~State() {
        if(thread!=std::this_thread::get_id())std::terminate();
        terminal=true;operating=true;reentered=true;
        for(auto& row:slots)row.second->terminal=true;
        slots.clear();active.reset(); // No common/token/battle cleanup.
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("Native spectator targets game owner mismatch");
    }
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s) {
            state.owner();if(state.operating) {
                state.reentered=true;if(state.active)state.active->terminal=true;
                throw std::logic_error("Native spectator targets reentry rejected");
            }
            state.operating=true;state.reentered=false;
        }
        ~Operation(){state.active.reset();state.operating=false;}
    };
    bool stored(const std::shared_ptr<Entry>& entry) const {
        const auto found=slots.find(entry->token.lease().session);
        return !terminal && found!=slots.end() && found->second==entry;
    }
    void advance_absence() noexcept {
        if(absence_generation==std::numeric_limits<std::uint64_t>::max()) {
            terminal=true;for(auto& row:slots)row.second->terminal=true;
        }else ++absence_generation;
    }
    bool endpoint(const Token& token,const Strong& actual) const {
        if(terminal || reentered || !transports->registry_current(token))return false;
        return std::visit([&](const auto& c) {
            if(!c || c->closing())return false;
            const auto& lease=token.lease();using C=typename std::decay_t<decltype(c)>::element_type;
            if constexpr(std::is_same_v<C,Session>)
                return c->id()==lease.session && c->account_id==lease.account && c->character_id==lease.character &&
                    c->recovered_world_ready() && (c->state()==SessionState::InWorld || c->state()==SessionState::InBattle) &&
                    c->common_world_delivery_current(lease.account,lease.character,lease.generation) &&
                    !c->common_world_entry_current(lease.account,lease.character,lease.generation);
        },actual);
    }
    std::optional<Strong> receiver(const Token& token) const {
        const auto actual=transports->lookup(token.lease());
        if(!actual || reentered || !transports->same_registration(token,actual->token()) || !endpoint(token,actual->transport()))return std::nullopt;
        return actual->transport(); // Strong before subsequent real observers.
    }
    std::optional<Scope> scope(const Token& token,const Strong& actual) const {
        if(!endpoint(token,actual))return std::nullopt;
        const auto tw=std::get_if<std::shared_ptr<Session>>(&actual);
        const auto phase=tw?std::optional{(*tw)->state()}:std::nullopt;
        const auto battle=tw?(*tw)->battle_generation():0;
        if(!transports->current(token) || !endpoint(token,actual))return std::nullopt;
        const auto rows=presence->ready_characters();if(!rows || !endpoint(token,actual))return std::nullopt;
        std::optional<SharedWorldPresence::ReadyCharacter> root;
        for(const auto& row:*rows)if(row.lease==token.lease()) {
            if(root || row.character.id!=row.lease.character || row.character.account_id!=row.lease.account)return std::nullopt;
            root=row;
        }
        if(!root || (tw && ((*tw)->state()!=*phase || (*tw)->battle_generation()!=battle)))return std::nullopt;
        return Scope{token.lease(),root->character,root->position,Pub::Protocol::Taiwan,phase,battle};
    }
    bool qualified(const Token& token,const Strong& actual,const Publication::Observation& ui,
        const std::vector<BindingView>& bindings,const std::shared_ptr<Issuer>& issuer,std::uint64_t generation,
        const std::vector<std::shared_ptr<Target>>& targets,const std::function<bool()>& exact) const {
        if(!issuer || !generation || targets.size()!=bindings.size() || !exact())return false;
        const auto before=scope(token,actual);if(!before || !exact())return false;
        const auto unchanged=[&] {
            if(!publication->current(ui) || !exact())return false;
            const auto after=scope(token,actual);
            return after && same_scope(*before,*after) && exact() && publication->registry_current(ui) && endpoint(token,actual);
        };
        if(!unchanged() || !issuer->current(*before,ui,bindings,generation) || !unchanged())return false;
        for(std::size_t i=0;i<targets.size();++i) {
            if(!targets[i] || targets[i]!=bindings[i].target.lock() ||
               !targets[i]->current(*before,bindings[i].target_generation) || !unchanged())return false;
        }
        // Each real issuer/target observer is bracketed by full root/position,
        // actual UI and tuple; the endpoint after the final repo is pure.
        return exact() && publication->registry_current(ui) && endpoint(token,actual);
    }
    bool issue_owned(const Publication::Observation& ui,std::span<const Binding> supplied,
        const std::shared_ptr<Issuer>& issuer,std::uint64_t generation) {
        if(terminal || !issuer || !generation || supplied.empty() || supplied.size()>budgets.max_bindings ||
           ui.status()!=Pub::Status::Published || !publication->registry_current(ui))return false;
        // Copy all input bodies/strong actual core objects before any callback.
        const auto original_ui=ui;const std::vector<Binding> inputs(supplied.begin(),supplied.end());
        const auto& token=original_ui.token();const auto actual=receiver(token);if(!actual)return false;
        std::shared_ptr<Entry> previous;
        if(const auto found=slots.find(token.lease().session);found!=slots.end()) {
            previous=found->second;
            if(previous->token.lease()!=token.lease() || !transports->same_registration(previous->token,token))return false;
            active=previous;if(previous->terminal)return false;
        }else if(slots.size()>=budgets.actual_session_capacity)return false;
        const auto latest=last_d0(original_ui);if(!latest)return false;
        std::vector<BindingView> values;std::vector<std::shared_ptr<Target>> targets;
        values.reserve(inputs.size());targets.reserve(inputs.size());
        for(const auto& input:inputs) {
            if(!input.target || !input.target_generation ||
               (input.operand!=Operand::First && input.operand!=Operand::Second))return false;
            const D0* selected=nullptr;
            for(const auto& [slot,raw]:*latest)if(raw.revision==input.event_revision && raw.ordinal==input.record_ordinal) {
                if(selected)return false;selected=&raw;
            }
            if(!selected)return false;
            for(const auto& existing:values)if(existing.event_revision==input.event_revision &&
                existing.record_ordinal==input.record_ordinal && existing.operand==input.operand)return false;
            values.push_back({input.event_revision,input.record_ordinal,input.operand,selected->slot,
                input.operand==Operand::First?selected->first:selected->second,input.target,input.target_generation});
            targets.push_back(input.target);
        }
        const auto candidate=std::make_shared<Entry>(original_ui,std::move(values),issuer,generation,original_ui.ui_epoch());
        const auto exact=[&] {
            const auto found=slots.find(token.lease().session);
            return !terminal && !reentered && publication->registry_current(original_ui) && endpoint(token,*actual) &&
                (previous?(found!=slots.end() && found->second==previous && !previous->terminal):(found==slots.end()));
        };
        if(!qualified(token,*actual,original_ui,candidate->bindings,issuer,generation,targets,exact))return false;
        if(absence_generation==std::numeric_limits<std::uint64_t>::max())return false;
        slots.insert_or_assign(token.lease().session,candidate);advance_absence();return true;
    }
    std::shared_ptr<const Observed> resolve_owned(const Token& token,std::uint32_t raw) {
        auto data=std::make_shared<Observed>(identity,token,raw);data->absence_generation=absence_generation;
        const auto found=slots.find(token.lease().session);
        const auto entry=found==slots.end()?nullptr:found->second;
        const bool matches=entry && entry->token.lease()==token.lease() && transports->same_registration(entry->token,token);
        if(entry) {
            data->entry=entry->identity;
            if(matches) {
                active=entry;data->bindings=std::make_shared<const std::vector<BindingView>>(entry->bindings);
                data->issuer_generation=entry->generation;data->retired=entry->retired;data->terminal=entry->terminal;
            }else data->blocked=true; // No foreign history or core objects leaked.
        }
        const auto actual=receiver(token);if(!actual)return data;
        const auto before=scope(token,*actual);if(!before)return data;
        data->ui=publication->observe(token);
        if(!publication->current(*data->ui) || reentered)return data;
        const auto after=scope(token,*actual);
        if(!after || !same_scope(*before,*after) || !publication->registry_current(*data->ui) || !endpoint(token,*actual))return data;
        data->ready=true;
        if(entry && !matches) {data->status=Status::ForeignContext;return data;}
        if(entry && entry->terminal)return data;
        if(entry && entry->retired) {data->status=Status::Retired;return data;}
        if(raw>std::numeric_limits<std::uint16_t>::max()) {data->status=Status::ForeignContext;return data;}
        if(data->ui->status()!=Pub::Status::Published) {
            data->status=!entry && data->ui->status()==Pub::Status::Missing?Status::Missing:Status::Unavailable;return data;
        }
        if(!entry) {data->status=Status::Missing;return data;}
        if(entry->epoch!=data->ui->ui_epoch()) {data->status=Status::Expired;return data;}
        const auto latest=last_d0(*data->ui);if(!latest)return data;
        bool context_found=false;
        for(const auto& value:entry->bindings)if(value.raw_context==raw)context_found=true;
        if(!context_found) {data->status=Status::ForeignContext;return data;}
        const auto issuer=entry->issuer.lock();
        std::vector<std::shared_ptr<Target>> targets;targets.reserve(entry->bindings.size());
        for(const auto& value:entry->bindings) {
            if(!binding_current(value,*latest)) {data->status=Status::Expired;return data;}
            const auto target=value.target.lock();if(!target) {data->status=Status::Expired;return data;}
            targets.push_back(target); // All strong before any real issuer/target observer.
        }
        if(!issuer) {data->status=Status::Expired;return data;}
        const auto exact=[&] {return !reentered && stored(entry) && !entry->retired && !entry->terminal &&
            transports->same_registration(entry->token,token) && publication->registry_current(*data->ui) && endpoint(token,*actual);};
        if(!qualified(token,*actual,*data->ui,entry->bindings,issuer,entry->generation,targets,exact)) {
            data->status=Status::Expired;return data;
        }
        std::shared_ptr<Target> selected;std::weak_ptr<Target> selected_owner;std::uint64_t selected_generation=0;
        for(std::size_t i=0;i<entry->bindings.size();++i)if(entry->bindings[i].raw_context==raw) {
            if(selected && (selected!=targets[i] || !same_weak(selected_owner,entry->bindings[i].target) ||
               selected_generation!=entry->bindings[i].target_generation)) {
                data->status=Status::Ambiguous;return data;
            }
            selected=targets[i];selected_owner=entry->bindings[i].target;selected_generation=entry->bindings[i].target_generation;
        }
        data->target=selected;data->target_generation=selected_generation;data->status=Status::Matched;return data;
    }
    bool registry_current(const Observed& data) const {
        owner();if(terminal || reentered || data.source!=identity || !data.ready || !data.ui ||
            !transports->registry_current(data.token) || !publication->registry_current(*data.ui))return false;
        const auto found=slots.find(data.token.lease().session);
        if(!data.entry)return found==slots.end() && data.absence_generation==absence_generation;
        if(found==slots.end() || found->second->identity!=data.entry)return false;
        const auto& entry=found->second;
        if(data.blocked)return entry->token.lease()!=data.token.lease() || !transports->same_registration(entry->token,data.token);
        return entry->token.lease()==data.token.lease() && transports->same_registration(entry->token,data.token) &&
            entry->generation==data.issuer_generation && entry->retired==data.retired && entry->terminal==data.terminal;
    }
    bool same(const Observed& a,const Observed& b) const {
        return registry_current(a) && registry_current(b) && a.source==b.source && a.entry==b.entry &&
            transports->same_registration(a.token,b.token) && a.context==b.context && a.status==b.status &&
            a.blocked==b.blocked && a.retired==b.retired && a.terminal==b.terminal &&
            a.issuer_generation==b.issuer_generation && a.target_generation==b.target_generation && same_weak(a.target,b.target) &&
            publication->same(*a.ui,*b.ui) && (a.entry || a.absence_generation==b.absence_generation);
    }
    bool cleanup(const Observed& data,bool remove) {
        if(data.source!=identity || !data.entry || data.blocked)return false;
        const auto found=slots.find(data.token.lease().session);if(found==slots.end())return false;
        const auto entry=found->second;
        if(entry->identity!=data.entry || entry->token.lease()!=data.token.lease())return false;
        entry->retired=true;
        if(remove) {slots.erase(found);advance_absence();} // Exact old entry before weak object destruction.
        return true;
    }
    std::shared_ptr<const Retirement> retirement_for_ui(const Publication::Observation& ui) const {
        if(terminal || reentered)return {};
        const auto found=slots.find(ui.lease().session);if(found==slots.end())return {};
        const auto entry=found->second; // No iterator survives an external observer (none are called).
        if(entry->retired || entry->terminal || entry->token.lease()!=ui.lease() || entry->epoch!=ui.ui_epoch() ||
           ui.status()!=Pub::Status::Published || !publication->same(entry->issued_ui,ui) ||
           !transports->same_registration(entry->token,ui.token()))return {};
        return std::make_shared<const Retirement>(identity,*entry);
    }
    bool retire_for_ui(const Retirement& ticket) {
        // Exact captured private entry proof works after registry/token/UI/core
        // teardown. No current/lookup/repository or permission observer here.
        if(ticket.source!=identity)return false;
        const auto found=slots.find(ticket.token.lease().session);if(found==slots.end())return false;
        const auto entry=found->second;
        if(entry->identity!=ticket.entry || entry->token.lease()!=ticket.token.lease() ||
           entry->epoch!=ticket.epoch || entry->generation!=ticket.generation ||
           &entry->issued_ui.token()!=&ticket.issued_ui.token())return false;
        entry->retired=true;return true; // Only own flag; no common/successor cleanup.
    }
};
SharedNativeSpectatorTargets::Observation::Observation(std::shared_ptr<const Observed> value):storage_(std::move(value)) {}
SharedNativeSpectatorTargets::Observation::Observation(Observation&& other) noexcept:storage_(other.storage_) {}
SharedNativeSpectatorTargets::Observation& SharedNativeSpectatorTargets::Observation::operator=(Observation&& other) noexcept {storage_=other.storage_;return *this;}
SharedNativeSpectatorTargets::Status SharedNativeSpectatorTargets::Observation::status() const noexcept {return storage_->status;}
const SharedNativeSpectatorTargets::Token& SharedNativeSpectatorTargets::Observation::token() const noexcept {return storage_->token;}
const std::optional<SharedNativeSpectatorTargets::Publication::Observation>& SharedNativeSpectatorTargets::Observation::ui() const noexcept {return storage_->ui;}
std::uint32_t SharedNativeSpectatorTargets::Observation::raw_context() const noexcept {return storage_->context;}
const std::vector<SharedNativeSpectatorTargets::BindingView>& SharedNativeSpectatorTargets::Observation::bindings() const noexcept {return *storage_->bindings;}
std::weak_ptr<SharedNativeSpectatorTargets::Target> SharedNativeSpectatorTargets::Observation::target() const noexcept {return storage_->target;}
std::uint64_t SharedNativeSpectatorTargets::Observation::target_generation() const noexcept {return storage_->target_generation;}
std::uint64_t SharedNativeSpectatorTargets::Observation::issuer_generation() const noexcept {return storage_->issuer_generation;}
SharedNativeSpectatorTargets::UiRetirement::UiRetirement(std::shared_ptr<const Retirement> value):storage_(std::move(value)) {}
SharedNativeSpectatorTargets::UiRetirement::UiRetirement(UiRetirement&& other) noexcept:storage_(other.storage_) {}
SharedNativeSpectatorTargets::UiRetirement& SharedNativeSpectatorTargets::UiRetirement::operator=(UiRetirement&& other) noexcept {storage_=other.storage_;return *this;}
const SharedNativeSpectatorTargets::Token& SharedNativeSpectatorTargets::UiRetirement::token() const noexcept {return storage_->token;}
const SharedNativeSpectatorTargets::Publication::Observation& SharedNativeSpectatorTargets::UiRetirement::ui() const noexcept {return storage_->issued_ui;}
std::uint64_t SharedNativeSpectatorTargets::UiRetirement::ui_epoch() const noexcept {return storage_->epoch;}
std::uint64_t SharedNativeSpectatorTargets::UiRetirement::issuer_generation() const noexcept {return storage_->generation;}
SharedNativeSpectatorTargets::SharedNativeSpectatorTargets(std::shared_ptr<State> state):state_(std::move(state)) {}
SharedNativeSpectatorTargets::~SharedNativeSpectatorTargets(){state_->owner();}
std::shared_ptr<SharedNativeSpectatorTargets> SharedNativeSpectatorTargets::create(std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<SharedNativeWorldTransports> transports,std::shared_ptr<Publication> publication,Budgets budgets) {
    if(!presence || !transports || !publication || !transports->owns_presence(presence) ||
       !publication->owns_source(presence,transports) || !budgets.max_bindings || !budgets.actual_session_capacity)
        throw std::invalid_argument("Actual spectator target same-host sources/budgets required");
    return std::shared_ptr<SharedNativeSpectatorTargets>(new SharedNativeSpectatorTargets(
        std::make_shared<State>(std::move(presence),std::move(transports),std::move(publication),budgets)));
}
bool SharedNativeSpectatorTargets::owns_source(const std::shared_ptr<SharedWorldPresence>& presence,
    const std::shared_ptr<SharedNativeWorldTransports>& transports,const std::shared_ptr<Publication>& publication) const {
    state_->owner();return !state_->terminal && presence && transports && publication && state_->presence==presence &&
        state_->transports==transports && state_->publication==publication && transports->owns_presence(presence) && publication->owns_source(presence,transports);
}
bool SharedNativeSpectatorTargets::issue(const Publication::Observation& ui,std::span<const Binding> bindings,
    std::shared_ptr<Issuer> issuer,std::uint64_t generation) {
    State::Operation operation(*state_);return state_->issue_owned(ui,bindings,issuer,generation);
}
SharedNativeSpectatorTargets::Observation SharedNativeSpectatorTargets::resolve(const Token& token,std::uint32_t raw) const {
    State::Operation operation(*state_);return Observation(state_->resolve_owned(token,raw));
}
bool SharedNativeSpectatorTargets::current(const Observation& value) const {
    State::Operation operation(*state_);if(!state_->registry_current(*value.storage_))return false;
    const auto after=state_->resolve_owned(value.storage_->token,value.storage_->context);return state_->same(*value.storage_,*after);
}
bool SharedNativeSpectatorTargets::same(const Observation& a,const Observation& b) const {state_->owner();return state_->same(*a.storage_,*b.storage_);}
bool SharedNativeSpectatorTargets::registry_current(const Observation& value) const {return state_->registry_current(*value.storage_);}
bool SharedNativeSpectatorTargets::retire(const Observation& value) {State::Operation operation(*state_);return state_->cleanup(*value.storage_,false);}
bool SharedNativeSpectatorTargets::remove(const Observation& value) {State::Operation operation(*state_);return state_->cleanup(*value.storage_,true);}
std::optional<SharedNativeSpectatorTargets::UiRetirement> SharedNativeSpectatorTargets::retirement_for_ui(const Publication::Observation& ui) const {
    State::Operation operation(*state_);const auto ticket=state_->retirement_for_ui(ui);
    return ticket?std::optional{UiRetirement(ticket)}:std::nullopt;
}
bool SharedNativeSpectatorTargets::retire_for_ui(const UiRetirement& ticket) {
    State::Operation operation(*state_);return state_->retire_for_ui(*ticket.storage_);
}
}
