#include "game/OwnedPveWorldCatalog.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredRemoteActor.h"
#include <algorithm>
#include <limits>
#include <set>
namespace god2 { namespace {
using J=nlohmann::json;using P=RecoveredPveRoomProjection;
void need(bool b,const char* m){if(!b)throw std::invalid_argument(m);}
std::uint64_t number(const J& j,std::uint64_t max=UINT64_MAX) {
    need(j.is_number_integer(),"PvE catalog integer required");
    if(j.is_number_unsigned()){const auto n=j.get<std::uint64_t>();need(n<=max,"PvE catalog integer overflow");return n;}
    const auto n=j.get<std::int64_t>();need(n>=0&&std::uint64_t(n)<=max,"PvE catalog negative/overflow");return std::uint64_t(n);
}
template<std::size_t N>std::array<std::uint8_t,N> raw(const J& j) {
    need(j.is_array()&&j.size()==N,"PvE catalog complete native record required");
    std::array<std::uint8_t,N> out;for(std::size_t i=0;i<N;++i)out[i]=std::uint8_t(number(j[i],255));return out;
}
template<class T>T present(std::optional<T> v){need(v.has_value(),"PvE catalog native record grammar invalid");return *v;}
void put16(auto& b,std::size_t at,std::uint16_t n){b[at]=std::uint8_t(n);b[at+1]=std::uint8_t(n>>8);}
void put32(auto& b,std::size_t at,std::uint32_t n){for(unsigned i=0;i<4;++i)b[at+i]=std::uint8_t(n>>(8*i));}
P::ActorProfile actor(const J& j) {
    return {present(RecoveredBattleIdentity::parse_logical(raw<45>(j.at("identity")))),
        j.at("appearance").is_null()?std::nullopt:std::optional{present(RecoveredBattlePlayerAppearance::parse(raw<17>(j.at("appearance"))))},
        present(RecoveredBattleVitals::parse_logical(raw<17>(j.at("hp")))),
        j.at("mp").is_null()?std::nullopt:std::optional{present(RecoveredBattleVitals::parse_logical(raw<17>(j.at("mp"))))}};
}
P::ActorProfile positioned(P::ActorProfile p,std::uint8_t position,std::optional<std::uint16_t> identity={}) {
    auto b=RecoveredBattleIdentity::encode_logical(p.identity);b[1]=position;
    if(identity)put16(b,3,*identity);
    p.identity=present(RecoveredBattleIdentity::parse_logical(b));
    if(p.appearance)p.appearance=RecoveredBattlePlayerAppearance::at_position(*p.appearance,position);
    auto hp=RecoveredBattleVitals::encode_logical(p.hp);hp[2]=position;
    p.hp=present(RecoveredBattleVitals::parse_logical(hp));
    if(p.mp){auto mp=RecoveredBattleVitals::encode_logical(*p.mp);mp[2]=position;p.mp=present(RecoveredBattleVitals::parse_logical(mp));}
    return p;
}
void validate_friendly(const P::ActorProfile& p,bool pet) {
    const auto slot=p.identity.position();
    need(slot<14&&(p.identity.variant()&0x6000)==(pet?0x4000:0x2000)&&
        bool(p.appearance)==!pet&&p.mp&&p.hp.position()==slot&&p.mp->position()==slot&&
        p.hp.resource()==RecoveredBattleVitals::Resource::Hp&&p.mp->resource()==RecoveredBattleVitals::Resource::Mp&&
        p.hp.maximum()&&p.hp.current()<=p.hp.maximum()&&p.mp->current()<=p.mp->maximum()&&
        (!p.appearance||p.appearance->position()==slot),
        "PvE friendly native variant/appearance/resource topology invalid");
    const auto bytes=RecoveredBattleIdentity::encode_logical(p.identity);
    const auto nul=[&](std::size_t first,std::size_t last){
        return std::find(bytes.begin()+first,bytes.begin()+last,std::uint8_t(0))!=bytes.begin()+last;};
    // The native player branch copies two16-byte strings, the pet branch one
    //32-byte string. This is a complete-prototype safety check, not a name issuer.
    need(pet?nul(9,41):(nul(9,25)&&nul(25,41)),"PvE native identity string lacks its bounded terminator");
}
P::ActorProfile saved_values(P::ActorProfile p,std::uint8_t level,std::uint64_t hp,
        std::uint64_t max_hp,std::uint32_t mp,std::uint32_t max_mp) {
    need(p.mp&&max_hp&&hp<=max_hp&&mp<=max_mp,"PvE saved resource projection invalid");
    auto identity=RecoveredBattleIdentity::encode_logical(p.identity);identity[2]=level;
    p.identity=present(RecoveredBattleIdentity::parse_logical(identity));
    auto h=RecoveredBattleVitals::encode_logical(p.hp);
    put32(h,5,RecoveredBattleBootstrap::native_hp_dword(max_hp));
    put32(h,9,RecoveredBattleBootstrap::native_hp_dword(hp));
    p.hp=present(RecoveredBattleVitals::parse_logical(h));
    auto m=RecoveredBattleVitals::encode_logical(*p.mp);put32(m,5,max_mp);put32(m,9,mp);
    p.mp=present(RecoveredBattleVitals::parse_logical(m));return p;
}
BattleAction policy(const J& j) {
    need(j.at("magical").is_boolean(),"PvE action must declare its stat family");
    BattleAction p{0,{},j.at("magical").get<bool>(),std::uint32_t(number(j.at("power_percent"),UINT32_MAX)),
        std::uint32_t(number(j.at("defense_percent"),UINT32_MAX)),std::uint32_t(number(j.at("mp_cost"),UINT32_MAX)),
        std::uint32_t(number(j.at("critical_chance_bp"),10000)),std::uint32_t(number(j.at("critical_multiplier_percent"),UINT32_MAX))};
    need(p.critical_multiplier_percent>=100,"PvE critical multiplier must be explicit >=100 percent");return p;
}
bool projects_saved_values(const J& variant) {
    if(!variant.contains("projection_policy"))return false;
    need(variant.at("projection_policy")=="owned_saved_vitals_level_v1","PvE unknown saved-pet projection policy");
    return true;
}
J pet_material_key(const J& saved,bool project_values=false) {
    const auto kind=saved.at("kind").get<std::string>();
    need(kind=="Pet1"||kind=="Pet2","PvE pet source kind missing");
    const auto metadata=raw<20>(saved.at("metadata"));
    const auto metadata_key=std::uint16_t(metadata[0])|(std::uint16_t(metadata[1])<<8);
    J stats;
    if(kind=="Pet2") {
        auto bytes=raw<RecoveredPet2Stats::logical_size>(saved.at("stats"));
        const auto parsed=present(RecoveredPet2Stats::parse_logical(bytes));
        need((metadata[2]&0x3f)==34&&parsed.metadata_key()==metadata_key&&parsed.slot()==44,
            "PvE Pet2 metadata family/key/active slot differs from complete stats");
        // Proven packed HP14/MP11 only; preserve the high seven opaque bits.
        bytes[5]=bytes[6]=bytes[7]=0;bytes[8]&=0xfe;
        if(project_values){bytes[4]=0;bytes[13]=bytes[14]=bytes[15]=0;bytes[16]&=0xfe;}
        stats=bytes;
    }else{
        auto bytes=raw<RecoveredPet1Stats::logical_size>(saved.at("stats"));
        const auto parsed=present(RecoveredPet1Stats::parse_logical(bytes));
        need((metadata[2]&0x3f)==32&&parsed.metadata_key()==metadata_key&&parsed.slot()==44,
            "PvE Pet1 metadata family/key/active slot differs from complete stats");
        bytes[1]=bytes[2]=bytes[5]=bytes[6]=0;
        if(project_values){bytes[3]=bytes[4]=bytes[7]=bytes[8]=0;bytes[0x24]=0;}
        stats=bytes;
    }
    const auto source=saved.at("source_sha256").get<std::string>();
    need(source.size()==64&&source.find_first_not_of("0123456789abcdef")==std::string::npos,
        "PvE pet source pin invalid");
    return {{"kind",kind},{"metadata",metadata},{"stats",stats},{"source_sha256",source}};
}
J validate_pet_variant(const J& variant) {
    const auto p=actor(variant.at("pet"));
    validate_friendly(p,true);
    const auto& saved=variant.at("active_pet_material");
    const bool project_values=projects_saved_values(variant);
    const auto key=pet_material_key(saved,project_values);
    if(saved.at("kind")=="Pet2"){
        const auto stats=present(RecoveredPet2Stats::parse_logical(raw<RecoveredPet2Stats::logical_size>(saved.at("stats"))));
        const auto v=stats.vitals();need(v.maximum_hp&&v.current_hp<=v.maximum_hp&&v.current_mp<=v.maximum_mp&&
            p.hp.maximum()==v.maximum_hp&&p.mp->maximum()==v.maximum_mp&&
            (!project_values||p.identity.displayed_level()==stats.level()),
            "PvE Pet2 profile maxima differ from complete saved material");
    }else{
        const auto stats=present(RecoveredPet1Stats::parse_logical(raw<RecoveredPet1Stats::logical_size>(saved.at("stats"))));
        const auto v=stats.vitals();need(v.maximum_hp&&v.current_hp<=v.maximum_hp&&v.current_mp<=v.maximum_mp&&
            p.hp.maximum()==v.maximum_hp&&p.mp->maximum()==v.maximum_mp&&
            (!project_values||p.identity.displayed_level()==stats.level()),
            "PvE Pet1 profile maxima differ from complete saved material");
    }
    return key;
}
void validate_templates(const J& j) {
    need(j.at("animation_group_policy")=="custom_contiguous_batch_0_254","PvE explicit animation group policy required");
    need(j.at("cycle_counter_policy")=="fixed_complete_profile","PvE explicit fixed native cycle counter policy required");
    const auto bulk=present(RecoveredBattleVitalsBatch::parse_logical(raw<121>(j.at("bulk"))));
    need(bulk.counter_bits()!=UINT32_MAX,"PvE fixed bulk counter cannot use the native uninitialized sentinel");
    const auto grant=raw<17>(j.at("grant"));need(grant[0]==0x86&&grant[1]==5,"PvE grant template invalid");
    const auto attack=present(RecoveredBattleAttackPresentation::parse(raw<15>(j.at("attack"))));
    need(attack.basic(),"PvE basic-only action owner cannot accept a skill template without skill authority");
    const auto support=raw<15>(j.at("support"));
    (void)present(RecoveredBattleAction08Control::parse(support));
    need(support[3]<255,"PvE initial support template uses a reserved animation batch label");
    const auto removal=raw<15>(j.at("withdrawal"));
    need(removal[0]==0x83&&removal[1]==6&&removal[12]==2,"PvE native successful withdrawal template invalid");
    const auto swap=present(RecoveredBattleRowSwapResult::parse(raw<15>(j.at("row_swap"))));
    need(swap.success_operand()!=0,"PvE row swap requires an explicit successful native template");
    const auto terminal=present(RecoveredBattleExperience::parse_logical(raw<57>(j.at("terminal"))));
    // CUSTOM-0161 currently has no reward issuer. Never display an award which
    // the same transaction has not granted to the actual participant.
    need(!terminal.character_received_exp_display()&&!terminal.companion_received_exp_display()&&
        !terminal.pet_received_exp_display()&&!terminal.cave_received_exp_display(),"PvE reward producer is not installed");
    (void)number(j.at("entry_context_b"),UINT32_MAX);
}
}
OwnedPveWorldCatalog::OwnedPveWorldCatalog(const nlohmann::json& j) {
    need(j.is_object()&&j.at("design_id")=="CUSTOM-0161"&&j.at("native_client_sha256")==
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48","PvE catalog source pin/design invalid");
    version_=number(j.at("version"),INT64_MAX);need(version_>0,"PvE catalog version required");
    source_sha256_=j.at("source_sha256").get<std::string>();source_record_=j.at("source_record").get<std::string>();
    need(source_sha256_.size()==64&&source_sha256_.find_first_not_of("0123456789abcdef")==std::string::npos&&
        !source_record_.empty(),"PvE catalog provenance missing");
    need(j.at("scenes").is_array()&&!j.at("scenes").empty()&&j.at("scenes").size()<=4096,"PvE catalog scenes missing/too many");
    std::set<std::pair<std::uint16_t,std::uint16_t>> places;std::set<std::uint64_t> ids;
    for(const auto& entry:j.at("scenes")) {
        Scene s;s.id=number(entry.at("id"),INT64_MAX);s.area=std::uint16_t(number(entry.at("area"),65535));
        s.scene=std::uint16_t(number(entry.at("scene"),65535));s.movement_steps=std::uint32_t(number(entry.at("movement_steps"),UINT32_MAX));
        need(s.id&&s.area&&s.movement_steps&&ids.insert(s.id).second&&places.emplace(s.area,s.scene).second,
            "PvE scene policy duplicate/missing, never a monster coordinate placement");
        const auto& topology=entry.at("formation");s.topology.source_record=topology.at("source_record").get<std::string>();
        s.topology.version=number(topology.at("version"),INT64_MAX);
        for(const auto& pair:topology.at("lanes")){need(pair.is_array()&&pair.size()==2,"PvE explicit row pair required");
            s.topology.lanes.push_back({std::uint8_t(number(pair[0],13)),std::uint8_t(number(pair[1],13))});}
        s.topology.validate();s.basic=policy(entry.at("basic"));s.ai=policy(entry.at("ai"));
        need(entry.at("support_enabled").is_boolean(),"PvE support policy must be explicit");s.support_enabled=entry.at("support_enabled").get<bool>();
        s.templates=entry.at("templates");validate_templates(s.templates);
        need(entry.at("enemies").is_array()&&!entry.at("enemies").empty()&&entry.at("enemies").size()<=14,"PvE actual encounter enemies missing");
        for(const auto& e:entry.at("enemies")) {
            BattleActor a{std::uint8_t(number(e.at("position"),27)),0,number(e.at("hp")),number(e.at("max_hp")),
                std::uint32_t(number(e.at("mp"),UINT32_MAX)),std::uint32_t(number(e.at("max_mp"),UINT32_MAX)),
                std::uint32_t(number(e.at("physical_attack"),UINT32_MAX)),std::uint32_t(number(e.at("magical_attack"),UINT32_MAX)),
                std::uint32_t(number(e.at("physical_defense"),UINT32_MAX)),std::uint32_t(number(e.at("magical_defense"),UINT32_MAX))};
            need(a.position>=14&&a.hp&&a.hp<=a.max_hp&&a.mp<=a.max_mp,"PvE enemy topology/resources invalid");
            auto p=actor(e.at("native"));need(p.identity.variant()==0x400&&p.identity.position()==a.position&&p.hp.position()==a.position&&
                p.hp.resource()==RecoveredBattleVitals::Resource::Hp&&p.hp.maximum()==a.max_hp&&p.hp.current()==a.hp&&
                !p.mp&&!p.appearance,"PvE enemy native profile differs from authoritative complete combat material");
            need(s.enemy_profiles.emplace(a.position,std::move(p)).second,"PvE duplicate enemy slot");s.enemies.push_back(a);
        }
        scenes_.push_back(std::move(s));
    }
    need(j.at("character_profiles").is_array()&&j.at("character_profiles").size()<=100000,"PvE character profile list invalid");
    for(const auto& a:j.at("character_profiles")) {
        const auto id=number(a.at("character"),INT64_MAX);need(id>0,"PvE full character ID missing");
        (void)raw<40>(a.at("root_profile"));
        need(raw<37>(a.at("entry_logical"))[0]==0x2a,"PvE complete entry material is not native2A");
        const auto spawn=raw<RecoveredRemoteActor::logical_size>(a.at("world_spawn"));
        const auto removal=raw<RecoveredRemoteActorRemove::logical_size>(a.at("world_remove"));
        (void)present(RecoveredRemoteActor::parse_logical(spawn));
        (void)present(RecoveredRemoteActorRemove::parse_logical(removal));
        (void)present(RecoveredRemoteActorMove::parse_logical(raw<13>(a.at("world_move"))));
        validate_friendly(actor(a.at("primary")),false);
        std::set<std::string> strict_keys,all_relaxed_keys,projected_keys;
        const auto add_variant=[&](const J& variant){
            (void)validate_pet_variant(variant);
            // A relaxed key is a superset of the strict key. The union domain
            // detects overlap in either order without a quadratic pair scan.
            const auto& saved=variant.at("active_pet_material");
            const auto strict=pet_material_key(saved).dump(),relaxed=pet_material_key(saved,true).dump();
            if(projects_saved_values(variant)){
                need(!all_relaxed_keys.contains(relaxed),"PvE ambiguous overlapping active-pet material profiles");
                projected_keys.insert(relaxed);
            }else need(!strict_keys.contains(strict)&&!projected_keys.contains(relaxed),
                "PvE ambiguous overlapping active-pet material profiles");
            strict_keys.insert(strict);all_relaxed_keys.insert(relaxed);
        };
        if(!a.at("pet").is_null())add_variant(a);
        if(a.contains("pet_profiles")){
            const auto& variants=a.at("pet_profiles");
            need(variants.is_array()&&variants.size()<=1024,"PvE complete pet variant list exceeds source format");
            for(const auto& variant:variants)add_variant(variant);
        }
        need(actors_.emplace(id,a).second,"PvE duplicate full character profile");
    }
}
const OwnedPveWorldCatalog::Scene* OwnedPveWorldCatalog::scene(std::uint16_t area,std::uint16_t scene)const noexcept {
    for(const auto& s:scenes_)if(s.area==area&&s.scene==scene)return &s;return nullptr;
}
const nlohmann::json& OwnedPveWorldCatalog::actor_profile(std::uint64_t character)const {
    const auto at=actors_.find(character);if(at==actors_.end())throw P::ProfileRequired("profile_required: complete current saved-player native profile missing");return at->second;
}
RecoveredPveRoomProjection::ActorProfile OwnedPveWorldCatalog::pet_profile(
        std::uint64_t character,const StoredPet2Slot& saved)const {
    need(saved.slot==44&&bool(saved.pet)!=bool(saved.pet1),"PvE actual active pet material missing/ambiguous");
    J actual{{"kind",saved.pet?"Pet2":"Pet1"},
        {"metadata",saved.pet?saved.pet->inventory:saved.pet1->inventory},
        {"stats",saved.pet?J(RecoveredPet2Stats::encode_logical(saved.pet->stats)):
            J(RecoveredPet1Stats::encode_logical(saved.pet1->stats))},
        {"source_sha256",saved.provenance.source_sha256}};
    // Full actual source is validated before matching. Only an explicit per-
    // variant CUSTOM adapter may exclude saved maxima/level from its key.
    (void)pet_material_key(actual);const auto& root=actor_profile(character);
    const J* selected=nullptr;
    const auto consider=[&](const J& variant){
        const bool projected=projects_saved_values(variant);
        if(pet_material_key(variant.at("active_pet_material"),projected)==pet_material_key(actual,projected)){
            need(!selected,"PvE ambiguous actual active-pet native profile");selected=&variant;
        }
    };
    if(!root.at("pet").is_null())consider(root);
    if(root.contains("pet_profiles"))for(const auto& variant:root.at("pet_profiles"))consider(variant);
    if(!selected)throw P::ProfileRequired("profile_required: complete current active-pet native profile missing");
    auto profile=actor(selected->at("pet"));
    if(projects_saved_values(*selected)){
        // This copies already-saved instance values. It neither computes growth
        // nor derives identity/species/name/status from E3/FB or combat stats.
        if(saved.pet){const auto v=saved.pet->stats.vitals();
            profile=saved_values(std::move(profile),saved.pet->stats.level(),v.current_hp,v.maximum_hp,v.current_mp,v.maximum_mp);
        }else{const auto v=saved.pet1->stats.vitals();
            profile=saved_values(std::move(profile),saved.pet1->stats.level(),v.current_hp,v.maximum_hp,v.current_mp,v.maximum_mp);}
    }
    return profile;
}
bool OwnedPveWorldCatalog::same_entry_material(const nlohmann::json& prototype,std::span<const std::uint8_t> actual) {
    if(actual.size()!=37||actual.front()!=0x2a)return false;
    auto expected=raw<37>(prototype);std::array<std::uint8_t,37> current;
    std::copy(actual.begin(),actual.end(),current.begin());
    const auto normalize=[](auto& b) {
        // Proven2A fields only: low14 actor handle, low16 map (area/scene),
        // X15/Y15 position. Keep world kind, appearance and ALL opaque bits.
        b[1]=0;b[2]&=0xc0;b[25]=0;b[26]=0;
        b[29]&=3;b[30]=0;b[31]=0;b[32]=0;
    };
    normalize(expected);normalize(current);return expected==current;
}
RecoveredPveRoomProjection::Profiles OwnedPveWorldCatalog::profiles(const Scene& scene,const Types::Snapshot& room,const Types::Change& change)const {
    P::Profiles out;
    for(const auto& [id,m]:room.members) {
        if(m.status==Types::MemberStatus::Returned||m.status==Types::MemberStatus::Retired||m.disconnected)continue;
        P::RecipientProfile p;p.character=id;p.entry=RecoveredBattleEntry::Record{m.input.command_context,
            std::uint32_t(number(scene.templates.at("entry_context_b"),UINT32_MAX))};
        p.actors=scene.enemy_profiles;
        for(const auto& [other,peer]:room.members) {
            if(peer.status==Types::MemberStatus::Returned||peer.status==Types::MemberStatus::Retired||
               peer.status==Types::MemberStatus::Withdrawn||peer.disconnected)continue;
            const auto& a=actor_profile(other);auto primary=positioned(actor(a.at("primary")),peer.primary_position(),peer.input.identity.actor_handle);
            const auto role=present(RecoveredRoleLevel::parse(peer.input.role.logical));
            const auto& resources=peer.input.resources;
            const auto& canonical=room.checkpoint.snapshot.actors[peer.primary_position()];
            need(role.max_hp()==resources.max_hp&&role.max_mp()==resources.max_mp&&canonical&&
                canonical->controller==other&&canonical->hp==resources.hp&&canonical->max_hp==resources.max_hp&&
                canonical->mp==resources.mp&&canonical->max_mp==resources.max_mp,
                "PvE actual role/resource/checkpoint material differs");
            primary=saved_values(std::move(primary),role.level(),resources.hp,resources.max_hp,resources.mp,resources.max_mp);
            p.actors.emplace(peer.primary_position(),std::move(primary));
            if(peer.input.pet) {
                need(peer.pet_position().has_value(),"PvE saved pet has no current formation assignment");
                auto secondary=positioned(pet_profile(other,peer.input.pet->saved),*peer.pet_position(),
                    std::uint16_t(peer.input.identity.actor_handle|0x4000));
                p.actors.emplace(*peer.pet_position(),std::move(secondary));
            }
        }
        // The native queue delays this boundary until the preceding83 batch
        // finishes. Its DWORD is a full source value, not a server turn count:
        // ordinary K0 compares the later cache against the first88 cache.
        p.bulk=present(RecoveredBattleVitalsBatch::parse_logical(raw<121>(scene.templates.at("bulk"))));
        p.grant=raw<17>(scene.templates.at("grant"));
        if(change.result)for(std::size_t n=0;n<change.result->hits.size();++n) {
            auto attack=raw<15>(scene.templates.at("attack"));
            // Explicit CUSTOM contiguous batch label. The room publishes this
            // exact group after source authorization; it is never a turn nonce.
            need(change.animation_group&&*change.animation_group<255,
                "PvE action lacks its actual server-owned animation batch");
            attack[3]=*change.animation_group;p.attacks.push_back(present(RecoveredBattleAttackPresentation::parse(attack)));
        }
        if(change.kind==Types::Change::Kind::Support) {
            const auto changed=room.members.find(change.character);need(changed!=room.members.end(),"PvE support owner missing");
            auto support=raw<15>(scene.templates.at("support"));
            need(change.actor_position.has_value(),"PvE support requires its actual primary/secondary producer");
            support[2]=*change.actor_position;
            need(change.animation_group&&*change.animation_group<255,"PvE support animation batch missing");
            support[3]=*change.animation_group;
            put16(support,9,room.support_enabled?1:0);p.support=present(RecoveredBattleAction08Control::parse(support));
        } else if((change.kind==Types::Change::Kind::Entry||
            (change.kind==Types::Change::Kind::Admission&&change.character==id))&&room.support_enabled) {
            auto support=raw<15>(scene.templates.at("support"));support[2]=m.primary_position();
            put16(support,9,1);p.support=present(RecoveredBattleAction08Control::parse(support));
        }
        if(change.kind==Types::Change::Kind::Withdrawal) {
            const auto changed=room.members.find(change.character);need(changed!=room.members.end(),"PvE withdrawal owner missing");
            std::vector<std::uint8_t> slots{changed->second.primary_position()};if(changed->second.pet_position())slots.push_back(*changed->second.pet_position());
            need(change.animation_group&&*change.animation_group<255,"PvE withdrawal animation batch missing");
            for(const auto slot:slots){auto removal=raw<15>(scene.templates.at("withdrawal"));removal[2]=slot;
                removal[3]=*change.animation_group;p.withdrawal.push_back(removal);}
        }
        if(change.kind==Types::Change::Kind::RowSwap) {
            need(change.formation_before&&change.actor_position,
                "PvE row swap lacks the actual original pair and acting role");
            const auto changed=room.members.find(change.character);
            need(changed!=room.members.end()&&change.formation_before->primary!=changed->second.primary_position(),
                "PvE row swap has no actual canonical destination");
            need(change.animation_group&&*change.animation_group<255,"PvE row swap animation batch missing");
            auto bytes=raw<15>(scene.templates.at("row_swap"));bytes[3]=*change.animation_group;
            const auto prototype=present(RecoveredBattleRowSwapResult::parse(bytes));
            p.row_swap=RecoveredBattleRowSwapResult::positioned(prototype,*change.actor_position,
                change.formation_before->primary,changed->second.primary_position());
        }
        p.terminal=present(RecoveredBattleExperience::parse_logical(raw<57>(scene.templates.at("terminal"))));
        out.emplace(id,std::move(p));
    }
    return out;
}
nlohmann::json OwnedPveWorldCatalog::schema_description() {
    return {{"design_id","CUSTOM-0161"},{"encoding","UTF-8 JSON; all native arrays complete unsigned bytes"},
        {"initial_material","Explicit complete root/2A/world/identity/appearance sources remain required; no generated opaque defaults"},
        {"saved_values_adapter","CUSTOM-0161: actual primary role/resources; optional per-pet owned_saved_vitals_level_v1 preserves all other source bits"},
        {"version_rule","one immutable whole DB snapshot; invalid reload retains previous whole version"}};
}
}
