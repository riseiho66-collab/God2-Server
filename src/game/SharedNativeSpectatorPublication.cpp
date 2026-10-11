#include "game/SharedNativeSpectatorPublication.h"
#include "protocol/RecoveredSpectatorTargetsD0.h"
#include "cn/protocol/CnSpectatorTargetsD0.h"
#include <exception>
#include <limits>
#include <map>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
using Pub=SharedNativeSpectatorPublication;
using Strong=SharedNativeWorldTransports::StrongTransport;
using Weak=SharedNativeWorldTransports::WeakTransport;
struct Identity {};
struct View {
    std::vector<Pub::Event> history;
    std::size_t bytes=0;
    std::shared_ptr<const Pub::Event> pending;
};
struct Entry {
    const Pub::Lease lease;
    const Pub::Token token;
    const Weak receiver;
    const Pub::Protocol protocol;
    const std::uint64_t epoch;
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    const std::weak_ptr<Pub::WorldOwner> owner;
    std::shared_ptr<const View> view;
    bool pending=false,retired=false,terminal=false,remove_requested=false;
    Entry(const Pub::Token& registered,Weak actual,Pub::Protocol profile,std::uint64_t ui_epoch,
        const std::shared_ptr<Pub::WorldOwner>& issuer,std::shared_ptr<const View> initial)
        :lease(registered.lease()),token(registered),receiver(std::move(actual)),protocol(profile),epoch(ui_epoch),
         owner(issuer),view(std::move(initial)) {}
};
struct Pending {
    const std::shared_ptr<Entry> entry;
    const Strong receiver;
    const std::shared_ptr<Pub::WorldOwner> owner;
    const std::shared_ptr<const Pub::Event> event;
    const std::shared_ptr<const View> candidate,released_view,failed_view;
    std::vector<std::uint8_t> taiwan_logical;
    std::vector<god2cn::Bytes> mainland_records;
    Pub::Completion completion;
    bool approved=false,completed=false,submitting=false;
    std::optional<bool> inline_release;
    Pending(std::shared_ptr<Entry> original,Strong actual,std::shared_ptr<Pub::WorldOwner> issuer,
        std::shared_ptr<const Pub::Event> supplied,std::shared_ptr<const View> staged,std::shared_ptr<const View> released,
        std::shared_ptr<const View> failed,
        std::vector<std::uint8_t> tw,std::vector<god2cn::Bytes> cn,Pub::Completion done)
        :entry(std::move(original)),receiver(std::move(actual)),owner(std::move(issuer)),event(std::move(supplied)),
         candidate(std::move(staged)),released_view(std::move(released)),failed_view(std::move(failed)),taiwan_logical(std::move(tw)),
         mainland_records(std::move(cn)),completion(std::move(done)) {}
};
bool same_character(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool same_scope(const Pub::Scope& a,const Pub::Scope& b) {
    return a.recipient==b.recipient && same_character(a.character,b.character) && a.saved_position==b.saved_position &&
        a.protocol==b.protocol && a.taiwan_phase==b.taiwan_phase && a.taiwan_battle_generation==b.taiwan_battle_generation;
}
Pub::Protocol protocol(const Strong& receiver) {
    return std::holds_alternative<std::shared_ptr<Session>>(receiver)?Pub::Protocol::Taiwan:Pub::Protocol::Mainland;
}
Weak weak(const Strong& receiver) {return std::visit([](const auto& c)->Weak{return c;},receiver);}
Strong lock(const Weak& receiver) {return std::visit([](const auto& c)->Strong{return c.lock();},receiver);}
}
struct SharedNativeSpectatorPublication::Observed {
    std::shared_ptr<const Identity> source;
    Token token;
    std::shared_ptr<const Identity> entry;
    std::shared_ptr<const View> view;
    Status status;
    std::uint64_t epoch,absence_generation;
    bool ready,blocked,retired,terminal,pending;
    Observed(std::shared_ptr<const Identity> issuer,const Token& actual):source(std::move(issuer)),token(actual),
        view(std::make_shared<const View>()),status(Status::Unavailable),epoch(0),absence_generation(0),
        ready(false),blocked(false),retired(false),terminal(false),pending(false) {}
};
struct SharedNativeSpectatorPublication::State:std::enable_shared_from_this<State> {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const Budgets budgets;
    const std::size_t capacity;
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    std::map<std::uint64_t,std::shared_ptr<Entry>> slots;
    std::uint64_t absence_generation=0; // Private missing-view fence, never native UI epoch.
    bool operating=false,reentered=false,terminal=false;
    std::shared_ptr<Entry> active;
    State(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<SharedNativeWorldTransports> t,Budgets b,std::size_t c)
        :presence(std::move(p)),transports(std::move(t)),budgets(b),capacity(c) {}
    ~State() {
        if(thread!=std::this_thread::get_id())std::terminate();
        terminal=true;operating=true;reentered=true;
        for(auto& row:slots)row.second->terminal=true;
        slots.clear();active.reset(); // Weak receivers/owners only; no common/native cleanup.
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("Native spectator publication game owner mismatch");
    }
    void poison() {reentered=true;if(active)active->terminal=true;}
    void advance_absence() noexcept {
        if(absence_generation==std::numeric_limits<std::uint64_t>::max()) {
            // No wrap/reused Missing capability. Preserve any released prefix
            // and complete its callback truthfully; this source becomes closed.
            terminal=true;
            for(auto& row:slots)row.second->terminal=true;
        }else ++absence_generation;
    }
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s) {
            state.owner();if(state.operating) {state.poison();throw std::logic_error("Native UI publication reentry rejected");}
            state.operating=true;state.reentered=false;
        }
        ~Operation(){state.active.reset();state.operating=false;}
    };
    bool stored(const std::shared_ptr<Entry>& entry) const {
        if(terminal || !entry)return false;
        const auto found=slots.find(entry->lease.session);return found!=slots.end() && found->second==entry;
    }
    bool endpoint(const Token& token,const Strong& receiver) const {
        if(terminal || reentered || !transports->registry_current(token))return false;
        return std::visit([&](const auto& c) {
            if(!c || c->closing())return false;
            const auto& lease=token.lease();
            using C=typename std::decay_t<decltype(c)>::element_type;
            if constexpr(std::is_same_v<C,Session>)
                return c->id()==lease.session && c->account_id==lease.account && c->character_id==lease.character &&
                    c->recovered_world_ready() && (c->state()==SessionState::InWorld || c->state()==SessionState::InBattle) &&
                    c->common_world_delivery_current(lease.account,lease.character,lease.generation) &&
                    !c->common_world_entry_current(lease.account,lease.character,lease.generation);
            else return c->role()==cn::SharedCredentialConnection::Transport::Role::World && c->world_admission_current() &&
                c->world_session_id()==lease.session && c->verified_account_id()==lease.account && c->world_character_offered(lease.character);
        },receiver);
    }
    std::optional<Strong> receiver(const Token& token) const {
        // lookup retains its real receiver before all repository observers.
        const auto actual=transports->lookup(token.lease());
        if(!actual || reentered || !transports->same_registration(token,actual->token()) ||
           !transports->registry_current(token))return std::nullopt;
        return actual->transport();
    }
    std::optional<Scope> scope(const Token& token,const Strong& actual) const {
        if(!endpoint(token,actual))return std::nullopt;
        const auto tw=std::get_if<std::shared_ptr<Session>>(&actual);
        const auto phase=tw?std::optional{(*tw)->state()}:std::nullopt;
        const auto battle=tw?(*tw)->battle_generation():0;
        if(!transports->current(token) || !endpoint(token,actual))return std::nullopt;
        const auto population=presence->ready_characters();if(!population || !endpoint(token,actual))return std::nullopt;
        std::optional<SharedWorldPresence::ReadyCharacter> root;
        for(const auto& row:*population)if(row.lease==token.lease()) {
            if(root || row.character.id!=row.lease.character || row.character.account_id!=row.lease.account)return std::nullopt;
            root=row;
        }
        if(!root || (tw && ((*tw)->state()!=*phase || (*tw)->battle_generation()!=battle)))return std::nullopt;
        return Scope{token.lease(),root->character,root->position,protocol(actual),phase,battle};
    }
    bool qualified(const Token& token,const Strong& actual,const std::shared_ptr<WorldOwner>& issuer,
        Check stage,const Event& event,const std::function<bool()>& private_current) const {
        if(!issuer || !private_current())return false;
        const auto before=scope(token,actual);if(!before || !private_current())return false;
        if(!issuer->current(stage,*before,event) || !private_current())return false;
        const auto after=scope(token,actual);
        return after && same_scope(*before,*after) && private_current() && endpoint(token,actual);
    }
    std::shared_ptr<const Observed> observe_owned(const Token& token) {
        auto data=std::make_shared<Observed>(identity,token);data->absence_generation=absence_generation;
        const auto found=slots.find(token.lease().session);
        std::shared_ptr<Entry> entry=found==slots.end()?nullptr:found->second;
        const bool matches=entry && entry->lease==token.lease() && transports->same_registration(entry->token,token);
        if(entry) {
            data->entry=entry->identity;
            if(matches) {
                active=entry;data->view=entry->view;data->epoch=entry->epoch;
                data->retired=entry->retired;data->terminal=entry->terminal;data->pending=entry->pending;
            }else data->blocked=true; // Never expose a foreign incarnation's history.
        }
        const auto actual=receiver(token);if(!actual)return data;
        const auto ready=scope(token,*actual);if(!ready || reentered)return data;
        data->ready=true;
        if(!entry) {data->status=Status::Missing;return data;}
        if(!matches || entry->terminal) {data->status=Status::Unavailable;return data;}
        if(entry->retired) {data->status=Status::Retired;return data;}
        const auto event=entry->view->pending?entry->view->pending.get():
            (entry->view->history.empty()?nullptr:&entry->view->history.back());
        const auto issuer=entry->owner.lock();
        const auto exact=[&] {return !reentered && stored(entry) && entry->view==data->view &&
            !entry->terminal && !entry->retired && entry->pending==data->pending &&
            transports->same_registration(entry->token,token) && lock(entry->receiver)==*actual;};
        if(!event || !issuer || !qualified(token,*actual,issuer,Check::Observe,*event,exact)) {
            data->status=Status::Unavailable;return data; // Accurate negative observation, no rights.
        }
        data->status=entry->pending?Status::Pending:Status::Published;return data;
    }
    bool registry_current(const Observed& data) const {
        owner();if(terminal || reentered || data.source!=identity || !data.ready || !transports->registry_current(data.token))return false;
        const auto found=slots.find(data.token.lease().session);
        if(!data.entry)return found==slots.end() && data.absence_generation==absence_generation;
        if(found==slots.end() || found->second->identity!=data.entry)return false;
        const auto& entry=found->second;
        if(data.blocked)return entry->lease!=data.token.lease() || !transports->same_registration(entry->token,data.token);
        return entry->lease==data.token.lease() && transports->same_registration(entry->token,data.token) &&
            entry->epoch==data.epoch && entry->view==data.view && entry->retired==data.retired &&
            entry->terminal==data.terminal && entry->pending==data.pending;
    }
    bool same(const Observed& a,const Observed& b) const {
        owner();return registry_current(a) && registry_current(b) && a.source==b.source &&
            transports->same_registration(a.token,b.token) && a.entry==b.entry && a.status==b.status &&
            a.epoch==b.epoch && a.ready==b.ready && a.blocked==b.blocked && a.retired==b.retired &&
            a.terminal==b.terminal && a.pending==b.pending &&
            (a.entry? (a.blocked || a.view==b.view):a.absence_generation==b.absence_generation);
    }
    std::vector<god2cn::Bytes> records(const Event& event) const {
        if(event.logical.empty() || event.logical.size()>budgets.max_logical_bytes)throw std::invalid_argument("Native UI logical budget");
        std::vector<god2cn::Bytes> result;result.reserve(budgets.max_records);
        for(std::size_t at=0;at<event.logical.size();) {
            const auto opcode=event.logical[at];std::size_t length=0;
            if(opcode==0xcd)length=65;else if(opcode==0xd0)length=7;
            else throw std::invalid_argument("Native UI requires complete actual CD/D0 only");
            if(length>event.logical.size()-at || result.size()==budgets.max_records)
                throw std::length_error("Native UI complete record boundary/budget");
            const std::span<const std::uint8_t> record(event.logical.data()+at,length);
            std::uint8_t slot=0;
            if(opcode==0xcd)slot=record[5]; // Entire64 body retained, flags never synthesized.
            else if(event.protocol==Protocol::Taiwan) {
                const auto view=RecoveredSpectatorTargetsD0::read(record);if(!view)throw std::invalid_argument("TW D0 shape");slot=view->slot();
            }else {
                const auto view=god2cn::CnSpectatorTargetsD0::read(record);if(!view)throw std::invalid_argument("CN own D0 shape");slot=view->slot();
            }
            // Qualified supplied output domain, not the native leaf's bound.
            if(slot<1 || slot>50)throw std::invalid_argument("Native UI supplier slot domain1..50");
            result.emplace_back(record.begin(),record.end());at+=length;
        }
        return result;
    }
    void prepare_submit(const Event& supplied,const std::shared_ptr<WorldOwner>& issuer,Completion& done,std::shared_ptr<Pending>& out) {
        const auto event=std::make_shared<const Event>(supplied); // Deep-copy all raw caller-owned bytes.
        if(!issuer || !event->ui_epoch || !event->revision || event->revision<=event->previous_revision ||
           (event->protocol!=Protocol::Taiwan && event->protocol!=Protocol::Mainland))throw std::invalid_argument("Actual UI issuer lineage required");
        auto frames=records(*event);if(frames.size()>256)throw std::length_error("Actual native batch capacity");
        const auto registered=transports->lookup(event->recipient);
        if(!registered || reentered || protocol(registered->transport())!=event->protocol)throw std::runtime_error("Actual UI recipient registration");
        const Strong actual=registered->transport(); // Strong before all following observers.
        const auto& token=registered->token();
        if(event->protocol==Protocol::Taiwan) {
            const auto tw=std::get<std::shared_ptr<Session>>(actual);
            if(tw->state()!=SessionState::InWorld || event->logical.size()>0xa00)
                throw std::invalid_argument("Existing TW held publication supports InWorld aggregate only");
        }
        std::shared_ptr<Entry> entry;
        if(const auto found=slots.find(event->recipient.session);found!=slots.end()) {
            entry=found->second;
            if(entry->lease!=event->recipient || !transports->same_registration(entry->token,token))
                throw std::invalid_argument("Foreign UI recipient incarnation");
            active=entry;
            if(entry->pending || entry->remove_requested)throw std::logic_error("Actual UI publication still pending");
            if(entry->epoch!=event->ui_epoch) {
                if(!entry->retired || event->previous_revision)throw std::invalid_argument("Actual UI epoch must retire before replacement");
                entry.reset();
            }else if(entry->retired || entry->terminal || entry->protocol!=event->protocol || entry->owner.lock()!=issuer ||
                entry->view->history.empty() || event->previous_revision!=entry->view->history.back().revision)
                throw std::invalid_argument("Actual UI history/issuer predecessor");
        }else if(event->previous_revision || slots.size()>=capacity)throw std::invalid_argument("Actual UI first predecessor/capacity");
        const auto original=entry?entry->view:std::make_shared<const View>();
        if(original->history.size()>=budgets.max_history_events || event->logical.size()>budgets.max_history_bytes-original->bytes)
            throw std::length_error("Actual UI immutable history budget");
        auto candidate=std::make_shared<View>(*original);candidate->pending=event;
        auto released=std::make_shared<View>(*original);released->history.push_back(*event);released->bytes+=event->logical.size();
        if(!entry)entry=std::make_shared<Entry>(token,weak(actual),event->protocol,event->ui_epoch,issuer,original);
        const auto predecessor=slots.find(event->recipient.session);
        const auto previous=predecessor==slots.end()?nullptr:predecessor->second;
        const auto before=[&] {const auto found=slots.find(event->recipient.session);
            return !reentered && (previous?(found!=slots.end() && found->second==previous):(found==slots.end())) &&
                (!previous || (!previous->pending && (previous==entry?!previous->terminal:previous->retired))) && endpoint(token,actual);};
        if(!qualified(token,actual,issuer,Check::BeforeQueue,*event,before))throw std::runtime_error("Actual UI prequeue Current failed");
        if(absence_generation==std::numeric_limits<std::uint64_t>::max())throw std::overflow_error("Private UI absence lineage exhausted");
        std::vector<std::uint8_t> tw=event->protocol==Protocol::Taiwan?event->logical:std::vector<std::uint8_t>{};
        out=std::make_shared<Pending>(entry,actual,issuer,event,candidate,released,original,std::move(tw),std::move(frames),std::move(done));
        // All source allocation/record/budget preparation precedes this effect.
        slots.insert_or_assign(event->recipient.session,entry);advance_absence();
        entry->view=candidate;entry->pending=true;active=entry;out->submitting=true;
        const auto self=shared_from_this();const auto pending=out;
        const auto approve=[self,pending] {
            Operation operation(*self);self->active=pending->entry;
            const auto exact=[&] {return self->stored(pending->entry) && !pending->entry->retired && !pending->entry->terminal &&
                pending->entry->pending && pending->entry->view==pending->candidate && !pending->approved &&
                lock(pending->entry->receiver)==pending->receiver && self->endpoint(pending->entry->token,pending->receiver);};
            const bool accepted=self->qualified(pending->entry->token,pending->receiver,pending->owner,Check::BeforeRelease,*pending->event,exact);
            if(accepted)pending->approved=true;else pending->entry->terminal=true;
            return accepted;
        };
        const auto complete=[self,pending](bool released) {
            self->owner(); // Including the wrapper's possible inline failure.
            if(pending->submitting) {pending->inline_release=released;return;}
            self->finish(pending,released);
        };
        try {
            std::visit([&](const auto& c) {
                using C=typename std::decay_t<decltype(c)>::element_type;
                if constexpr(std::is_same_v<C,Session>)c->send_common_world_records_with_publication(std::move(out->taiwan_logical),
                    entry->lease.account,entry->lease.character,entry->lease.generation,approve,complete);
                else c->send_world_batch_with_publication(std::move(out->mainland_records),approve,complete);
            },actual);
        }catch(...) {out->submitting=false;entry->terminal=true;throw;}
        out->submitting=false;
    }
    void finish(const std::shared_ptr<Pending>& pending,bool released) {
        Completion done;
        {
            Operation operation(*this);if(pending->completed)return;
            pending->completed=true;active=pending->entry;
            const auto entry=pending->entry;
            // A true transport completion is the released-prefix fact even if
            // retire/remove/common cleanup occurred meanwhile. Never rollback
            // or grant current authority to this old entry/successor.
            if(released)entry->view=pending->released_view;
            else {entry->view=pending->failed_view;entry->terminal=true;}
            entry->pending=false;
            if(released && !entry->retired && !entry->terminal && stored(entry)) {
                const auto exact=[&] {return !reentered && stored(entry) && !entry->retired && !entry->terminal &&
                    !entry->pending && entry->view==pending->released_view && lock(entry->receiver)==pending->receiver;};
                try {if(!pending->approved || !qualified(entry->token,pending->receiver,pending->owner,Check::AfterRelease,*pending->event,exact))entry->terminal=true;}
                catch(...) {entry->terminal=true;}
            }
            if(entry->remove_requested && stored(entry)) {slots.erase(entry->lease.session);advance_absence();}
            done=std::move(pending->completion);
        }
        if(done)done(released); // Local release only; callback sees accurate fresh history/status.
    }
    bool cleanup(const Observed& data,bool remove) {
        if(data.source!=identity || !data.entry || data.blocked)return false;
        const auto found=slots.find(data.token.lease().session);if(found==slots.end())return false;
        const auto entry=found->second;
        if(entry->identity!=data.entry || entry->lease!=data.token.lease() || entry->epoch!=data.epoch)return false;
        entry->retired=true;
        if(remove) {
            entry->remove_requested=true;
            if(!entry->pending) {slots.erase(found);advance_absence();} // Erase before weak owner/history destruction.
        }
        return true; // Own entry/epoch only, even after token/common lease cleanup.
    }
};
SharedNativeSpectatorPublication::Observation::Observation(std::shared_ptr<const Observed> value):storage_(std::move(value)) {}
SharedNativeSpectatorPublication::Observation::Observation(Observation&& other) noexcept:storage_(other.storage_) {}
SharedNativeSpectatorPublication::Observation& SharedNativeSpectatorPublication::Observation::operator=(Observation&& other) noexcept {storage_=other.storage_;return *this;}
SharedNativeSpectatorPublication::Status SharedNativeSpectatorPublication::Observation::status() const noexcept {return storage_->status;}
const SharedNativeSpectatorPublication::Lease& SharedNativeSpectatorPublication::Observation::lease() const noexcept {return storage_->token.lease();}
const SharedNativeSpectatorPublication::Token& SharedNativeSpectatorPublication::Observation::token() const noexcept {return storage_->token;}
std::uint64_t SharedNativeSpectatorPublication::Observation::ui_epoch() const noexcept {return storage_->epoch;}
std::uint64_t SharedNativeSpectatorPublication::Observation::revision() const noexcept {return storage_->view->history.empty()?0:storage_->view->history.back().revision;}
const std::vector<SharedNativeSpectatorPublication::Event>& SharedNativeSpectatorPublication::Observation::history() const noexcept {return storage_->view->history;}
const SharedNativeSpectatorPublication::Event* SharedNativeSpectatorPublication::Observation::pending_event() const noexcept {return storage_->view->pending.get();}
SharedNativeSpectatorPublication::SharedNativeSpectatorPublication(std::shared_ptr<State> state):state_(std::move(state)) {}
SharedNativeSpectatorPublication::~SharedNativeSpectatorPublication(){state_->owner();}
std::shared_ptr<SharedNativeSpectatorPublication> SharedNativeSpectatorPublication::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedNativeWorldTransports> transports,Budgets budgets,std::size_t capacity) {
    if(!presence || !transports || !transports->owns_presence(presence) || !capacity || !budgets.max_logical_bytes ||
       !budgets.max_records || !budgets.max_history_bytes || !budgets.max_history_events)
        throw std::invalid_argument("Actual spectator publication same-host source/budgets/capacity required");
    return std::shared_ptr<SharedNativeSpectatorPublication>(new SharedNativeSpectatorPublication(
        std::make_shared<State>(std::move(presence),std::move(transports),budgets,capacity)));
}
bool SharedNativeSpectatorPublication::owns_source(const std::shared_ptr<SharedWorldPresence>& presence,
    const std::shared_ptr<SharedNativeWorldTransports>& transports) const {
    state_->owner();return !state_->terminal && presence && transports && state_->presence==presence && state_->transports==transports && transports->owns_presence(presence);
}
void SharedNativeSpectatorPublication::publish(Event event,std::shared_ptr<WorldOwner> issuer,Completion done) {
    state_->owner();
    if(!done)throw std::invalid_argument("Actual UI local-release completion required");
    std::shared_ptr<Pending> pending;std::exception_ptr failure;
    try {State::Operation operation(*state_);state_->prepare_submit(event,issuer,done,pending);}
    catch(...) {failure=std::current_exception();}
    if(pending && (failure || pending->inline_release))state_->finish(pending,failure?false:*pending->inline_release);
    else if(failure && done)done(false);
}
SharedNativeSpectatorPublication::Observation SharedNativeSpectatorPublication::observe(const Token& token) const {
    State::Operation operation(*state_);return Observation(state_->observe_owned(token));
}
bool SharedNativeSpectatorPublication::current(const Observation& observed) const {
    State::Operation operation(*state_);
    if(!state_->registry_current(*observed.storage_))return false;
    const auto after=state_->observe_owned(observed.storage_->token);return state_->same(*observed.storage_,*after);
}
bool SharedNativeSpectatorPublication::registry_current(const Observation& observed) const {return state_->registry_current(*observed.storage_);}
bool SharedNativeSpectatorPublication::same(const Observation& a,const Observation& b) const {return state_->same(*a.storage_,*b.storage_);}
bool SharedNativeSpectatorPublication::retire(const Observation& observed) {State::Operation operation(*state_);return state_->cleanup(*observed.storage_,false);}
bool SharedNativeSpectatorPublication::remove(const Observation& observed) {State::Operation operation(*state_);return state_->cleanup(*observed.storage_,true);}
}
