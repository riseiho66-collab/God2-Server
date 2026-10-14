#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "db/SqliteSupport.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0105 explicit owned presentation projection, NOT a recovered original
// world->battle producer, action/equip permission or equal rendered appearance.
// Borrowed concrete repositories/connection must outlive every Observation and
// PK ticket. Live Current runs on game outside SQL scopes; RESERVED closed
// tuple reads borrow the actual room SQL scope and invoke no live callbacks.
class OwnedTaiwanPkAppearanceSource final {
    struct State;
public:
    struct Material {
        SharedWorldPresence::Lease lease; // Registry generation, NOT PK peer generation.
        std::uint64_t battle_generation;
        NativeWorldEntrySnapshot world;
        OwnedInventorySnapshot inventory;
        NativeEquipmentSnapshot equipment; // Full1215, INCLUDING trailing DA15.
        RecoveredWorldEntry::Frame entry_frame; // Actual typed40B, logical37.
        std::vector<std::uint8_t> entry_logical,accepted_tail;
        std::uint8_t config_flag;
        RecoveredBattlePlayerAppearance::Record appearance;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&& v)noexcept:state_(v.state_),material_(v.material_){}
        Observation& operator=(Observation&& v)noexcept{state_=v.state_;material_=v.material_;return *this;}
        const Material& material()const noexcept{return *material_;}
        bool current()const;
        bool uses_connection(const sqlite3*)const noexcept;
        // Identity only; no new qualifier supplied by the caller.
        bool owns_characters(const SqliteRecoveredCharacterRepository&)const noexcept;
        // CUSTOM-0113 identity only; valid independently of a live world phase.
        bool owns_presence(const std::shared_ptr<SharedWorldPresence>&)const noexcept;
        bool owns_initialization(const Session::NormalWorldInitialization&)const noexcept;
        bool qualified_scene_identity()const noexcept;
        // CUSTOM-0106 RESERVED read-only SQL fence, never a live Session grant.
        // No joint Current/Session/presence callbacks or nested read transaction.
        bool stored_current_in_room_transaction(sqlite3*)const;
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkAppearanceSource;
        Observation(std::shared_ptr<State> state,std::shared_ptr<const Material> material)
            :state_(std::move(state)),material_(std::move(material)){}
        std::shared_ptr<State> state_;
        std::shared_ptr<const Material> material_;
    };
    static std::optional<Observation> observe(std::shared_ptr<SqliteOwnedEquipmentTransaction>,
        const SqliteAccountRepository&,SqliteRecoveredCharacterRepository&,
        SqliteNativeWorldEntrySnapshotRepository&,std::shared_ptr<SharedWorldPresence>,
        std::weak_ptr<Session>,Session::NormalWorldInitialization,SharedWorldPresence::Lease,
        SqliteOwnedEquipmentTransaction::Committed);
