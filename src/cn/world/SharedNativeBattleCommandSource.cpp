#include "cn/world/SharedNativeBattleCommandSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>


namespace god2::cn {
SharedNativeBattleCommandSource::Reply::Reply(std::vector<god2cn::Bytes> records,bool no_reply)
    :records_(std::move(records)),no_reply_(no_reply) {}
SharedNativeBattleCommandSource::Reply SharedNativeBattleCommandSource::Reply::records(std::vector<god2cn::Bytes> actual) {
    if(actual.empty())throw std::invalid_argument("CN battle command actual records must be explicit and nonempty");
    return Reply(std::move(actual),false);
}
SharedNativeBattleCommandSource::Reply SharedNativeBattleCommandSource::Reply::no_reply() {return Reply({},true);}
namespace {
using Source=SharedNativeBattleCommandSource;

using Token=SharedNativeWorldTransports::Token;
struct Pending {
    const std::shared_ptr<Source::Connection> connection;
    const Source::Request request;
    std::optional<Token> token;
    std::optional<Source::Result> result;
    Source::Connection::Transport::Completion done;
    bool completed=false,approved=false,submitting=false,locally_released=false;
    std::optional<bool> inline_release;
    Pending(std::shared_ptr<Source::Connection> c,const Source::Request& raw,
        Source::Connection::Transport::Completion completion)
        :connection(std::move(c)),request(raw),done(std::move(completion)) {}
};
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
struct State:std::enable_shared_from_this<State> {
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<Source::Connection> connection;
    const std::shared_ptr<SharedWorldPresence> presence;
    const Source::Lease lease;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const std::shared_ptr<Source::WorldOwner> world;
    const Source::Budgets budgets;
    std::optional<Token> registered;
    std::weak_ptr<Pending> active;
    bool busy=false,in_stage=false,terminal=false;
    bool binding_released=false;
    State(const std::shared_ptr<Source::Connection>& c,std::shared_ptr<SharedWorldPresence> p,
        const Source::Lease& l,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Source::WorldOwner> w,Source::Budgets b)
        :connection(c),presence(std::move(p)),lease(l),transports(std::move(t)),world(std::move(w)),budgets(b) {}
    ~State() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN battle command source game owner mismatch");
    }
    void invalidate() {owner();if(busy)terminal=true;}
    struct Stage {
        State& state;
        explicit Stage(State& s):state(s) {
            state.owner();if(state.in_stage) {state.terminal=true;throw std::logic_error("CN battle command source reentry rejected");}
            state.in_stage=true;
        }
        ~Stage(){state.in_stage=false;}
    };
    bool tuple(const std::shared_ptr<Source::Connection>& actual) const {
        return !terminal && actual && connection.lock()==actual && !actual->closing() &&
            actual->role()==Source::Connection::Transport::Role::World && actual->world_session_id()==lease.session &&
            actual->verified_account_id()==lease.account && actual->world_character_offered(lease.character) &&
            actual->world_admission_current();
    }
    bool endpoint(const std::shared_ptr<Pending>& p) const {
        return busy && !p->completed && active.lock()==p && p->token && registered &&
            tuple(p->connection) && transports->same_registration(*p->token,*registered) &&
            transports->registry_current(*p->token);
    }
    bool acquire(const std::shared_ptr<Pending>& p) {
        if(!tuple(p->connection))return false;
        if(!registered) {
            const auto actual=transports->lookup(lease);
            if(!actual || !tuple(p->connection))return false;
            const auto cn=std::get_if<std::shared_ptr<Source::Connection>>(&actual->transport());
            if(!cn || *cn!=p->connection || !transports->registry_current(*actual))return false;
            registered=actual->token();
        }
        p->token=*registered;return endpoint(p);
    }
    std::optional<SharedWorldPresence::ReadyCharacter> root(const std::shared_ptr<Pending>& p) const {
        if(!endpoint(p) || !transports->current(*p->token) || !endpoint(p))return std::nullopt;
        const auto rows=presence->ready_characters();if(!rows || !endpoint(p))return std::nullopt;
        std::optional<SharedWorldPresence::ReadyCharacter> found;
        for(const auto& row:*rows)if(row.lease==lease) {
            if(found || row.character.id!=lease.character || row.character.account_id!=lease.account)return std::nullopt;
            found=row;
        }
        return found;
    }
    bool same_scope(const Source::Scope& a,const Source::Scope& b) const {
        return a.lease==b.lease && same_root(a.character,b.character) && a.saved_position==b.saved_position &&
            transports->same_registration(a.native_token,b.native_token);
    }
    std::optional<Source::Scope> snapshot(const std::shared_ptr<Pending>& p) const {
        const auto first=root(p);if(!first)return std::nullopt;
        // Both actual root/position populations and original-token Current
        // bracket the scope. No manufactured battle clock, grant or actor ID.
        const auto last=root(p);
        if(!last || !same_root(first->character,last->character) || first->position!=last->position || !endpoint(p))
            return std::nullopt;
        return Source::Scope{lease,last->character,last->position,*p->token};
    }
    std::optional<Source::Scope> qualify(const std::shared_ptr<Pending>& p,Source::Check check) const {
        const auto before=snapshot(p);if(!before)return std::nullopt;
        const auto result=p->result?&*p->result:nullptr;
        if(!world->current(*p->connection,check,*before,p->request,result) || !endpoint(p))return std::nullopt;
        const auto after=snapshot(p);return after && same_scope(*before,*after)?after:std::nullopt;
    }
    bool records(const Source::Reply& reply) const {
        const auto& rows=reply.logical_records();
        if(reply.native_no_reply())return rows.empty();
        if(rows.empty() || rows.size()>budgets.max_reply_records || rows.size()>256)return false;
        std::size_t size=0;
        for(const auto& row:rows) {
            if(row.empty() || row.size()>god2cn::CnTransport::max_logical || row.size()>budgets.max_reply_logical_bytes-size)return false;
            size+=row.size();
        }
        return true; // Real WorldOwner qualifies native records/profile, not a guessed codec.
    }
    void release_registered_binding() {
        owner();terminal=true;
        const auto pending=active.lock();
        if(in_stage || (pending && pending->submitting) || binding_released || !registered)return;
        // Consume the original private capability before external cleanup.
        // A nested release cannot invoke cancellation again or erase a successor.
        const auto token=*registered;
        binding_released=true;registered.reset();
        world->release_binding(lease,token); // Required noexcept real-owner contract.
    }
    void finish(const std::shared_ptr<Pending>& p,bool accepted) {
        owner();if(p->completed)return;
        p->completed=true;
        if(active.lock()==p) {active.reset();busy=false;}
        if(!accepted) {terminal=true;release_registered_binding();p->connection->close();}
        auto done=std::move(p->done);
        if(done)done(accepted); // Original continuation once, after source stage ends.
    }
    void completed(const std::shared_ptr<Pending>& p,bool released) {
        owner();
        // Monotonic local transport fact, even after source cancellation or a
        // failed post-release input qualification. Never retry/reopen done.
        if(released)p->locally_released=true;
        if(p->completed)return;
        if(p->submitting) {p->inline_release=released;return;}
        bool accepted=false;
        try {
            Stage stage(*this);
            accepted=released && p->approved && endpoint(p) && bool(qualify(p,Source::Check::AfterRelease));
        }catch(...) {accepted=false;}
        // A false post-release decision cannot retract a locally released
        // prefix or run execute again. Outer gameplay aborts/cleans up.
        finish(p,accepted);
    }
    void receive(god2cn::Bytes bytes,Source::Connection::Transport::Completion done) {
        owner();if(!done)throw std::invalid_argument("CN battle command completion required");
        if(busy || terminal) {invalidate();if(const auto c=connection.lock())c->close();done(false);return;}
        const auto actual=connection.lock(); // Strong before any repository observer.
        const auto request=god2cn::CnBattleCommand35::decode(bytes); // Own all actual logical17 bytes.
        // Grammar is not authority; unknown kinds and opaque fields survive.
        if(!actual || !request) {
            terminal=true;release_registered_binding();if(actual)actual->close();done(false);return;
        }
        auto p=std::make_shared<Pending>(actual,*request,std::move(done));
        busy=true;active=p;
        bool no_reply=false,failed=false;
        try {
            Stage stage(*this);
            if(!acquire(p))throw std::runtime_error("CN battle command exact ready registration unavailable");
            const auto before=qualify(p,Source::Check::BeforeExecute);
            if(!before)throw std::runtime_error("CN battle command real pre-execution authority failed");
            p->result=world->execute(*actual,*before,p->request); // Exactly once, never retried.
            if(!p->result || !endpoint(p) || !records(p->result->reply) || !qualify(p,Source::Check::AfterExecute) ||
               !qualify(p,Source::Check::BeforeQueue))throw std::runtime_error("CN battle command actual execution/reply failed");
            no_reply=p->result->reply.native_no_reply();
            if(!no_reply) {
                auto output=p->result->reply.logical_records(); // Full deep copy before native queue effects.
                const auto self=shared_from_this();
                const auto approve=[self,p] {
                    self->owner();if(p->completed)return false;
                    try {
                        Stage stage(*self);
                        if(p->approved || !self->endpoint(p) || !self->qualify(p,Source::Check::BeforeRelease)) {
                            self->terminal=true;return false;
                        }
                        p->approved=true;return true;
                    }catch(...) {self->terminal=true;return false;}
                };
                const auto complete=[self,p](bool released){self->completed(p,released);};
                p->submitting=true;
                try {actual->send_world_batch_with_publication(std::move(output),approve,complete);}
                catch(...) {p->submitting=false;throw;}
                p->submitting=false;
            }
        }catch(...) {failed=true;}
        if(failed)finish(p,false);
        else if(no_reply)finish(p,true); // Actual explicit handler decision, no emitted ACK.
        else if(p->inline_release)completed(p,*p->inline_release);
    }
    void release() {
        owner();terminal=true;
        const auto pending=active.lock();
        // Do not call the outer batch continuation inside its observer/execute
        // stack. In-stage rejection propagates; async release cancels once.
        if(pending && !in_stage && !pending->submitting)finish(pending,false);
        release_registered_binding(); // Defer while observing/submitting; no fabricated token.
    }
};
}
SharedNativeBattleCommandSource::Binding SharedNativeBattleCommandSource::create(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedNativeWorldTransports> transports,std::shared_ptr<WorldOwner> world,Budgets budgets) {
    if(!connection || !presence || !lease.session || !lease.account || !lease.character || !lease.generation ||
       !transports || !transports->owns_presence(presence) || !world || !budgets.max_reply_records ||
       budgets.max_reply_records>256 || !budgets.max_reply_logical_bytes)
        throw std::invalid_argument("CN battle command requires actual same-source connection/lease/handler/budgets");
    auto state=std::make_shared<State>(connection,std::move(presence),lease,std::move(transports),std::move(world),
        budgets);
    return {[state](god2cn::Bytes bytes,Connection::Transport::Completion done){state->receive(std::move(bytes),std::move(done));},
        [state]{state->invalidate();},[state]{state->release();}};
}
}
