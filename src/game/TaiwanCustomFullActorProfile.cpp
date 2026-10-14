#include "game/TaiwanCustomFullActorProfile.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "text/OwnedCharacterNameText.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <array>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
template<std::size_t N> void word(std::array<std::uint8_t,N>& bytes,std::size_t at,std::uint32_t value) {
    for(unsigned i=0;i<4;++i)bytes[at+i]=static_cast<std::uint8_t>(value>>(8*i));
}
bool bounded_text(std::string_view text) {
    return text.size()<=15&&text.find('\0')==std::string_view::npos;
}
bool session_tuple(const std::shared_ptr<Session>& session,const SharedWorldPresence::Lease& lease) {
    return session&&!session->closing()&&session->id()==lease.session&&
        session->account_id==lease.account&&session->character_id==lease.character;
}
bool rom_row(const std::shared_ptr<const TaiwanNativeActorResourceBank>& bank,
        const std::shared_ptr<const TaiwanNativeActorResourceBank::ResolvedRom>& rom,
        TaiwanNativeActorResourceBank::ResolvedRom::Family family,std::size_t ordinal) {
    if(!rom||&rom->bank()!=bank.get()||rom->family()!=family||rom->row_ordinal()!=ordinal||
       !rom->rom().find_action(rom->full_action_operand()))return false;
    const auto& request=rom->native_request();
    return request&&&request->bank()==bank.get()&&request->family()==family&&request->row_ordinal()==ordinal&&
        request->request().original_reference==rom->selection().request().original_reference&&
        request->request().native_prefix==rom->selection().request().native_prefix&&
        request->request().full_bank_operand==rom->selection().request().full_bank_operand&&
        request->request().actual_working_directory==rom->selection().request().actual_working_directory&&
        rom->rom().source()==rom->selection().actual_source()&&
        rom->rom().encoded_bytes()==rom->selection().encoded_bytes();
}
}
TaiwanCustomFullActorProfile::Policy::Policy(Version version_value,std::uint32_t a,std::uint32_t b,
        std::uint32_t c,std::uint32_t d,std::uint8_t e,std::uint16_t f,std::uint16_t g,std::uint32_t h,std::uint16_t i)
    :version(version_value),word1_unknown(a),word5_unknown(b),opaque9(c),opaque17(d),position_low2(e),
     move_identity_upper(f),move_state_upper(g),move_position_upper(h),remove_identity_upper(i) {
    if(version!=Version::Custom0133FullActorV1||(a&~std::uint32_t{0xfde03000})||
       (b&~std::uint32_t{0xffff80ff})||e>3||(h&~std::uint32_t{0xffc00000}))
        throw std::invalid_argument("CUSTOM full actor policy overlaps qualified fields");
}
struct TaiwanCustomFullActorProfile::Data {
    const TaiwanCustomFullActorProfile* const owner;
    const std::shared_ptr<const Identity> identity;
    const std::shared_ptr<const SavedInput> saved;
    const std::size_t row;
    const Equipment equipment;
    const SourceInput source_input;
    const Lease source,recipient;
    const ReceiverInput receiver;
    const ResourceInput resources;
    const StatusInput status;
    const OwnedTaiwanPkReturnRoleTextSource::Observation role;
    const RecoveredRemoteActor::Record spawn;
    const RecoveredRemoteActorMove::Record movement;
    const RecoveredRemoteActorRemove::Record removal;
    const std::uint64_t revision;
    Data(const TaiwanCustomFullActorProfile* issuer,std::shared_ptr<const Identity> key,
        std::shared_ptr<const SavedInput> input,std::size_t index,Equipment eq,SourceInput source_state,
        Lease source_lease,Lease recipient_lease,ReceiverInput receiver_state,ResourceInput resource_state,
        StatusInput status_state,OwnedTaiwanPkReturnRoleTextSource::Observation text,
        RecoveredRemoteActor::Record actor,RecoveredRemoteActorMove::Record move,
        RecoveredRemoteActorRemove::Record remove,std::uint64_t sequence)
        :owner(issuer),identity(std::move(key)),saved(std::move(input)),row(index),equipment(std::move(eq)),
         source_input(std::move(source_state)),source(std::move(source_lease)),recipient(std::move(recipient_lease)),
         receiver(std::move(receiver_state)),resources(std::move(resource_state)),status(std::move(status_state)),
         role(std::move(text)),spawn(std::move(actor)),movement(std::move(move)),removal(std::move(remove)),revision(sequence){}
};
struct TaiwanCustomFullActorProfile::Operation {
    const TaiwanCustomFullActorProfile& owner;
    explicit Operation(const TaiwanCustomFullActorProfile& value):owner(value) {
        if(owner.thread_!=std::this_thread::get_id())throw std::logic_error("Full actor profile game owner mismatch");
        if(owner.busy_){owner.poisoned_=true;throw std::logic_error("Full actor profile reentered");}
        if(owner.stopped_||owner.poisoned_)throw std::logic_error("Full actor profile retired");
        owner.busy_=true;
    }
    ~Operation(){owner.busy_=false;}
};
TaiwanCustomFullActorProfile::TaiwanCustomFullActorProfile(std::shared_ptr<SharedWorldPresence> presence,
        std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll_bank,Policy policy)
    :presence_(std::move(presence)),bank_(std::move(bank)),drv_doll_bank_(std::move(drv_doll_bank)),policy_(std::move(policy)){}
