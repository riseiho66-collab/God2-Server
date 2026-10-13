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
bool has_shared_skill(const Data::Resolved& data) {
    return std::any_of(data.rows.begin(),data.rows.end(),[](const auto& row){return row.domain==Data::Domain::Skill;});
}
bool same_group_identity(const Data::Plan& a,const Data::Plan& b) {
    return same_cap(a.issuer,b.issuer) && same_cap(a.group,b.group) &&
        a.actual_issuer_generation==b.actual_issuer_generation && a.actual_group_generation==b.actual_group_generation;
}
bool same_selection_values(const CnBattleSkillSelectionSource::Snapshot& a,
    const CnBattleSkillSelectionSource::Snapshot& b) {
    const auto& x=a.native();const auto& y=b.native();
    if(x.scope()!=y.scope() || x.selected_path()!=y.selected_path() || x.selector()!=y.selector() ||
       x.raw_signed_index()!=y.raw_signed_index() || !same_cap(x.catalog(),y.catalog()) ||
       !std::equal(x.component_bytes().begin(),x.component_bytes().end(),y.component_bytes().begin(),y.component_bytes().end()) ||
       !std::equal(x.bank_bytes().begin(),x.bank_bytes().end(),y.bank_bytes().begin(),y.bank_bytes().end()) ||
       !std::equal(x.index_bytes().begin(),x.index_bytes().end(),y.index_bytes().begin(),y.index_bytes().end()) ||
       !std::equal(x.flag_bytes().begin(),x.flag_bytes().end(),y.flag_bytes().begin(),y.flag_bytes().end()) ||
       !std::equal(x.entries().begin(),x.entries().end(),y.entries().begin(),y.entries().end()) ||
       a.entries().size()!=b.entries().size())return false;
    for(std::size_t i=0;i<a.entries().size();++i)
        if(a.entries()[i].native!=b.entries()[i].native || a.entries()[i].definition!=b.entries()[i].definition)return false;
    return true; // Value/source equality only; never claims equal private Storage.
}
bool same_prefix_row(const Data::Row& a,const Data::Row& b) {
    if(a.request!=b.request || a.domain!=b.domain || a.skill!=b.skill || a.skill_fields!=b.skill_fields ||
       a.common_definition!=b.common_definition || a.inventory_slot!=b.inventory_slot ||
       bool(a.item)!=bool(b.item) || bool(a.native_skill_selection)!=bool(b.native_skill_selection))return false;
    if(a.item && !std::equal(a.item->raw_bytes().begin(),a.item->raw_bytes().end(),
        b.item->raw_bytes().begin(),b.item->raw_bytes().end()))return false;
    return !a.native_skill_selection || same_selection_values(*a.native_skill_selection,*b.native_skill_selection);
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
                std::optional<SharedSkillLookup> common;
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
                    common=configuration.catalog.skills->lookup_shared(
                        std::uint8_t(actual->definition.kind),std::uint8_t(actual->definition.definition_id));
                    if(!common || !common->requested_native ||
                       *common->requested_native!=actual->definition || !catalog_current(c,scope))return {};
                }else {
                    // Actual common learned/actor/source authority remains
                    // mandatory; definition existence alone grants nothing.
                    common=configuration.catalog.skills->lookup_shared(std::uint8_t(word>>8),std::uint8_t(word));
                }
                if(!common || !common->requested_native || !fence(c,scope))return {};
                // Original requested-native CN row stays separate from the
                // owner-selected complete common profile, names and formal rules.
                row.skill=std::move(*common->requested_native);
                row.common_definition=std::move(common->definition);
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
        // Domains/inventory/later row observers may change a TW counterpart
        // without changing the qualified CN453 bank. Keep the captured value;
        // never replace it with a newer definition to make a check succeed.
        return resolved_resources_current(c,scope,result,nullptr)?std::optional{std::move(result)}:std::nullopt;
    }
    bool resolved_resources_current(const std::shared_ptr<Connection>& c,const Scope& scope,
        const Resolved& supplied,const Result* actual) const {
        const auto data=supplied; // Own all argument values before any observer.
        if(!catalog_current(c,scope))return false;
        for(const auto& row:data.rows)if(row.skill) {
            if(row.native_skill_selection) {
                if(!configuration.skill_selection ||
                   !configuration.skill_selection->source->current(*row.native_skill_selection) ||
                   !catalog_current(c,scope))return false;
                const auto selected=configuration.skill_selection->source->selected(
                    *row.native_skill_selection,row.request.operand());
                if(!selected || selected->definition!=*row.skill || !catalog_current(c,scope))return false;
            }
            const auto found=configuration.catalog.skills->lookup_shared(
                std::uint8_t(row.skill->kind),std::uint8_t(row.skill->definition_id));
            if(!found || !found->requested_native || *found->requested_native!=*row.skill ||
               !row.common_definition || found->definition!=*row.common_definition || !fence(c,scope))return false;
        }
        if(data.inventory && (!configuration.inventory->current(*c,scope,*data.inventory,actual) || !fence(c,scope)))
            return false;
        return catalog_current(c,scope);
    }
    bool resources_current(const std::shared_ptr<Connection>& c,const Scope& scope,
        const Input& retained,const Result* actual) const {
        return resolved_resources_current(c,scope,retained.data,actual);
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
        // Own old arguments and Input before acquire/domains/resource observers.
        const std::vector<Request> prefix(saved.begin(),saved.end());
        const std::optional<Plan> old_plan=saved_plan ? std::optional{*saved_plan} : std::nullopt;
        const auto prior=state_->input;
        const bool prior_shared=!prefix.empty() && prior && has_shared_skill(prior->data);
        const auto c=state_->connection.lock();
        const auto old_prefix_current=[&] {
            if(prefix.empty())return !old_plan; // Never borrow a consumed Single as pending.
            return old_plan && prior && state_->input==prior && !prior->executed &&
                prior->plan.part==Groups::Part::Append && state_->retained(*prior,prefix,scope,*old_plan) &&
                state_->resources_current(c,scope,*prior,nullptr) && state_->input==prior && !state_->terminal;
        };
        if(!c || c.get()!=&receiver || !state_->acquire(c,scope) || prefix.size()>=state_->configuration.budgets.max_requests ||
           (prior_shared && !old_prefix_current())) {
            state_->terminal=true;return {};
        }
        // Own all requests before any domain/resource callback; saved physical
        // continuations are never deduplicated, normalized or silently omitted.
        std::vector<Request> complete(prefix.begin(),prefix.end());complete.push_back(request);
        auto data=state_->resolve(c,scope,complete);
        if(!data) {state_->terminal=true;return {};}
        const bool shared_group=prior_shared || has_shared_skill(*data);
        const auto prefix_stable=[&] {
            if(!shared_group)return true; // Pure Item/Opaque groups keep their old policy.
            if(!old_prefix_current() || !state_->resolved_resources_current(c,scope,*data,nullptr))return false;
            if(!prefix.empty()) {
                if(prior->data.rows.size()!=prefix.size() || data->rows.size()<=prefix.size())return false;
                for(std::size_t i=0;i<prefix.size();++i)
                    if(!same_prefix_row(prior->data.rows[i],data->rows[i]))return false;
            }
            return !state_->terminal && state_->input==prior;
        };
        if(!prefix_stable()) {state_->terminal=true;return {};}
        if(shared_group && !prefix.empty()) {
            // Newly resolved equal values do not create the old private native
            // selection holder. Retain every OLD prefix Row/capability instead.
            // Inventory validity stays with both actual Current policies and
            // the used prefix cells; no new whole-bank equality rule is added.
            for(std::size_t i=0;i<prefix.size();++i)data->rows[i]=prior->data.rows[i];
        }
        if(!state_->resolved_resources_current(c,scope,*data,nullptr) || !prefix_stable() ||
           !state_->configuration.authority->current(*c,Check::BeforeExecute,scope,old_plan ? &*old_plan : nullptr,
               *data,state_->configuration.catalog,nullptr) ||
           !state_->resolved_resources_current(c,scope,*data,nullptr) || !prefix_stable()) {state_->terminal=true;return {};}
        auto plan=state_->configuration.authority->prepare(*c,scope,*data,old_plan ? &*old_plan : nullptr);
        if(!plan || !state_->resolved_resources_current(c,scope,*data,nullptr) || !prefix_stable() ||
           (shared_group && !prefix.empty() &&
            ((plan->part!=Groups::Part::Append && plan->part!=Groups::Part::Final) || !same_group_identity(*old_plan,*plan)))) {
            state_->terminal=true;return {};
        }
        auto next=std::make_shared<Input>(scope,*plan,std::move(*data));
        if(shared_group && !old_prefix_current()) {state_->terminal=true;return {};}
        state_->input=std::move(next);
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
