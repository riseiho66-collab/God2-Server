#include "cn/world/SharedNativeBattleCommandData.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2::cn {
namespace {
using Data=SharedNativeBattleCommandData;
template<class T> bool same_cap(const std::shared_ptr<T>& a,const std::shared_ptr<T>& b) {
    return a && b && a.get()==b.get() && !a.owner_before(b) && !b.owner_before(a);
}
bool same_plan(const Data::Plan& a,const Data::Plan& b) {
    if(a.part!=b.part || !same_cap(a.issuer,b.issuer) || !same_cap(a.group,b.group) ||
       a.actual_issuer_generation!=b.actual_issuer_generation || a.actual_group_generation!=b.actual_group_generation ||
       bool(a.intermediate_reply)!=bool(b.intermediate_reply))return false;
    return !a.intermediate_reply || (a.intermediate_reply->native_no_reply()==b.intermediate_reply->native_no_reply() &&
        a.intermediate_reply->logical_records()==b.intermediate_reply->logical_records());
}
bool same_inventory(const Data::InventorySnapshot& a,const Data::InventorySnapshot& b) {
    if(a.lease!=b.lease || a.actual_generation!=b.actual_generation || a.cells.size()!=b.cells.size())return false;
    auto x=a.cells.begin(),y=b.cells.begin();
    for(;x!=a.cells.end();++x,++y)if(x->first!=y->first ||
        !std::equal(x->second.raw_bytes().begin(),x->second.raw_bytes().end(),y->second.raw_bytes().begin()))return false;
    return true;
}
struct Input {
    const Data::Scope before;
    const Data::Plan plan;
    const Data::Resolved data;
    bool executed=false;
    Input(const Data::Scope& s,Data::Plan p,Data::Resolved d):before(s),plan(std::move(p)),data(std::move(d)) {}
};
}
struct SharedNativeBattleCommandData::State {
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<Connection> connection;
    const Lease lease;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const Configuration configuration;
    std::optional<Groups::Token> registered;
    std::shared_ptr<Input> input;
    bool operating=false,terminal=false;
    State(const std::shared_ptr<Connection>& c,const Lease& l,std::shared_ptr<SharedNativeWorldTransports> t,Configuration cfg)
        :connection(c),lease(l),transports(std::move(t)),configuration(std::move(cfg)) {}
    ~State() {
        if(thread!=std::this_thread::get_id())std::terminate();
        terminal=true;operating=true;input.reset();
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN battle data game owner mismatch");
    }
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s) {
            state.owner();if(state.operating) {state.terminal=true;throw std::logic_error("CN battle data reentry rejected");}
            state.operating=true;
        }
        ~Operation(){if(state.terminal)state.input.reset();state.operating=false;}
    };
    bool endpoint(const std::shared_ptr<Connection>& c,const Scope& scope) const {
        return !terminal && c && connection.lock()==c && !c->closing() &&
            c->role()==Connection::Transport::Role::World && c->world_admission_current() &&
            c->world_session_id()==lease.session && c->verified_account_id()==lease.account && c->world_character_offered(lease.character) &&
            scope.lease==lease && scope.character.id==lease.character && scope.character.account_id==lease.account &&
            scope.native_token.lease()==lease && registered && transports->same_registration(*registered,scope.native_token) &&
            transports->registry_current(scope.native_token);
    }
    bool fence(const std::shared_ptr<Connection>& c,const Scope& scope) const {
        // Existing command Source supplies complete common-root/position
        // pre/post snapshots. This adapter qualifies actual retained resources.
        return endpoint(c,scope) && transports->current(scope.native_token) && endpoint(c,scope);
    }
    bool acquire(const std::shared_ptr<Connection>& c,const Scope& scope) {
        if(!c || connection.lock()!=c || scope.lease!=lease || scope.native_token.lease()!=lease)return false;
        if(!registered) {
            const auto found=transports->lookup(lease);if(!found)return false;
            const auto actual=std::get_if<std::shared_ptr<Connection>>(&found->transport());
            if(!actual || *actual!=c || !transports->same_registration(found->token(),scope.native_token))return false;
            registered=scope.native_token;
        }
        return fence(c,scope);
    }
    bool catalog_current(const std::shared_ptr<Connection>& c,const Scope& scope) const {
        if(!fence(c,scope) || !configuration.authority->catalog_current(*c,scope,configuration.catalog) || !fence(c,scope))return false;
        return configuration.catalog.skills->current() && fence(c,scope);
    }
    bool retained(const Input& original,std::span<const Request> requests,const Scope& scope,const Plan& plan) const {
        if(original.before.lease!=scope.lease || !transports->same_registration(original.before.native_token,scope.native_token) ||
           !same_plan(original.plan,plan) || original.data.rows.size()!=requests.size())return false;
        for(std::size_t i=0;i<requests.size();++i)if(original.data.rows[i].request!=requests[i])return false;
        return true;
    }
    std::optional<Resolved> resolve(const std::shared_ptr<Connection>& c,const Scope& scope,std::span<const Request> requests) const {
        if(requests.empty() || requests.size()>configuration.budgets.max_requests || !catalog_current(c,scope))return {};
        auto domains=configuration.authority->domains(*c,scope,requests);
        if(!domains || domains->size()!=requests.size() || !fence(c,scope))return {};
        Resolved result;result.rows.reserve(requests.size());
        const bool needs_inventory=std::find(domains->begin(),domains->end(),Domain::Item)!=domains->end();
        if(needs_inventory) {
            result.inventory=configuration.inventory->read(*c,scope);
            if(!result.inventory || result.inventory->lease!=lease ||
               result.inventory->cells.size()>configuration.budgets.max_inventory_records || !fence(c,scope))return {};
            if(!configuration.inventory->current(*c,scope,*result.inventory,nullptr) || !fence(c,scope))return {};
        }
        for(std::size_t i=0;i<requests.size();++i) {
            const auto& request=requests[i];const auto domain=(*domains)[i];
            Row row{request,domain,{},{},{},{},{}};
            if(domain==Domain::Skill) {
                const auto kind=request.raw_command_kind();
                // Four independently qualified native branches, not generic80 masking.
                if((kind!=0x03 && kind!=0x17 && kind!=0x83 && kind!=0x97) || request.operand()>0xffff)return {};
                if(!catalog_current(c,scope))return {};
                const auto word=std::uint16_t(request.operand());
                if(configuration.skill_selection) {
                    const auto& selection=*configuration.skill_selection;
                    // Retain the actual producer/list incarnation, not an
                    // equal key searched in a different actor or later list.
                    const auto native=selection.read(*c,scope,request);
                    if(!native || !catalog_current(c,scope))return {};
                    row.native_skill_selection=selection.source->resolve(*native);
                    if(!row.native_skill_selection || !catalog_current(c,scope))return {};
                    const auto actual=selection.source->selected(*row.native_skill_selection,request.operand());
                    if(!actual || !catalog_current(c,scope))return {};
                    row.skill=actual->definition;
                }else {
                    // Actual common learned/actor/source authority remains
                    // mandatory; definition existence alone grants nothing.
                    row.skill=configuration.catalog.skills->lookup(std::uint8_t(word>>8),std::uint8_t(word));
                }
                if(!row.skill || !fence(c,scope))return {};
                row.skill_fields=god2cn::CnBattleSkillDefinition::read_raw(row.skill->raw_record);
                if(!row.skill_fields || row.skill_fields->raw_key_word()!=word)return {};
            }else if(domain==Domain::Item) {
                const auto operand=request.operand();const auto slot=std::uint8_t(operand>>24);
                if((request.raw_command_kind()!=0x05 && request.raw_command_kind()!=0x0c) ||
                   (operand&0x00ff0000u)!=0 || slot>=0x80 || !god2cn::CnBattleInventorySlot::getter_slot_domain(slot))return {};
                const auto found=result.inventory->cells.find(slot);
                if(found==result.inventory->cells.end() || !found->second.raw_item_word() ||
                   found->second.raw_item_word()!=std::uint16_t(operand))return {};
                row.inventory_slot=slot;row.item=found->second;
                // Preserve quantity exactly; no count cap, consume amount or
                // slot30..37 scan/selectedbyte29 repair is synthesized here.
            }else if(domain!=Domain::Opaque)return {};
            result.rows.push_back(std::move(row));
        }
        if(result.inventory) {
            const auto again=configuration.inventory->read(*c,scope);
            if(!again || !fence(c,scope) || !same_inventory(*result.inventory,*again) ||
               !configuration.inventory->current(*c,scope,*result.inventory,nullptr) || !fence(c,scope))return {};
        }
        return catalog_current(c,scope)?std::optional{std::move(result)}:std::nullopt;
    }
    bool resources_current(const std::shared_ptr<Connection>& c,const Scope& scope,const Input& retained,const Result* actual) const {
        if(!catalog_current(c,scope))return false;
        for(const auto& row:retained.data.rows)if(row.skill) {
            if(row.native_skill_selection) {
                if(!configuration.skill_selection ||
                   !configuration.skill_selection->source->current(*row.native_skill_selection) ||
                   !catalog_current(c,scope))return false;
                const auto selected=configuration.skill_selection->source->selected(
                    *row.native_skill_selection,row.request.operand());
                if(!selected || selected->definition!=*row.skill || !catalog_current(c,scope))return false;
            }
            const auto found=configuration.catalog.skills->lookup(std::uint8_t(row.skill->kind),std::uint8_t(row.skill->definition_id));
            if(!found || *found!=*row.skill || !fence(c,scope))return false;
        }
        if(retained.data.inventory && (!configuration.inventory->current(*c,scope,*retained.data.inventory,actual) || !fence(c,scope)))
            return false;
        return catalog_current(c,scope);
    }
};
SharedNativeBattleCommandData::SharedNativeBattleCommandData(std::shared_ptr<State> state):state_(std::move(state)) {}
SharedNativeBattleCommandData::~SharedNativeBattleCommandData(){state_->owner();}
std::shared_ptr<SharedNativeBattleCommandData> SharedNativeBattleCommandData::create(const std::shared_ptr<Connection>& connection,
    const Lease& lease,std::shared_ptr<SharedNativeWorldTransports> transports,Configuration config) {
    if(!connection || !lease.session || !lease.account || !lease.character || !lease.generation || !transports ||
       !config.catalog.skills || !config.catalog.shared_reader || !config.catalog.actual_store_lifetime || !config.inventory ||
       !config.authority || !config.budgets.max_requests || !config.budgets.max_inventory_records)
        throw std::invalid_argument("CN battle data requires actual bound catalog lifetime/inventory/authority/budgets");
    if(config.skill_selection && (!config.skill_selection->source || !config.skill_selection->read ||
       !config.skill_selection->source->owns_catalog(config.catalog.skills)))
        throw std::invalid_argument("CN battle skill selection requires the same actual catalog and source reader");
    return std::shared_ptr<SharedNativeBattleCommandData>(new SharedNativeBattleCommandData(
        std::make_shared<State>(connection,lease,std::move(transports),std::move(config))));
}
std::optional<SharedNativeBattleCommandData::Plan> SharedNativeBattleCommandData::prepare(Connection& receiver,const Scope& scope,
    const Request& request,std::span<const Request> saved,const Plan* saved_plan) {
    State::Operation operation(*state_);
    try {
        const auto c=state_->connection.lock();
        if(!c || c.get()!=&receiver || !state_->acquire(c,scope) || saved.size()>=state_->configuration.budgets.max_requests) {
            state_->terminal=true;return {};
        }
        // Own all requests before any domain/resource callback; saved physical
        // continuations are never deduplicated, normalized or silently omitted.
        std::vector<Request> complete(saved.begin(),saved.end());complete.push_back(request);
        auto data=state_->resolve(c,scope,complete);if(!data) {state_->terminal=true;return {};}
        if(!state_->configuration.authority->current(*c,Check::BeforeExecute,scope,saved_plan,*data,state_->configuration.catalog,nullptr) ||
           !state_->fence(c,scope)) {state_->terminal=true;return {};}
        auto plan=state_->configuration.authority->prepare(*c,scope,*data,saved_plan);
        if(!plan || !state_->fence(c,scope)) {state_->terminal=true;return {};}
        state_->input=std::make_shared<Input>(scope,*plan,std::move(*data));
        return plan;
    }catch(...) {state_->terminal=true;throw;}
}
bool SharedNativeBattleCommandData::current(Connection& receiver,Check check,const Scope& scope,const Request& request,
    const Plan& plan,std::span<const Request> complete,const Result* actual) {
    State::Operation operation(*state_);
    try {
        const auto c=state_->connection.lock();const auto retained=state_->input;
        if(!c || c.get()!=&receiver || !retained || complete.empty() || complete.back()!=request ||
           !state_->retained(*retained,complete,scope,plan) || !state_->resources_current(c,scope,*retained,actual)) {
            state_->terminal=true;return false;
        }
        const bool valid=state_->configuration.authority->current(*c,check,scope,&plan,retained->data,state_->configuration.catalog,actual) &&
            state_->resources_current(c,scope,*retained,actual);
        if(!valid)state_->terminal=true;
        return valid;
    }catch(...) {state_->terminal=true;throw;}
}
std::optional<SharedNativeBattleCommandData::Result> SharedNativeBattleCommandData::execute_group(Connection& receiver,
    const Scope& scope,std::span<const Request> complete,const Plan& plan) {
    State::Operation operation(*state_);
    try {
        const auto c=state_->connection.lock();const auto retained=state_->input;
        if(!c || c.get()!=&receiver || !retained || retained->executed || plan.part==Groups::Part::Append ||
           !state_->retained(*retained,complete,scope,plan) || !state_->resources_current(c,scope,*retained,nullptr)) {
            state_->terminal=true;return {};
        }
        retained->executed=true; // Consumed before real settlement; never reset or replayed.
        auto result=state_->configuration.authority->execute_group(*c,scope,plan,retained->data);
        if(!result || !state_->fence(c,scope)) {state_->terminal=true;return {};}
        return result; // Group retains exact actual result in its private receipt.
    }catch(...) {state_->terminal=true;throw;}
}
}
