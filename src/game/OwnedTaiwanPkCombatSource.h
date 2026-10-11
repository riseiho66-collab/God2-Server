#pragma once
#include "game/OwnedTaiwanPkAppearanceSource.h"
#include "game/Battle.h"
#include "db/SqliteRoleAuxiliaryRepository.h"
#include "db/SqliteSupport.h"
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0106 adopts actual stored server values under an explicit policy.
// The old6bf snapshot/origin label is NOT current149c native stat authority.
// No base/equipment aggregation, formula, skill or default value is invented.
// Borrowed concrete repositories/connection must outlive all retained receipts.
class OwnedTaiwanPkCombatSource final {
    struct State;
public:
    static constexpr const char* legacy_client_pin="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
    static constexpr const char* legacy_design="CUSTOM-0045";
    struct Material {
        CharacterRoleSnapshot role;
        CharacterResources resources;
        RoleAuxiliarySnapshot auxiliary; // Complete61, revision and original labels.
        bool operator==(const Material&)const=default;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&& v)noexcept:state_(v.state_),material_(v.material_){}
        Observation& operator=(Observation&& v)noexcept{state_=v.state_;material_=v.material_;return *this;}
        const Material& material()const noexcept{return *material_;}
        const OwnedTaiwanPkAppearanceSource::Observation& appearance()const noexcept;
        BattleActor actor(std::uint8_t relative_position)const;
        bool current()const;
        bool uses_connection(const sqlite3*)const noexcept;
        bool stored_current_in_room_transaction(sqlite3*)const;
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkCombatSource;
        Observation(std::shared_ptr<State> state,std::shared_ptr<const Material> material)
            :state_(std::move(state)),material_(std::move(material)){}
        std::shared_ptr<State> state_;
        std::shared_ptr<const Material> material_;
    };
    static std::optional<Observation> observe(sqlite3*,SqliteRecoveredCharacterRepository&,
        SqliteRoleAuxiliaryRepository&,OwnedTaiwanPkAppearanceSource::Observation);
