#include "db/GuildOfficerSqliteMigrations.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteOwnedPkRoomRepository.h"
#include "handlers/OwnedBagProjectionService.h"
#include "protocol/RecoveredArmorSourceInstance.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteNativeAccountSnapshotRepository.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include "db/SqliteOwnedInventoryRepository.h"
#include "db/SqliteOwnedBlacklistRepository.h"
#include "db/SqliteCharacterRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "db/NativeDeliverySnapshotSchema.h"
#include "game/OwnedTaiwanPkReturnRoleTextSource.h"
#include <utility>
namespace god2 {
struct SqliteDatabase::Impl {
    struct Close { void operator()(sqlite3* db) const noexcept { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3, Close> connection;
    std::unique_ptr<SqliteAccountRepository> accounts;
    std::unique_ptr<SqliteNativeAccountSnapshotRepository> account_native_snapshots;
    std::unique_ptr<SqliteNativeCharacterSummarySnapshotRepository> native_character_summaries;
    std::unique_ptr<SqliteFruitQuestRepository> fruit_quests;
    std::unique_ptr<SqliteTradeRepository> trades;
    std::unique_ptr<SqliteBankRepository> banks;
    std::unique_ptr<SqliteBankAccessRepository> bank_access;
    std::unique_ptr<SqliteBankItemsRepository> bank_items;
    std::unique_ptr<SqliteOwnedArmorBankRepository> armor_bank;
    std::unique_ptr<SqliteOwnedForeignBankRepository> foreign_bank;
    std::unique_ptr<SqliteOwnedMixedBankRepository> mixed_bank;
    std::unique_ptr<SqliteOwnedInstanceTradeRepository> instance_trades;
    std::unique_ptr<SqliteOwnedInstanceDiscardRepository> instance_discards;
    std::unique_ptr<SqliteOwnedGuildMembershipRepository> candidate_guild_membership;
    std::unique_ptr<GuildRelations53FactoryDraft> relations53;
    std::unique_ptr<GuildSuccessionRepositoryFactoryDraft> succession52;
    std::optional<bool> succession52_enabled;
    std::unique_ptr<EffectiveGuildAdmissionRepositoryDraft> admission52;
    std::unique_ptr<EffectiveGuildAnnouncementRepositoryDraft> effective_announcements52;
    std::unique_ptr<SqliteOwnedGuildAnnouncementRepository> guild_announcements;
    std::unique_ptr<NativeFruitQuestSources> fruit_sources;
    std::unique_ptr<SqliteCharacterRepository> characters;
    std::unique_ptr<SqliteRecoveredCharacterRepository> recovered_characters;
    // Destroy raw entry reader before its borrowed common character source.
    std::unique_ptr<SqliteNativeWorldEntrySnapshotRepository> native_world_entries;
    std::unique_ptr<SqliteNativeEquipmentSnapshotRepository> native_equipment_snapshots;
    std::unique_ptr<SqliteOwnedInventoryRepository> owned_inventory;
    std::unique_ptr<SqliteOwnedBlacklistRepository> blacklist;
    std::unique_ptr<SqliteCompanionRepository> companions;
    std::unique_ptr<SqliteBeastSnapshotRepository> beast_snapshots;
    std::unique_ptr<SqliteWorldDisplayRepository> world_displays;
    std::unique_ptr<SqliteQuestJournalRepository> quest_journals;
    std::unique_ptr<NativeMapCatalog> native_map_catalog;
    std::unique_ptr<NativeNpcDisplayCatalog> native_npc_display_catalog;
    std::unique_ptr<NativeEnemyDisplayCatalog> native_enemy_display_catalog;
    std::unique_ptr<NativeSupplyCatalog> native_supply_catalog;
    std::unique_ptr<NativeSkillCatalog> native_skill_catalog;
    std::unique_ptr<NativeSkillBookCatalog> native_skill_book_catalog;
    std::unique_ptr<NativeSkillBookSourceCatalog> native_skill_book_source_catalog;
    std::unique_ptr<NativeQuestCatalog> native_quest_catalog;
    std::unique_ptr<NativeMultiMessageCatalog> native_multi_message_catalog;
    std::unique_ptr<NativeMapItemCatalog> native_map_item_catalog;
    std::unique_ptr<NativeWeaponCatalog> native_weapon_catalog;
    std::unique_ptr<NativeArmorCatalog> native_armor_catalog;
    std::unique_ptr<SqliteRoleAuxiliaryRepository> role_auxiliary;
    std::unique_ptr<SqliteWeaponSlotRepository> weapon_slots;
    std::unique_ptr<SqliteArmorSlotRepository> armor_slots;
    std::unique_ptr<SqlitePlayerAppearanceRepository> player_appearance;
    std::unique_ptr<SqliteRoleTextRepository> role_text;
    std::unique_ptr<SqliteGuildRepository> guilds;
    std::unique_ptr<SqliteGuildRosterRepository> guild_roster;
    std::unique_ptr<SqliteOwnedGuildLeaveRepository> guild_leave;
    std::unique_ptr<SqliteTeleportGemRepository> teleport_gems;
    // Borrowed sources above outlive this concrete shared learning coordinator.
    std::unique_ptr<SqliteSkillBookLearningRepository> skill_book_learning;
};
SqliteDatabase::SqliteDatabase(std::filesystem::path path, std::vector<Migration> migrations)
    : path_(std::move(path)), migrations_(std::move(migrations)) {}
SqliteDatabase::~SqliteDatabase() = default;
void SqliteDatabase::initialize() {
    if (impl_) return;
    if (path_.empty()) throw DatabaseError("SQLite path must not be empty");
    const auto utf8 = path_.u8string();
    if (utf8.find(u8'\0') != std::u8string::npos) throw DatabaseError("SQLite path contains NUL");
    auto candidate = std::make_unique<Impl>();
    sqlite3* raw = nullptr;
    const int result = sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()), &raw,
                                      SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nullptr);
    candidate->connection.reset(raw);
    if (result != SQLITE_OK) throw DatabaseError(raw ? sqlite3_errmsg(raw) : "Unable to allocate SQLite connection");
    sqlite_detail::check(raw, sqlite3_busy_timeout(raw, 5000));
    sqlite_detail::execute(raw, "PRAGMA foreign_keys=ON");
    {
        sqlite_detail::Statement foreign_keys(raw, "PRAGMA foreign_keys");
        if (!foreign_keys.row() || foreign_keys.integer(0) != 1) throw DatabaseError("SQLite foreign keys unavailable");
    }
    candidate->fruit_sources=std::make_unique<NativeFruitQuestSources>(raw);
    candidate->fruit_quests=std::make_unique<SqliteFruitQuestRepository>(raw,[raw]{NativeFruitQuestSources(raw).require_qualified();});
    candidate->trades=std::make_unique<SqliteTradeRepository>(raw);
    candidate->banks=std::make_unique<SqliteBankRepository>(raw);
    candidate->bank_access=std::make_unique<SqliteBankAccessRepository>(raw);
    candidate->bank_items=std::make_unique<SqliteBankItemsRepository>(raw);
    candidate->guild_announcements=std::make_unique<SqliteOwnedGuildAnnouncementRepository>(raw);
    candidate->accounts = std::make_unique<SqliteAccountRepository>(raw);
    candidate->characters = std::make_unique<SqliteCharacterRepository>(raw);
    candidate->recovered_characters = std::make_unique<SqliteRecoveredCharacterRepository>(raw);
    candidate->companions = std::make_unique<SqliteCompanionRepository>(raw);
    candidate->world_displays = std::make_unique<SqliteWorldDisplayRepository>(raw);
    candidate->quest_journals = std::make_unique<SqliteQuestJournalRepository>(raw);
    candidate->native_npc_display_catalog=std::make_unique<NativeNpcDisplayCatalog>(raw);
    candidate->native_map_catalog = std::make_unique<NativeMapCatalog>(raw);
    candidate->native_enemy_display_catalog = std::make_unique<NativeEnemyDisplayCatalog>(raw);
    candidate->native_supply_catalog = std::make_unique<NativeSupplyCatalog>(raw);
    candidate->native_skill_catalog = std::make_unique<NativeSkillCatalog>(raw);
    candidate->native_skill_book_catalog = std::make_unique<NativeSkillBookCatalog>(raw);
    candidate->native_quest_catalog = std::make_unique<NativeQuestCatalog>(raw);
    candidate->native_multi_message_catalog = std::make_unique<NativeMultiMessageCatalog>(raw);
    candidate->native_map_item_catalog = std::make_unique<NativeMapItemCatalog>(raw);
    candidate->native_weapon_catalog = std::make_unique<NativeWeaponCatalog>(raw);
    candidate->native_armor_catalog = std::make_unique<NativeArmorCatalog>(raw);
    candidate->role_auxiliary = std::make_unique<SqliteRoleAuxiliaryRepository>(raw);
    candidate->player_appearance=std::make_unique<SqlitePlayerAppearanceRepository>(raw);
    candidate->role_text=std::make_unique<SqliteRoleTextRepository>(raw);
    candidate->guilds=std::make_unique<SqliteGuildRepository>(raw);
    candidate->guild_roster=std::make_unique<SqliteGuildRosterRepository>(raw);
    candidate->guild_leave=std::make_unique<SqliteOwnedGuildLeaveRepository>(raw);
    candidate->teleport_gems=std::make_unique<SqliteTeleportGemRepository>(raw);
    candidate->weapon_slots=std::make_unique<SqliteWeaponSlotRepository>(raw,[raw](std::uint16_t item) {
        const auto definition=NativeWeaponCatalog(raw).lookup(item);
        return definition && (definition->family=="WPN" || definition->family=="TWP") &&
            definition->parsed_record.size()==396 && (definition->parsed_record[0x11a]&4)!=0;
    });
    candidate->armor_slots=std::make_unique<SqliteArmorSlotRepository>(raw,[raw](std::uint16_t item) {return NativeArmorCatalog(raw).equipment_slot(item);},[raw](std::uint16_t item,const auto& bytes) {const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);});
    candidate->armor_bank=std::make_unique<SqliteOwnedArmorBankRepository>(raw,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);});
    candidate->foreign_bank=std::make_unique<SqliteOwnedForeignBankRepository>(raw,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);},
        [raw](std::uint16_t item){return NativeWeaponCatalog(raw).lookup(item);});
    candidate->mixed_bank=std::make_unique<SqliteOwnedMixedBankRepository>(raw,*candidate->foreign_bank,
        [raw](std::uint16_t item){return NativeSupplyCatalog(raw).lookup(item).has_value();});
    candidate->instance_trades=std::make_unique<SqliteOwnedInstanceTradeRepository>(raw,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);},
        [raw](std::uint16_t item){return NativeWeaponCatalog(raw).lookup(item);},
        [raw](std::uint16_t item){return NativeSupplyCatalog(raw).lookup(item).has_value();});
    candidate->instance_discards=std::make_unique<SqliteOwnedInstanceDiscardRepository>(raw,*candidate->armor_slots,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);},
        [raw](std::uint16_t item){return NativeWeaponCatalog(raw).lookup(item);});
    impl_ = std::move(candidate);
}
void SqliteDatabase::migrate() {
    if (!impl_) throw DatabaseError("Initialize database before migrating");
    migrated_ = false;
    if(migrations_.back().version==53) {
        auto* raw=impl_->connection.get();int installed=0;
        {sqlite_detail::Statement q(raw,"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'");if(q.row()&&q.integer(0)){sqlite_detail::Statement h(raw,"SELECT max(version) FROM schema_migrations");if(h.row())installed=static_cast<int>(h.integer(0));}}
        if(installed==53){GuildRelations53FactoryDraft exact(raw);}
        else {auto base=migrations_;base.pop_back();SqliteMigrationManager(raw,base).migrate();GuildRelations53FactoryDraft::append53(raw,{true,true,true,true,true});}
    } else SqliteMigrationManager(impl_->connection.get(), migrations_).migrate();
    migrated_ = true;
}
AccountRepository& SqliteDatabase::accounts() {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->accounts;
}
NativeAccountSnapshotRepository& SqliteDatabase::account_native_snapshots() {
    if(!migrated_)throw DatabaseError("Migrate database before accessing native account snapshot source");
    // Lazy reader on SAME existing connection/accounts. No constructor SQL,
    // DDL, schema install, import or change to any migration vector.
    if(!impl_->account_native_snapshots)
        impl_->account_native_snapshots=std::make_unique<SqliteNativeAccountSnapshotRepository>(
            impl_->connection.get(),*impl_->accounts);
    return *impl_->account_native_snapshots;
}
SqliteNativeAccountSnapshotRepository& SqliteDatabase::native_account_snapshot_writer() {
    (void)account_native_snapshots(); //Existing migration/lazy same-object guard.
    return *impl_->account_native_snapshots;
}
NativeCharacterSummarySnapshotRepository& SqliteDatabase::native_character_summaries() {
    if(!migrated_)throw DatabaseError("Migrate database before accessing native character summary source");
    // Same existing connection/accounts/characters; constructor performs no SQL.
    if(!impl_->native_character_summaries)
        impl_->native_character_summaries=std::make_unique<SqliteNativeCharacterSummarySnapshotRepository>(
            impl_->connection.get(),*impl_->accounts,*impl_->recovered_characters);
    return *impl_->native_character_summaries;
}
SqliteNativeCharacterSummarySnapshotRepository& SqliteDatabase::native_character_summary_writer() {
    (void)native_character_summaries(); //Existing migration/lazy same-object guard.
    return *impl_->native_character_summaries;
}
NativeWorldEntrySnapshotRepository& SqliteDatabase::native_world_entries() {
    if(!migrated_)throw DatabaseError("Migrate before accessing native world entry source");
    if(!impl_->native_world_entries)
        impl_->native_world_entries=std::make_unique<SqliteNativeWorldEntrySnapshotRepository>(
            impl_->connection.get(),*impl_->accounts,*impl_->recovered_characters);
    return *impl_->native_world_entries;
}
SqliteNativeWorldEntrySnapshotRepository& SqliteDatabase::native_world_entry_writer() {
    (void)native_world_entries();
    return *impl_->native_world_entries;
}
NativeEquipmentSnapshotRepository& SqliteDatabase::native_equipment_snapshots() {
    if(!migrated_)throw DatabaseError("Migrate before accessing native equipment witness source");
    if(!impl_->native_equipment_snapshots)
        impl_->native_equipment_snapshots=std::make_unique<SqliteNativeEquipmentSnapshotRepository>(
            impl_->connection.get(),*impl_->accounts,*impl_->recovered_characters);
    return *impl_->native_equipment_snapshots;
}
SqliteNativeEquipmentSnapshotRepository& SqliteDatabase::native_equipment_snapshot_writer() {
    (void)native_equipment_snapshots();return *impl_->native_equipment_snapshots;
}
OwnedInventoryRepository& SqliteDatabase::owned_inventory_storage() {
    if(!migrated_)throw DatabaseError("Migrate before accessing shared owned inventory");
    if(!impl_->owned_inventory)
        impl_->owned_inventory=std::make_unique<SqliteOwnedInventoryRepository>(
            impl_->connection.get(),*impl_->accounts,*impl_->recovered_characters);
    return *impl_->owned_inventory;
}
SqliteOwnedInventoryRepository& SqliteDatabase::owned_inventory_writer() {
    (void)owned_inventory_storage();return *impl_->owned_inventory;
}
SqliteOwnedBlacklistRepository& SqliteDatabase::blacklist() {
    if(!migrated_)throw DatabaseError("Migrate before accessing blacklist storage");
    if(!impl_->blacklist)impl_->blacklist=std::make_unique<SqliteOwnedBlacklistRepository>(impl_->connection.get());
    return *impl_->blacklist;
}
void SqliteDatabase::install_owned_blacklist_schema() {
    if(!migrated_ || !impl_)throw DatabaseError("Migrate before explicit blacklist schema installation");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db) || !impl_->recovered_characters->uses_connection(db))
        throw DatabaseError("Blacklist requires exact common sources");
    SqliteOwnedBlacklistRepository::install_schema(db);
}
void SqliteDatabase::install_owned_inventory_schema() {
    if(!migrated_)throw DatabaseError("Migrate before explicit owned inventory schema installation");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db)||!impl_->recovered_characters->uses_connection(db)||!sqlite3_get_autocommit(db))
        throw DatabaseError("Owned inventory schema requires exact common sources and own transaction");
    sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
    if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Owned inventory schema requires foreign keys");
    sqlite_detail::Transaction tx(db);
    sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master WHERE name IN ('accounts','recovered_characters','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases') OR tbl_name IN ('accounts','recovered_characters','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases')");
    if(shadow.row())throw DatabaseError("Owned inventory schema TEMP collision");
    sqlite_detail::execute(db,SqliteOwnedInventoryRepository::schema());tx.commit();
}
void SqliteDatabase::install_native_equipment_snapshot_schema() {
    if(!migrated_)throw DatabaseError("Migrate before explicit native equipment schema installation");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db) || !impl_->recovered_characters->uses_connection(db) ||
       !sqlite3_get_autocommit(db))throw DatabaseError("Native equipment schema requires exact sources and own transaction");
    sqlite_detail::Statement keys(db,"PRAGMA foreign_keys");
    if(!keys.row() || keys.integer(0)!=1 || keys.row())throw DatabaseError("Native equipment schema requires foreign keys");
    sqlite_detail::Transaction tx(db);
    sqlite_detail::Statement collision(db,"SELECT 1 FROM temp.sqlite_master "
        "WHERE name='character_native_equipment_snapshots' OR tbl_name='character_native_equipment_snapshots'");
    if(collision.row())throw DatabaseError("Native equipment schema collides with TEMP objects");
    sqlite_detail::execute(db,SqliteNativeEquipmentSnapshotRepository::schema());tx.commit();
}
void SqliteDatabase::install_owned_equipment_schema() {
    if(!migrated_ || !impl_ || !impl_->connection || !impl_->accounts || !impl_->recovered_characters)
        throw DatabaseError("Migrate before explicit owned equipment schema installation");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db) || !impl_->recovered_characters->uses_connection(db) ||
       !sqlite3_get_autocommit(db))
        throw DatabaseError("Owned equipment schema requires exact common sources and own transaction");
    {
        sqlite_detail::Statement keys(db,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())
            throw DatabaseError("Owned equipment schema requires foreign keys");
    }
    sqlite_detail::Transaction tx(db);
    {
        sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master "
            "WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements',"
            "'owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots') "
            "OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements',"
            "'owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(shadow.row())throw DatabaseError("Owned equipment schema TEMP collision");
    }
    {
        sqlite_detail::Statement base(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN "
            "('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements')");
        if(!base.row() || base.integer(0)!=5 || base.row())
            throw DatabaseError("Owned equipment schema requires all five common base tables in main");
    }
    // Both existing exact CREATE schemas share this outer transaction. Never
    // call the standalone installers: each would try to own another BEGIN.
    // Existing feature objects deliberately fail; no IF NOT EXISTS or repair.
    sqlite_detail::execute(db,SqliteOwnedInventoryRepository::schema());
    sqlite_detail::execute(db,SqliteNativeEquipmentSnapshotRepository::schema());
    tx.commit();
}
void SqliteDatabase::install_native_world_entry_snapshot_schema() {
    if(!migrated_)throw DatabaseError("Migrate before explicit native world entry schema installation");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db) || !impl_->recovered_characters->uses_connection(db) ||
       !sqlite3_get_autocommit(db))throw DatabaseError("Native world entry schema requires same sources and own transaction");
    sqlite_detail::Statement keys(db,"PRAGMA foreign_keys");
    if(!keys.row() || keys.integer(0)!=1 || keys.row())throw DatabaseError("Native world entry schema requires foreign keys");
    sqlite_detail::Transaction tx(db);
    {
        sqlite_detail::Statement collision(db,"SELECT 1 FROM temp.sqlite_master "
            "WHERE name='character_native_world_entries' OR tbl_name='character_native_world_entries'");
        if(collision.row())throw DatabaseError("Native world entry schema collides with TEMP objects");
    }
    // Fresh exact CREATE deliberately fails if any table of this name exists.
    // No IF NOT EXISTS, v1 schema substitution or default migration change.
    sqlite_detail::execute(db,SqliteNativeWorldEntrySnapshotRepository::schema());
    tx.commit();
}
void SqliteDatabase::install_native_delivery_snapshot_schema() {
    if(!migrated_)throw DatabaseError("Migrate database before native delivery snapshot schema installation");
    auto* connection=impl_->connection.get();
    if(!impl_->accounts->uses_connection(connection))
        throw DatabaseError("Native delivery snapshot schema requires same account connection");
    NativeDeliverySnapshotSchema::install(connection,migrations_);
}
void SqliteDatabase::require_native_delivery_snapshot_schema() {
    if(!migrated_)throw DatabaseError("Migrate database before native delivery snapshot schema qualification");
    auto* connection=impl_->connection.get();
    if(!impl_->accounts->uses_connection(connection))
        throw DatabaseError("Native delivery snapshot schema requires same account connection");
    NativeDeliverySnapshotSchema::require_existing(connection,migrations_);
}
CharacterRepository& SqliteDatabase::characters() {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->characters;
}
RecoveredCharacterRepository& SqliteDatabase::recovered_characters() {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->recovered_characters;
}
SqliteCompanionRepository& SqliteDatabase::companions() {
    if(!migrated_) throw DatabaseError("Migrate database before accessing companion repository");
    return *impl_->companions;
}
SqliteBeastSnapshotRepository& SqliteDatabase::beast_snapshots() {
    if(!migrated_)throw DatabaseError("Migrate database before beast custody access");
    // No DDL-on-read and no inference that a missing feature table is empty.
    sqlite_detail::Statement table(impl_->connection.get(),"SELECT 1 FROM sqlite_master WHERE type='table' AND name='character_beast_snapshot_custody'");
    if(!table.row())throw DatabaseError("Beast custody schema has not been explicitly registered");
    if(!impl_->beast_snapshots)impl_->beast_snapshots=std::make_unique<SqliteBeastSnapshotRepository>(impl_->connection.get());
    return *impl_->beast_snapshots;
}
void SqliteDatabase::install_beast_snapshot_schema(){
    if(!migrated_)throw DatabaseError("Migrate base database before beast feature schema");
    SqliteBeastSnapshotRepository::install_schema(impl_->connection.get());
    SqliteBeastBagRepository::install_discard_schema(impl_->connection.get());
}
std::unique_ptr<SqliteBeastBagRepository> SqliteDatabase::make_beast_bag_repository(OwnedBagProjectionService& projector){
    if(!migrated_)throw DatabaseError("Migrate before owned beast bag transfer");
    return std::make_unique<SqliteBeastBagRepository>(impl_->connection.get(),beast_snapshots(),armor_slots(),projector);
}
std::unique_ptr<SqliteOwnedInstanceTradeRepository> SqliteDatabase::make_beast_instance_trade_repository(){
    if(!migrated_)throw DatabaseError("Migrate before owned PET trade access");
    auto* raw=impl_->connection.get();
    return std::make_unique<SqliteOwnedInstanceTradeRepository>(raw,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);},
        [raw](std::uint16_t item){return NativeWeaponCatalog(raw).lookup(item);},
        [raw](std::uint16_t item){return NativeSupplyCatalog(raw).lookup(item).has_value();},
        &beast_snapshots());
}
void SqliteDatabase::install_beast_bank_schema(){
    if(!migrated_)throw DatabaseError("Migrate before explicit PET bank schema extension");
    SqliteBeastBankRepository::install_schema(impl_->connection.get());
}
void SqliteDatabase::install_owned_pk_room_schema(){
    if(!migrated_)throw DatabaseError("Migrate base database before explicit PK feature schema");
    SqliteOwnedPkRoomRepository::install_schema(impl_->connection.get());
}
void SqliteDatabase::install_owned_pk_round_schema(){
    if(!migrated_)throw DatabaseError("Migrate before explicit PK round schema extension");
    SqliteOwnedPkRoomRepository::install_round_schema(impl_->connection.get());
}
std::unique_ptr<SqliteOwnedPkRoomRepository> SqliteDatabase::make_owned_pk_room_repository(){
    if(!migrated_)throw DatabaseError("Migrate before owned PK room access");
    auto* raw=impl_->connection.get();
    SqliteOwnedPkRoomRepository::require_schema(raw);
    return std::make_unique<SqliteOwnedPkRoomRepository>(raw);
}
void SqliteDatabase::install_owned_pk_terminal_resource_schema(){
    if(!migrated_)throw DatabaseError("Migrate before explicit PK terminal resource extension");
    SqliteOwnedPkRoomRepository::install_terminal_resource_schema(impl_->connection.get());
}
std::shared_ptr<OwnedTaiwanPkEntryPreparation> SqliteDatabase::make_owned_taiwan_pk_entry_preparation(
    SqliteOwnedPkRoomRepository& rooms,std::shared_ptr<SharedWorldPresence> presence,
    TaiwanNativeFightCatalog catalog,OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkEntryPreparation::Companions companions){
    if(!migrated_||!impl_||!presence||!presence->owns_repository(*impl_->recovered_characters)||
       !rooms.uses_connection(impl_->connection.get()))
        throw DatabaseError("TW PK preparation requires actual common Database/presence/room sources");
    // These existing accessors only assemble the exact same-Database readers/
    // writers; they perform no schema installation or source population.
    auto& inventory=owned_inventory_writer();
    auto& equipment=native_equipment_snapshot_writer();
    auto& worlds=native_world_entry_writer();
    auto joint=std::make_shared<SqliteOwnedEquipmentTransaction>(inventory,equipment);
    return std::make_shared<OwnedTaiwanPkEntryPreparation>(impl_->connection.get(),
        *impl_->accounts,*impl_->recovered_characters,worlds,*impl_->role_auxiliary,
        *impl_->role_text,std::move(catalog),std::move(presence),std::move(joint),rooms,
        std::move(sessions),std::move(initializations),std::move(peers),std::move(seed),std::move(companions));
}
std::shared_ptr<OwnedTaiwanPkEntryPreparation> SqliteDatabase::make_owned_taiwan_pk_entry_preparation_from_archive(
    SqliteOwnedPkRoomRepository& rooms,std::shared_ptr<SharedWorldPresence> presence,
    const std::filesystem::path& archive_path,OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkEntryPreparation::Companions companions){
    // CUSTOM-0120 fail invalid owner composition before file I/O or reader
    // assembly. These checks are identities, never SQL/schema qualification.
    if(!migrated_||!impl_||!presence||!presence->owns_repository(*impl_->recovered_characters)||
       !rooms.uses_connection(impl_->connection.get())||!sessions||!initializations||!peers||!seed)
        throw DatabaseError("TW PK archive preparation requires actual sources and resolver owners");
    auto catalog=TaiwanNativeFightCatalog::from_archive_file(archive_path);
    // Full immutable catalog owns its bytes. Only the established same-DB
    // factory assembles borrowed writers; loading never reserves a room.
    return make_owned_taiwan_pk_entry_preparation(rooms,std::move(presence),std::move(catalog),
        std::move(sessions),std::move(initializations),std::move(peers),std::move(seed),std::move(companions));
}
std::unique_ptr<OwnedTaiwanPkRoomBackend> SqliteDatabase::make_owned_taiwan_pk_room_backend(
    asio::any_io_executor game,LuaEngine& lua,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<cn::SharedActorVisibility> visibility,const std::filesystem::path& archive_path,
    OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkRoomBackend::Parameters parameters,std::array<std::uint8_t,2> order,
    std::chrono::milliseconds retry,OwnedTaiwanPkEntryPreparation::Companions companions,
    OwnedTaiwanPkRoomBackend::ReturnSceneSource return_scene){
    // Identity/policy checks precede all file I/O and reader assembly. This
    // factory has no supplied repository/preparer that could split issuers.
    if(!migrated_||!impl_||!presence||!presence->owns_repository(*impl_->recovered_characters)||
       !visibility||!visibility->owns_presence(presence)||
       !game||!sessions||!initializations||!peers||!seed||archive_path.empty())
        throw DatabaseError("TW PK backend requires actual common sources and explicit resolver owners");
    OwnedTaiwanPkRoomBackend::require_policy(parameters,order,retry);
    // This owned basic backend now consumes terminal saved resources. Require
    // its explicit extension before archive I/O; never install/migrate here.
    SqliteOwnedPkRoomRepository::require_terminal_resource_schema(impl_->connection.get());
    const auto path=archive_path; // Stable explicit path, no default/current-directory substitution.
    auto resolvers=std::make_shared<OwnedTaiwanPkRoomBackend::Resolvers>(
        OwnedTaiwanPkRoomBackend::Resolvers{std::move(sessions),std::move(initializations),
                                          std::move(peers),std::move(seed),std::move(companions),std::move(return_scene)});
    auto catalog=TaiwanNativeFightCatalog::from_archive_file(path);
    auto repository=make_owned_pk_room_repository(); // Requires existing schema; never installs it.
    auto rooms=std::make_unique<OwnedPkRoomState>(*repository);
    auto session_source=[resolvers](std::uint64_t id)->std::shared_ptr<Session>{
        if(resolvers->stopped)return {};
        auto value=resolvers->sessions(id);return resolvers->stopped?nullptr:std::move(value);
    };
    auto peer_source=[resolvers](std::uint64_t id)->std::optional<OwnedPkInvitationService::Peer>{
        if(resolvers->stopped)return {};
        auto value=resolvers->peers(id);return resolvers->stopped?std::nullopt:std::move(value);
    };
    OwnedTaiwanPkEntryPreparation::Companions companion_source;
    if(resolvers->companions)companion_source=[resolvers](const std::shared_ptr<Session>& session,
            const Session::NormalWorldInitialization& initialization)
            ->std::optional<OwnedTaiwanPkCompanionSource::Observation>{
        if(resolvers->stopped)return {};
        auto value=resolvers->companions(session,initialization);
        return resolvers->stopped?std::nullopt:std::move(value);
    };
    auto preparation=make_owned_taiwan_pk_entry_preparation(*repository,presence,std::move(catalog),
        session_source,[resolvers](const std::shared_ptr<Session>& session)
                ->std::optional<Session::NormalWorldInitialization>{
            if(resolvers->stopped)return {};
            auto value=resolvers->initializations(session);
            return resolvers->stopped?std::nullopt:std::move(value);},peer_source,
        [resolvers](const OwnedPkInvitationService::Pair& pair)->std::optional<std::uint32_t>{
            if(resolvers->stopped)return {};
            auto value=resolvers->seed(pair);return resolvers->stopped?std::nullopt:std::move(value);},
        std::move(companion_source));
    // CUSTOM-0133 one actual callable in the shared resolver bundle. A
    // configured source is mandatory at return; stop never produces empties.
    OwnedTaiwanPkRoomBackend::ReturnSceneSource return_source;
    if(resolvers->return_scene){
        // CUSTOM-0135/0136/0137 exact shared factory supplies concrete text,
        // guild and current common root/pose owners. Full actor/resources/
        // selection still require their genuine complete source.
        auto role_text_source=std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>(
            new OwnedTaiwanPkReturnRoleTextSource(impl_->connection.get(),*impl_->role_text,*impl_->guilds,
                *impl_->recovered_characters,presence));
        return_source=[resolvers,role_text_source](const OwnedPkOutboxPublication::ReturnSceneRequest& request)
            ->std::optional<cn::SharedActorVisibility::TaiwanReturnScene>{
        if(resolvers->stopped)return {};
        auto value=resolvers->return_scene(request);
        if(resolvers->stopped||!value||!value->current||
           (value->role_text_source&&value->role_text_source!=role_text_source))return {};
        value->role_text_source=role_text_source;
        const auto current=value->current;
        value->current=[resolvers,current](cn::SharedActorVisibility::TaiwanReturnCheck check){
            if(resolvers->stopped)return false;
            const bool accepted=current(check);return accepted&&!resolvers->stopped;
        };
        return value;
        };
    }
    auto driver=std::make_unique<OwnedTaiwanPkBasicDriver>(std::move(game),*rooms,lua,parameters,order,retry,
        std::move(return_source));
    // CUSTOM-0130 capture actual owners BEFORE argument evaluation can move
    // them into Admission. The genuine Attempt token reaches the same driver.
    const auto departure_visibility=visibility;const auto departure_presence=presence;
    auto admission=std::make_unique<OwnedPkEntryAdmission>(*rooms,
        [preparation](const OwnedPkInvitationService::Pair& pair){return preparation->prepare(pair);},
        session_source,peer_source,std::move(visibility),std::move(presence),
        OwnedPkEntryAdmission::Bind{},
        [owner=driver.get(),departure_visibility,departure_presence](const OwnedPkRoomState::Ticket& ticket,
            const std::array<std::shared_ptr<Session>,2>& bound,
            const std::array<Session::NativePkEntryHold,2>& holds,
            const cn::SharedActorVisibility::TaiwanPkDeparture& departure){
            return owner->bind(ticket,bound,holds,
                OwnedTaiwanPkBasicDriver::WorldDeparture{departure_visibility,departure_presence,departure});});
    // The private constructor only moves already assembled owners; no callback
    // captures a partly constructed backend. On exceptions local reverse-order
    // destruction also retires Admission before driver/state/repository.
    return std::unique_ptr<OwnedTaiwanPkRoomBackend>(new OwnedTaiwanPkRoomBackend(std::move(resolvers),
        std::move(repository),std::move(rooms),std::move(preparation),std::move(driver),std::move(admission)));
}
std::optional<OwnedTaiwanPkCompanionSource::Observation> SqliteDatabase::observe_owned_taiwan_pk_companions(
        RecoveredOwnedCompanions& helper,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        std::vector<Session::WorldRecordsWrite> writes){
    if(!migrated_||!impl_)throw DatabaseError("TW PK companion source requires actual Database");
    return OwnedTaiwanPkCompanionSource::observe(impl_->connection.get(),*impl_->companions,helper,
        *impl_->native_skill_catalog,std::move(session),std::move(initialization),
        std::move(restoration),std::move(writes));
}
std::unique_ptr<SqliteBeastBankRepository> SqliteDatabase::make_beast_bank_repository(){
    if(!migrated_)throw DatabaseError("Migrate before PET bank access");
    auto* raw=impl_->connection.get();
    return std::make_unique<SqliteBeastBankRepository>(raw,foreign_bank(),beast_snapshots(),
        [raw](std::uint16_t item){return NativeWeaponCatalog(raw).lookup(item);},
        [raw](std::uint16_t item){return NativeSupplyCatalog(raw).lookup(item).has_value();});
}
SqliteBankRepository& SqliteDatabase::banks() {
    if(!migrated_)throw DatabaseError("Migrate before bank access");
    return *impl_->banks;
}
SqliteBankAccessRepository& SqliteDatabase::bank_access() {
    if(!migrated_)throw DatabaseError("Migrate before bank role access");
    return *impl_->bank_access;
}
SqliteBankItemsRepository& SqliteDatabase::bank_items() {
    if(!migrated_)throw DatabaseError("Migrate before bank item access");
    return *impl_->bank_items;
}
SqliteOwnedArmorBankRepository& SqliteDatabase::armor_bank() {
    if(!migrated_)throw DatabaseError("Migrate before owned armor bank access");
    return *impl_->armor_bank;
}
SqliteOwnedForeignBankRepository& SqliteDatabase::foreign_bank() {
    if(!migrated_)throw DatabaseError("Migrate before owned foreign bank access");
    return *impl_->foreign_bank;
}
SqliteOwnedMixedBankRepository& SqliteDatabase::mixed_bank() {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->mixed_bank;
}
SqliteOwnedInstanceTradeRepository& SqliteDatabase::instance_trades() {
    if(!migrated_)throw DatabaseError("Migrate before owned instance trade access");
    return *impl_->instance_trades;
}
SqliteOwnedInstanceDiscardRepository& SqliteDatabase::instance_discards() {
    if(!migrated_)throw DatabaseError("Migrate before owned instance discard access");
    return *impl_->instance_discards;
}
SqliteTeleportGemRepository& SqliteDatabase::teleport_gems() {
    if(!migrated_)throw DatabaseError("Migrate database before accessing teleport gems");
    return *impl_->teleport_gems;
}
SqliteWorldDisplayRepository& SqliteDatabase::world_displays() {
    if(!migrated_)throw DatabaseError("Migrate before world display access");
    return *impl_->world_displays;
}
SqliteQuestJournalRepository& SqliteDatabase::quest_journals() {
    if(!migrated_)throw DatabaseError("Migrate database before accessing quest journals");
    return *impl_->quest_journals;
}
const NativeMapCatalog& SqliteDatabase::native_map_catalog() const {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_map_catalog;
}
const NativeEnemyDisplayCatalog& SqliteDatabase::native_enemy_display_catalog() const {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_enemy_display_catalog;
}
const NativeSupplyCatalog& SqliteDatabase::native_supply_catalog() const {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_supply_catalog;
}
const NativeSkillCatalog& SqliteDatabase::native_skill_catalog() const {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_skill_catalog;
}
cn::CnNativeSkillCatalogImport::Result SqliteDatabase::import_cn_native_skill_catalog(
    std::shared_ptr<const god2cn::CnNativeSkillCatalog> native) {
    if(!migrated_)throw DatabaseError("Migrate database before explicit CN skill import");
    return cn::CnNativeSkillCatalogImport::import_actual_source(impl_->connection.get(),std::move(native));
}
const NativeSkillBookCatalog& SqliteDatabase::native_skill_book_catalog() const {
    if (!migrated_) throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_skill_book_catalog;
}
SqliteSkillBookLearningRepository& SqliteDatabase::skill_book_learning() {
    if(!migrated_)throw DatabaseError("Migrate before accessing skill-book learning sources");
    if(!impl_->skill_book_learning)
        impl_->skill_book_learning=std::make_unique<SqliteSkillBookLearningRepository>(
            owned_inventory_writer(),native_equipment_snapshot_writer(),companions(),
            native_skill_book_catalog(),native_skill_catalog());
    return *impl_->skill_book_learning;
}
void SqliteDatabase::install_skill_book_learning_schema() {
    if(!migrated_ || !impl_ || !sqlite3_get_autocommit(impl_->connection.get()))
        throw DatabaseError("Skill-book learning schema requires initialized common storage and its own transaction");
    auto* db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db) || !impl_->recovered_characters->uses_connection(db))
        throw DatabaseError("Skill-book learning schema requires exact common sources");
    sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
    if(!fk.row() || fk.integer(0)!=1 || fk.row())
        throw DatabaseError("Skill-book learning schema requires foreign keys");
    sqlite_detail::Transaction transaction(db);
    // Explicit installer only; Main never calls this or backfills activation.
    sqlite_detail::execute(db,SqliteSkillBookLearningRepository::schema());
    transaction.commit();
}
const NativeSkillBookSourceCatalog& SqliteDatabase::native_skill_book_source_catalog() {
    if(!migrated_)throw DatabaseError("Migrate before shared book source reader access");
    // No SQL/install/import on construction. Caller keeps THIS database alive.
    if(!impl_->native_skill_book_source_catalog)
        impl_->native_skill_book_source_catalog=std::make_unique<NativeSkillBookSourceCatalog>(impl_->connection.get());
    return *impl_->native_skill_book_source_catalog;
}
void SqliteDatabase::install_native_skill_book_source_schema() {
    if(!migrated_)throw DatabaseError("Migrate before explicit shared book source schema");
    cn::CnNativeSkillBookSourceImport::install_schema(impl_->connection.get());
}
cn::CnNativeSkillBookSourceImport::Result SqliteDatabase::import_cn_native_skill_book_sources(
    std::shared_ptr<const cn::CnNativeSkillBookBindings> native) {
    if(!migrated_)throw DatabaseError("Migrate before explicit CN book source import");
    return cn::CnNativeSkillBookSourceImport::import_actual_source(impl_->connection.get(),std::move(native));
}
const NativeQuestCatalog& SqliteDatabase::native_quest_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate database before accessing repositories");
    return *impl_->native_quest_catalog;
}
const NativeMultiMessageCatalog& SqliteDatabase::native_multi_message_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate before MultiMessage source access");
    return *impl_->native_multi_message_catalog;
}
const NativeMapItemCatalog& SqliteDatabase::native_map_item_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate before map item source access");
    return *impl_->native_map_item_catalog;
}
const NativeWeaponCatalog& SqliteDatabase::native_weapon_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate before weapon catalog access");
    return *impl_->native_weapon_catalog;
}
const NativeArmorCatalog& SqliteDatabase::native_armor_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate before armor catalog access");
    return *impl_->native_armor_catalog;
}
SqliteArmorSlotRepository& SqliteDatabase::armor_slots() {
    if(!migrated_)throw DatabaseError("Migrate before armor instance access");
    return *impl_->armor_slots;
}
std::unique_ptr<OwnedBagProjectionService> SqliteDatabase::make_bag_projection(
    std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)> plain,bool beasts) {
    if(!migrated_)throw DatabaseError("Migrate before owner-bound bag projection");
    auto* raw=impl_->connection.get();
    return std::make_unique<OwnedBagProjectionService>(raw,
        [raw](std::uint16_t item){return NativeArmorCatalog(raw).equipment_slot(item);},
        [raw](std::uint16_t item){const auto row=NativeWeaponCatalog(raw).lookup(item);return row &&
            (row->family=="WPN"||row->family=="TWP") && row->parsed_record.size()==396 && (row->parsed_record[0x11a]&4)!=0;},
        std::move(plain),[raw](std::uint16_t item,const auto& bytes){const auto row=NativeArmorCatalog(raw).lookup(item);return row && RecoveredArmorSourceInstance::matches(row->item_id,row->family,bytes);},beasts?&beast_snapshots():nullptr);
}
SqliteRoleAuxiliaryRepository& SqliteDatabase::role_auxiliary() {
    if(!migrated_)throw DatabaseError("Migrate before auxiliary snapshot access");
    return *impl_->role_auxiliary;
}
SqlitePlayerAppearanceRepository& SqliteDatabase::player_appearance() {
    if(!migrated_)throw DatabaseError("Migrate before player appearance access");
    return *impl_->player_appearance;
}
SqliteGuildRepository& SqliteDatabase::guilds() {
    if(!migrated_)throw DatabaseError("Migrate before owned guild access");
    return *impl_->guilds;
}
SqliteGuildRosterRepository& SqliteDatabase::guild_roster() {
    if(!migrated_)throw DatabaseError("Migrate before owned guild roster access");
    return *impl_->guild_roster;
}
SqliteOwnedGuildLeaveRepository& SqliteDatabase::guild_leave() {
    if(!migrated_)throw DatabaseError("Migrate before owned guild leave access");
    return *impl_->guild_leave;
}
SqliteOwnedGuildMembershipRepository& SqliteDatabase::candidate_guild_membership() {
    if(!migrated_)throw DatabaseError("Migrate before candidate guild membership access");
    if(!impl_->candidate_guild_membership) {
        auto candidate=migrations_;
        const bool announcement50=candidate.size()>=2 && candidate.back().version==50 &&
            candidate.back().name=="owned_guild_announcements_candidate" &&
            candidate.back().sql==SqliteOwnedGuildAnnouncementRepository::schema() &&
            candidate[candidate.size()-2].version==49 &&
            candidate[candidate.size()-2].name=="owned_player_guild_membership_candidate" &&
            candidate[candidate.size()-2].sql==SqliteOwnedGuildMembershipRepository::schema();
        if(!announcement50 && (candidate.empty() || (candidate.back().version!=48 &&
           (candidate.back().version!=49 || candidate.back().name!="owned_player_guild_membership_candidate" ||
            candidate.back().sql!=SqliteOwnedGuildMembershipRepository::schema()))))
            throw DatabaseError("Guild membership candidate requires the exact migration48 baseline");
        if(candidate.back().version==48)
            candidate.push_back({49,"owned_player_guild_membership_candidate",SqliteOwnedGuildMembershipRepository::schema()});
        SqliteMigrationManager(impl_->connection.get(),candidate).migrate();
        impl_->candidate_guild_membership=std::make_unique<SqliteOwnedGuildMembershipRepository>(impl_->connection.get());
    }
    return *impl_->candidate_guild_membership;
}
SqliteOwnedGuildAnnouncementRepository& SqliteDatabase::guild_announcements() {
    if(!migrated_)throw DatabaseError("Migrate before guild announcement access");
    if(migrations_.empty() || migrations_.back().version!=50 ||
       migrations_.back().name!="owned_guild_announcements_candidate" ||
       migrations_.back().sql!=SqliteOwnedGuildAnnouncementRepository::schema())
        throw DatabaseError("Guild announcements require exact explicit migration50");
    return *impl_->guild_announcements;
}
SqliteRoleTextRepository& SqliteDatabase::role_text() {
    if(!migrated_)throw DatabaseError("Migrate before secondary role text access");
    return *impl_->role_text;
}
SqliteWeaponSlotRepository& SqliteDatabase::weapon_slots() {
    if(!migrated_)throw DatabaseError("Migrate before owned weapon slots");
    return *impl_->weapon_slots;
}
SqliteFruitQuestRepository& SqliteDatabase::fruit_quests() {
    if(!migrated_)throw DatabaseError("Migrate before fruit quests");return *impl_->fruit_quests;
}
SqliteTradeRepository& SqliteDatabase::trades() {
    if(!migrated_)throw DatabaseError("Migrate before trade repository");return *impl_->trades;
}
const NativeFruitQuestSources& SqliteDatabase::fruit_sources() const {
    if(!migrated_)throw DatabaseError("Migrate before fruit sources");return *impl_->fruit_sources;
}

