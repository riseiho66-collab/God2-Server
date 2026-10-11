#pragma once
#include "db/Database.h"
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
#include "cn/assets/CnNativeSkillCatalogImport.h"
#include "db/NativeSkillBookCatalog.h"
#include "db/NativeSkillBookSourceCatalog.h"
#include "cn/assets/CnNativeSkillBookSourceImport.h"
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
class SqliteDatabase final : public Database {
public:
    explicit SqliteDatabase(std::filesystem::path path,
                            std::vector<Migration> migrations = default_sqlite_migrations());
    ~SqliteDatabase() override;
    SqliteDatabase(const SqliteDatabase&) = delete;
    SqliteDatabase& operator=(const SqliteDatabase&) = delete;
    void initialize() override;
    void migrate() override;
    AccountRepository& accounts() override;
    CharacterRepository& characters() override;
    RecoveredCharacterRepository& recovered_characters() override;
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
        OwnedTaiwanPkEntryPreparation::Resolve,OwnedTaiwanPkEntryPreparation::Seed);
    // CUSTOM-0120 explicit bounded/hash-pinned archive file -> the same
    // concrete preparation factory. No default path, schema installation,
    // reservation, Session transition, invitation enable or Application host.
    std::shared_ptr<OwnedTaiwanPkEntryPreparation> make_owned_taiwan_pk_entry_preparation_from_archive(
        SqliteOwnedPkRoomRepository&,std::shared_ptr<SharedWorldPresence>,const std::filesystem::path&,
        OwnedTaiwanPkEntryPreparation::Sessions,OwnedTaiwanPkEntryPreparation::Initializations,
        OwnedTaiwanPkEntryPreparation::Resolve,OwnedTaiwanPkEntryPreparation::Seed);
    SqliteWorldDisplayRepository& world_displays();
    SqliteQuestJournalRepository& quest_journals();
    // Borrowed reader; valid only for this database's lifetime, after migration.
    const NativeMapCatalog& native_map_catalog() const;
    const NativeEnemyDisplayCatalog& native_enemy_display_catalog() const;
    const NativeSupplyCatalog& native_supply_catalog() const;
    const NativeSkillCatalog& native_skill_catalog() const;
    // Explicit source-data import only; default migration/Application never
    // invokes it. No grants or character changes. Requires a migrated DB and
    // actual pinned provider; bind the same native_skill_catalog() afterward.
    cn::CnNativeSkillCatalogImport::Result import_cn_native_skill_catalog(
        std::shared_ptr<const god2cn::CnNativeSkillCatalog>);
    const NativeSkillBookCatalog& native_skill_book_catalog() const;
    // Additive shared raw evidence; lazy borrowed reader on this same DB.
    // Existing TW parsed catalog/default migrations/Main remain unchanged.
    const NativeSkillBookSourceCatalog& native_skill_book_source_catalog();
    void install_native_skill_book_source_schema(); // Explicit source schema only.
    cn::CnNativeSkillBookSourceImport::Result import_cn_native_skill_book_sources(
        std::shared_ptr<const cn::CnNativeSkillBookBindings>);
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
    std::unique_ptr<Impl> impl_;
    bool migrated_ = false;
};
}
