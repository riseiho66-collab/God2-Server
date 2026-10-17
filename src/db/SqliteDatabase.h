#pragma once
#include "db/Database.h"
#include "db/SqliteOrdinaryMovementPolicyRepository.h"
#include "relations53/GuildRelations53FactoryDraft.h"
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/EffectiveGuildAdmissionRepositoryDraft.h"
#include "db/EffectiveGuildAnnouncementRepositoryDraft.h"
#include "db/SqliteWorldDisplayRepository.h"
#include "db/SqliteFruitQuestRepository.h"
#include "db/SqliteTradeRepository.h"
#include "db/SqliteBankRepository.h"
#include "db/SqliteBankAccessRepository.h"
#include "db/SqliteBankItemsRepository.h"
#include "db/SqliteOwnedArmorBankRepository.h"
#include "db/SqliteOwnedForeignBankRepository.h"
#include "db/SqliteOwnedInstanceTradeRepository.h"
#include "db/SqliteOwnedMixedBankRepository.h"
#include "db/SqliteOwnedInstanceDiscardRepository.h"
#include "db/NativeFruitQuestSources.h"
#include "db/NativeNpcDisplayCatalog.h"
#include "db/Migration.h"
#include "db/NativeMapCatalog.h"
#include "db/NativeEnemyDisplayCatalog.h"
#include "db/NativeSupplyCatalog.h"
#include "db/NativeSkillCatalog.h"
#include "db/TaiwanInstalledSkillCatalogImport.h"
#include "db/NativeSkillBookCatalog.h"
#include "db/SqliteSkillBookLearningRepository.h"
#include "db/NativeSkillBookSourceCatalog.h"
#include "db/SqliteCompanionRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include "db/SqliteBeastBagRepository.h"
#include "db/SqliteBeastBankRepository.h"
#include "db/NativeQuestCatalog.h"
#include "db/SqliteQuestJournalRepository.h"
#include "db/NativeMultiMessageCatalog.h"
#include "db/NativeMapItemCatalog.h"
#include "db/NativeWeaponCatalog.h"
#include "db/NativeArmorCatalog.h"
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteRoleAuxiliaryRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "db/SqlitePlayerAppearanceRepository.h"
#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteGuildRepository.h"
#include "db/SqliteGuildRosterRepository.h"
#include "db/SqliteOwnedGuildLeaveRepository.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteTeleportGemRepository.h"
#include "handlers/OwnedTaiwanPkEntryPreparation.h"
#include "game/OwnedTaiwanPkPlayerEntrySource.h"
#include "handlers/OwnedTaiwanPkRoomBackend.h"
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include <filesystem>
#include <memory>
namespace god2 {
class OwnedBagProjectionService;
class SqliteOwnedPkRoomRepository;
class SqliteNativeAccountSnapshotRepository;
class SqliteNativeCharacterSummarySnapshotRepository;
class SqliteNativeWorldEntrySnapshotRepository;
class SqliteNativeEquipmentSnapshotRepository;
class SqliteOwnedInventoryRepository;
class SqliteOwnedBlacklistRepository;
class OwnedTaiwanReturnActorSavedSource;
class SqliteDatabase final : public Database {
public:
    explicit SqliteDatabase(std::filesystem::path path,
                            std::vector<Migration> migrations = default_sqlite_migrations(),
                            NativeTaiwanSkillProfile taiwan_skill_profile = NativeTaiwanSkillProfile::Historical448);
    ~SqliteDatabase() override;
    SqliteDatabase(const SqliteDatabase&) = delete;
    SqliteDatabase& operator=(const SqliteDatabase&) = delete;
    void initialize() override;
    // Dedicated fresh connection to an existing regular DB, for explicit453
    // import only. No CREATE, migration, guild selector or gameplay owners.
    // Ordinary initialize/migrate and repository access remain unavailable.
    void initialize_existing_for_taiwan_skill_import();
    void migrate() override;
    AccountRepository& accounts() override;
    CharacterRepository& characters() override;
    RecoveredCharacterRepository& recovered_characters() override;
    // Exact same-Database lazy configuration reader; no SQL/DDL on access.
    SqliteOrdinaryMovementPolicyRepository& ordinary_movement_policies() override;
    // Explicit fresh empty CUSTOM-0150 schema, never an automatic migration.
    void install_ordinary_movement_policy_schema();
    NativeAccountSnapshotRepository& account_native_snapshots() override;
    SqliteNativeAccountSnapshotRepository& native_account_snapshot_writer();
    NativeCharacterSummarySnapshotRepository& native_character_summaries() override;
    // Explicit source writer on the exact same reader/connection, never called
    // by default migration/login. Does not install schema or invent data.
    SqliteNativeCharacterSummarySnapshotRepository& native_character_summary_writer();
    NativeWorldEntrySnapshotRepository& native_world_entries() override;
    SqliteNativeWorldEntrySnapshotRepository& native_world_entry_writer();
    NativeEquipmentSnapshotRepository& native_equipment_snapshots() override;
    SqliteNativeEquipmentSnapshotRepository& native_equipment_snapshot_writer();
    OwnedInventoryRepository& owned_inventory_storage() override;
    SqliteOwnedInventoryRepository& owned_inventory_writer();
    // Explicit same-DB saved observations; no schema, material or native actor
    // is installed. ReadyPopulation, visibility and transport remain separate.
    std::shared_ptr<OwnedTaiwanReturnActorSavedSource> make_owned_taiwan_return_actor_saved_source(
        std::shared_ptr<SharedWorldPresence>);
    // Same private Database/Presence initial-population issuer; no schema or
    // native actor defaults. Its saved source refuses an expired DB lifetime.
    std::shared_ptr<OwnedTaiwanReturnActorSavedSource::InitialIssuer> make_owned_taiwan_initial_actor_input_source(
        std::shared_ptr<SharedWorldPresence>);
    // Explicit fresh shared custody schema only. No import, automatic grants
    // or legacy promotion; ordinary migration/access does not install it.
    void install_owned_inventory_schema();
    // Fresh raw delivery-witness schema only. No default migration/import or
    // canonical item/equipment authority; ordinary access never installs it.
    void install_native_equipment_snapshot_schema();
    // Explicit fresh installation of both existing schemas in ONE transaction.
    // No population, repair, migration-version change or gameplay activation.
    void install_owned_equipment_schema();
    SqliteOwnedBlacklistRepository& blacklist(); // Same connection; never installs schema.
    void install_owned_blacklist_schema(); // Explicit fresh CUSTOM-0096 storage only.
    // Explicit fresh schema only. Not part of the existing v1 delivery schema,
    // ordinary migrations, default login or Main. Does not populate material.
    void install_native_world_entry_snapshot_schema();
    // Explicit storage schema operations only; ordinary access/login never calls these.
    void install_native_delivery_snapshot_schema();
    void require_native_delivery_snapshot_schema();
    SqliteCompanionRepository& companions();
    // CUSTOM-0085 source backend. Explicit custody schema must already exist;
    // this accessor never installs it or populates/creates owned beasts.
    SqliteBeastSnapshotRepository& beast_snapshots();
    void install_beast_snapshot_schema(); // opt-in; no instance import
    std::unique_ptr<SqliteBeastBagRepository> make_beast_bag_repository(OwnedBagProjectionService&);
    std::unique_ptr<SqliteOwnedInstanceTradeRepository> make_beast_instance_trade_repository();
    void install_beast_bank_schema();
    std::unique_ptr<SqliteBeastBankRepository> make_beast_bank_repository();
    // CUSTOM-0086 incomplete PK backend, separate explicit schema/factory.
    // Application must not install it until the full room adapter is ready.
    void install_owned_pk_room_schema();
    void install_owned_pk_round_schema();
    void install_owned_pk_terminal_resource_schema();
    void install_owned_pk_finished_return_schema(); // CUSTOM-0133 explicit opt-in only.
    std::unique_ptr<SqliteOwnedPkRoomRepository> make_owned_pk_room_repository();
    // CUSTOM-0112 explicit preparation source on this exact common connection.
    // No raw connection escapes, schema installation, reservation or sends at
    // construction. The genuine Session/initialization/peer/seed owners must
    // remain alive and drain with the preparer before this Database/room owner.
    // Complete room visibility/turn/return/recovery hosting remains required;
    // this factory alone never installs Application's RoomAuthority.
    std::shared_ptr<OwnedTaiwanPkEntryPreparation> make_owned_taiwan_pk_entry_preparation(
        SqliteOwnedPkRoomRepository&,std::shared_ptr<SharedWorldPresence>,TaiwanNativeFightCatalog,
        OwnedTaiwanPkEntryPreparation::Sessions,OwnedTaiwanPkEntryPreparation::Initializations,
        OwnedTaiwanPkEntryPreparation::Resolve,OwnedTaiwanPkEntryPreparation::Seed,
        OwnedTaiwanPkEntryPreparation::Companions={},OwnedTaiwanPkEntryPreparation::Players={});
    // CUSTOM-0120 explicit bounded/hash-pinned archive file -> the same
    // concrete preparation factory. No default path, schema installation,
    // reservation, Session transition, invitation enable or Application host.
    std::shared_ptr<OwnedTaiwanPkEntryPreparation> make_owned_taiwan_pk_entry_preparation_from_archive(
        SqliteOwnedPkRoomRepository&,std::shared_ptr<SharedWorldPresence>,const std::filesystem::path&,
        OwnedTaiwanPkEntryPreparation::Sessions,OwnedTaiwanPkEntryPreparation::Initializations,
        OwnedTaiwanPkEntryPreparation::Resolve,OwnedTaiwanPkEntryPreparation::Seed,
        OwnedTaiwanPkEntryPreparation::Companions={},OwnedTaiwanPkEntryPreparation::Players={});
    // CUSTOM-0125 complete source composition of preparation/admission/basic
    // transport on this connection, including exact Driver/Admission retirement
    // for a configured return supplier. Its existing finished-return schema must
    // be explicit before construction; absent historical return stays absent.
    // Explicit policy/archive/live owners only;
    // no schema install, callback invocation, reservation, sends or App install.
    // Drain InvitationService offers before stop/destruction; this Database,
    // initialized Lua/executor and callback dependencies must outlive backend.
    std::unique_ptr<OwnedTaiwanPkRoomBackend> make_owned_taiwan_pk_room_backend(
        asio::any_io_executor,LuaEngine&,std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<shared::SharedActorVisibility>,const std::filesystem::path&,
        OwnedTaiwanPkEntryPreparation::Sessions,OwnedTaiwanPkEntryPreparation::Initializations,
        OwnedTaiwanPkEntryPreparation::Resolve,OwnedTaiwanPkEntryPreparation::Seed,
        OwnedTaiwanPkRoomBackend::Parameters,std::array<std::uint8_t,2>,std::chrono::milliseconds,
        OwnedTaiwanPkEntryPreparation::Companions={},OwnedTaiwanPkRoomBackend::ReturnSceneSource={},
        OwnedTaiwanPkEntryPreparation::Players={});
    // CUSTOM-0105/0106/0107 actual original INIT/full Lease and same-Database
    // saved source graph. Read-only observations; no values, grants or schemas
    // are created. Database and genuine game/presence owners outlive receipts.
    std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> observe_owned_taiwan_pk_player(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        SharedWorldPresence::Lease,TaiwanWorldEntryIdentity=TaiwanWorldEntryIdentity::SelectedCharacter);
    bool owned_taiwan_pk_player_current(const OwnedTaiwanPkPlayerEntrySource::Observation&);
    // CUSTOM-0148 full immediate-before -> actual Written learning -> paired PK source.
    // No old Current renewal, schemas, sends or original-resource replacement.
    std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> observe_owned_taiwan_pk_learning_player(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        SharedWorldPresence::Lease,const OwnedTaiwanPkPlayerEntrySource::Observation&,
        OwnedSkillBookLearningService::WrittenLearningSource);
    std::optional<OwnedTaiwanPkCompanionSource::Observation> observe_owned_taiwan_pk_learning_companions(
        RecoveredOwnedCompanions&,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        const OwnedTaiwanPkCompanionSource::Observation&,const OwnedTaiwanPkPlayerEntrySource::Observation&,
        OwnedSkillBookLearningService::WrittenLearningSource);
    // CUSTOM-0129 same concrete DB/helper/catalog and genuine private Session
    // normal-entry/fullwrite observations. No connection escapes or new sends.
    // Helper, Database and original game owner must outlive every observation.
    std::optional<OwnedTaiwanPkCompanionSource::Observation> observe_owned_taiwan_pk_companions(
        RecoveredOwnedCompanions&,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        RecoveredOwnedCompanions::Restoration,std::vector<Session::WorldRecordsWrite>);
    // CUSTOM-0129 actual one original response, including its existing prefix
    // and the privately verified ordered restoration suffix. No per-frame
    // receipt conversion, replay, schema installation or native ACK is inferred.
    std::optional<OwnedTaiwanPkCompanionSource::Observation> observe_owned_taiwan_pk_companions(
        RecoveredOwnedCompanions&,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        RecoveredOwnedCompanions::Restoration,Session::WorldResponseWrite,std::vector<std::uint8_t>);
    // CUSTOM-0129 genuine Application-issued no-deity publication. The private
    // zero token owns its original player/INIT/full Lease and issued response;
    // a generic Written receipt or caller empty roster cannot mint this path.
    std::optional<OwnedTaiwanPkCompanionSource::Observation> observe_owned_taiwan_pk_zero_companions(
        RecoveredOwnedCompanions&,std::shared_ptr<Session>,Session::NormalWorldInitialization,
        RecoveredOwnedCompanions::Restoration,OwnedTaiwanPkCompanionSource::ZeroPublication);
    SqliteWorldDisplayRepository& world_displays();
    SqliteQuestJournalRepository& quest_journals();
    // Borrowed reader; valid only for this database's lifetime, after migration.
    const NativeMapCatalog& native_map_catalog() const;
    const NativeEnemyDisplayCatalog& native_enemy_display_catalog() const;
    const NativeSupplyCatalog& native_supply_catalog() const;
    const NativeSkillCatalog& native_skill_catalog() const;
    // Explicit insertion-only453 source installation on this actual connection.
    // The writer is bound to the chosen initialization's installation thread;
    // migrated normal DB or explicit private import-only connection allowed.
    // No default/Main import, schema install, profile change or learned rights.
    TaiwanInstalledSkillCatalogImport::Outcome import_taiwan_installed_skill_catalog(
        std::shared_ptr<const TaiwanInstalledSkillCatalogSource>);
    const NativeSkillBookCatalog& native_skill_book_catalog() const;
    // CUSTOM-0148: exact shared writers/readers; access performs no schema install.
    SqliteSkillBookLearningRepository& skill_book_learning();
    // Explicit empty event/activation schema only. No import/backfill or grants.
    void install_skill_book_learning_schema();
    // Additive shared raw evidence; lazy borrowed reader on this same DB.
    // Existing TW parsed catalog/default migrations/Main remain unchanged.
    const NativeSkillBookSourceCatalog& native_skill_book_source_catalog();
    const NativeQuestCatalog& native_quest_catalog() const;
    const NativeMultiMessageCatalog& native_multi_message_catalog() const;
    const NativeMapItemCatalog& native_map_item_catalog() const;
    const NativeWeaponCatalog& native_weapon_catalog() const;
    const NativeArmorCatalog& native_armor_catalog() const;
    SqliteRoleAuxiliaryRepository& role_auxiliary();
    SqliteWeaponSlotRepository& weapon_slots();
    SqliteArmorSlotRepository& armor_slots();
    std::unique_ptr<OwnedBagProjectionService> make_bag_projection(
        std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)> plain,bool beasts=false);
    SqlitePlayerAppearanceRepository& player_appearance();
    SqliteRoleTextRepository& role_text();
    SqliteGuildRepository& guilds();
    SqliteGuildRosterRepository& guild_roster();
    SqliteOwnedGuildLeaveRepository& guild_leave();
    // CUSTOM-0078: explicitly invoked by the validated disposable loopback lab.
    // Does not change default/formal migration48 or provide implicit grants.
    SqliteOwnedGuildMembershipRepository& candidate_guild_membership();
    // Requires explicit exact migration50; this accessor never installs schema.
    SqliteOwnedGuildAnnouncementRepository& guild_announcements() override;
    GuildRelations53FactoryDraft& guild53(GuildRelations53FlagsDraft flags);
    SqliteOwnedGuildMembershipRepository& guild_membership52();
    SqliteOwnedGuildSuccessionRepositoryDraft& guild_succession52(bool enabled);
    EffectiveGuildAdmissionRepositoryDraft& guild_admission52(bool enabled);
    EffectiveGuildAnnouncementRepositoryDraft& guild_effective_announcements52(bool enabled);
    SqliteOwnedGuildMembershipRepository& guild_membership51();
    SqliteOwnedGuildAnnouncementRepository& guild_announcements51();
    SqliteTeleportGemRepository& teleport_gems();
    SqliteFruitQuestRepository& fruit_quests();
    SqliteTradeRepository& trades();
    SqliteBankRepository& banks();
    SqliteBankAccessRepository& bank_access();
    SqliteBankItemsRepository& bank_items();
    SqliteOwnedArmorBankRepository& armor_bank();
    SqliteOwnedForeignBankRepository& foreign_bank();
    SqliteOwnedMixedBankRepository& mixed_bank();
    SqliteOwnedInstanceTradeRepository& instance_trades();
    SqliteOwnedInstanceDiscardRepository& instance_discards();
    const NativeFruitQuestSources& fruit_sources() const;
    const NativeNpcDisplayCatalog& native_npc_display_catalog() const;
private:
    struct Impl;
    std::filesystem::path path_;
    std::vector<Migration> migrations_;
    const NativeTaiwanSkillProfile taiwan_skill_profile_;
    std::unique_ptr<Impl> impl_;
    bool migrated_ = false;
};
}
