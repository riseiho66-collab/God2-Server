#pragma once
#include "db/DbTypes.h"
#include "db/AccountRepository.h"
#include "db/CharacterRepository.h"
#include "db/RecoveredCharacterRepository.h"
namespace god2 {
class SqliteOwnedGuildAnnouncementRepository;
class NativeAccountSnapshotRepository;
class NativeCharacterSummarySnapshotRepository;
class NativeWorldEntrySnapshotRepository;
class NativeEquipmentSnapshotRepository;
class OwnedInventoryRepository;
class OrdinaryMovementPolicyRepository;
// Synchronous API. The owner serializes calls on the game executor, not network callbacks.
// Repository references are valid only for the lifetime of the database.
class Database {
public:
    virtual ~Database() = default;
    virtual void initialize() = 0;
    virtual void migrate() = 0;
    virtual AccountRepository& accounts() = 0;
    virtual CharacterRepository& characters() = 0;
    virtual RecoveredCharacterRepository& recovered_characters() = 0;
    // CUSTOM-0150 optional typed shared configuration; access never installs
    // schema/data or invents a native movement policy for unsupported backends.
    virtual OrdinaryMovementPolicyRepository& ordinary_movement_policies() {
        throw UnsupportedDatabaseError("Ordinary movement policy storage is unavailable for this database backend");
    }
    // Optional common read-only delivery source. No schema install/import or
    // implicit profile/entitlement data. Backends opt in independently.
    virtual NativeAccountSnapshotRepository& account_native_snapshots() {
        throw UnsupportedDatabaseError("Native account snapshot storage is unavailable for this database backend");
    }
    virtual NativeCharacterSummarySnapshotRepository& native_character_summaries() {
        throw UnsupportedDatabaseError("Native character summary storage is unavailable for this database backend");
    }
    virtual NativeWorldEntrySnapshotRepository& native_world_entries() {
        throw UnsupportedDatabaseError("Native world entry storage is unavailable for this database backend");
    }
    virtual NativeEquipmentSnapshotRepository& native_equipment_snapshots() {
        throw UnsupportedDatabaseError("Native equipment witness storage is unavailable for this database backend");
    }
    virtual OwnedInventoryRepository& owned_inventory_storage() {
        throw UnsupportedDatabaseError("Shared owned inventory storage is unavailable for this database backend");
    }
    // CUSTOM-0078: optional backend capability; no migration or grants here.
    virtual SqliteOwnedGuildAnnouncementRepository& guild_announcements() {
        throw UnsupportedDatabaseError("Guild announcement storage is unavailable for this database backend");
    }
};
}
