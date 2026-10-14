#include "game/TaiwanNativeActorArgumentSource.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
std::uint8_t selector_value(std::uint32_t value) {
    if(value>127)throw std::invalid_argument("CUSTOM actor selectors exceed native7-bit fields");
    return static_cast<std::uint8_t>(value);
}
}
TaiwanNativeActorArgumentSource::CustomSelectors::CustomSelectors(std::uint32_t first,std::uint32_t second)
    :first_(selector_value(first)),second_(selector_value(second)){}
struct TaiwanNativeActorArgumentSource::Data {
    const TaiwanNativeActorArgumentSource* const owner;
    const std::shared_ptr<const Identity> identity;
    const std::shared_ptr<const SavedInput> saved;
    const std::size_t row;
    const Equipment equipment;
    const std::shared_ptr<const TaiwanNativeActorResourceBank> bank;
    const std::shared_ptr<const TaiwanNativeDrvDoll> tail_bank;
    const Origin origin;
    const std::uint8_t first,second,act_type;
    const std::array<Lookup,4> lookups;
    const Lookup head;
    const std::uint8_t sixth,modifier;
    Data(const TaiwanNativeActorArgumentSource* issuer,std::shared_ptr<const Identity> key,
        std::shared_ptr<const SavedInput> input,std::size_t index,Equipment eq,
        std::shared_ptr<const TaiwanNativeActorResourceBank> resource_bank,
        std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll,Origin source_origin,
        std::uint8_t a,std::uint8_t b,std::uint8_t type,std::array<Lookup,4> arguments,
        Lookup head_lookup,std::uint8_t foot_sixth,std::uint8_t foot_value)
        :owner(issuer),identity(std::move(key)),saved(std::move(input)),row(index),equipment(std::move(eq)),
         bank(std::move(resource_bank)),tail_bank(std::move(drv_doll)),origin(source_origin),
         first(a),second(b),act_type(type),lookups(std::move(arguments)),head(head_lookup),
         sixth(foot_sixth),modifier(foot_value){}
};
struct TaiwanNativeActorArgumentSource::Operation {
    const TaiwanNativeActorArgumentSource& owner;
    explicit Operation(const TaiwanNativeActorArgumentSource& value):owner(value) {
        if(owner.thread_!=std::this_thread::get_id())throw std::logic_error("Actor arguments game owner mismatch");
        if(owner.busy_){owner.poisoned_=true;throw std::logic_error("Actor arguments reentered");}
        if(owner.stopped_||owner.poisoned_)throw std::logic_error("Actor arguments retired");
        owner.busy_=true;
    }
    ~Operation(){owner.busy_=false;}
};
TaiwanNativeActorArgumentSource::TaiwanNativeActorArgumentSource(std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<const TaiwanNativeActorResourceBank> bank,std::shared_ptr<const TaiwanNativeDrvDoll> tail)
    :presence_(std::move(presence)),bank_(std::move(bank)),drv_doll_bank_(std::move(tail)){}