private:
    struct State {
        sqlite3* db;
        SqliteRecoveredCharacterRepository& characters;
        SqliteRoleAuxiliaryRepository& auxiliary;
        OwnedTaiwanPkAppearanceSource::Observation appearance;
        const std::thread::id thread=std::this_thread::get_id();
        bool reading=false,reentered=false;
        struct Operation {
            State& state;
            explicit Operation(State& s):state(s){
                if(s.thread!=std::this_thread::get_id())throw std::logic_error("TW PK combat game owner mismatch");
                if(s.reading){s.reentered=true;throw std::logic_error("TW PK combat source reentry");}
                s.reading=true;s.reentered=false;
            }
            ~Operation(){state.reading=false;}
        };
        struct ReadScope {
            sqlite3* db;bool finished=false;
            explicit ReadScope(sqlite3* p):db(p){
                if(!sqlite3_get_autocommit(db))throw DatabaseError("TW PK combat needs its own read scope");
                sqlite_detail::execute(db,"BEGIN");
            }
            ~ReadScope(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
            void finish(){sqlite_detail::execute(db,"COMMIT");finished=true;}
        };
        bool owns(sqlite3* supplied)const noexcept{
            return supplied==db&&characters.uses_connection(db)&&auxiliary.uses_connection(db)&&
                appearance.uses_connection(db)&&appearance.owns_characters(characters);
        }
        void namespaces(){
            // Existing legacy readers have unqualified names. Reject shadows,
            // and require their real main tables before calling those readers.
            sqlite_detail::Statement shadows(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_role_snapshots','character_resources','character_role_auxiliary_snapshots') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_role_snapshots','character_resources','character_role_auxiliary_snapshots')");
            if(shadows.row())throw DatabaseError("TW PK combat TEMP shadow rejected");
            sqlite_detail::Statement tables(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_role_snapshots','character_resources','character_role_auxiliary_snapshots')");
            if(!tables.row()||tables.integer(0)!=6||tables.row())throw DatabaseError("TW PK combat requires actual main tables");
        }
        std::optional<Material> read(){
            if(!owns(db)||sqlite3_get_autocommit(db)||reentered)return {};
            namespaces();
            // Full267 material and common root/current pose use this same
            // already-open scope. No live Session/joint Current runs in SQL.
            if(!appearance.stored_current_in_room_transaction(db))return {};
            const auto& owner=appearance.material().lease;
            const auto role=characters.load_role(owner.account,owner.character);
            const auto resources=characters.load_resources(owner.account,owner.character);
            const auto aux=auxiliary.load(owner.account,owner.character);
            if(!role||!resources||!aux||aux->origin!="NATIVE_CAPTURE_VERIFIED")return {};
            // This label is only the custom policy's stored-data filter, NOT
            // independent proof of capture quality or current native authority.
            const auto parsed=RecoveredRoleLevel::parse(role->logical);
            if(!parsed||role->design_id!="CUSTOM-0013"||resources->design_id!="CUSTOM-0012"||
               !resources->legacy_vitals()||!resources->hp||parsed->max_hp()!=resources->max_hp||
               parsed->max_mp()!=resources->max_mp)return {};
            // Unchanged LegacyCustom Battle admission domain. No native cap,
            // clamp, signed display conversion or Extended64 opt-in is inferred.
            if(resources->max_hp>1'000'000||resources->max_mp>1'000'000||
               RecoveredRoleAuxiliary::physical_attack(aux->logical)>1'000'000||
               RecoveredRoleAuxiliary::magical_attack(aux->logical)>1'000'000||
               RecoveredRoleAuxiliary::physical_defense(aux->logical)>1'000'000||
               RecoveredRoleAuxiliary::magical_defense(aux->logical)>1'000'000)return {};
            namespaces();
            return reentered?std::nullopt:std::optional{Material{*role,*resources,*aux}};
        }
        bool current(const Material& expected){
            Operation operation(*this);
            if(!owns(db)||!sqlite3_get_autocommit(db)||!appearance.current())return false;
            std::optional<Material> actual;
            {ReadScope scope(db);actual=read();scope.finish();}
            return actual&&*actual==expected&&!reentered&&appearance.current()&&!reentered;
        }
        bool stored_current(const Material& expected,sqlite3* supplied){
            Operation operation(*this);
            if(!owns(supplied)||sqlite3_get_autocommit(db))return false;
            const auto actual=read();return actual&&*actual==expected&&!reentered;
        }
    };
};
inline const OwnedTaiwanPkAppearanceSource::Observation& OwnedTaiwanPkCombatSource::Observation::appearance()const noexcept{
    return state_->appearance;
}
inline bool OwnedTaiwanPkCombatSource::Observation::uses_connection(const sqlite3* db)const noexcept{
    return state_->db==db&&state_->characters.uses_connection(db)&&state_->auxiliary.uses_connection(db)&&
        state_->appearance.uses_connection(db)&&state_->appearance.owns_characters(state_->characters);
}
inline bool OwnedTaiwanPkCombatSource::Observation::current()const{return state_->current(*material_);}
inline bool OwnedTaiwanPkCombatSource::Observation::stored_current_in_room_transaction(sqlite3* db)const{
    return state_->stored_current(*material_,db);
}
inline BattleActor OwnedTaiwanPkCombatSource::Observation::actor(std::uint8_t position)const{
    if(position!=0&&position!=14)throw std::invalid_argument("TW PK owned actor requires relative slot0");
    const auto& r=material_->resources;const auto& aux=material_->auxiliary.logical;
    return BattleActor{position,state_->appearance.material().lease.character,r.hp,r.max_hp,r.mp,r.max_mp,
        RecoveredRoleAuxiliary::physical_attack(aux),RecoveredRoleAuxiliary::magical_attack(aux),
        RecoveredRoleAuxiliary::physical_defense(aux),RecoveredRoleAuxiliary::magical_defense(aux)};
}
inline std::optional<OwnedTaiwanPkCombatSource::Observation> OwnedTaiwanPkCombatSource::observe(
        sqlite3* db,SqliteRecoveredCharacterRepository& characters,SqliteRoleAuxiliaryRepository& auxiliary,
        OwnedTaiwanPkAppearanceSource::Observation appearance){
    if(!db||!characters.uses_connection(db)||!auxiliary.uses_connection(db)||
       !appearance.uses_connection(db)||!appearance.owns_characters(characters)||
       !sqlite3_get_autocommit(db)||!appearance.current())return {};
    auto state=std::make_shared<State>(State{db,characters,auxiliary,std::move(appearance)});
    std::optional<Material> material;
    {State::Operation operation(*state);State::ReadScope scope(db);material=state->read();scope.finish();}
    if(!material)return {};
    auto saved=std::make_shared<const Material>(std::move(*material));
    if(!state->current(*saved))return {};
    return Observation(std::move(state),std::move(saved));
}
}
