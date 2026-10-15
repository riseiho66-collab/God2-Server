#include "game/TaiwanNativeActorResourceSource.h"
#include <exception>
#include <ios>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
using Bank=TaiwanNativeActorResourceBank;
using Tail=TaiwanNativeDrvDoll;
bool same_lookup(const Bank::HeroLookup& a,const Bank::HeroLookup& b) noexcept {
    return a.family==b.family&&a.component==b.component&&a.component_index==b.component_index&&
        a.variant==b.variant&&a.act_type==b.act_type;
}
bool same_context(const Bank::NativeRomContext& a,const Bank::NativeRomContext& b) {
    return a.actual_52f550_root==b.actual_52f550_root&&a.actual_model_prefix==b.actual_model_prefix&&
        a.actual_working_directory==b.actual_working_directory&&a.actual_manager_bank_operand==b.actual_manager_bank_operand;
}
bool same_context(const Tail::NativeRomContext& a,const Tail::NativeRomContext& b) {
    return a.actual_52f550_root==b.actual_52f550_root&&
        a.actual_working_directory==b.actual_working_directory&&a.actual_manager_bank_operand==b.actual_manager_bank_operand;
}
bool same_request(const TaiwanNativeResourceSelection::Request& a,const TaiwanNativeResourceSelection::Request& b) {
    return a.kind==b.kind&&a.original_reference==b.original_reference&&a.native_prefix==b.native_prefix&&
        a.actual_working_directory==b.actual_working_directory&&a.full_bank_operand==b.full_bank_operand;
}
bool same_selection(const TaiwanNativeResourceSelection& a,const TaiwanNativeResourceSelection& b) {
    return same_request(a.request(),b.request())&&a.request_bytes()==b.request_bytes()&&
        a.candidate_bytes()==b.candidate_bytes()&&a.candidate_source()==b.candidate_source()&&
        a.actual_source()==b.actual_source()&&a.candidate_original()==b.candidate_original()&&
        a.encoded_bytes()==b.encoded_bytes()&&a.probe()==b.probe()&&a.branch()==b.branch();
}
}
TaiwanNativeActorResourceSource::Configuration::Configuration(std::array<NativeRomContext,4> input_contexts,
    std::array<std::uint32_t,4> actions,std::size_t encoded_bound,std::size_t plain_bound,Scope source_scope,
    std::optional<TaiwanNativeActorArgumentSource::CustomSelectors> input_selectors,std::optional<DrvRom> input_drv,
    std::optional<TailRom> input_tail)
    :contexts(std::move(input_contexts)),full_actions(actions),max_encoded_bytes(encoded_bound),
     max_plain_bytes(plain_bound),scope(source_scope),selectors(std::move(input_selectors)),drv(std::move(input_drv)),
     tail(std::move(input_tail)) {
    if(!encoded_bound||!plain_bound||encoded_bound>=static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max())||
       (scope!=Scope::CurrentServerImmutableAssetGeneration&&scope!=Scope::WholePhysicalSelection))
        throw std::invalid_argument("Actor resource configuration lacks explicit supported bounds/scope");
}
struct TaiwanNativeActorResourceSource::Data {
    const TaiwanNativeActorResourceSource* const owner;
    const std::shared_ptr<const Identity> identity;
    const std::size_t slot;
    const std::uint64_t epoch;
    const std::shared_ptr<const SavedInput> input;
    const std::size_t row;
    const Equipment equipment;
    const TaiwanNativeActorArgumentSource::Observation arguments;
    const std::vector<TaiwanCustomFullActorProfile::ComponentRom> components;
    const std::shared_ptr<const Bank::ResolvedRom> drv;
    const std::shared_ptr<const Tail::ResolvedRom> tail;
    const Scope scope;
    Data(const TaiwanNativeActorResourceSource* issuer,std::shared_ptr<const Identity> key,std::size_t index,
        std::uint64_t generation,std::shared_ptr<const SavedInput> saved,std::size_t actor_row,Equipment eq,
        TaiwanNativeActorArgumentSource::Observation args,std::vector<TaiwanCustomFullActorProfile::ComponentRom> resources,
        std::shared_ptr<const Bank::ResolvedRom> drv_resource,std::shared_ptr<const Tail::ResolvedRom> tail_resource,
        Scope source_scope)
        :owner(issuer),identity(std::move(key)),slot(index),epoch(generation),input(std::move(saved)),
        row(actor_row),equipment(std::move(eq)),arguments(std::move(args)),components(std::move(resources)),
        drv(std::move(drv_resource)),tail(std::move(tail_resource)),scope(source_scope){}
};
struct TaiwanNativeActorResourceSource::CurrentCarrier {
    const std::shared_ptr<const TaiwanNativeActorResourceSource> source;
    const std::shared_ptr<const Data> data;
    bool operator()(TaiwanCustomFullActorProfile::Check check,const ResourceInput& input) const {
        if(check!=TaiwanCustomFullActorProfile::Check::Prepare&&check!=TaiwanCustomFullActorProfile::Check::Retained&&
           check!=TaiwanCustomFullActorProfile::Check::Consumed)return false;
        return source&&data&&source->current_for(input,data);
    }
};
struct TaiwanNativeActorResourceSource::Operation {
    const TaiwanNativeActorResourceSource& owner;
    explicit Operation(const TaiwanNativeActorResourceSource& value):owner(value) {
        if(owner.thread_!=std::this_thread::get_id())throw std::logic_error("Actor assets game owner mismatch");
        if(owner.busy_){owner.poisoned_=true;throw std::logic_error("Actor assets reentered");}
        if(owner.stopped_||owner.poisoned_)throw std::logic_error("Actor assets retired");
        owner.busy_=true;
    }
    ~Operation(){owner.busy_=false;}
};
TaiwanNativeActorResourceSource::TaiwanNativeActorResourceSource(std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<TaiwanNativeActorArgumentSource> arguments,Configuration configuration)
    :presence_(std::move(presence)),arguments_(std::move(arguments)),configuration_(std::move(configuration)){}