const NativeNpcDisplayCatalog& SqliteDatabase::native_npc_display_catalog() const {
    if(!migrated_)throw DatabaseError("Migrate before NPC source catalog");return *impl_->native_npc_display_catalog;
}

GuildRelations53FactoryDraft& SqliteDatabase::guild53(GuildRelations53FlagsDraft flags) {
    if(!migrated_||migrations_.back().version!=53)throw DatabaseError("Migrate exact53 before private guild factory");
    if(!impl_->relations53)impl_->relations53=std::make_unique<GuildRelations53FactoryDraft>(impl_->connection.get(),flags);
    impl_->relations53->require_flags(flags);return *impl_->relations53;
}
SqliteOwnedGuildMembershipRepository& SqliteDatabase::guild_membership52() {
    if(!migrated_ || migrations_.back().version!=52)throw DatabaseError("Migrate exact52 before guild membership access");
    require_exact_guild_succession_migrations_draft(impl_->connection.get(),migrations_);
    if(!impl_->candidate_guild_membership)impl_->candidate_guild_membership=std::make_unique<SqliteOwnedGuildMembershipRepository>(impl_->connection.get());
    return *impl_->candidate_guild_membership;
}
SqliteOwnedGuildSuccessionRepositoryDraft& SqliteDatabase::guild_succession52(bool enabled) {
    if(!migrated_ || migrations_.back().version!=52)throw DatabaseError("Migrate exact52 before effective ownership access");
    if(impl_->succession52_enabled && *impl_->succession52_enabled!=enabled)throw DatabaseError("Succession feature flags are immutable during one database lifetime");
    if(!impl_->succession52){impl_->succession52=std::make_unique<GuildSuccessionRepositoryFactoryDraft>(impl_->connection.get(),migrations_,GuildSuccessionFlagsDraft{true,true,true,enabled});impl_->succession52_enabled=enabled;}
    return impl_->succession52->effective_owner();
}
EffectiveGuildAdmissionRepositoryDraft& SqliteDatabase::guild_admission52(bool enabled) {
    auto& effective=guild_succession52(enabled);auto& original=guild_membership52();
    if(!impl_->admission52)impl_->admission52=std::make_unique<EffectiveGuildAdmissionRepositoryDraft>(impl_->connection.get(),original,effective);
    return *impl_->admission52;
}
EffectiveGuildAnnouncementRepositoryDraft& SqliteDatabase::guild_effective_announcements52(bool enabled) {
    auto& effective=guild_succession52(enabled);
    if(!impl_->effective_announcements52)impl_->effective_announcements52=std::make_unique<EffectiveGuildAnnouncementRepositoryDraft>(impl_->connection.get(),effective);
    return *impl_->effective_announcements52;
}

SqliteOwnedGuildMembershipRepository& SqliteDatabase::guild_membership51() {
    if(!migrated_)throw DatabaseError("Migrate before exact51 guild membership access");
    require_exact_guild_officer_migrations(impl_->connection.get(),migrations_);
    if(!impl_->candidate_guild_membership)
        impl_->candidate_guild_membership=std::make_unique<SqliteOwnedGuildMembershipRepository>(impl_->connection.get());
    return *impl_->candidate_guild_membership;
}
SqliteOwnedGuildAnnouncementRepository& SqliteDatabase::guild_announcements51() {
    if(!migrated_)throw DatabaseError("Migrate before exact51 guild announcement access");
    require_exact_guild_officer_migrations(impl_->connection.get(),migrations_);
    return *impl_->guild_announcements;
}

}
