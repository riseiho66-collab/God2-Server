#pragma once
#include "game/OwnedTaiwanPkCombatSource.h"
#include "handlers/OwnedSkillBookLearningService.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include "db/SqliteRoleTextRepository.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0107 complete owned normal-player S1C projection. Actual primary and
// saved secondary text supply the two consumed strings. Variant2000, ordinal0
// and statusDWORD0 are explicit restricted server policy, NOT native defaults
// or unused padding. Borrowed concrete repositories must outlive receipts.
class OwnedTaiwanPkPlayerEntrySource final {
    struct State;
public:
    struct Material {
        RecoveredRoleText::Text primary_source;
        std::uint16_t primary_codepage;
        std::string primary_utf8;
        StoredRoleText secondary; // Missing is rejected; saved empty is distinct.
        std::uint8_t level;
        bool operator==(const Material&)const=default;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&& other)noexcept:state_(other.state_),material_(other.material_){}
        Observation& operator=(Observation&& other)noexcept{state_=other.state_;material_=other.material_;return *this;}
        const Material& material()const noexcept{return *material_;}
        const OwnedTaiwanPkCombatSource::Observation& combat()const noexcept;
        std::uint16_t recipient_codepage()const;
        TaiwanWorldEntryIdentity identity_profile()const noexcept;
        RecoveredBattleIdentity::Record identity(std::uint8_t position,std::uint16_t recipient_codepage)const;
        bool current()const;
        bool matches_learning_source(const OwnedSkillBookLearningService::WrittenLearningSource&)const noexcept;
        bool uses_connection(const sqlite3*)const noexcept;
        bool stored_current_in_room_transaction(sqlite3*)const;
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkPlayerEntrySource;
        Observation(std::shared_ptr<State> state,std::shared_ptr<const Material> material)
            :state_(std::move(state)),material_(std::move(material)){}
        std::shared_ptr<State> state_;
        std::shared_ptr<const Material> material_;
    };
    static std::optional<Observation> observe(sqlite3*,SqliteRoleTextRepository&,
        OwnedTaiwanPkCombatSource::Observation,
        TaiwanWorldEntryIdentity=TaiwanWorldEntryIdentity::SelectedCharacter);
    static std::optional<Observation> observe_after_learning(sqlite3*,SqliteRoleTextRepository&,
        OwnedTaiwanPkCombatSource::Observation,const Observation&,
        OwnedSkillBookLearningService::WrittenLearningSource,std::shared_ptr<Session>);