private:
    struct State {
        std::shared_ptr<SqliteOwnedEquipmentTransaction> joint;
        const SqliteAccountRepository& accounts;
        SqliteRecoveredCharacterRepository& characters;
        SqliteNativeWorldEntrySnapshotRepository& worlds;
        std::shared_ptr<SharedWorldPresence> presence;
        std::weak_ptr<Session> session;
        Session::NormalWorldInitialization initialization;
        // CUSTOM-0116 exact actual prebattle phase, private to this live source.
        // Normal native bootstrap retains CharacterSelected; never promote it.
        const SessionState prebattle_phase;
        SqliteOwnedEquipmentTransaction::Committed committed;
        const std::thread::id thread=std::this_thread::get_id();
        bool reading=false,reentered=false;
        bool stored_current_in_room_transaction(const Material& m,sqlite3* db){
            if(thread!=std::this_thread::get_id())throw std::logic_error("TW PK appearance game owner mismatch");
            if(reading){reentered=true;return false;}
            reading=true;reentered=false;
            struct End{bool& busy;~End(){busy=false;}}end{reading};
            if(!characters.uses_connection(db)||sqlite3_get_autocommit(db)||
               !joint->owns_sources(accounts,characters)||!worlds.owns_sources(accounts,characters))return false;
            // These concrete readers borrow this exact SQL scope; their full
            // snapshot/namespace checks remain in force. No callbacks run here.
            const auto equipment=joint->equipment_writer().load(m.lease.account,m.lease.character,
                m.equipment.client_sha256,m.equipment.record_kind);
            const auto inventory=joint->inventory_writer().load(m.lease.account,m.lease.character);
            const auto world=worlds.load(m.lease.account,m.lease.character,m.world.client_sha256,m.world.record_kind);
            if(equipment!=std::optional{m.equipment}||inventory!=std::optional{m.inventory}||
               world!=std::optional{m.world})return false;
            std::size_t found=0;
            for(const auto& root:characters.list_for_account(m.lease.account))if(root.id==m.lease.character){
                if(!NativeEquipmentSnapshot::same_root(root,m.equipment.root))return false;
                ++found;
            }
            return found==1&&characters.load_position(m.lease.account,m.lease.character)==
                std::optional{m.equipment.position}&&!reentered;
        }
        bool current(const Material& m){
            if(thread!=std::this_thread::get_id())throw std::logic_error("TW PK appearance game owner mismatch");
            if(reading){reentered=true;return false;}
            reading=true;reentered=false;
            struct End{bool& busy;~End(){busy=false;}}end{reading};
            const auto qualify=[&]{
                // Private captured entry receipt is checked BEFORE Session fields.
                const auto peer=session.lock();
                if(reentered||!peer||!peer->normal_world_initialization_current_on_game(initialization)||
                   !initialization.entry_written())return false;
                if(peer->closing()||peer->state()!=prebattle_phase||peer->id()!=m.lease.session||
                   peer->account_id!=m.lease.account||peer->character_id!=m.lease.character||
                   peer->battle_generation()!=m.battle_generation||
                   initialization.entry_frame()!=m.entry_frame||initialization.entry_logical()!=m.entry_logical||
                   initialization.accepted_tail()!=m.accepted_tail||initialization.config_flag()!=m.config_flag||
                   !joint->owns_sources(accounts,characters)||!worlds.owns_sources(accounts,characters)||
                   !presence->owns_repository(characters))return false;
                const auto actual=presence->ready_lease(m.lease.session,m.lease.account,m.lease.character);
                if(reentered||!actual||*actual!=m.lease)return false;
                const auto saved=presence->saved_position(m.lease);
                return !reentered&&saved&&*saved==m.equipment.position;
            };
            const auto stored=[&]{
                const auto world=worlds.load(m.lease.account,m.lease.character,m.world.client_sha256,m.world.record_kind);
                return !reentered&&world&&*world==m.world;
            };
            // committed_current owns its consistent read transaction. Never call
            // this Current from inside the room's reservation/activation SQL tx.
            return qualify()&&stored()&&joint->committed_current(committed)&&qualify()&&stored()&&
                joint->committed_current(committed)&&qualify()&&!reentered;
        }
    };
};
inline bool OwnedTaiwanPkAppearanceSource::Observation::current()const{
    return state_->current(*material_);
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::owns_presence(
    const std::shared_ptr<SharedWorldPresence>& presence)const noexcept{
    return state_ && presence && state_->presence==presence;
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::owns_initialization(
    const Session::NormalWorldInitialization& initialization)const noexcept{
    return state_&&state_->initialization.same_initialization(initialization);
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::qualified_scene_identity()const noexcept{
    return state_->initialization.qualified_scene_identity();
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::uses_connection(const sqlite3* db)const noexcept{
    return state_->characters.uses_connection(db);
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::owns_characters(const SqliteRecoveredCharacterRepository& c)const noexcept{
    return &state_->characters==&c;
}
inline bool OwnedTaiwanPkAppearanceSource::Observation::stored_current_in_room_transaction(sqlite3* db)const{
    return state_->stored_current_in_room_transaction(*material_,db);
}
inline std::optional<OwnedTaiwanPkAppearanceSource::Observation> OwnedTaiwanPkAppearanceSource::observe(
        std::shared_ptr<SqliteOwnedEquipmentTransaction> joint,const SqliteAccountRepository& accounts,
        SqliteRecoveredCharacterRepository& characters,SqliteNativeWorldEntrySnapshotRepository& worlds,
        std::shared_ptr<SharedWorldPresence> presence,std::weak_ptr<Session> session,
        Session::NormalWorldInitialization initialization,SharedWorldPresence::Lease lease,
        SqliteOwnedEquipmentTransaction::Committed committed){
    const auto peer=session.lock();
    if(!peer||!peer->normal_world_initialization_current_on_game(initialization)||
       !initialization.entry_written())return {};
    // Capture only after the actual private game-owner receipt qualifies reads.
    const auto prebattle_phase=peer->state();
    if(prebattle_phase!=SessionState::CharacterSelected&&prebattle_phase!=SessionState::InWorld)return {};
    if(!joint||!presence||!joint->owns_sources(accounts,characters)||!worlds.owns_sources(accounts,characters)||
       !presence->owns_repository(characters)||peer->closing()||peer->state()!=prebattle_phase||
       peer->id()!=lease.session||peer->account_id!=lease.account||peer->character_id!=lease.character)return {};
    const auto& equipment=committed.equipment().snapshot();
    const auto& inventory=committed.inventory().snapshot();
    auto world=worlds.load(lease.account,lease.character,NativeEquipmentSnapshot::client_pin,"tw.world-entry.2a.zero-seed");
    const auto& frame=initialization.entry_frame();
    const auto entry=RecoveredWorldEntryView::read(frame);
    const auto da=equipment.appearance();
    if(!world||!entry||!da||!world->revision||!world->position.revision||
       world->client_sha256!=NativeEquipmentSnapshot::client_pin||world->record_kind!="tw.world-entry.2a.zero-seed"||
       world->record.size()!=RecoveredWorldEntry::Frame{}.size()||
       !std::equal(world->record.begin(),world->record.end(),frame.begin())||world->position!=lease.position||
       !NativeWorldEntrySnapshot::same_root(world->root,equipment.root)||
       !OwnedInventorySnapshot::same_root(inventory.root,equipment.root)||
       equipment.root.id!=lease.character||equipment.root.account_id!=lease.account||
       equipment.client_sha256!=NativeEquipmentSnapshot::client_pin||equipment.record_kind!=NativeEquipmentSnapshot::kind||
       equipment.actor_handle!=lease.actor_handle||entry->actor_handle!=lease.actor_handle||
       da->actor_identity()!=lease.actor_handle||entry->area!=lease.position.area||entry->scene!=lease.position.scene||
       entry->x!=lease.position.x||entry->y!=lease.position.y||
       initialization.entry_logical()!=std::vector<std::uint8_t>(entry->logical.begin(),entry->logical.end()))return {};
    const auto& raw=RecoveredTaiwanPlayerAppearanceUpdate::encode_logical(*da);
    // Explicit restricted CUSTOM domain, not a necessary native ordinary rule.
    if(entry->entry_appearance_baseline().transform_key||raw[3]||raw[4])return {};
    RecoveredBattlePlayerAppearance::Bytes projected{0x86,4,0,1};
    std::copy_n(raw.begin()+7,8,projected.begin()+4);
    // logical12/15/16 are canonical zero ONLY in this branch-qualified policy;
    // mode1 and specialWORD0 are explicit policy, not inferred from DA scalars.
    const auto appearance=RecoveredBattlePlayerAppearance::parse(projected);
    if(!appearance)return {};
    auto material=std::make_shared<const Material>(Material{lease,peer->battle_generation(),std::move(*world),
        inventory,equipment,frame,initialization.entry_logical(),initialization.accepted_tail(),
        initialization.config_flag(),*appearance});
    auto state=std::make_shared<State>(State{std::move(joint),accounts,characters,worlds,std::move(presence),
        std::move(session),std::move(initialization),prebattle_phase,std::move(committed)});
    if(!state->current(*material))return {};
    return Observation(std::move(state),std::move(material));
}
}