std::shared_ptr<TaiwanNativeActorResourceSource> TaiwanNativeActorResourceSource::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<TaiwanNativeActorArgumentSource> arguments,
    Configuration configuration) {
    if(!presence||!arguments||!arguments->owns_presence(presence))return {};
    return std::shared_ptr<TaiwanNativeActorResourceSource>(new TaiwanNativeActorResourceSource(
        std::move(presence),std::move(arguments),std::move(configuration)));
}
TaiwanNativeActorResourceSource::~TaiwanNativeActorResourceSource() {
    if(thread_!=std::this_thread::get_id())std::terminate();stopped_=true;
}
bool TaiwanNativeActorResourceSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& value) const noexcept {
    return thread_==std::this_thread::get_id()&&!stopped_&&!poisoned_&&value==presence_;
}
bool TaiwanNativeActorResourceSource::owns_argument_source(const std::shared_ptr<TaiwanNativeActorArgumentSource>& value) const noexcept {
    return thread_==std::this_thread::get_id()&&!stopped_&&!poisoned_&&value==arguments_;
}
bool TaiwanNativeActorResourceSource::retained(const Data& data) const noexcept {
    if(thread_!=std::this_thread::get_id()||stopped_||poisoned_||data.owner!=this||data.identity!=identity_||
       data.slot>=cache_.size()||!data.epoch||data.scope!=configuration_.scope||cache_[data.slot].lock().get()!=&data||
       !arguments_->matches_inputs(data.arguments,data.input,data.row,data.equipment)||
       !arguments_->owns_presence(presence_)||data.components.size()!=4)return false;
    try {
        for(std::size_t i=0;i<4;++i){
            const auto& component=data.components[i];if(!same_lookup(component.lookup,data.arguments.lookups()[i]))return false;
            const auto& rom=component.rom;if(!rom)continue;
            const auto& request=rom->native_request();
            if(!request||&request->bank()!=data.arguments.bank().get()||&rom->bank()!=data.arguments.bank().get()||
               request->family()!=Bank::ResolvedRom::Family::Hero||rom->family()!=Bank::ResolvedRom::Family::Hero||
               request->row_ordinal()!=rom->row_ordinal()||!same_context(request->context(),configuration_.contexts[i])||
               !same_request(request->request(),rom->selection().request())||
               rom->full_action_operand()!=configuration_.full_actions[i]||
               !rom->rom().find_action(configuration_.full_actions[i])||rom->rom().images().empty()||
               rom->rom().source()!=rom->selection().actual_source()||
               rom->rom().encoded_bytes()!=rom->selection().encoded_bytes())return false;
        }
        const auto* drv=data.arguments.bank()->find_drv(data.arguments.full_drv_ordinal());
        if(!drv)return false;
        if(drv->filename.empty()){
            if(data.drv)return false;
        }else{
            if(!configuration_.drv||!data.drv)return false;
            const auto& rom=data.drv;const auto& request=rom->native_request();
            if(!(request && &request->bank()==data.arguments.bank().get() && &rom->bank()==data.arguments.bank().get() &&
                request->family()==Bank::ResolvedRom::Family::Drv&&rom->family()==Bank::ResolvedRom::Family::Drv&&
                request->row_ordinal()==data.arguments.full_drv_ordinal()&&rom->row_ordinal()==data.arguments.full_drv_ordinal()&&
                same_context(request->context(),configuration_.drv->context)&&
                same_request(request->request(),rom->selection().request())&&
                rom->full_action_operand()==configuration_.drv->full_action&&
                rom->rom().find_action(configuration_.drv->full_action)&&!rom->rom().images().empty()&&
                rom->rom().source()==rom->selection().actual_source()&&
                rom->rom().encoded_bytes()==rom->selection().encoded_bytes()))return false;
        }
        // Always qualify the independent136B tail, including an empty ordinary Drv.
        const auto* tail=data.arguments.drv_doll_bank()->find(data.arguments.first_selector());
        if(!tail||tail!=&data.arguments.actual_tail_source())return false;
        if(tail->filename.empty())return !data.tail;
        if(!configuration_.tail||!data.tail)return false;
        const auto& rom=data.tail;const auto& request=rom->native_request();
        return request && &request->bank()==data.arguments.drv_doll_bank().get() && &rom->bank()==data.arguments.drv_doll_bank().get() &&
            request->row_ordinal()==data.arguments.first_selector()&&rom->row_ordinal()==data.arguments.first_selector()&&
            same_context(request->context(),configuration_.tail->context)&&
            same_request(request->request(),rom->selection().request())&&
            rom->full_action_operand()==configuration_.tail->full_action&&
            rom->rom().find_action(configuration_.tail->full_action)&&!rom->rom().images().empty()&&
            rom->rom().source()==rom->selection().actual_source()&&
            rom->rom().encoded_bytes()==rom->selection().encoded_bytes();
    }catch(...){return false;}
}
bool TaiwanNativeActorResourceSource::same_material(const ResourceInput& input,const Data& data) const noexcept {
    if(!retained(data)||input.bank!=data.arguments.bank()||input.drv_doll_bank!=data.arguments.drv_doll_bank()||
       input.epoch!=data.epoch||input.mode!=(data.drv?ResourceInput::Mode::HeroComponentsAndDrv:ResourceInput::Mode::HeroComponents)||
       input.drv!=data.drv||input.tail!=data.tail||
       input.first_selector!=data.arguments.first_selector()||input.second_selector!=data.arguments.second_selector()||
       input.full_drv_ordinal!=data.arguments.full_drv_ordinal()||input.arguments_source!=arguments_||
       !input.arguments||*input.arguments!=data.arguments||input.dependency_owner.get()!=&data||
       input.components.size()!=data.components.size())return false;
    const auto origin=data.arguments.origin()==TaiwanNativeActorArgumentSource::Origin::CurrentSavedWorldWitness?
        ResourceInput::Origin::SavedWorldSelectors:ResourceInput::Origin::Custom0133Explicit;
    if(input.origin!=origin)return false;
    const auto* carrier=input.current.target<CurrentCarrier>();
    if(!carrier||carrier->source.get()!=this||carrier->data.get()!=&data)return false;
    for(std::size_t i=0;i<4;++i)if(!same_lookup(input.components[i].lookup,data.components[i].lookup)||
        input.components[i].rom!=data.components[i].rom)return false;
    return true;
}
bool TaiwanNativeActorResourceSource::physical_current(const Data& data) const {
    if(data.scope==Scope::CurrentServerImmutableAssetGeneration)return retained(data);
    if(data.scope!=Scope::WholePhysicalSelection)return false;
    for(const auto& component:data.components){
        if(!component.rom)continue;
        const auto& original=component.rom->selection();
        const auto selected=TaiwanNativeResourceSelection::select(original.request(),configuration_.max_encoded_bytes);
        if(!selected||!same_selection(*selected,original)||!retained(data))return false;
    }
    if(data.drv){
        const auto& original=data.drv->selection();
        const auto selected=TaiwanNativeResourceSelection::select(original.request(),configuration_.max_encoded_bytes);
        if(!selected||!same_selection(*selected,original)||!retained(data))return false;
    }
    if(data.tail){
        const auto& original=data.tail->selection();
        const auto selected=TaiwanNativeResourceSelection::select(original.request(),configuration_.max_encoded_bytes);
        if(!selected||!same_selection(*selected,original)||!retained(data))return false;
    }
    // Sequential opened-file observations only; not filesystem atomicity.
    return retained(data);
}
bool TaiwanNativeActorResourceSource::qualify_current(const Data& data) const {
    if(!retained(data)||!physical_current(data)||!retained(data))return false;
    // Last observer is the actual joint saved/EQ cut. Assets are immutable
    // owned values (or just wholly reselected); no old NormalINIT is consulted.
    return arguments_->current(data.arguments)&&retained(data);
}
TaiwanNativeActorResourceSource::ResourceInput TaiwanNativeActorResourceSource::material(
    const std::shared_ptr<const Data>& data) const {
    ResourceInput result{};
    result.bank=data->arguments.bank();result.drv_doll_bank=data->arguments.drv_doll_bank();result.epoch=data->epoch;
    result.origin=data->arguments.origin()==TaiwanNativeActorArgumentSource::Origin::CurrentSavedWorldWitness?
        ResourceInput::Origin::SavedWorldSelectors:ResourceInput::Origin::Custom0133Explicit;
    result.mode=data->drv?ResourceInput::Mode::HeroComponentsAndDrv:ResourceInput::Mode::HeroComponents;
    result.drv=data->drv;result.tail=data->tail;result.first_selector=data->arguments.first_selector();
    result.second_selector=data->arguments.second_selector();result.full_drv_ordinal=data->arguments.full_drv_ordinal();
    result.components=data->components;result.arguments_source=arguments_;result.arguments=data->arguments;
    result.dependency_owner=data;result.current=CurrentCarrier{shared_from_this(),data};return result;
}
std::optional<TaiwanNativeActorResourceSource::ResourceInput> TaiwanNativeActorResourceSource::observe(
    std::shared_ptr<const SavedInput> input,std::size_t row,const Equipment& supplied_equipment) const {
    Operation operation(*this);
    const auto equipment=supplied_equipment;const auto configuration=configuration_;
    std::size_t free_slot=cache_.size();
    for(std::size_t i=0;i<cache_.size();++i){
        const auto data=cache_[i].lock();
        if(!data){if(free_slot==cache_.size())free_slot=i;continue;}
        if(data->input==input&&data->row==row&&data->equipment==equipment){
            if(!retained(*data))return {};auto result=material(data);
            if(!same_material(result,*data)||!qualify_current(*data)||!same_material(result,*data))return {};
            return result;
        }
    }
    if(free_slot==cache_.size()||next_epoch_==std::numeric_limits<std::uint64_t>::max())return {};
    const auto arguments=arguments_->observe(input,row,equipment,configuration.selectors);
    if(!arguments||poisoned_)return {};
    const auto& tail=arguments->actual_tail_source();
    if(!tail.filename.empty()&&!configuration.tail)return {};
    const auto* drv=arguments->bank()->find_drv(arguments->full_drv_ordinal());
    if(!drv||(!drv->filename.empty()&&!configuration.drv))return {};
    std::vector<TaiwanCustomFullActorProfile::ComponentRom> components;components.reserve(4);
    for(std::size_t i=0;i<4;++i){
        const auto& lookup=arguments->lookups()[i];const auto* hero=arguments->bank()->find_hero(lookup);
        if(!hero)return {};
        std::shared_ptr<const Bank::ResolvedRom> resolved;
        if(!hero->filename.empty()){
            const auto request=Bank::native_hero_request(arguments->bank(),lookup,configuration.contexts[i]);if(!request)return {};
            const auto selected=TaiwanNativeResourceSelection::select(request->request(),configuration.max_encoded_bytes);if(!selected)return {};
            auto parsed=TaiwanNativeRomAsset::from_selected_resource(selected->actual_source(),selected->encoded_bytes(),configuration.max_plain_bytes);
            if(!parsed||parsed->images().empty()||!parsed->find_action(configuration.full_actions[i]))return {};
            auto rom=std::make_shared<const TaiwanNativeRomAsset>(std::move(*parsed));
            resolved=Bank::bind_native_rom(request,*selected,std::move(rom),configuration.full_actions[i]);if(!resolved)return {};
        }
        components.push_back({lookup,std::move(resolved)});
    }
    std::shared_ptr<const Bank::ResolvedRom> drv_resource;
    if(!drv->filename.empty()){
        const auto request=Bank::native_drv_request(arguments->bank(),arguments->full_drv_ordinal(),configuration.drv->context);
        if(!request)return {};
        const auto selected=TaiwanNativeResourceSelection::select(request->request(),configuration.max_encoded_bytes);if(!selected)return {};
        auto parsed=TaiwanNativeRomAsset::from_selected_resource(selected->actual_source(),selected->encoded_bytes(),configuration.max_plain_bytes);
        if(!parsed||parsed->images().empty()||!parsed->find_action(configuration.drv->full_action))return {};
        auto rom=std::make_shared<const TaiwanNativeRomAsset>(std::move(*parsed));
        drv_resource=Bank::bind_native_rom(request,*selected,std::move(rom),configuration.drv->full_action);if(!drv_resource)return {};
    }
    std::shared_ptr<const Tail::ResolvedRom> tail_resource;
    if(!tail.filename.empty()){
        const auto request=Tail::native_rom_request(arguments->drv_doll_bank(),arguments->first_selector(),configuration.tail->context);
        if(!request)return {};
        const auto selected=TaiwanNativeResourceSelection::select(request->request(),configuration.max_encoded_bytes);if(!selected)return {};
        auto parsed=TaiwanNativeRomAsset::from_selected_resource(selected->actual_source(),selected->encoded_bytes(),configuration.max_plain_bytes);
        if(!parsed||parsed->images().empty()||!parsed->find_action(configuration.tail->full_action))return {};
        auto rom=std::make_shared<const TaiwanNativeRomAsset>(std::move(*parsed));
        tail_resource=Tail::bind_native_rom(request,*selected,std::move(rom),configuration.tail->full_action);if(!tail_resource)return {};
    }
    const auto epoch=next_epoch_++;
    auto data=std::make_shared<const Data>(this,identity_,free_slot,epoch,input,row,equipment,*arguments,
        std::move(components),std::move(drv_resource),std::move(tail_resource),configuration.scope);
    cache_[free_slot]=data;auto result=material(data);
    if(!same_material(result,*data)||!qualify_current(*data)||!same_material(result,*data))return {};
    return result;
}
bool TaiwanNativeActorResourceSource::current(const ResourceInput& supplied) const {
    Operation operation(*this);const auto input=supplied;
    // Arbitrary shared<void> is NEVER cast/dereferenced. Find the installed
    // private node first; matching pointer alone is not sufficient authority.
    for(const auto& slot:cache_){
        const auto data=slot.lock();if(!data||input.dependency_owner.get()!=data.get())continue;
        if(!same_material(input,*data)||!qualify_current(*data))return false;
        return same_material(input,*data);
    }
    return false;
}
bool TaiwanNativeActorResourceSource::current_for(const ResourceInput& supplied,
    const std::shared_ptr<const Data>& expected) const {
    Operation operation(*this);const auto input=supplied;const auto data=expected;
    if(!data||!same_material(input,*data)||!qualify_current(*data))return false;
    return same_material(input,*data);
}
}