private:
    struct LearningLineage {
        const Observation predecessor;
        const OwnedSkillBookLearningService::WrittenLearningSource source;
        const std::weak_ptr<Session> session;
    };
    struct State {
        sqlite3* db;
        SqliteRoleTextRepository& texts;
        OwnedTaiwanPkCombatSource::Observation combat;
        const TaiwanWorldEntryIdentity identity_profile;
        const std::thread::id thread=std::this_thread::get_id();
        bool reading=false,reentered=false;
        std::shared_ptr<const LearningLineage> learning{}; // Only genuine Written successor mode.
        struct Operation {
            State& state;
            explicit Operation(State& s):state(s){
                if(s.thread!=std::this_thread::get_id())throw std::logic_error("TW PK player source game owner mismatch");
                if(s.reading){s.reentered=true;throw std::logic_error("TW PK player source reentry");}
                s.reading=true;s.reentered=false;
            }
            ~Operation(){state.reading=false;}
        };
        struct ReadScope {
            sqlite3* db;bool finished=false;
            explicit ReadScope(sqlite3* value):db(value){
                if(!sqlite3_get_autocommit(db))throw DatabaseError("TW PK player source needs its own read scope");
                sqlite_detail::execute(db,"BEGIN");
            }
            ~ReadScope(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
            void finish(){sqlite_detail::execute(db,"COMMIT");finished=true;}
        };
        bool owns(const sqlite3* supplied)const noexcept{
            return supplied==db&&texts.uses_connection(db)&&combat.uses_connection(db);
        }
        void namespaces(){
            sqlite_detail::Statement shadows(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('character_role_text','recovered_characters') OR tbl_name COLLATE NOCASE IN ('character_role_text','recovered_characters')");
            if(shadows.row())throw DatabaseError("TW PK player text TEMP shadow rejected");
            sqlite_detail::Statement tables(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('character_role_text','recovered_characters')");
            if(!tables.row()||tables.integer(0)!=2||tables.row())throw DatabaseError("TW PK player text requires actual main tables");
        }
        std::optional<Material> read(){
            if(!owns(db)||sqlite3_get_autocommit(db)||reentered)return {};
            namespaces();
            if(!combat.stored_current_in_room_transaction(db))return {};
            const auto& appearance=combat.appearance().material();
            const auto& root=appearance.equipment.root;
            const auto role=RecoveredRoleLevel::parse(combat.material().role.logical);
            if(!root.id||root.id!=appearance.lease.character||
               !valid_taiwan_world_entry_identity(identity_profile)||
               !qualified_taiwan_scene_handle(appearance.lease.actor_handle)||
               (identity_profile==TaiwanWorldEntryIdentity::QualifiedSceneHandle&&
                   !combat.appearance().qualified_scene_identity())||
               (identity_profile==TaiwanWorldEntryIdentity::SelectedCharacter&&
                   (root.id>0xfff||root.id!=appearance.lease.actor_handle))||
               appearance.config_flag>1||!role||!role->level()||
               (root.name_codepage!=936&&root.name_codepage!=950))return {};
            const auto secondary=texts.load(root.account_id,root.id);
            if(!secondary)return {}; // Never fabricate an absent saved title.
            RecoveredRoleText::Text primary;
            std::copy_n(root.profile.begin(),primary.size(),primary.begin());
            const auto end=std::find(primary.begin(),primary.end(),0);
            if(end==primary.begin()||end==primary.end())return {};
            const std::string bytes(reinterpret_cast<const char*>(primary.data()),
                static_cast<std::size_t>(end-primary.begin()));
            std::string utf8;
            try{
                utf8=LegacyChineseCodec::decode(bytes,root.name_codepage==936);
                if(LegacyChineseCodec::encode(utf8,root.name_codepage==936)!=bytes)return {};
            }catch(const std::exception&){return {};}
            namespaces();
            return reentered?std::nullopt:std::optional{Material{primary,root.name_codepage,
                std::move(utf8),*secondary,role->level()}};
        }
        bool learning_current(){
            if(!learning)return true;
            const auto peer=learning->session.lock();
            return peer&&learning->source.current(*peer)&&!reentered;
        }
        bool current(const Material& expected){
            Operation operation(*this);
            if(!owns(db)||!sqlite3_get_autocommit(db)||!learning_current()||!combat.current())return false;
            std::optional<Material> actual;
            {ReadScope scope(db);actual=read();scope.finish();}
            return actual&&*actual==expected&&!reentered&&learning_current()&&!reentered&&
                combat.current()&&!reentered&&learning_current()&&!reentered;
        }
        bool stored_current(const Material& expected,sqlite3* supplied){
            Operation operation(*this);
            if(!owns(supplied)||sqlite3_get_autocommit(db))return false;
            const auto actual=read();return actual&&*actual==expected&&!reentered;
        }
    };
};
inline const OwnedTaiwanPkCombatSource::Observation& OwnedTaiwanPkPlayerEntrySource::Observation::combat()const noexcept{
    return state_->combat;
}
inline TaiwanWorldEntryIdentity OwnedTaiwanPkPlayerEntrySource::Observation::identity_profile()const noexcept{
    return state_->identity_profile;
}
inline std::uint16_t OwnedTaiwanPkPlayerEntrySource::Observation::recipient_codepage()const{
    // Actual accepted tail grammar admits only0/1, and Session stores this
    // exact flag as client language. No arbitrary nonzero-to-page conversion.
    const auto flag=state_->combat.appearance().material().config_flag;
    if(flag>1)throw std::invalid_argument("TW PK recipient language is not qualified");
    return flag==1?936:950;
}
inline RecoveredBattleIdentity::Record OwnedTaiwanPkPlayerEntrySource::Observation::identity(
        std::uint8_t position,std::uint16_t page)const{
    if((position!=0&&position!=14)||(page!=936&&page!=950))
        throw std::invalid_argument("TW PK player identity requires exact relative slot and recipient page");
    const auto secondary=SqliteRoleTextRepository::project(material_->secondary,page);
    if(!secondary)throw std::invalid_argument("TW PK secondary text cannot project losslessly");
    const auto primary=LegacyChineseCodec::encode(material_->primary_utf8,page==936);
    if(primary.empty()||primary.size()>15||primary.find('\0')!=std::string::npos||
       LegacyChineseCodec::decode(primary,page==936)!=material_->primary_utf8)
        throw std::invalid_argument("TW PK primary name cannot project losslessly");
    const auto& lease=state_->combat.appearance().material().lease;
    // Only the genuine private INIT/equipment/Lease source may select this
    // independent native actor. Saved owner/text identity remains full64.
    const auto character=state_->identity_profile==TaiwanWorldEntryIdentity::QualifiedSceneHandle?
        lease.actor_handle:lease.character;
    if(!character||character>0xfff)throw std::invalid_argument("TW PK player identity exceeds qualified domain");
    RecoveredBattleIdentity::Bytes bytes{};
    bytes[0]=0x1c;bytes[1]=position;bytes[2]=material_->level;
    bytes[3]=static_cast<std::uint8_t>(character);bytes[4]=static_cast<std::uint8_t>(character>>8);
    bytes[6]=0x20; // CUSTOM-0107 exact normal player variant2000.
    // WORD7=0: no extra ordinal marker; DWORD41=0: normal status0, not9/149.
    // Both are consumed semantic policy, not unknown-field padding.
    std::copy(primary.begin(),primary.end(),bytes.begin()+9);
    std::copy(secondary->begin(),secondary->end(),bytes.begin()+25);
    return *RecoveredBattleIdentity::parse_logical(bytes);
}
inline bool OwnedTaiwanPkPlayerEntrySource::Observation::current()const{return state_->current(*material_);}
inline bool OwnedTaiwanPkPlayerEntrySource::Observation::uses_connection(const sqlite3* db)const noexcept{
    return state_->owns(db);
}
inline bool OwnedTaiwanPkPlayerEntrySource::Observation::stored_current_in_room_transaction(sqlite3* db)const{
    return state_->stored_current(*material_,db);
}
// CUSTOM-0148: distinct genuine learned graph. The original remains immutable.
inline bool OwnedTaiwanPkPlayerEntrySource::Observation::matches_learning_source(
        const OwnedSkillBookLearningService::WrittenLearningSource& source)const noexcept{
    return state_->learning&&state_->learning->source==source;
}
inline std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> OwnedTaiwanPkPlayerEntrySource::observe_after_learning(
        sqlite3* db,SqliteRoleTextRepository& texts,OwnedTaiwanPkCombatSource::Observation combat,
        const Observation& predecessor,OwnedSkillBookLearningService::WrittenLearningSource source,
        std::shared_ptr<Session> peer){
    if(!peer||!predecessor.uses_connection(db)||!combat.uses_connection(db)||!source.current(*peer))return {};
    const auto previous=predecessor.state_->learning?
        std::optional<OwnedSkillBookLearningService::LearningPublication>{predecessor.state_->learning->source.publication()}:
        std::nullopt;
    if(!source.follows(previous))return {};
    const auto& before=predecessor.combat().appearance();const auto& next=combat.appearance();
    const auto& b=before.material();const auto& n=next.material();
    // Full immediate-before/after tuples, not a new observation of the old state.
    // Only book-bank bytes/provenance/revisions may advance; world, DA, role,
    // actual published resources, auxiliary and text must remain exactly stable.
    if(b.inventory!=source.before_source().inventory()||b.equipment!=source.before_source().equipment()||
       n.inventory!=source.after_source().inventory()||n.equipment!=source.after_source().equipment()||
       !before.owns_initialization(source.initialization())||!next.owns_initialization(source.initialization())||
       b.lease!=n.lease||b.battle_generation!=n.battle_generation||b.world!=n.world||
       b.entry_frame!=n.entry_frame||b.entry_logical!=n.entry_logical||b.accepted_tail!=n.accepted_tail||
       b.config_flag!=n.config_flag||b.appearance!=n.appearance||
       !NativeEquipmentSnapshot::same_root(b.equipment.root,n.equipment.root)||
       b.equipment.position!=n.equipment.position||b.equipment.actor_handle!=n.equipment.actor_handle||
       b.equipment.record.size()!=NativeEquipmentSnapshot::record_bytes||
       n.equipment.record.size()!=NativeEquipmentSnapshot::record_bytes||
       !std::equal(b.equipment.record.begin()+NativeEquipmentSnapshot::inventory_bytes,b.equipment.record.end(),
           n.equipment.record.begin()+NativeEquipmentSnapshot::inventory_bytes)||
       predecessor.combat().material()!=combat.material())return {};
    auto result=observe(db,texts,std::move(combat),predecessor.identity_profile());
    if(!result||result->material()!=predecessor.material()||!source.current(*peer))return {};
    auto lineage=std::make_shared<const LearningLineage>(LearningLineage{predecessor,source,peer});
    result->state_->learning=std::move(lineage); // New private graph, never changes predecessor.
    if(!result->current()||!result->matches_learning_source(source))return {};
    return result;
}
inline std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> OwnedTaiwanPkPlayerEntrySource::observe(
        sqlite3* db,SqliteRoleTextRepository& texts,OwnedTaiwanPkCombatSource::Observation combat,
        TaiwanWorldEntryIdentity identity){
    if(!valid_taiwan_world_entry_identity(identity)||!db||!texts.uses_connection(db)||!combat.uses_connection(db)||
       !sqlite3_get_autocommit(db)||!combat.current())return {};
    auto state=std::make_shared<State>(State{db,texts,std::move(combat),identity});
    std::optional<Material> material;
    {State::Operation operation(*state);State::ReadScope scope(db);material=state->read();scope.finish();}
    if(!material)return {};
    auto saved=std::make_shared<const Material>(std::move(*material));
    if(!state->current(*saved))return {};
    return Observation(std::move(state),std::move(saved));
}
}