std::shared_ptr<TaiwanNativeActorArgumentSource> TaiwanNativeActorArgumentSource::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
    std::shared_ptr<const TaiwanNativeDrvDoll> tail) {
    if(!presence||!bank||!tail)return {};
    return std::shared_ptr<TaiwanNativeActorArgumentSource>(new TaiwanNativeActorArgumentSource(
        std::move(presence),std::move(bank),std::move(tail)));
}
TaiwanNativeActorArgumentSource::~TaiwanNativeActorArgumentSource() {
    if(thread_!=std::this_thread::get_id())std::terminate();stopped_=true;
}
bool TaiwanNativeActorArgumentSource::retained(const Data& data) const noexcept {
    if(thread_!=std::this_thread::get_id()||stopped_||poisoned_||data.owner!=this||data.identity!=identity_||
       data.bank!=bank_||data.tail_bank!=drv_doll_bank_||!data.saved||!data.saved->source()||
       !data.saved->source()->owns_presence(presence_)||!data.saved->source()->owns_readset(data.saved->readset())||
       !data.saved->source()->profile_equipment_matches(data.equipment,data.saved->readset(),data.row)||
       data.row>=data.saved->readset().materials().size()||data.first>127||data.second>127||data.act_type>=3||
       !data.tail_bank->find(data.first)||!data.bank->find_drv(data.second)||
       !data.saved->readset().matches_population(data.saved->population().characters()))return false;
    try{return presence_->retained_population_current(data.saved->population());}catch(...){return false;}
}
bool TaiwanNativeActorArgumentSource::owns_observation(const Observation& observation) const noexcept {
    return observation.data_&&retained(*observation.data_);
}
bool TaiwanNativeActorArgumentSource::matches_inputs(const Observation& observation,
    const std::shared_ptr<const SavedInput>& input,std::size_t row,const Equipment& equipment) const noexcept {
    return owns_observation(observation)&&observation.data_->saved==input&&observation.data_->row==row&&
        observation.data_->equipment==equipment;
}
bool TaiwanNativeActorArgumentSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& value) const noexcept {
    return thread_==std::this_thread::get_id()&&!stopped_&&!poisoned_&&value==presence_;
}
bool TaiwanNativeActorArgumentSource::owns_resource_bank(const std::shared_ptr<const TaiwanNativeActorResourceBank>& value) const noexcept {
    return thread_==std::this_thread::get_id()&&!stopped_&&!poisoned_&&value==bank_;
}
bool TaiwanNativeActorArgumentSource::owns_drv_doll_bank(const std::shared_ptr<const TaiwanNativeDrvDoll>& value) const noexcept {
    return thread_==std::this_thread::get_id()&&!stopped_&&!poisoned_&&value==drv_doll_bank_;
}
std::optional<TaiwanNativeActorArgumentSource::Observation> TaiwanNativeActorArgumentSource::observe(
    std::shared_ptr<const SavedInput> input,std::size_t row,const Equipment& supplied_equipment,
    std::optional<CustomSelectors> selectors) const {
    Operation operation(*this);
    // Check game ownership before owner members; own inputs before observers.
    const auto equipment=supplied_equipment;const auto bank=bank_;const auto tail=drv_doll_bank_;
    if(!input||!input->source()||row>=input->readset().materials().size()||
       !input->source()->owns_presence(presence_)||!input->source()->owns_readset(input->readset())||
       !input->source()->profile_equipment_matches(equipment,input->readset(),row)||
       !input->readset().matches_population(input->population().characters())||
       !presence_->retained_population_current(input->population()))return {};
    const auto material=input->readset().materials()[row];
    const auto da=equipment.equipment().appearance();if(!da||da->transform_key()!=0)return {};
    std::array<std::uint8_t,8> packed{};std::copy(da->components().begin(),da->components().end(),packed.begin());
    std::uint8_t first=0,second=0;Origin origin=Origin::CurrentSavedWorldWitness;
    if(selectors){first=selectors->first_selector();second=selectors->second_selector();origin=Origin::Custom0133Selectors;}
    else {
        if(!material.world||!NativeWorldEntrySnapshot::same_root(material.world->root,material.actor.character)||
           material.world->position!=material.actor.position||material.world->record.size()!=RecoveredWorldEntry::Frame{}.size())return {};
        RecoveredWorldEntry::Frame frame;std::copy(material.world->record.begin(),material.world->record.end(),frame.begin());
        const auto world=RecoveredWorldEntryView::read(frame);
        if(!world||world->actor_handle!=material.actor.lease.actor_handle||world->area!=material.actor.position.area||
           world->scene!=material.actor.position.scene||world->x!=material.actor.position.x||world->y!=material.actor.position.y)return {};
        const auto selected=world->entry_resource_selectors();first=selected.drv_doll_selector;second=selected.drv_selector;
    }
    // Actual46995B/469962 call: formal1/BP==header second (full Drv ordinal),
    // formal2==header first (independent136B DrvDoll row). Never a cache ID.
    if(first>127||second>127)return {};
    const auto* drv=bank->find_drv(second);if(!drv||drv->act_type>=3||!tail->find(first))return {};
    const auto type=static_cast<std::uint8_t>(drv->act_type);
    std::array<Lookup,4> arguments{};
    for(std::size_t slot=0;slot<4;++slot)arguments[slot]={static_cast<std::uint8_t>(packed[2*slot]&15),
        static_cast<TaiwanNativeActorResourceBank::Component>(slot),static_cast<std::uint8_t>(packed[2*slot]>>4),
        static_cast<std::uint8_t>(packed[2*slot+1]&31),type};
    // 4612A8 signed BP>0 ordinary branch fixes only Weapon category/variant.
    // Zero BP still resolves all four components and the actual Drv0 ActType.
    if(second>0){arguments[3].component_index=8;arguments[3].variant=0;}
    const auto head=arguments[2];const auto sixth=static_cast<std::uint8_t>(packed[3]&31);
    const auto modifier=bank->native_component_modifier(head,sixth);if(!modifier)return {};
    arguments[1].variant=*modifier;
    for(const auto& argument:arguments)if(!bank->find_hero(argument))return {};
    // Allocate immutable custody before the final qualified saved cut.
    auto data=std::make_shared<const Data>(this,identity_,input,row,equipment,bank,tail,origin,
        first,second,type,arguments,head,sixth,*modifier);
    const std::array<Equipment,1> profiles{equipment};
    if(!input->source()->current_with_role_text(input->readset(),{}, {}, {},profiles)||poisoned_||
       !presence_->retained_population_current(input->population()))return {};
    if(!retained(*data))return {};
    return Observation(std::move(data));
}
bool TaiwanNativeActorArgumentSource::current(const Observation& supplied) const {
    const auto observation=supplied;Operation operation(*this);
    if(!observation.data_||!retained(*observation.data_))return false;
    const auto& data=*observation.data_;const std::array<Equipment,1> profiles{data.equipment};
    if(!data.saved->source()->current_with_role_text(data.saved->readset(),{}, {}, {},profiles))return false;
    return retained(data);
}
const std::shared_ptr<const TaiwanNativeActorArgumentSource::SavedInput>& TaiwanNativeActorArgumentSource::Observation::saved_input() const noexcept{return data_->saved;}
std::size_t TaiwanNativeActorArgumentSource::Observation::row_index() const noexcept{return data_->row;}
const TaiwanNativeActorArgumentSource::Equipment& TaiwanNativeActorArgumentSource::Observation::equipment() const noexcept{return data_->equipment;}
std::uint8_t TaiwanNativeActorArgumentSource::Observation::first_selector() const noexcept{return data_->first;}
std::uint8_t TaiwanNativeActorArgumentSource::Observation::second_selector() const noexcept{return data_->second;}
std::uint32_t TaiwanNativeActorArgumentSource::Observation::full_drv_ordinal() const noexcept{return data_->second;}
std::uint8_t TaiwanNativeActorArgumentSource::Observation::act_type() const noexcept{return data_->act_type;}
const std::array<TaiwanNativeActorArgumentSource::Lookup,4>& TaiwanNativeActorArgumentSource::Observation::lookups() const noexcept{return data_->lookups;}
const std::shared_ptr<const TaiwanNativeActorResourceBank>& TaiwanNativeActorArgumentSource::Observation::bank() const noexcept{return data_->bank;}
const std::shared_ptr<const TaiwanNativeDrvDoll>& TaiwanNativeActorArgumentSource::Observation::drv_doll_bank() const noexcept{return data_->tail_bank;}
TaiwanNativeActorArgumentSource::Origin TaiwanNativeActorArgumentSource::Observation::origin() const noexcept{return data_->origin;}
const TaiwanNativeDrvDoll::Record& TaiwanNativeActorArgumentSource::Observation::actual_tail_source() const noexcept{return *data_->tail_bank->find(data_->first);}
const TaiwanNativeActorArgumentSource::Lookup& TaiwanNativeActorArgumentSource::Observation::head_modifier_lookup() const noexcept{return data_->head;}
std::uint8_t TaiwanNativeActorArgumentSource::Observation::foot_sixth_argument() const noexcept{return data_->sixth;}
std::uint8_t TaiwanNativeActorArgumentSource::Observation::foot_modifier() const noexcept{return data_->modifier;}
}
