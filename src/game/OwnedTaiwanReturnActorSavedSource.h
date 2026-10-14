#pragma once
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "db/NativeEquipmentSnapshotRepository.h"
#include "db/OwnedInventoryRepository.h"
#include "game/OwnedTaiwanPkReturnRoleTextSource.h"
#include "game/SharedWorldPresence.h"
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
class SqliteDatabase;
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
        bool operator==(const Readset& other) const noexcept {return data_==other.data_;}
    private:
        friend class OwnedTaiwanReturnActorSavedSource;
        explicit Readset(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    using Snapshot=Readset;
    OwnedTaiwanReturnActorSavedSource(const OwnedTaiwanReturnActorSavedSource&)=delete;
    OwnedTaiwanReturnActorSavedSource& operator=(const OwnedTaiwanReturnActorSavedSource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_readset(const Readset&) const noexcept;
    std::optional<Readset> observe_population(std::span<const SharedWorldPresence::ReadyCharacter>) const;
    bool current(const Readset&) const;
    bool current_with_role_text(const Readset&,const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>&,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::Observation>,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::EndpointObservation>) const;
    // Borrow the actual room connection/transaction. No BEGIN/COMMIT, Session,
    // Presence observer, provider, live Current or new observation in this cut.
    bool stored_current_in_scope(sqlite3*,const Readset&) const;
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
    std::optional<Material> read_actor(const SharedWorldPresence::ReadyCharacter&,sqlite3_int64) const;
    bool stored(const Readset&,sqlite3_int64) const;
};
}