std::shared_ptr<TaiwanCustomFullActorProfile> TaiwanCustomFullActorProfile::create(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll_bank,Policy policy) {
    if(!presence||!bank||!drv_doll_bank)return {};
    return std::shared_ptr<TaiwanCustomFullActorProfile>(new TaiwanCustomFullActorProfile(
        std::move(presence),std::move(bank),std::move(drv_doll_bank),std::move(policy)));
}
TaiwanCustomFullActorProfile::~TaiwanCustomFullActorProfile() {
    if(thread_!=std::this_thread::get_id())std::terminate();stopped_=true;
}
bool TaiwanCustomFullActorProfile::retained(const Data& data) const noexcept {
    if(thread_!=std::this_thread::get_id()||stopped_||poisoned_||data.owner!=this||data.identity!=identity_||
       !data.saved||!data.saved->source()||!data.saved->role_text_source()||!data.revision||
       !data.saved->source()->owns_presence(presence_)||!data.saved->source()->owns_readset(data.saved->readset())||
       !data.saved->source()->profile_equipment_matches(data.equipment,data.saved->readset(),data.row)||
       !data.saved->readset().matches_population(data.saved->population().characters()))return false;
    return presence_->retained_population_current(data.saved->population());
}
bool TaiwanCustomFullActorProfile::resources_qualified(const Data& data) const {
    const auto& resource=data.resources;
    if(resource.bank!=bank_||resource.drv_doll_bank!=drv_doll_bank_||!resource.epoch||!resource.dependency_owner||!resource.current||
       resource.first_selector>127||resource.second_selector>127)return false;
    const auto arguments=resource.arguments_source;
    if(!arguments||!resource.arguments||!arguments->owns_presence(presence_)||
       !arguments->owns_resource_bank(bank_)||!arguments->owns_drv_doll_bank(drv_doll_bank_)||
       !arguments->matches_inputs(*resource.arguments,data.saved,data.row,data.equipment))return false;
    const auto& derived=*resource.arguments;
    if(derived.first_selector()!=resource.first_selector||derived.second_selector()!=resource.second_selector||
       derived.full_drv_ordinal()!=resource.full_drv_ordinal)return false;
    // The tail is a DISTINCT136-byte native bank even for selector0. Support
    // only its actual pinned empty-filename/not-requested row with real epoch
    // Current. Nonempty tail ROM/cache/window qualification remains OPEN.
    const auto* tail=drv_doll_bank_->find(resource.first_selector);
    if(!tail||!tail->filename.empty())return false;
    if(resource.origin==ResourceInput::Origin::SavedWorldSelectors){
        if(derived.origin()!=TaiwanNativeActorArgumentSource::Origin::CurrentSavedWorldWitness)return false;
        const auto& material=data.saved->readset().materials()[data.row];
        if(!material.world||!NativeWorldEntrySnapshot::same_root(material.world->root,material.actor.character)||
           material.world->position!=material.actor.position||material.world->record.size()!=40)return false;
        RecoveredWorldEntry::Frame frame;std::copy(material.world->record.begin(),material.world->record.end(),frame.begin());
        const auto world=RecoveredWorldEntryView::read(frame);
        if(!world||world->actor_handle!=data.source.actor_handle||world->x!=material.actor.position.x||
           world->y!=material.actor.position.y)return false;
        const auto selectors=world->entry_resource_selectors();
        if(selectors.drv_doll_selector!=resource.first_selector||selectors.drv_selector!=resource.second_selector)return false;
    }else if(resource.origin!=ResourceInput::Origin::Custom0133Explicit||
             derived.origin()!=TaiwanNativeActorArgumentSource::Origin::Custom0133Selectors)return false;
    const auto* drv=bank_->find_drv(resource.full_drv_ordinal);if(!drv)return false;
    // Drv0 classification alone NEVER removes the four native component
    // requests. DrvOnly is an explicit unsupported V1 mode, not a fallback.
    if(resource.mode!=ResourceInput::Mode::HeroComponents||resource.drv||resource.components.size()!=4)return false;
    std::array<bool,4> found{};
    for(const auto& component:resource.components){
        const auto slot=static_cast<std::uint8_t>(component.lookup.component);
        if(slot>=4||found[slot]||component.lookup.act_type!=drv->act_type)return false;found[slot]=true;
        const auto& expected=derived.lookups()[slot];
        if(component.lookup.family!=expected.family||component.lookup.component!=expected.component||
           component.lookup.component_index!=expected.component_index||component.lookup.variant!=expected.variant||
           component.lookup.act_type!=expected.act_type)return false;
        const auto* hero=bank_->find_hero(component.lookup);if(!hero)return false;
        if(hero->filename.empty()){if(component.rom)return false;}
        else if(!rom_row(bank_,component.rom,TaiwanNativeActorResourceBank::ResolvedRom::Family::Hero,hero->ordinal))return false;
    }
    // The private source owns the proven native DA/header-to-argument join.
    // Asset/action/window lifecycle Current and equipment authority remain
    // separate; this derivation never grants either or client cache ownership.
    return true;
}
bool TaiwanCustomFullActorProfile::observers_current(const Data& data,Check check) const {
    const auto local=[&]{return retained(data)&&session_tuple(data.source_input.session,data.source)&&
        session_tuple(data.receiver.session,data.recipient)&&data.source.session!=data.recipient.session;};
    if(!local()||!data.source_input.phase_owner||!data.source_input.current||!data.receiver.phase_owner||
       !data.receiver.current||!data.status.dependency_owner||!data.status.current||!data.status.epoch||
       data.status.unsupported_domains||!data.status.actor_override||!resources_qualified(data))return false;
    if(!data.source_input.current(check,data.source,*data.source_input.session)||!local())return false;
    if(!data.receiver.current(check,*data.receiver.session,data.receiver.selector)||!local())return false;
    if(!data.resources.current(check,data.resources)||!local())return false;
    if(!data.status.current(check,data.status)||!local())return false;
    return true;
}
bool TaiwanCustomFullActorProfile::joint_current(const Data& data) const {
    const std::array<OwnedTaiwanPkReturnRoleTextSource::Observation,1> roles{data.role};
    const std::array<Equipment,1> profiles{data.equipment};
    return data.saved->source()->current_with_role_text(data.saved->readset(),data.saved->role_text_source(),roles,{},profiles)&&retained(data);
}
std::optional<TaiwanCustomFullActorProfile::Profile> TaiwanCustomFullActorProfile::observe(
        std::shared_ptr<const SavedInput> saved,std::size_t index,Equipment equipment,SourceInput source_state,
        Lease recipient,ReceiverInput receiver,ResourceInput resources,StatusInput status) {
    try{
        Operation operation(*this);
        // Every value, function and strong dependency is already owned before
        // observers. Bank/ResolvedRom own immutable full VALUE/source lineage.
        if(!saved||!saved->source()||!saved->role_text_source()||index>=saved->readset().materials().size()||
           !saved->source()->owns_presence(presence_)||!saved->source()->owns_readset(saved->readset())||
           !saved->source()->profile_equipment_matches(equipment,saved->readset(),index)||
           !saved->readset().matches_population(saved->population().characters())||
           !presence_->retained_population_current(saved->population()))return {};
        const auto& material=saved->readset().materials()[index];const Lease source=material.actor.lease;
        bool recipient_found=false;
        for(const auto& row:saved->population().characters())if(row.lease==recipient){if(recipient_found)return {};recipient_found=true;}
        if(!recipient_found||!source.actor_handle||source.actor_handle>0xfff||source.session==recipient.session||
           !session_tuple(source_state.session,source)||!session_tuple(receiver.session,recipient)||
           !source_state.phase_owner||!source_state.current||!receiver.phase_owner||!receiver.current||
           !resources.dependency_owner||!resources.current||!status.dependency_owner||!status.current||
           !status.actor_override||!status.epoch||status.unsupported_domains||material.actor.character.streamer_privilege)return {};
        const auto da=equipment.equipment().appearance();if(!da)return {};
        if(da->transform_key()!=0||material.actor.position.x>0x7ff||material.actor.position.y>0x7ff)return {};
        const auto& replay=status.actor_override->replay();
        if(status.domain==StatusInput::Domain::OrdinaryKnownAbsence){if(replay)return {};}
        else if(status.domain==StatusInput::Domain::OrdinaryExplicitClear){
            if(!replay||replay->identity()!=source.actor_handle||replay->type()!=0)return {};
        }else return {};
        const auto page=receiver.selector.wire_codepage();if(page!=936&&page!=950)return {};
        if(!source_state.current(Check::Prepare,source,*source_state.session)||poisoned_||
           !receiver.current(Check::Prepare,*receiver.session,receiver.selector)||poisoned_)return {};
        const auto role=saved->role_text_source()->observe(source);if(!role||poisoned_)return {};
        const auto& root=material.actor.character;
        const auto end=std::find(root.profile.begin(),root.profile.begin()+15,0);
        if(end==root.profile.begin()||end==root.profile.begin()+15)return {};
        const auto original=OwnedCharacterNameText::from_encoded(std::string_view(
            reinterpret_cast<const char*>(root.profile.data()),static_cast<std::size_t>(end-root.profile.begin())),root.name_codepage);
        if(!original)return {};
        const auto name=OwnedCharacterNameText::from_utf8(original->original_utf8(),page);
        if(!name||name->original_utf8()!=original->original_utf8())return {};
        const auto secondary=SqliteRoleTextRepository::project(role->row(),page);if(!secondary)return {};
        const auto secondary_end=std::find(secondary->begin(),secondary->end(),0);
        if(secondary_end==secondary->end())return {};
        const std::string second(reinterpret_cast<const char*>(secondary->data()),static_cast<std::size_t>(secondary_end-secondary->begin()));
        std::string guild;
        if(role->guild()){
            guild=LegacyChineseCodec::encode(role->guild()->name_utf8,page==936);
            if(LegacyChineseCodec::decode(guild,page==936)!=role->guild()->name_utf8)return {};
        }
        if(!bounded_text(name->encoded_bytes())||!bounded_text(second)||!bounded_text(guild)||
           (role->guild()&&guild.empty()))return {};
        // Every field is authored from qualified input or an explicit named
        // CUSTOM policy. String termination/padding are canonical field bytes.
        RecoveredRemoteActor::LogicalRecord bytes{};bytes[0]=0x6f;
        word(bytes,1,source.actor_handle|(std::uint32_t{resources.first_selector}<<14)|
            (std::uint32_t{receiver.selector.reported_simplified()}<<25)|policy_.word1_unknown);
        word(bytes,5,(std::uint32_t{resources.second_selector}<<8)|policy_.word5_unknown);
        word(bytes,9,policy_.opaque9);
        word(bytes,13,(std::uint32_t{material.actor.position.x}<<2)|(std::uint32_t{material.actor.position.y}<<17)|policy_.position_low2);
        word(bytes,17,policy_.opaque17);std::copy(da->components().begin(),da->components().end(),bytes.begin()+21);
        const std::array<std::string_view,3> text{name->encoded_bytes(),second,guild};
        for(std::size_t i=0;i<text.size();++i)std::copy(text[i].begin(),text[i].end(),bytes.begin()+29+16*i);
        bytes[77]=0;bytes[78]=0;bytes[79]=da->raw_scalar5();bytes[80]=da->raw_scalar6();
        RecoveredRemoteActorMove::LogicalRecord move{};move[0]=0x5e;
        word(move,1,source.actor_handle|(std::uint32_t{policy_.move_identity_upper}<<16));
        const auto state=std::uint16_t(bytes[7])|(std::uint16_t(bytes[8])<<8);
        word(move,5,state|(std::uint32_t{policy_.move_state_upper}<<16));
        word(move,9,material.actor.position.x|(std::uint32_t{material.actor.position.y}<<11)|policy_.move_position_upper);
        RecoveredRemoteActorRemove::LogicalRecord remove{};remove[0]=0x73;
        word(remove,1,source.actor_handle|(std::uint32_t{policy_.remove_identity_upper}<<16));
        const auto actor_record=RecoveredRemoteActor::parse_logical(bytes);
        const auto move_record=RecoveredRemoteActorMove::parse_logical(move);
        const auto remove_record=RecoveredRemoteActorRemove::parse_logical(remove);
        if(!actor_record||!move_record||!remove_record||next_revision_==std::numeric_limits<std::uint64_t>::max())return {};
        Profile result(std::make_shared<const Data>(this,identity_,saved,index,equipment,std::move(source_state),source,
            recipient,std::move(receiver),std::move(resources),std::move(status),*role,*actor_record,*move_record,*remove_record,next_revision_++));
        if(!observers_current(*result.data_,Check::Prepare)||!joint_current(*result.data_)||!retained(*result.data_))return {};
        return result;
    }catch(const std::exception&){return {};}
}
bool TaiwanCustomFullActorProfile::current(const Profile& value,Check check) const {
    try{
        Operation operation(*this);const Profile profile=value;
        if(!retained(*profile.data_)||!observers_current(*profile.data_,check))return false;
        // The complete saved/role/equipment cut follows every live provider.
        // Only pure private/whole-population fences follow it.
        return joint_current(*profile.data_)&&retained(*profile.data_);
    }catch(const std::exception&){return false;}
}
bool TaiwanCustomFullActorProfile::owns_profile(const Profile& value) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){poisoned_=true;return false;}
    return value.data_&&retained(*value.data_);
}
bool TaiwanCustomFullActorProfile::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){poisoned_=true;return false;}
    return !stopped_&&!poisoned_&&presence&&presence==presence_;
}
bool TaiwanCustomFullActorProfile::owns_resource_bank(const std::shared_ptr<const TaiwanNativeActorResourceBank>& bank) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){poisoned_=true;return false;}
    return !stopped_&&!poisoned_&&bank&&bank==bank_;
}
const RecoveredRemoteActor::Record& TaiwanCustomFullActorProfile::Profile::spawn()const noexcept{return data_->spawn;}
const RecoveredRemoteActorMove::Record& TaiwanCustomFullActorProfile::Profile::movement()const noexcept{return data_->movement;}
const RecoveredRemoteActorRemove::Record& TaiwanCustomFullActorProfile::Profile::removal()const noexcept{return data_->removal;}
const std::shared_ptr<const TaiwanCustomFullActorProfile::SavedInput>& TaiwanCustomFullActorProfile::Profile::saved_input()const noexcept{return data_->saved;}
const TaiwanCustomFullActorProfile::Equipment& TaiwanCustomFullActorProfile::Profile::equipment()const noexcept{return data_->equipment;}
const OwnedTaiwanPkReturnRoleTextSource::Observation& TaiwanCustomFullActorProfile::Profile::role_text()const noexcept{return data_->role;}
const TaiwanCustomFullActorProfile::Lease& TaiwanCustomFullActorProfile::Profile::source()const noexcept{return data_->source;}
const TaiwanCustomFullActorProfile::Lease& TaiwanCustomFullActorProfile::Profile::recipient()const noexcept{return data_->recipient;}
const std::shared_ptr<Session>& TaiwanCustomFullActorProfile::Profile::source_session()const noexcept{return data_->source_input.session;}
const TaiwanCustomFullActorProfile::SourceInput& TaiwanCustomFullActorProfile::Profile::source_input()const noexcept{return data_->source_input;}
const TaiwanCustomFullActorProfile::ReceiverInput& TaiwanCustomFullActorProfile::Profile::receiver()const noexcept{return data_->receiver;}
const TaiwanCustomFullActorProfile::ResourceInput& TaiwanCustomFullActorProfile::Profile::resources()const noexcept{return data_->resources;}
const TaiwanCustomFullActorProfile::StatusInput& TaiwanCustomFullActorProfile::Profile::status()const noexcept{return data_->status;}
const std::shared_ptr<const cn::SharedActorVisibility::TaiwanReturnActorOverride>& TaiwanCustomFullActorProfile::Profile::actor_override()const noexcept{return data_->status.actor_override;}
std::uint64_t TaiwanCustomFullActorProfile::Profile::revision()const noexcept{return data_->revision;}
}
