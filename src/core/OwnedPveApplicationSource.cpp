#include "core/OwnedPveApplicationSource.h"
#include "game/OwnedBattleRowPreference.h"
#include "handlers/RecoveredPeerRoleText.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "protocol/RecoveredBattleRowPreference.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <algorithm>
#include <bit>
#include <random>
#include <spdlog/spdlog.h>
namespace god2 { namespace {
void need(bool b,const char* m){if(!b)throw DatabaseError(m);}
bool finished(OwnedPveRoomTypes::MemberStatus status){return status==OwnedPveRoomTypes::MemberStatus::Returned||
    status==OwnedPveRoomTypes::MemberStatus::Retired;}
bool same_population(const std::vector<RecoveredVisibility::Presence>& a,const std::vector<RecoveredVisibility::Presence>& b) {
    if(a.size()!=b.size())return false;
    for(std::size_t n=0;n<a.size();++n)if(a[n].session!=b[n].session||a[n].account!=b[n].account||a[n].character!=b[n].character||
        a[n].location!=b[n].location||a[n].pose!=b[n].pose||
        RecoveredRemoteActor::encode_logical(a[n].spawn)!=RecoveredRemoteActor::encode_logical(b[n].spawn)||
        RecoveredRemoteActorRemove::encode_logical(a[n].departure)!=RecoveredRemoteActorRemove::encode_logical(b[n].departure))return false;
    return true;
}
bool same_pet(const StoredPet2Slot& a,const StoredPet2Slot& b) {
    if(a.slot!=b.slot||a.revision!=b.revision||a.provenance!=b.provenance||bool(a.display_category)!=bool(b.display_category)||
       bool(a.pet)!=bool(b.pet)||bool(a.pet1)!=bool(b.pet1))return false;
    if(a.display_category&&(a.display_category->group!=b.display_category->group||a.display_category->index!=b.display_category->index||
       a.display_category->source_line!=b.display_category->source_line||a.display_category->name!=b.display_category->name))return false;
    if(a.pet&&(a.pet->owner.account!=b.pet->owner.account||a.pet->owner.character!=b.pet->owner.character||
       a.pet->inventory!=b.pet->inventory||RecoveredPet2Stats::encode_logical(a.pet->stats)!=RecoveredPet2Stats::encode_logical(b.pet->stats)))return false;
    return !a.pet1||(a.pet1->owner.account==b.pet1->owner.account&&a.pet1->owner.character==b.pet1->owner.character&&
        a.pet1->inventory==b.pet1->inventory&&RecoveredPet1Stats::encode_logical(a.pet1->stats)==RecoveredPet1Stats::encode_logical(b.pet1->stats));
}
}
OwnedPveApplicationSource::OwnedPveApplicationSource(SqliteDatabase& db,LuaEngine& lua,
        RecoveredMovementService& movement,RecoveredVisibility& visibility,
        Deliver deliver)
    :db_(db),lua_(lua),movement_(movement),visibility_(visibility),deliver_(std::move(deliver)),
     catalog_(db.load_owned_pve_world_catalog()),repository_(db.make_owned_pve_room_repository()),
     host_(std::make_shared<OwnedPveRoomHost>(*repository_)) {
    need(movement.owns_repository(db.recovered_characters())&&bool(deliver_),"PvE actual Application sources mismatch");
}
OwnedPveApplicationSource::~OwnedPveApplicationSource(){stop();}
void OwnedPveApplicationSource::install_return_handoff(PrepareReturnHandoff prepare) {
    need(!stopped_&&!retiring_&&!prepare_return_handoff_&&bool(prepare)&&worlds_.empty()&&pending_.empty(),
        "PvE return handoff must be installed once by its actual Application owner before use");
    prepare_return_handoff_=std::move(prepare);
}
bool OwnedPveApplicationSource::bound(const Session& s)const noexcept{return host_&&host_->bound(s);}
void OwnedPveApplicationSource::observe_world(Session& s) {
    if(stopped_||retiring_||bound(s)||s.closing()||!s.recovered_world_ready()||
       (s.state()!=SessionState::CharacterSelected&&s.state()!=SessionState::InWorld))return;
    const auto initialization=s.normal_world_initialization();if(!initialization||!initialization->entry_written())return;
    const auto normal=RecoveredNormalCompanionCurrent::capture(s,movement_,[this]{return !stopped_&&!retiring_;});
    if(!normal)return;
    const DeliveryCurrent current=[this,normal,weak=s.weak_from_this()]{
        const auto peer=weak.lock();return peer&&normal->current()&&!bound(*peer);
    };
    const auto position=movement_.current_location(s.id(),s.account_id,s.character_id);
    need(current(),"PvE world identity source retired during location observation");
    if(!position||!catalog_->scene(position->area,position->scene)||!catalog_->has_actor_profile(s.character_id))return;
    const auto& native=catalog_->actor_profile(s.character_id);
    const auto roots=db_.recovered_characters().list_for_account(s.account_id);
    need(current(),"PvE world identity source retired during saved root observation");
    const auto root=std::find_if(roots.begin(),roots.end(),[&](const auto& r){return r.id==s.character_id;});
    need(root!=roots.end()&&native.at("root_profile")==nlohmann::json(root->profile)&&
        OwnedPveWorldCatalog::same_entry_material(native.at("entry_logical"),initialization->entry_logical()),
        "profile_required: normal PvE world actor source is stale");
    const auto raw=native.at("world_spawn").get<std::vector<std::uint8_t>>();
    const auto removed=native.at("world_remove").get<std::vector<std::uint8_t>>();
    const auto spawn=RecoveredRemoteActor::parse_logical(raw);
    const auto departure=RecoveredRemoteActorRemove::parse_logical(removed);
    need(spawn&&departure,"profile_required: complete normal world actor native material missing");
    const auto kind=movement_.qualified_scene_kind(position->area,position->scene);
    need(kind.has_value(),"PvE normal world scene kind unavailable");
    auto actor=RecoveredPlayerPresence::from_world_entry(s.id(),s.account_id,s.character_id,
        initialization->entry_frame(),root->profile,*spawn,*departure,*kind);
    actor.location={position->area,position->scene};
    const auto placed=RecoveredRemoteActor::with_position(actor.spawn,position->x,position->y);
    need(placed.has_value(),"PvE current world actor position unrepresentable");actor.spawn=*placed;
    const auto before=visibility_.snapshot(s.id());
    need(current(),"PvE world identity source retired before visibility publication");
    if(!before)deliver_(visibility_.enter(actor),current);
    else if(before->location!=actor.location)deliver_(visibility_.transfer(actor),current);
    // Existing same-scene movement/appearance owners retain their complete
    // actual row. A second scalar overwrite would discard their pose queue.
}
void OwnedPveApplicationSource::title(Session& s,bool active) {
    const auto before=visibility_.snapshot(s.id());if(!before)return;
    const auto position=movement_.current_world_location(s.id(),s.account_id,s.character_id);
    need(position&&before->account==s.account_id&&before->character==s.character_id&&
        before->location==RecoveredVisibility::Scene{position->area,position->scene},"PvE world marker source drift");
    const auto source=worlds_.find(s.id());
    need(source!=worlds_.end()&&source->second.movement,"PvE world marker lacks retained movement source");
    const auto binding=source->second.binding;const auto movement=source->second.movement;
    const auto normal=active?std::optional<RecoveredNormalCompanionCurrent>{}:
        RecoveredNormalCompanionCurrent::capture(s,movement_,[this]{return !stopped_;},position);
    const DeliveryCurrent current=[this,binding,movement,normal,active,weak=s.weak_from_this()] {
        const auto peer=weak.lock();if(stopped_||!peer||peer->closing())return false;
        const auto world=worlds_.find(peer->id());
        return world!=worlds_.end()&&world->second.binding.same_binding(binding)&&
            movement_.world_location_current(*movement)&&
            (active?peer->owned_pve_current(binding):(normal&&normal->current()));
    };
    need(current(),"PvE world marker source retired before publication");
    deliver_(visibility_.set_fight_title(s.id(),s.account_id,s.character_id,before->location,active),current);
}
void OwnedPveApplicationSource::committed_movement(Session& session,const RecoveredMovementService::CommittedMove& committed) {
    const auto before=visibility_.snapshot(session.id());if(!before)return;
    need(!stopped_&&!bound(session)&&!host_->pending(session)&&committed.before&&before->account==session.account_id&&before->character==session.character_id&&
        before->location==RecoveredVisibility::Scene{committed.after.area,committed.after.scene}&&
        movement_.current_world_location(session.id(),session.account_id,session.character_id)==std::optional{committed.after},
        "PvE world movement lacks its actual committed current source");
    const auto normal=RecoveredNormalCompanionCurrent::capture(session,movement_,[this]{return !stopped_;},committed.after);
    need(normal.has_value(),"PvE world movement lost its actual normal source");
    const auto& material=catalog_->actor_profile(session.character_id);
    const auto raw=material.at("world_move").get<std::vector<std::uint8_t>>();
    const auto prototype=RecoveredRemoteActorMove::parse_logical(raw);
    need(prototype.has_value(),"profile_required: complete native world move template missing");
    const auto named=RecoveredRemoteActorMove::with_identity(*prototype,before->spawn.identity());
    need(named.has_value(),"PvE world move native handle unrepresentable");
    std::vector<RecoveredRemoteActorMove::Record> path;
    for(const auto& step:committed.path){const auto positioned=RecoveredRemoteActorMove::with_position(*named,step.x,step.y);
        need(positioned.has_value(),"PvE actual world path unrepresentable");path.push_back(*positioned);}
    const DeliveryCurrent current=[normal]{return normal->current();};
    deliver_(visibility_.move_batch(session.id(),session.account_id,session.character_id,before->location,path),current);
}
OwnedPveRoomTypes::MemberInput OwnedPveApplicationSource::member(const OwnedPveWorldCatalog::Scene& scene,
        const std::shared_ptr<Session>& session,const Binding& binding,std::shared_ptr<const T::Snapshot> room) {
    need(!stopped_&&!retiring_&&session&&session->owned_pve_prepared_current(binding),"PvE member lacks its actual private preparation");
    const auto movement=movement_.observe_world_location(session->id(),binding.account(),binding.character());
    const auto entry=RecoveredWorldEntryView::read(binding.initialization().entry_frame());
    const auto position=movement_.current_location(session->id(),binding.account(),binding.character());
    need(entry&&entry->actor_handle&&entry->actor_handle<0x4000&&movement&&movement_.world_location_current(*movement)&&position&&
        movement_.current_world_location(session->id(),binding.account(),binding.character())==position&&
        position->area==scene.area&&position->scene==scene.scene,"PvE member location/native actor source missing");
    const auto roots=db_.recovered_characters().list_for_account(binding.account());
    const auto root=std::find_if(roots.begin(),roots.end(),[&](const auto& r){return r.id==binding.character();});
    const auto role=db_.recovered_characters().load_role(binding.account(),binding.character());
    const auto resources=db_.recovered_characters().load_resources(binding.account(),binding.character());
    const auto auxiliary=db_.role_auxiliary().load(binding.account(),binding.character());
    const auto row=db_.native_world_entry_writer().load(binding.account(),binding.character(),
        OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::record_kind);
    need(root!=roots.end()&&role&&resources&&auxiliary&&row&&row->source_sha256==OwnedBattleRowPreference::client_pin&&
        row->source_record==OwnedBattleRowPreference::source_record&&row->record.size()==2&&row->record[0]==0xe8&&row->record[1]<=1&&
        NativeWorldEntrySnapshot::same_root(row->root,*root),"PvE requires complete saved role/resources and explicit B4 row; no default row");
    const auto& profile=catalog_->actor_profile(binding.character());
    need(profile.at("root_profile")==nlohmann::json(root->profile)&&
        OwnedPveWorldCatalog::same_entry_material(profile.at("entry_logical"),binding.initialization().entry_logical()),
        "profile_required: player native template does not match actual saved root/entry");
    std::size_t lane=scene.topology.lanes.size();
    for(std::size_t n=0;n<scene.topology.lanes.size();++n){
        const auto pair=scene.topology.lanes[n];bool used=false;
        if(room)for(const auto& [id,m]:room->members){(void)id;
            // Retained tombstones still occupy canonical actor slots. Reuse is
            // a distinct lifecycle; do not admit a different owner over them.
            used=used||m.input.primary_slot==pair.row0||m.input.primary_slot==pair.row1||
                (m.input.pet&&(m.input.pet->actor_slot==pair.row0||m.input.pet->actor_slot==pair.row1));}
        if(!used){lane=n;break;}
    }
    need(lane<scene.topology.lanes.size(),"PvE actual room has no configured free formation lane");
    const auto assigned=scene.topology.positions(lane,row->record[1]);
    T::MemberInput result;result.identity={binding.session_id(),binding.account(),binding.character(),
        binding.world_generation(),binding.battle_generation(),binding.channel(),entry->actor_handle};
    result.root=*root;result.role=*role;result.auxiliary=*auxiliary;result.resources=*resources;result.row_preference=*row;
    result.return_position=*position;result.primary_slot=assigned.row0;result.reserved_partner=assigned.row1;
    std::random_device entropy;result.command_context=entropy(); // CUSTOM opaque source context, not a room ID.
    const auto pets=db_.companions().load_pet2_slots(binding.account(),binding.character());
    for(const auto& pet:pets)if(pet.slot==44){
        if(!pet.occupied()){result.empty_active_pet=pet;continue;}
        need(!result.pet,"PvE duplicate occupied active44 source");
        // Preserve the whole original native Pet1/Pet2 slot in the room. The
        // repository compares its full raw metadata/revision before HP/MP CAS.
        (void)catalog_->pet_profile(binding.character(),pet);
        result.pet=T::PetInput{assigned.row1,pet};
    }
    need(session->owned_pve_prepared_current(binding)&&
        movement_.world_location_current(*movement)&&
        movement_.current_world_location(session->id(),binding.account(),binding.character())==position,
        "PvE member actual source changed during saved observations");
    need(bool(prepare_return_handoff_),"PvE actual Application return handoff is not installed");
    const auto handoff=prepare_return_handoff_(*session,binding);
    need(handoff&&handoff->retained_current(*session,binding)&&session->owned_pve_prepared_current(binding),
        "PvE companion/learning continuation is not an actual retained source");
    auto actors=visibility_.retained_scene({position->area,position->scene});
    need(movement_.world_location_current(*movement),"PvE member original movement incarnation changed during handoff");
    worlds_.insert_or_assign(session->id(),WorldBefore{binding,*position,std::move(actors),{},handoff,movement});
    return result;
}
std::shared_ptr<const OwnedPveRoomHost::Sources> OwnedPveApplicationSource::sources(const OwnedPveWorldCatalog::Scene& scene) {
    auto source=std::make_shared<OwnedPveRoomHost::Sources>();
    source->encounter.enemies=scene.enemies;source->encounter.numeric_profile=BattleNumericProfile::Extended64;
    std::random_device entropy;source->encounter.seed=entropy();source->encounter.support_enabled=scene.support_enabled;
    source->encounter.source_sha256=catalog_->source_sha256();source->encounter.source_record=catalog_->source_record()+";scene="+std::to_string(scene.id);
    const auto* policy=&scene;
    source->member=[this,policy](const auto& peer,const auto& binding,auto snapshot){return member(*policy,peer,binding,std::move(snapshot));};
    source->entered=[this](const auto& peer,const Binding& binding,const auto&) {
        const auto world=worlds_.find(peer->id());
        need(!stopped_&&world!=worlds_.end()&&world->second.binding.same_binding(binding)&&
            peer->owned_pve_current(binding),"PvE fight title lacks an actual committed member");
        title(*peer,true);
    };
    source->cancelled=[this](const auto& peer,const Binding& binding) {
        if(!peer)return;const auto world=worlds_.find(peer->id());
        if(world!=worlds_.end()&&world->second.binding.same_binding(binding))worlds_.erase(world);
    };
    source->member_continuation_current=[this](Session& peer,const Binding& binding) {
        const auto at=worlds_.find(peer.id());
        return !stopped_&&at!=worlds_.end()&&at->second.binding.same_binding(binding)&&
            at->second.movement&&movement_.world_location_current(*at->second.movement)&&
            at->second.handoff&&at->second.handoff->retained_current(peer,binding);
    };
    const auto catalog=catalog_;
    source->project=[catalog,policy](const auto& snapshot,const auto& change){
        return RecoveredPveRoomProjection::prepare(snapshot,change,catalog->profiles(*policy,snapshot,change));};
    source->rule=[this](const auto& input){need(!stopped_,"PvE rule source retired");return lua_.combat_damage(input);};
    source->action=[policy](const auto& snapshot,const auto&,const RecoveredBattleCommand::BasicAttackRequest& request){
        // side_flag selects native primary/secondary grants, not Battle side.
        // The actual room host validates it against that member's live role.
        need(request.actor_position<14&&request.target_masks[0]==0&&
            std::popcount(request.target_masks[1])==1,"PvE basic requires one actual enemy target");
        auto action=policy->basic;action.source=request.actor_position;
        for(std::uint8_t n=0;n<14;++n)if(request.target_masks[1]&(1u<<n)){
            const auto slot=std::uint8_t(14+n);need(snapshot.checkpoint.snapshot.actors[slot].has_value(),
                "PvE target is not an actual canonical enemy");action.targets.push_back(slot);}
        return action;
    };
    source->ai=[policy](const auto& snapshot,std::uint8_t enemy)->std::optional<BattleAction>{
        auto action=policy->ai;action.source=enemy;
        for(std::uint8_t n=0;n<14;++n)if(snapshot.checkpoint.snapshot.actors[n]&&snapshot.checkpoint.snapshot.actors[n]->hp){
            bool live=false;for(const auto& [id,m]:snapshot.members){(void)id;if(!finished(m.status)&&!m.disconnected&&
                m.status!=T::MemberStatus::Withdrawn&&(m.primary_position()==n||(m.pet_position()&&*m.pet_position()==n)))live=true;}
            if(live){action.targets={n};return action;}}
        return std::nullopt; // Explicit CUSTOM lowest-live-slot target policy.
    };
    source->control=[](const auto&,const auto&,bool action2,const auto&) {
        // CUSTOM-0161 chooses an explicit pass for action2 and observes0B.
        // Neither input is treated as full-write or animation-completion proof.
        return action2?OwnedPveRoomHost::Sources::ControlDecision::Pass:OwnedPveRoomHost::Sources::ControlDecision::ObserveOnly;
    };
    source->return_world=[this](const auto& peer,const auto& binding,const auto& m,const auto& context){return return_world(peer,binding,m,context);};
    source->returned=[this](const auto& peer,const auto& binding,const auto& member,const auto& receipt) {
        const auto at=worlds_.find(peer->id());
        need(!stopped_&&at!=worlds_.end()&&at->second.binding.same_binding(binding)&&at->second.return_actors,
            "PvE returned WORLD lost its actual last-written scene source");
        const auto before=*at->second.return_actors;const auto handoff=at->second.handoff;
        const auto movement=at->second.movement;
        const auto returned=peer->owned_pve_return_source(binding);
        need(handoff&&returned&&movement&&movement_.world_location_current(*movement),"PvE return lost its private completed Session/movement lineage");
        handoff->returned(*peer,binding,repository_,receipt,*returned);
        const auto now=visibility_.retained_scene({member.return_position.area,member.return_position.scene});
        const auto init=peer->normal_world_initialization_on_game();
        auto latest=world_reconciliation(*peer,before,now);
        need(!stopped_&&init&&peer->normal_world_initialization_current_on_game(*init)&&movement_.world_location_current(*movement)&&
            same_population(now,visibility_.retained_scene({member.return_position.area,member.return_position.scene})),
            "PvE fresh WORLD catch-up source changed during saved observers");
        // Ordinary WORLD updates after terminal Written, with GAME -> NET FIFO
        // order before explicit input resumption. They are Queued, not another
        // claimed client ACK or terminal full-write receipt.
        if(!latest.empty()) {
            const auto records=RecoveredTaiwanServerRecords::read_aggregate(latest);
            need(records.has_value(),"PvE WORLD catch-up record boundaries invalid");
            std::vector<std::uint8_t> frame;
            for(const auto& record:*records){
                if(frame.size()>RecoveredWorldFrame::max_logical_size-record.bytes.size()){
                    peer->send_world_records(std::move(frame));frame.clear();}
                frame.insert(frame.end(),record.bytes.begin(),record.bytes.end());
            }
            if(!frame.empty())peer->send_world_records(std::move(frame));
        }
        movement_.resume_after_battle(peer->id(),peer->account_id,peer->character_id);
        const auto live=[&] {
            const auto world=worlds_.find(peer->id());
            return !stopped_&&init&&peer->normal_world_initialization_current_on_game(*init)&&
                movement_.world_location_current(*movement)&&
                world!=worlds_.end()&&world->second.binding.same_binding(binding)&&
                movement_.current_world_location(peer->id(),peer->account_id,peer->character_id)==std::optional{member.return_position};
        };
        need(live(),"PvE returned movement handoff retired its exact WORLD owner");
        title(*peer,false);
        need(live(),"PvE returned visibility handoff retired its exact WORLD owner");
        worlds_.erase(peer->id());steps_.erase(peer->id());
    };
    return source;
}
std::vector<std::uint8_t> OwnedPveApplicationSource::return_world(const std::shared_ptr<Session>& peer,
        const Binding& binding,const T::MemberInput& m,const RecoveredWorldRecords::ContextNotification&) {
    const auto at=worlds_.find(peer->id());
    need(!stopped_&&at!=worlds_.end()&&at->second.binding.same_binding(binding),"PvE return retained source missing");
    const auto before=at->second; // Never retain a map iterator across a SQL/provider callback.
    need(peer->owned_pve_current(binding)&&before.movement&&movement_.world_location_current(*before.movement)&&
        before.handoff&&before.handoff->retained_current(*peer,binding)&&
        movement_.current_location(peer->id(),binding.account(),binding.character())==std::optional{m.return_position}&&
        before.position==m.return_position,"PvE return lost its retained actual world/source position");
    const auto resources=db_.recovered_characters().load_resources(binding.account(),binding.character());
    need(resources&&*resources==m.resources,"PvE return resources differ from whole-room committed save");
    const auto row=db_.native_world_entry_writer().load(binding.account(),binding.character(),
        OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::record_kind);
    need(row&&row->record.size()==2&&row->record[0]==0xe8&&row->record[1]<=1&&
        row->source_sha256==OwnedBattleRowPreference::client_pin&&row->source_record==OwnedBattleRowPreference::source_record&&
        NativeWorldEntrySnapshot::same_root(row->root,m.root)&&m.row_preference&&*row==*m.row_preference,
        "PvE return saved row source missing");
    const auto current=visibility_.retained_scene({m.return_position.area,m.return_position.scene});
    std::vector<std::uint8_t> result=row->record;
    const auto pets=db_.companions().load_pet2_slots(binding.account(),binding.character());
    const StoredPet2Slot* active=nullptr;
    for(const auto& pet:pets)if(pet.slot==44){need(!active,"PvE return duplicate active44 source");active=&pet;}
    if(m.pet) {
        need(active&&same_pet(*active,m.pet->saved)&&active->occupied(),"PvE return active44 differs from complete room save");
        // Current aaf0 REA: ordinary E3/FB overwrite the existing native cell;
        // they do not append S30 or need a repeated metadata declaration.
        // Battle frames already update normal caches. This exact saved body
        // makes the final value part of the same full-written Return cohort.
        if(active->pet){const auto bytes=RecoveredPet2Stats::encode_logical(active->pet->stats);
            result.insert(result.end(),bytes.begin(),bytes.end());}
        else {const auto bytes=RecoveredPet1Stats::encode_logical(active->pet1->stats);
            result.insert(result.end(),bytes.begin(),bytes.end());}
    } else need(m.empty_active_pet?(active&&same_pet(*active,*m.empty_active_pet)):!active,
        "PvE return active44 absence source changed");
    // Retained WORLD, never CF/2A/S30. Remove the exact former player set and
    // rebuild it from fresh actual GAME visibility. NPC geometry is retained;
    // this normal legacy source is not a substitute for common-world leases.
    const auto scene=world_reconciliation(*peer,before.actors,current);result.insert(result.end(),scene.begin(),scene.end());
    const auto final=worlds_.find(peer->id());
    need(!stopped_&&final!=worlds_.end()&&final->second.binding.same_binding(binding)&&
        movement_.world_location_current(*before.movement)&&before.handoff->retained_current(*peer,binding)&&
        final->second.position==before.position&&result.size()<=RecoveredTaiwanServerRecords::max_aggregate_logical_size&&peer->owned_pve_current(binding),
        "PvE complete individual return exceeds bounded whole native aggregate/source changed");
    need(same_population(current,visibility_.retained_scene({m.return_position.area,m.return_position.scene})),
        "PvE return population changed during saved source observations");
    final->second.return_actors=current;
    return result;
}
std::vector<std::uint8_t> OwnedPveApplicationSource::world_reconciliation(Session& peer,
        const std::vector<RecoveredVisibility::Presence>& previous,const std::vector<RecoveredVisibility::Presence>& current) {
    std::vector<std::uint8_t> result;
    for(const auto& old:previous)if(old.session!=peer.id()){
        const auto removal=RecoveredRemoteActorRemove::encode_logical(old.departure);result.insert(result.end(),removal.begin(),removal.end());}
    for(const auto& actor:current)if(actor.session!=peer.id()) {
        const auto text=db_.role_text().load(actor.account,actor.character);
        const auto projected=RecoveredPeerRoleText::per_recipient(actor.spawn,text,peer.recovered_client_language()==1?936:950);
        const auto spawn=RecoveredRemoteActor::encode_logical(projected.spawn);result.insert(result.end(),spawn.begin(),spawn.end());
        if(actor.pose){const auto pose=RecoveredCharacterPose::logical(projected.spawn.identity(),*actor.pose);
            need(pose.has_value(),"PvE retained peer pose source invalid");result.insert(result.end(),pose->begin(),pose->end());}
    }
    return result;
}
bool OwnedPveApplicationSource::handle(Session& s,std::span<const RecoveredWorldRecords::Record> records) {
    need(!stopped_&&!retiring_&&!busy_,"PvE Application callback reentered/retired");
    busy_=true;struct End{bool& b;~End(){b=false;}} end{busy_};
    if(host_->bound(s))return host_->handle(s,records);
    const RecoveredSosSupportRequest::Request* request=nullptr;
    for(const auto& r:records){if(std::holds_alternative<RecoveredWorldRecords::Tick>(r))continue;
        if(const auto* value=std::get_if<RecoveredSosSupportRequest::Request>(&r)){
            need(!request,"PvE duplicate support request");request=value;
        }else if(std::holds_alternative<RecoveredSosBattleCommand::Request>(r))throw DatabaseError("SOS action outside an owned room");
        else if(request)throw DatabaseError("SOS request mixed with another mutation");
    }
    if(!request)return false;
    need(!host_->pending(s),"SOS support already has its actual prepared admission");
    need(std::all_of(records.begin(),records.end(),[](const auto& r){return
        std::holds_alternative<RecoveredWorldRecords::Tick>(r)||std::holds_alternative<RecoveredSosSupportRequest::Request>(r);}),
        "SOS support must own the whole callback before any prefix");
    const auto observer=visibility_.snapshot(s.id());
    need(observer&&observer->account==s.account_id&&observer->character==s.character_id,
        "SOS requester lacks its actual normal-world visibility source");
    const auto peers=visibility_.retained_scene(observer->location);
    need(std::any_of(peers.begin(),peers.end(),[&](const auto& p){return p.session!=s.id()&&p.spawn.identity()==request->target;}),
        "SOS selected target is not in this actual scene's world actor source");
    host_->support(s.shared_from_this(),*request);return true;
}
void OwnedPveApplicationSource::observe_movement(Session& s,std::span<const RecoveredWorldRecords::Record> records,
        std::span<const std::uint8_t> response) {
    if(stopped_||retiring_||host_->bound(s)||host_->pending(s)||response.empty())return;
    const auto count=std::count_if(records.begin(),records.end(),[](const auto& r){return std::holds_alternative<RecoveredMovement::Request>(r);});
    if(!count)return;
    const auto init=s.normal_world_initialization();const auto position=movement_.current_world_location(s.id(),s.account_id,s.character_id);
    if(!init||!init->entry_written()||!position)return;
    const auto normal=RecoveredNormalCompanionCurrent::capture(s,movement_,[this]{return !stopped_&&!retiring_;},position);
    if(!normal)return;
    const auto* policy=catalog_->scene(position->area,position->scene);if(!policy)return;
    if(!catalog_->has_actor_profile(s.character_id)||!visibility_.contains(s.id()))return;
    auto& steps=steps_[s.id()];need(std::uint64_t(count)<=UINT64_MAX-steps,"PvE movement source count exhausted");steps+=std::uint64_t(count);
    if(steps<policy->movement_steps)return;
    auto capture=s.current_world_response_capture_on_game();if(!capture)capture=s.observe_world_response(response);
    need(capture->wire()==std::vector<std::uint8_t>(response.begin(),response.end()),"PvE encounter lost original complete movement reply");
    s.hold_world_input_until_response_written(*capture);
    need(normal->current(),"PvE movement reply lost its original normal source");
    pending_.insert_or_assign(s.id(),Pending{s.shared_from_this(),*init,*capture,*position,*normal});
}
void OwnedPveApplicationSource::poll() {
    if(stopped_||retiring_)return;
    for(auto it=pending_.begin();it!=pending_.end();) {
        const auto source=it->second;const auto peer=source.session.lock();
        if(peer&&(host_->bound(*peer)||host_->pending(*peer))){it=pending_.erase(it);continue;}
        if(!peer||peer->closing()||!source.current.current()||source.written.status()==Session::WorldResponseWriteStatus::Failed||
           !peer->normal_world_initialization_current_on_game(source.initialization)||
           movement_.current_world_location(peer->id(),peer->account_id,peer->character_id)!=std::optional{source.position}){
            it=pending_.erase(it);continue;}
        if(source.written.status()!=Session::WorldResponseWriteStatus::Written||!peer->owned_pve_entry_available_on_game()){++it;continue;}
        const auto* policy=catalog_->scene(source.position.area,source.position.scene);
        it=pending_.erase(it); // One actual attempt; NEVER retry an unknown durable outcome.
        if(!policy)continue;
        try {host_->create({peer},sources(*policy));steps_.erase(peer->id());}
        catch(const std::exception& error){spdlog::warn("OWNED_PVE_ENTRY_REFUSED session={} reason={}",peer->id(),error.what());
            if(host_->bound(*peer))peer->close();else worlds_.erase(peer->id());}
        if(stopped_||retiring_)break;
        it=pending_.begin(); // Supplier may have retired/erased any other pending member.
    }
}
void OwnedPveApplicationSource::disconnected(Session& s) {
    pending_.erase(s.id());steps_.erase(s.id());host_->disconnected(s);worlds_.erase(s.id());
}
void OwnedPveApplicationSource::retire_dispatch()noexcept {
    if(retiring_)return;retiring_=true;pending_.clear();if(host_)host_->retire_dispatch();
}
void OwnedPveApplicationSource::stop()noexcept{if(stopped_)return;stopped_=true;if(host_)host_->stop();pending_.clear();worlds_.clear();}
}
