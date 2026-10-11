#include "cn/world/SharedNativeSkillBookUseSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>
#include <variant>


namespace god2::cn {
SharedNativeSkillBookUseSource::Reply::Reply(std::vector<god2cn::Bytes> records,bool no_reply)
    :records_(std::move(records)),no_reply_(no_reply) {}
SharedNativeSkillBookUseSource::Reply SharedNativeSkillBookUseSource::Reply::records(std::vector<god2cn::Bytes> actual) {
    if(actual.empty())throw std::invalid_argument("CN skill-book use actual records must be explicit and nonempty");
    return Reply(std::move(actual),false);
}
SharedNativeSkillBookUseSource::Reply SharedNativeSkillBookUseSource::Reply::no_reply() {return Reply({},true);}
namespace {
using Source=SharedNativeSkillBookUseSource;

using Token=SharedNativeWorldTransports::Token;
struct Pending {
    const std::shared_ptr<Source::Connection> connection;
    const std::variant<Source::Request,Source::ControlRequest> request;
    std::optional<Source::Book> book;
    std::optional<Source::StoredBook> stored_book;
    std::optional<Token> token;
    std::optional<Source::Result> result;
    Source::Connection::Transport::Completion done;
    bool completed=false,approved=false,submitting=false,locally_released=false;
    std::optional<bool> inline_release;
    Pending(std::shared_ptr<Source::Connection> c,std::variant<Source::Request,Source::ControlRequest> raw,
        Source::Connection::Transport::Completion completion)
        :connection(std::move(c)),request(std::move(raw)),done(std::move(completion)) {}
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
    const std::shared_ptr<Source::ControlOwner> control;
    const std::shared_ptr<const CnNativeSkillBookBindings> books;
    const std::shared_ptr<const CnSharedSkillBookSourceCatalog> stored_books;
    const Source::Budgets budgets;
    std::optional<Token> registered;
    std::weak_ptr<Pending> active;
    bool busy=false,in_stage=false,terminal=false;
    bool binding_released=false;
    State(const std::shared_ptr<Source::Connection>& c,std::shared_ptr<SharedWorldPresence> p,
        const Source::Lease& l,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Source::WorldOwner> w,Source::Budgets b,
        std::shared_ptr<Source::ControlOwner> ctrl,std::shared_ptr<const CnNativeSkillBookBindings> bk,
        std::shared_ptr<const CnSharedSkillBookSourceCatalog> stored)
        :connection(c),presence(std::move(p)),lease(l),transports(std::move(t)),world(std::move(w)),control(std::move(ctrl)),books(std::move(bk)),stored_books(std::move(stored)),budgets(b) {}
    ~State() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN skill-book use source game owner mismatch");
    }
    void invalidate() {owner();if(busy)terminal=true;}
    struct Stage {
        State& state;
        explicit Stage(State& s):state(s) {
            state.owner();if(state.in_stage) {state.terminal=true;throw std::logic_error("CN skill-book use source reentry rejected");}
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
    bool owner_current(const std::shared_ptr<Pending>& p,Source::Check check,const Source::Scope& scope) const {
        const auto result=p->result?&*p->result:nullptr;
        if(const auto request=std::get_if<Source::Request>(&p->request))
            return world && world->current(*p->connection,check,scope,*request,
                check==Source::Check::BeforeCatalog?nullptr:(p->book?&*p->book:nullptr),
                check==Source::Check::BeforeCatalog?nullptr:(p->stored_book?&*p->stored_book:nullptr),
                check==Source::Check::BeforeCatalog?nullptr:result);
        return control && control->current(*p->connection,check,scope,std::get<Source::ControlRequest>(p->request),result);
    }
    static bool same_book(const Source::Book& a,const Source::Book& b) {
        return a.source==b.source && a.source_record_index==b.source_record_index && a.source_line==b.source_line &&
            a.decoded_offset==b.decoded_offset && a.item_id==b.item_id && a.record_sha256==b.record_sha256 &&
            a.raw_line==b.raw_line && a.native_alias==b.native_alias && a.opaque_tail_fields==b.opaque_tail_fields;
    }
    std::optional<Source::Scope> qualify(const std::shared_ptr<Pending>& p,Source::Check check) const {
        const auto before=snapshot(p);if(!before)return std::nullopt;
        if(const auto request=std::get_if<Source::Request>(&p->request)) {
            // Actual store/reader lifetime qualification precedes every borrowed
            // catalog observation; factory creation never reads that reader.
            if(!owner_current(p,Source::Check::BeforeCatalog,*before) || !endpoint(p))return std::nullopt;
            const auto qualified=snapshot(p);
            if(!qualified || !same_scope(*before,*qualified) || !stored_books || !stored_books->current() || !endpoint(p))return std::nullopt;
            const auto fresh=stored_books->lookup_item(request->item());
            if(!fresh || !endpoint(p) || (p->book && !same_book(*p->book,fresh->book)) ||
               (p->stored_book && *p->stored_book!=fresh->stored))return std::nullopt;
            if(!p->book)p->book=fresh->book;
            if(!p->stored_book)p->stored_book=fresh->stored;
        }
        const auto middle=snapshot(p);
        if(!middle || !same_scope(*before,*middle) || !owner_current(p,check,*middle) || !endpoint(p))return std::nullopt;
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
        if(world)world->release_binding(lease,token);
        if(control)control->release_binding(lease,token); // Required noexcept actual-owner contracts.
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
    void receive(god2cn::Bytes bytes,Source::Connection::Transport::Completion done,bool is_control) {
        owner();if(!done)throw std::invalid_argument("CN skill-book use completion required");
        if(busy || terminal) {invalidate();if(const auto c=connection.lock())c->close();done(false);return;}
        const auto actual=connection.lock(); // Strong before any repository observer.
        std::optional<std::variant<Source::Request,Source::ControlRequest>> request;
        if(is_control) {
            if(control)if(const auto raw=god2cn::CnSkillBookUse25::read_control1f(bytes))request=*raw;
        } else if(world) {
            if(const auto raw=god2cn::CnSkillBookUse25::decode(bytes);raw && raw->slot()<30)request=*raw;
            // This source explicitly selects ordinary bag-slot domain only;
            // slot validity is not custody or a native acquisition rule.
        }
        if(!actual || !request) {
            terminal=true;release_registered_binding();if(actual)actual->close();done(false);return;
        }
        auto p=std::make_shared<Pending>(actual,std::move(*request),std::move(done));
        busy=true;active=p;
        bool no_reply=false,failed=false;
        try {
            Stage stage(*this);
            if(!acquire(p))throw std::runtime_error("CN skill-book use exact ready registration unavailable");
            const auto before=qualify(p,Source::Check::BeforeExecute);
            if(!before)throw std::runtime_error("CN skill-book use real pre-execution authority failed");
            if(const auto raw=std::get_if<Source::Request>(&p->request))
                p->result=world->execute(*actual,*before,*raw,*p->book,*p->stored_book);
            else p->result=control->execute(*actual,*before,std::get<Source::ControlRequest>(p->request));
            // Exactly once. Retained result/evidence are actual owner output,
            // not reconstructed from reply bytes or a fabricated success.

            if(!p->result || !p->result->evidence || !endpoint(p) || !records(p->result->reply) || !qualify(p,Source::Check::AfterExecute) ||
               !qualify(p,Source::Check::BeforeQueue))throw std::runtime_error("CN skill-book use actual execution/reply failed");
            no_reply=p->result->reply.native_no_reply();
        }catch(...) {failed=true;}
        if(!failed && !no_reply) {
            // End the observing stage BEFORE actual held transport invocation;
            // its approval gets its own stage and inline completion is retained.
            try {
                auto output=p->result->reply.logical_records();
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
            }catch(...) {failed=true;}
        }
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
SharedNativeSkillBookUseSource::Binding SharedNativeSkillBookUseSource::create(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedNativeWorldTransports> transports,std::shared_ptr<const CnNativeSkillBookBindings> books,
    std::shared_ptr<const CnSharedSkillBookSourceCatalog> stored_books,std::shared_ptr<WorldOwner> world,
    Budgets budgets,std::shared_ptr<ControlOwner> control) {
    if(!connection || !presence || !lease.session || !lease.account || !lease.character || !lease.generation ||
       !transports || !transports->owns_presence(presence) || (!world && !control) ||
       (world && (!books || !stored_books || !stored_books->uses_native_books(*books))) ||
       !budgets.max_reply_records || budgets.max_reply_records>256 || !budgets.max_reply_logical_bytes)
        throw std::invalid_argument("CN skill-book use requires actual same-source connection/lease/handler/budgets");
    auto state=std::make_shared<State>(connection,std::move(presence),lease,std::move(transports),world,
        budgets,control,std::move(books),std::move(stored_books));
    Binding binding;
    if(world)binding.ingress=[state](god2cn::Bytes bytes,Connection::Transport::Completion done){
        state->receive(std::move(bytes),std::move(done),false);};
    if(control)binding.control_ingress=[state](god2cn::Bytes bytes,Connection::Transport::Completion done){
        state->receive(std::move(bytes),std::move(done),true);};
    binding.invalidate_active=[state]{state->invalidate();};binding.release=[state]{state->release();};
    return binding;
}
}
