#pragma once
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "db/NativeEquipmentSnapshotRepository.h"
#include "db/OwnedInventoryRepository.h"
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/OwnedTaiwanPkReturnRoleTextSource.h"
#include "game/SharedWorldPresence.h"
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <utility>
#include <variant>
#include <vector>

namespace god2 {
class SqliteDatabase;
class TaiwanInitialNpcSceneObservation;
class SqliteAccountRepository;
class SqliteRecoveredCharacterRepository;
class SqliteNativeWorldEntrySnapshotRepository;
class SqliteNativeEquipmentSnapshotRepository;
class SqliteOwnedInventoryRepository;
// Actual same-DB saved observations only. A delivered native witness may be
// historical; no appearance, resources, audience, permission or wire is minted.
class OwnedTaiwanReturnActorSavedSource final {
    friend class SqliteDatabase;
    struct Identity {};
    struct Data;
    struct ProfileData;
public:
    struct Material {
        SharedWorldPresence::ReadyCharacter actor;
        std::optional<NativeWorldEntrySnapshot> world;
        std::optional<NativeEquipmentSnapshot> equipment;
        OwnedInventorySnapshot inventory;
        bool operator==(const Material&) const;
    };
    class Readset {
    public:
        Readset(const Readset&)=default;
        Readset& operator=(const Readset&)=default;
        Readset(Readset&& other) noexcept:data_(other.data_){}
        Readset& operator=(Readset&& other) noexcept {data_=other.data_;return *this;}
        const std::vector<Material>& materials() const noexcept;
        bool matches_population(std::span<const SharedWorldPresence::ReadyCharacter>) const noexcept;
        bool matches_initial_population(const SharedWorldPresence::InitialPopulation&) const noexcept;
        bool operator==(const Readset& other) const noexcept {return data_==other.data_;}
    private:
        friend class OwnedTaiwanReturnActorSavedSource;
        explicit Readset(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    using Snapshot=Readset;
    class InitialIssuer;
    class PopulationInput final {
    public:
        const std::shared_ptr<OwnedTaiwanReturnActorSavedSource>& source() const noexcept{return source_;}
        // Legacy Ready-only accessor rejects the initial domain rather than
        // manufacturing a ReadyPopulation from a prepared joining actor.
        const SharedWorldPresence::ReadyPopulation& population() const {return std::get<SharedWorldPresence::ReadyPopulation>(population_);}
        std::span<const SharedWorldPresence::ReadyCharacter> characters() const noexcept;
        const SharedWorldPresence::InitialPopulation* initial_population() const noexcept;
        bool population_current(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
        const Readset& readset() const noexcept{return readset_;}
        const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>& role_text_source() const noexcept{return role_text_source_;}
    private:
        friend class SqliteDatabase;
        friend class InitialIssuer;
        PopulationInput(std::shared_ptr<OwnedTaiwanReturnActorSavedSource> source,
            SharedWorldPresence::ReadyPopulation population,Readset readset,
            std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource> role_text_source={})
            :source_(std::move(source)),population_(std::move(population)),readset_(std::move(readset)),
             role_text_source_(std::move(role_text_source)){}
        PopulationInput(std::shared_ptr<OwnedTaiwanReturnActorSavedSource> source,
            SharedWorldPresence::InitialPopulation population,Readset readset,
            std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource> role_text_source)
            :source_(std::move(source)),population_(std::move(population)),readset_(std::move(readset)),
             role_text_source_(std::move(role_text_source)){}
        const std::shared_ptr<OwnedTaiwanReturnActorSavedSource> source_;
        const std::variant<SharedWorldPresence::ReadyPopulation,SharedWorldPresence::InitialPopulation> population_;
        const Readset readset_;
        const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource> role_text_source_;
    };
    // Only the actual database assembles this issuer from its same-connection
    // Saved/Role owners. Issuing input grants no native actor/status authority.
    class InitialIssuer final {
    public:
        InitialIssuer(const InitialIssuer&)=delete;
        InitialIssuer& operator=(const InitialIssuer&)=delete;
        bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
        std::shared_ptr<const PopulationInput> observe(const SharedWorldPresence::InitialPopulation&) const;
    private:
        friend class SqliteDatabase;
        InitialIssuer(std::shared_ptr<OwnedTaiwanReturnActorSavedSource> source,
            std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource> role)
            :source_(std::move(source)),role_(std::move(role)){}
        struct Operation;
        const std::shared_ptr<OwnedTaiwanReturnActorSavedSource> source_;
        const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource> role_;
        const std::thread::id thread_=std::this_thread::get_id();
        mutable bool reading_=false,poisoned_=false;
    };
    // Consistent saved tuple input for explicit CUSTOM fresh projection.
    // No native equip permission, canonical-slot or item-to-appearance authority.
    // Historical snapshots are never rebased or relabelled as current.
    class ProfileEquipment final {
    public:
        ProfileEquipment(const ProfileEquipment&)=default;
        ProfileEquipment& operator=(const ProfileEquipment&)=default;
        ProfileEquipment(ProfileEquipment&& other) noexcept:data_(other.data_){}
        ProfileEquipment& operator=(ProfileEquipment&& other) noexcept{data_=other.data_;return *this;}
        const Readset& saved_readset() const noexcept;
        std::size_t row_index() const noexcept;
        const OwnedInventorySnapshot& inventory() const noexcept;
        const NativeEquipmentSnapshot& equipment() const noexcept;
        bool operator==(const ProfileEquipment& other) const noexcept{return data_==other.data_;}
    private:
        friend class OwnedTaiwanReturnActorSavedSource;
        explicit ProfileEquipment(std::shared_ptr<const ProfileData> data):data_(std::move(data)){}
        std::shared_ptr<const ProfileData> data_;
    };
    OwnedTaiwanReturnActorSavedSource(const OwnedTaiwanReturnActorSavedSource&)=delete;
    OwnedTaiwanReturnActorSavedSource& operator=(const OwnedTaiwanReturnActorSavedSource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_readset(const Readset&) const noexcept;
    bool owns_profile_equipment(const ProfileEquipment&) const noexcept;
    bool profile_equipment_matches(const ProfileEquipment&,const Readset&,std::size_t) const noexcept;
    std::optional<ProfileEquipment> observe_profile_equipment(const Readset&,std::size_t) const;
    bool profile_equipment_current(const ProfileEquipment&) const;
    bool profile_equipment_stored_current_in_scope(sqlite3*,const ProfileEquipment&) const;
    std::optional<Readset> observe_population(std::span<const SharedWorldPresence::ReadyCharacter>) const;
    std::optional<Readset> observe_initial_population(const SharedWorldPresence::InitialPopulation&) const;
    bool current(const Readset&) const;
    bool current_with_role_text(const Readset&,const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>&,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::Observation>,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::EndpointObservation>,
        std::span<const ProfileEquipment> profiles={}) const;
    // Actual initial actor/role/equipment/NPC values share ONE final saved
    // read transaction. The private NPC proof cannot be forged or rebased.
    bool current_with_role_text_and_initial_npc(const Readset&,
        const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>&,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::Observation>,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::EndpointObservation>,
        std::span<const ProfileEquipment>,
        const std::shared_ptr<const TaiwanInitialNpcSceneObservation>&) const;
    // Borrow the actual room connection/transaction. No BEGIN/COMMIT, Session,
    // Presence observer, provider, live Current or new observation in this cut.
    bool stored_current_in_scope(sqlite3*,const Readset&,std::span<const ProfileEquipment> profiles={}) const;
private:
    OwnedTaiwanReturnActorSavedSource(sqlite3*,SqliteAccountRepository&,SqliteRecoveredCharacterRepository&,
        SqliteNativeWorldEntrySnapshotRepository&,SqliteNativeEquipmentSnapshotRepository&,
        SqliteOwnedInventoryRepository&,std::shared_ptr<SharedWorldPresence>,std::weak_ptr<const void>);
    struct Operation;
    struct ReadScope;
    sqlite3* const db_;
    SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    SqliteNativeWorldEntrySnapshotRepository& worlds_;
    SqliteNativeEquipmentSnapshotRepository& equipment_;
    SqliteOwnedInventoryRepository& inventory_;
    mutable SqliteOwnedEquipmentTransaction joint_;
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::weak_ptr<const void> database_lifetime_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool reading_=false,poisoned_=false;
    mutable ReadScope* own_read_scope_=nullptr;
    bool owns_database() const noexcept;
    void fence(sqlite3_int64,bool autocommit) const;
    void namespaces(sqlite3_int64) const;
    bool identity_current(const Readset&) const noexcept;
    bool registry_current(const Readset&) const;
    bool row_live_current(const Readset&,const SharedWorldPresence::ReadyCharacter&) const;
    bool row_retained_current(const Readset&,const SharedWorldPresence::ReadyCharacter&) const;
    bool input_population_current(const PopulationInput&,const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    std::optional<Material> read_actor(const SharedWorldPresence::ReadyCharacter&,sqlite3_int64) const;
    bool stored(const Readset&,sqlite3_int64) const;
    bool profile_shape(const ProfileEquipment&) const noexcept;
    bool profiles_stored(const Readset&,std::span<const ProfileEquipment>,sqlite3_int64) const;
};
}
