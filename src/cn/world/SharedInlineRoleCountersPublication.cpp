#include "cn/world/SharedInlineRoleCountersPublication.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2::cn {
namespace {
using Publication=SharedInlineRoleCountersPublication;
template<class T> bool same_owner(const std::shared_ptr<T>& a,const std::shared_ptr<T>& b) {
    return a && b && a.get()==b.get() && !a.owner_before(b) && !b.owner_before(a);
}
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
struct Pending {
    const std::shared_ptr<Publication::Connection> connection;
    const Publication::Plan plan;
    std::optional<Publication::Token> token;
    std::optional<Publication::Scope> original_scope;
    // Preallocated immutable receipt alternatives; no allocation after release.
    std::shared_ptr<const void> qualified_receipt,unqualified_receipt;
    Publication::Connection::Transport::Completion done;
    bool completed=false,approved=false,submitting=false,submitted=false,locally_released=false;
    std::optional<bool> inline_release;
    Pending(std::shared_ptr<Publication::Connection> c,Publication::Plan p,
        Publication::Connection::Transport::Completion callback)
        :connection(std::move(c)),plan(std::move(p)),done(std::move(callback)) {}
};
}
struct SharedInlineRoleCountersPublication::ReceiptStorage {
    const Scope original_scope;
    const Plan plan;
    const bool post_current;
    ReceiptStorage(const Pending& p,bool qualified)
        :original_scope(*p.original_scope),plan(p.plan),post_current(qualified) {}
};
struct SharedInlineRoleCountersPublication::State:std::enable_shared_from_this<State> {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const std::shared_ptr<WorldOwner> world;
    const Budgets budgets;
    std::weak_ptr<Connection> connection;
    std::optional<Lease> lease;
    std::optional<Token> registered;
    std::weak_ptr<Pending> active;
    std::optional<std::pair<std::uint64_t,std::uint64_t>> last_attempt;
    std::shared_ptr<const ReceiptStorage> released;
    bool busy=false,in_stage=false,terminal=false;
    State(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<WorldOwner> w,Budgets b)
        :presence(std::move(p)),transports(std::move(t)),world(std::move(w)),budgets(b) {}
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN inline role counters publication game owner mismatch");
    }
    struct Stage {
        State& state;
        explicit Stage(State& s):state(s) {
            state.owner();if(state.in_stage){state.terminal=true;throw std::logic_error("CN inline role counters publication reentry rejected");}
            state.in_stage=true;
        }
        ~Stage(){state.in_stage=false;}
    };
    bool tuple(const std::shared_ptr<Connection>& c) const {
        return !terminal && lease && c && connection.lock()==c && !c->closing() &&
            c->role()==Connection::Transport::Role::World && c->world_session_id()==lease->session &&
            c->verified_account_id()==lease->account && c->world_character_offered(lease->character) && c->world_admission_current();
    }
    bool endpoint(const std::shared_ptr<Pending>& p) const {
        return busy && !p->completed && active.lock()==p && p->token && registered && tuple(p->connection) &&
            p->plan.recipient==*lease && transports->same_registration(*p->token,*registered) &&
            transports->registry_current(*p->token);
    }
    bool acquire(const std::shared_ptr<Pending>& p) {
        if(!tuple(p->connection) || p->plan.recipient!=*lease)return false;
        if(!registered) {
            const auto actual=transports->lookup(*lease);
            if(!actual || !tuple(p->connection))return false;
            const auto cn=std::get_if<std::shared_ptr<Connection>>(&actual->transport());
            if(!cn || *cn!=p->connection || !transports->registry_current(*actual))return false;
            registered=actual->token();
        }
        p->token=*registered;return endpoint(p);
    }
    std::optional<SharedWorldPresence::ReadyCharacter> root(const std::shared_ptr<Pending>& p) const {
        if(!endpoint(p) || !transports->current(*p->token) || !endpoint(p))return {};
        const auto rows=presence->ready_characters();if(!rows || !endpoint(p))return {};
        std::optional<SharedWorldPresence::ReadyCharacter> found;
        for(const auto& row:*rows)if(row.lease==*lease) {
            if(found || row.character.id!=lease->character || row.character.account_id!=lease->account)return {};
            found=row;
        }
        return found;
    }
    bool same_scope(const Scope& a,const Scope& b) const {
        return a.lease==b.lease && same_root(a.character,b.character) && a.saved_position==b.saved_position &&
            transports->same_registration(a.native_token,b.native_token);
    }
    std::optional<Scope> snapshot(const std::shared_ptr<Pending>& p) const {
        const auto first=root(p);if(!first)return {};
        const auto last=root(p);
        if(!last || !endpoint(p) || !same_root(first->character,last->character) || first->position!=last->position)return {};
        return Scope{*lease,last->character,last->position,*p->token};
    }
    std::optional<Scope> qualify(const std::shared_ptr<Pending>& p,Check check) const {
        const auto before=snapshot(p);if(!before)return {};
        if(p->original_scope && !same_scope(*p->original_scope,*before))return {};
        if(!world->current(*p->connection,check,*before,p->plan) || !endpoint(p))return {};
        const auto after=snapshot(p);
        if(!after || !same_scope(*before,*after) ||
           (p->original_scope && !same_scope(*p->original_scope,*after)))return {};
        return after;
    }
    void close_captured(const std::shared_ptr<Pending>& p) const {
        // Never look up or close a successor connection or release a shared Token.
        // The captured old connection remains strong throughout this operation.
        if(p->connection && connection.lock()==p->connection && lease && p->plan.recipient==*lease &&
           (!p->token || transports->registry_current(*p->token)))p->connection->close();
    }
    void finish(const std::shared_ptr<Pending>& p,bool actual_released) {
        owner();if(p->completed)return;
        p->completed=true;
        if(active.lock()==p){active.reset();busy=false;}
        if(!actual_released || terminal){terminal=true;close_captured(p);}
        auto done=std::move(p->done);
        // True is a confirmed local release. Legacy false is ambiguous after
        // strand release followed by close/drain before game completion.
        // Do not turn false into an unsent fact or a retry permission.
        if(done)done(actual_released);
    }
    void completed(const std::shared_ptr<Pending>& p,bool actual_released) {
        owner();
        if(actual_released)p->locally_released=true;
        if(p->submitting){p->inline_release=p->locally_released;return;}
        bool post_current=false;
        if(actual_released && !p->completed) {
            try {Stage stage(*this);post_current=p->approved && bool(qualify(p,Check::AfterRelease));}
            catch(...){post_current=false;}
        }
        if(actual_released && p->original_scope) {
            // Keep every delivered-true prefix even after cancellation/late
            // callback. A legacy false cannot recover released-then-closed.
            released=std::static_pointer_cast<const ReceiptStorage>(
                post_current?p->qualified_receipt:p->unqualified_receipt);
        }
        if(p->completed)return;
        if(!post_current)terminal=true;
        finish(p,actual_released);
    }
    void publish(Plan supplied,Connection::Transport::Completion done) {
        owner();if(!done)throw std::invalid_argument("CN inline role counters publication completion required");
        if(busy || terminal || !lease){if(busy)terminal=true;done(false);return;}
        const auto actual=connection.lock(); // Strong before any real observer.
        auto p=std::make_shared<Pending>(actual,std::move(supplied),std::move(done));
        busy=true;active=p;bool failed=false;
        std::vector<god2cn::Bytes> output;
        std::function<bool()> approve;
        Connection::Transport::Completion complete;
        try {
            Stage stage(*this);
            const auto event=std::pair{p->plan.actual_event_id,p->plan.actual_committed_revision};
            if(!p->plan.actual_event_id || !p->plan.actual_committed_revision || !acquire(p) ||
               p->plan.actual_records.empty() || p->plan.actual_records.size()>budgets.max_records ||
               (last_attempt && *last_attempt==event))throw std::runtime_error("CN committed inline role counters event unavailable");
            output.reserve(p->plan.actual_records.size());
            std::size_t total=0;
            for(const auto& record:p->plan.actual_records) {
                const auto raw=record.logical_bytes();
                if(!Wire::read(raw) || total>budgets.max_logical_bytes ||
                   raw.size()>budgets.max_logical_bytes-total)
                    throw std::runtime_error("CN supplied inline role counter record unavailable");
                total+=raw.size();output.emplace_back(raw.begin(),raw.end());
            }
            p->original_scope=qualify(p,Check::BeforeQueue);
            if(!p->original_scope)throw std::runtime_error("CN real committed inline-role event qualification failed");
            p->qualified_receipt=std::make_shared<const ReceiptStorage>(*p,true);
            p->unqualified_receipt=std::make_shared<const ReceiptStorage>(*p,false);
            last_attempt=event; // Own immediate attempt only; durable replay remains real owner.
            const auto self=shared_from_this();
            approve=[self,p] {
                self->owner();if(p->completed)return false;
                try {
                    Stage stage(*self);
                    if(p->approved || !self->qualify(p,Check::BeforeRelease)){self->terminal=true;return false;}
                    p->approved=true;return true;
                }catch(...){self->terminal=true;return false;}
            };
            complete=[self,p](bool released){self->completed(p,released);};
        }catch(...){failed=true;}
        if(failed){terminal=true;finish(p,false);return;}
        // Preparation's observer stage has ended. A real synchronous approval
        // owns its own stage; busy/submitting still reject external operations.
        p->submitting=true;p->submitted=true;
        try {actual->send_world_batch_with_publication(std::move(output),std::move(approve),std::move(complete));}
        catch(...){failed=true;}
        p->submitting=false;
        if(failed) {
            terminal=true;
            // A throwing send cannot erase an actual inline release fact.
            if(p->locally_released)completed(p,true);else finish(p,false);
        }else if(p->inline_release)completed(p,*p->inline_release);
    }
    void release() {
        owner();terminal=true;
        const auto p=active.lock();
        if(p && !in_stage && !p->submitting) {
            // Once handed to the real held queue, wait for its existing bool
            // completion. Cancellation cannot invent an unsent fact; false
            // may mask release followed by close before the game callback.
            if(p->submitted)close_captured(p);else finish(p,false);
        }
        // No common registry/lease/token/core or real committed event mutation.
    }
};
SharedInlineRoleCountersPublication::ReleaseReceipt::ReleaseReceipt(std::shared_ptr<const ReceiptStorage> s):storage_(std::move(s)) {}
const SharedInlineRoleCountersPublication::Scope& SharedInlineRoleCountersPublication::ReleaseReceipt::original_scope() const {
    if(!storage_)throw std::logic_error("Empty inline role counters release receipt");return storage_->original_scope;
}
const SharedInlineRoleCountersPublication::Plan& SharedInlineRoleCountersPublication::ReleaseReceipt::plan() const {
    if(!storage_)throw std::logic_error("Empty inline role counters release receipt");return storage_->plan;
}
bool SharedInlineRoleCountersPublication::ReleaseReceipt::post_release_current() const {
    if(!storage_)throw std::logic_error("Empty inline role counters release receipt");return storage_->post_current;
}
SharedInlineRoleCountersPublication::SharedInlineRoleCountersPublication(std::shared_ptr<State> s):state_(std::move(s)) {}
SharedInlineRoleCountersPublication::~SharedInlineRoleCountersPublication(){state_->owner();}
std::shared_ptr<SharedInlineRoleCountersPublication> SharedInlineRoleCountersPublication::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedNativeWorldTransports> transports,
    std::shared_ptr<WorldOwner> world,Budgets budgets) {
    if(!presence || !transports || !transports->owns_presence(presence) || !world ||
       !budgets.max_records || budgets.max_records>256 || budgets.max_logical_bytes<Wire::logical_size ||
       budgets.max_logical_bytes>god2cn::CnTransport::max_logical)
        throw std::invalid_argument("CN inline role counters publication requires actual same source/owner/budgets");
    return std::shared_ptr<SharedInlineRoleCountersPublication>(new SharedInlineRoleCountersPublication(
        std::make_shared<State>(std::move(presence),std::move(transports),std::move(world),budgets)));
}
bool SharedInlineRoleCountersPublication::owns_source(const std::shared_ptr<SharedWorldPresence>& presence,
    const std::shared_ptr<SharedNativeWorldTransports>& transports) const {
    state_->owner();return same_owner(presence,state_->presence) && same_owner(transports,state_->transports);
}
bool SharedInlineRoleCountersPublication::bind(const std::shared_ptr<Connection>& original,const Lease& original_lease) {
    auto state=state_;state->owner();
    if(state->in_stage || state->busy){state->terminal=true;return false;}
    const auto connection=original;const auto lease=original_lease;
    if(state->terminal || state->lease || !connection || !lease.session || !lease.account || !lease.character ||
       !lease.generation || connection->closing() || connection->role()!=Connection::Transport::Role::World ||
       connection->world_session_id()!=lease.session || connection->verified_account_id()!=lease.account ||
       !connection->world_character_offered(lease.character))return false;
    state->connection=connection;state->lease=lease;return true;
}
void SharedInlineRoleCountersPublication::publish(Plan plan,Connection::Transport::Completion done) {
    const auto state=state_;state->publish(std::move(plan),std::move(done));
}
void SharedInlineRoleCountersPublication::invalidate_active() {
    state_->owner();if(state_->busy || state_->in_stage)state_->terminal=true;
}
void SharedInlineRoleCountersPublication::release(){const auto state=state_;state->release();}
std::optional<SharedInlineRoleCountersPublication::ReleaseReceipt> SharedInlineRoleCountersPublication::last_release() const {
    state_->owner();const auto receipt=state_->released;
    return receipt?std::optional{ReleaseReceipt(receipt)}:std::nullopt;
}
}
