#include "cn/world/SharedNativeSpectatorSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>
#include <variant>

namespace god2::cn {
SharedNativeSpectatorSource::Reply::Reply(std::vector<god2cn::Bytes> records,bool no_reply)
    :records_(std::move(records)),no_reply_(no_reply) {}
SharedNativeSpectatorSource::Reply SharedNativeSpectatorSource::Reply::records(std::vector<god2cn::Bytes> actual) {
    if(actual.empty())throw std::invalid_argument("CN spectator actual records must be explicit and nonempty");
    return Reply(std::move(actual),false);
}
SharedNativeSpectatorSource::Reply SharedNativeSpectatorSource::Reply::no_reply() {return Reply({},true);}
namespace {
using Source=SharedNativeSpectatorSource;
using Input=std::variant<Source::Request,Source::CloseRequest>;
using Token=SharedNativeWorldTransports::Token;
struct Pending {
    const std::shared_ptr<Source::Connection> connection;
    const Input request;
    std::optional<Token> token;
    std::optional<Source::Result> result;
    Source::Connection::Transport::Completion done;
    bool completed=false,approved=false,submitting=false,locally_released=false;
    std::optional<bool> inline_release;
    Pending(std::shared_ptr<Source::Connection> c,const Input& raw,
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
    const std::shared_ptr<Source::CloseOwner> close;
    const Source::Budgets budgets;
    const std::shared_ptr<SharedNativeSpectatorPublication> publication;
    const std::shared_ptr<SharedNativeSpectatorTargets> targets;
    std::optional<Token> registered;
    std::weak_ptr<Pending> active;
    bool busy=false,in_stage=false,terminal=false;
    State(const std::shared_ptr<Source::Connection>& c,std::shared_ptr<SharedWorldPresence> p,
        const Source::Lease& l,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Source::WorldOwner> w,Source::Budgets b,
        std::shared_ptr<SharedNativeSpectatorPublication> ui,std::shared_ptr<SharedNativeSpectatorTargets> target,
        std::shared_ptr<Source::CloseOwner> close_owner)
        :connection(c),presence(std::move(p)),lease(l),transports(std::move(t)),world(std::move(w)),close(std::move(close_owner)),
         budgets(b),publication(std::move(ui)),targets(std::move(target)) {}
    ~State() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN spectator source game owner mismatch");
    }
    void invalidate() {owner();if(busy)terminal=true;}
    struct Stage {
        State& state;
        explicit Stage(State& s):state(s) {
            state.owner();if(state.in_stage) {state.terminal=true;throw std::logic_error("CN spectator source reentry rejected");}
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
    bool same_views(const Source::Scope& a,const Source::Scope& b) const {
        if(a.lease!=b.lease || !same_root(a.character,b.character) || a.saved_position!=b.saved_position ||
           bool(a.native_ui)!=bool(b.native_ui) || bool(a.target)!=bool(b.target))return false;
        if(a.native_ui && (!publication || !publication->same(*a.native_ui,*b.native_ui)))return false;
        return !a.target || (targets && targets->same(*a.target,*b.target));
    }
    std::optional<Source::Scope> view(const std::shared_ptr<Pending>& p,
        const SharedWorldPresence::ReadyCharacter& row) const {
        Source::Scope scope{lease,row.character,row.position,std::nullopt,std::nullopt};
        if(publication) {
            scope.native_ui=publication->observe(*p->token);
            if(scope.native_ui->lease()!=lease || !transports->same_registration(scope.native_ui->token(),*p->token) ||
               !publication->current(*scope.native_ui) || !endpoint(p))return std::nullopt;
        }
        if(const auto six=std::get_if<Source::Request>(&p->request);targets && six) {
            scope.target=targets->resolve(*p->token,six->context()); // Full DWORD, never WORD/low12.
            if(scope.target->raw_context()!=six->context() ||
               !transports->same_registration(scope.target->token(),*p->token) ||
               !targets->current(*scope.target) || !endpoint(p))return std::nullopt;
            const auto& ui=scope.target->ui();
            if(!ui || !scope.native_ui || !publication || !publication->same(*scope.native_ui,*ui))return std::nullopt;
        }
        return scope;
    }
    std::optional<Source::Scope> snapshot(const std::shared_ptr<Pending>& p) const {
        const auto first=root(p);if(!first)return std::nullopt;
        const auto a=view(p,*first);if(!a)return std::nullopt;
        const auto middle=root(p);if(!middle || !same_root(first->character,middle->character) || first->position!=middle->position)return std::nullopt;
        const auto b=view(p,*middle);if(!b || !same_views(*a,*b))return std::nullopt;
        const auto last=root(p);
        if(!last || !same_root(middle->character,last->character) || middle->position!=last->position ||
           (b->native_ui && !publication->registry_current(*b->native_ui)) ||
           (b->target && !targets->registry_current(*b->target)) || !endpoint(p))return std::nullopt;
        return b;
    }
    std::optional<Source::Scope> qualify(const std::shared_ptr<Pending>& p,Source::Check check) const {
        const auto before=snapshot(p);if(!before)return std::nullopt;
        const auto result=p->result?&*p->result:nullptr;
        const auto six=std::get_if<Source::Request>(&p->request);
        const bool actual_current=six?world->current(*p->connection,check,*before,*six,result):
            (close && close->current(*p->connection,check,*before,std::get<Source::CloseRequest>(p->request),result));
        if(!actual_current || !endpoint(p))return std::nullopt;
        const auto after=snapshot(p);return after && same_views(*before,*after)?after:std::nullopt;
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
    void finish(const std::shared_ptr<Pending>& p,bool accepted) {
        owner();if(p->completed)return;
        p->completed=true;
        if(active.lock()==p) {active.reset();busy=false;}
        if(!accepted) {terminal=true;p->connection->close();}
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
    void receive(god2cn::Bytes bytes,Source::Connection::Transport::Completion done,bool closing=false) {
        owner();if(!done)throw std::invalid_argument("CN spectator completion required");
        if(busy || terminal) {invalidate();if(const auto c=connection.lock())c->close();done(false);return;}
        const auto actual=connection.lock(); // Strong before any repository observer.
        std::optional<Input> request;
        if(closing) {
            if(close && publication)if(const auto raw=god2cn::CnSpectatorClose::decode(bytes))request=*raw;
        }else if(const auto raw=god2cn::CnSpectator6E::decode(bytes)) {
            if(god2cn::CnSpectator6E::observed_producer_shape(*raw))request=*raw;
        }
        if(!actual || !request) {
            terminal=true;if(actual)actual->close();done(false);return;
        }
        auto p=std::make_shared<Pending>(actual,*request,std::move(done));
        busy=true;active=p;
        bool no_reply=false,failed=false;
        try {
            Stage stage(*this);
            if(!acquire(p))throw std::runtime_error("CN spectator exact ready registration unavailable");
            const auto before=qualify(p,Source::Check::BeforeExecute);
            if(!before)throw std::runtime_error("CN spectator real pre-execution authority failed");
            const auto six=std::get_if<Source::Request>(&p->request);
            p->result=six?world->execute(*actual,*before,*six):
                close->execute(*actual,*before,std::get<Source::CloseRequest>(p->request)); // Exactly once.
            if(!p->result || !endpoint(p) || !records(p->result->reply) || !qualify(p,Source::Check::AfterExecute) ||
               !qualify(p,Source::Check::BeforeQueue))throw std::runtime_error("CN spectator actual execution/reply failed");
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
        registered.reset(); // Own saved weak token only, no common/successor cleanup.
    }
};
}
SharedNativeSpectatorSource::Binding SharedNativeSpectatorSource::create(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedNativeWorldTransports> transports,std::shared_ptr<WorldOwner> world,Budgets budgets,
    std::shared_ptr<SharedNativeSpectatorPublication> publication,std::shared_ptr<SharedNativeSpectatorTargets> targets,
    std::shared_ptr<CloseOwner> close) {
    if(!connection || !presence || !lease.session || !lease.account || !lease.character || !lease.generation ||
       !transports || !transports->owns_presence(presence) || !world || !budgets.max_reply_records ||
       budgets.max_reply_records>256 || !budgets.max_reply_logical_bytes ||
       (close && !publication) || (publication && !publication->owns_source(presence,transports)) ||
       (targets && (!publication || !targets->owns_source(presence,transports,publication))))
        throw std::invalid_argument("CN spectator requires actual same-source connection/lease/handler/budgets");
    auto state=std::make_shared<State>(connection,std::move(presence),lease,std::move(transports),std::move(world),
        budgets,std::move(publication),std::move(targets),std::move(close));
    Binding binding{[state](god2cn::Bytes bytes,Connection::Transport::Completion done){state->receive(std::move(bytes),std::move(done));},
        [state]{state->invalidate();},[state]{state->release();},{}};
    if(state->close)binding.close_ingress=[state](god2cn::Bytes bytes,Connection::Transport::Completion done){
        state->receive(std::move(bytes),std::move(done),true);
    };
    return binding;
}
}
