#include "cn/world/SharedNativeBattleCommandGroups.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2::cn {
namespace {
using Groups=SharedNativeBattleCommandGroups;
struct Identity {};
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool same_scope(const Groups::Scope& a,const Groups::Scope& b) {
    return a.lease==b.lease && same_root(a.character,b.character) && a.saved_position==b.saved_position;
}
template<class T> bool same_owner(const std::shared_ptr<T>& a,const std::shared_ptr<T>& b) {
    return a && b && a.get()==b.get() && !a.owner_before(b) && !b.owner_before(a);
}
bool same_group(const Groups::Plan& a,const Groups::Plan& b) {
    return same_owner(a.issuer,b.issuer) && same_owner(a.group,b.group) &&
        a.actual_issuer_generation==b.actual_issuer_generation && a.actual_group_generation==b.actual_group_generation;
}
bool same_reply(const Groups::Reply& a,const Groups::Reply& b) {
    return a.native_no_reply()==b.native_no_reply() && a.logical_records()==b.logical_records();
}
struct Prepared {
    const Groups::Scope scope;
    const Groups::Request request;
    const Groups::Plan plan;
    const std::vector<Groups::Request> complete;
    Prepared(const Groups::Scope& s,const Groups::Request& r,Groups::Plan p,std::vector<Groups::Request> all)
        :scope(s),request(r),plan(std::move(p)),complete(std::move(all)) {}
};
struct Receipt final:Groups::Source::OperationEvidence {
    const std::shared_ptr<const Identity> source,operation=std::make_shared<const Identity>();
    const std::shared_ptr<const Prepared> input;
    std::optional<Groups::Result> actual; // Assigned once, before readonly evidence escapes.
    Receipt(std::shared_ptr<const Identity> owner,std::shared_ptr<const Prepared> retained)
        :source(std::move(owner)),input(std::move(retained)) {}
};
}
struct SharedNativeBattleCommandGroups::State {
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<Connection> connection;
    const Lease lease;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const std::shared_ptr<Authority> authority;
    const Budgets budgets;
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    std::optional<Token> registered;
    std::shared_ptr<const Prepared> prepared,pending;
    std::weak_ptr<const Receipt> latest;
    bool operating=false,terminal=false;
    State(const std::shared_ptr<Connection>& c,const Lease& l,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Authority> a,Budgets b):connection(c),lease(l),transports(std::move(t)),authority(std::move(a)),budgets(b) {}
    ~State() {
        if(thread!=std::this_thread::get_id())std::terminate();
        terminal=true;operating=true;prepared.reset();pending.reset();latest.reset();
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN grouped battle game owner mismatch");
    }
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s) {
            state.owner();if(state.operating) {state.terminal=true;throw std::logic_error("CN grouped battle reentry rejected");}
            state.operating=true;
        }
        ~Operation(){
            // Caught observer reentry or an exact release retires local input
            // only after its active callback unwinds; stay fenced during drops.
            if(state.terminal) {state.prepared.reset();state.pending.reset();state.latest.reset();}
            state.operating=false;
        }
    };
    bool tuple(const std::shared_ptr<Connection>& actual) const {
        return !terminal && actual && connection.lock()==actual && !actual->closing() &&
            actual->role()==Connection::Transport::Role::World && actual->world_admission_current() &&
            actual->world_session_id()==lease.session && actual->verified_account_id()==lease.account &&
            actual->world_character_offered(lease.character);
    }
    bool endpoint(const std::shared_ptr<Connection>& actual,const Scope& scope) const {
        return tuple(actual) && scope.lease==lease && scope.character.id==lease.character &&
            scope.character.account_id==lease.account && scope.native_token.lease()==lease && registered &&
            transports->same_registration(*registered,scope.native_token) && transports->registry_current(scope.native_token);
    }
    bool fence(const std::shared_ptr<Connection>& actual,const Scope& scope) const {
        // Source::qualify separately rereads the entire common root/position
        // before/after this adapter. This observes the exact native registry,
        // not an invented independent battle/position authority.
        return endpoint(actual,scope) && transports->current(scope.native_token) && endpoint(actual,scope);
    }
    bool acquire(const std::shared_ptr<Connection>& actual,const Scope& scope) {
        if(!tuple(actual) || scope.lease!=lease || scope.native_token.lease()!=lease)return false;
        if(!registered) {
            const auto found=transports->lookup(lease);
            if(!found || !tuple(actual))return false;
            const auto cn=std::get_if<std::shared_ptr<Connection>>(&found->transport());
            if(!cn || *cn!=actual || !transports->same_registration(found->token(),scope.native_token))return false;
            registered=scope.native_token;
        }
        return fence(actual,scope);
    }
    bool valid_plan(const Plan& plan) const {
        if(!plan.issuer || !plan.group)return false;
        if(plan.part==Part::Append)return bool(plan.intermediate_reply);
        return (plan.part==Part::Single || plan.part==Part::Final) && !plan.intermediate_reply;
    }
    bool authority_current(const std::shared_ptr<Connection>& actual,Check check,const Scope& scope,
        const Request& request,const Prepared& input,const Result* result) const {
        if(!fence(actual,scope))return false;
        const bool qualified=authority->current(*actual,check,scope,request,input.plan,input.complete,result);
        return qualified && fence(actual,scope);
    }
    bool before(const std::shared_ptr<Connection>& actual,const Scope& scope,const Request& request) {
        if(prepared || !acquire(actual,scope))return false;
        const auto prior=pending; // Strong complete input before real observer.
        const auto saved=prior?std::span<const Request>(prior->complete):std::span<const Request>{};
        auto plan=authority->prepare(*actual,scope,request,saved,prior?&prior->plan:nullptr);
        if(!plan || !fence(actual,scope) || !valid_plan(*plan))return false;
        if(plan->part==Part::Single && prior)return false;
        if(plan->part==Part::Final && !prior)return false;
        if(prior && !same_group(prior->plan,*plan))return false;
        const auto count=saved.size();
        if(count>=budgets.max_request_records || count>=budgets.max_request_logical_bytes/god2cn::CnBattleCommand35::logical_size)
            return false;
        std::vector<Request> complete;complete.reserve(count+1);
        complete.insert(complete.end(),saved.begin(),saved.end());complete.push_back(request);
        auto input=std::make_shared<const Prepared>(scope,request,std::move(*plan),std::move(complete));
        if(!authority_current(actual,Check::BeforeExecute,scope,request,*input,nullptr))return false;
        prepared=std::move(input);return true;
    }
    bool post(const std::shared_ptr<Connection>& actual,Check check,const Scope& scope,
        const Request& request,const Result& supplied) const {
        const auto receipt=std::dynamic_pointer_cast<const Receipt>(supplied.evidence);
        if(!receipt || receipt->source!=identity || latest.lock()!=receipt || !receipt->actual ||
           receipt->input->request!=request || receipt->input->scope.lease!=scope.lease ||
           !transports->same_registration(receipt->input->scope.native_token,scope.native_token) ||
           !same_reply(supplied.reply,receipt->actual->reply))return false;
        return authority_current(actual,check,scope,request,*receipt->input,&*receipt->actual);
    }
    std::optional<Result> execute_owned(const std::shared_ptr<Connection>& actual,const Scope& scope,const Request& request) {
        const auto input=prepared;
        prepared.reset(); // Consumed before any real callback; never retried.
        if(!input || input->request!=request || !same_scope(input->scope,scope) ||
           !transports->same_registration(input->scope.native_token,scope.native_token) || !fence(actual,scope))return {};
        // Allocation/deep copies of all group inputs happen before settlement.
        auto receipt=std::make_shared<Receipt>(identity,input);
        if(input->plan.part==Part::Append) {
            receipt->actual.emplace(*input->plan.intermediate_reply);
            pending=input; // No cost/settlement callback in this branch.
        }else {
            pending.reset(); // Retire old local group before actual once execution.
            receipt->actual=authority->execute_group(*actual,scope,input->complete,input->plan);
        }
        if(!receipt->actual || !fence(actual,scope))return {};
        latest=receipt;
        auto reply=receipt->actual->reply; // Own full output before handing off evidence.
        return Result(std::move(reply),std::move(receipt));
    }
};
SharedNativeBattleCommandGroups::SharedNativeBattleCommandGroups(std::shared_ptr<State> state):state_(std::move(state)) {}
SharedNativeBattleCommandGroups::~SharedNativeBattleCommandGroups(){state_->owner();}
std::shared_ptr<SharedNativeBattleCommandGroups> SharedNativeBattleCommandGroups::create(
    const std::shared_ptr<Connection>& connection,const Lease& lease,std::shared_ptr<SharedNativeWorldTransports> transports,
    std::shared_ptr<Authority> authority,Budgets budgets) {
    if(!connection || !lease.session || !lease.account || !lease.character || !lease.generation || !transports || !authority ||
       !budgets.max_request_records || budgets.max_request_logical_bytes<god2cn::CnBattleCommand35::logical_size)
        throw std::invalid_argument("Actual grouped battle connection/lease/transport/authority/budgets required");
    return std::shared_ptr<SharedNativeBattleCommandGroups>(new SharedNativeBattleCommandGroups(
        std::make_shared<State>(connection,lease,std::move(transports),std::move(authority),budgets)));
}
bool SharedNativeBattleCommandGroups::current(Connection& connection,Check check,const Scope& scope,
    const Request& request,const Result* result) {
    State::Operation operation(*state_);
    try {
        const auto actual=state_->connection.lock();
        if(!actual || actual.get()!=&connection || state_->terminal)return false;
        const bool valid=check==Check::BeforeExecute?!result && state_->before(actual,scope,request):
            result && state_->post(actual,check,scope,request,*result);
        if(!valid)state_->terminal=true;
        return valid;
    }catch(...) {state_->terminal=true;throw;}
}
std::optional<SharedNativeBattleCommandGroups::Result> SharedNativeBattleCommandGroups::execute(
    Connection& connection,const Scope& scope,const Request& request) {
    State::Operation operation(*state_);
    try {
        const auto actual=state_->connection.lock();
        if(!actual || actual.get()!=&connection || state_->terminal)return {};
        auto result=state_->execute_owned(actual,scope,request);
        if(!result)state_->terminal=true;
        return result;
    }catch(...) {state_->terminal=true;throw;}
}
void SharedNativeBattleCommandGroups::release_binding(const Lease& lease,const Token& token) noexcept {
    if(state_->thread!=std::this_thread::get_id())std::terminate();
    // Original registration may already have been removed. Token private
    // identity is retained in the prepared/pending scope, so no live registry
    // Current is required and a foreign successor cannot be cleared.
    if(lease!=state_->lease || token.lease()!=lease || !state_->registered)return;
    const auto matches=[&](const auto& input) {
        return input && &input->scope.native_token.lease()==&token.lease();
    };
    if(&state_->registered->lease()!=&token.lease() ||
       (state_->prepared && !matches(state_->prepared)) || (state_->pending && !matches(state_->pending)))return;
    state_->terminal=true;
    if(!state_->operating) {
        state_->operating=true;
        state_->prepared.reset();state_->pending.reset();state_->latest.reset();
        state_->operating=false;
    }
}
}
