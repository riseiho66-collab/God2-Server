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
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include <utility>
#include <system_error>
namespace god2 {
struct SqliteDatabase::Impl {
    bool taiwan_skill_import_only=false;
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
    // Reverse member destruction revokes this repository before connection.
    std::unique_ptr<SqliteOrdinaryMovementPolicyRepository> ordinary_movement_policies;
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
    std::unique_ptr<TaiwanInstalledSkillCatalogImport> taiwan_installed_skill_import;
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
    const std::thread::id pk_player_thread=std::this_thread::get_id();
    bool pk_player_reading=false,pk_player_reentered=false;
    struct PkPlayerReadScope {
        Impl& owner;
        sqlite3* const connection;
        sqlite3_int64 changes=0;
        explicit PkPlayerReadScope(Impl& value):owner(value),connection(value.connection.get()) {
            if(owner.pk_player_thread!=std::this_thread::get_id())
                throw DatabaseError("TW PK player Database game owner mismatch");
            if(owner.pk_player_reading) {
                owner.pk_player_reentered=true;
                throw DatabaseError("TW PK player Database source reentered");
            }
            if(!connection||!sqlite3_get_autocommit(connection))
                throw DatabaseError("TW PK player Database source requires closed outer transaction");
            changes=sqlite3_total_changes64(connection); // Before any source observer.
            owner.pk_player_reading=true;owner.pk_player_reentered=false;
        }
        ~PkPlayerReadScope(){owner.pk_player_reading=false;}
        void fence()const {
            if(owner.pk_player_thread!=std::this_thread::get_id()||!owner.pk_player_reading||
               owner.pk_player_reentered||owner.connection.get()!=connection||
               !sqlite3_get_autocommit(connection)||sqlite3_total_changes64(connection)!=changes)
                throw DatabaseError("TW PK player Database source changed or reentered");
        }
    };
    // Separate whole-observer latch: the genuine zero issuer may invoke the
    // existing guarded Player Current; nesting that same player latch is invalid.
    const std::thread::id pk_zero_companion_thread=std::this_thread::get_id();
    bool pk_zero_companion_reading=false,pk_zero_companion_reentered=false;
    struct PkZeroCompanionReadScope {
        Impl& owner;
        sqlite3* const connection;
        sqlite3_int64 changes=0;
        explicit PkZeroCompanionReadScope(Impl& value):owner(value),connection(value.connection.get()) {
            if(owner.pk_zero_companion_thread!=std::this_thread::get_id())
                throw DatabaseError("TW PK zero companion Database game owner mismatch");
            if(owner.pk_zero_companion_reading) {
                owner.pk_zero_companion_reentered=true;
                throw DatabaseError("TW PK zero companion Database source reentered");
            }
            if(!connection||!sqlite3_get_autocommit(connection))
                throw DatabaseError("TW PK zero companion Database source requires closed outer transaction");
            changes=sqlite3_total_changes64(connection); // Before any source observer.
            owner.pk_zero_companion_reading=true;owner.pk_zero_companion_reentered=false;
        }
        ~PkZeroCompanionReadScope(){owner.pk_zero_companion_reading=false;}
        void fence()const {
            if(owner.pk_zero_companion_thread!=std::this_thread::get_id()||!owner.pk_zero_companion_reading||
               owner.pk_zero_companion_reentered||owner.connection.get()!=connection||
               !sqlite3_get_autocommit(connection)||sqlite3_total_changes64(connection)!=changes)
                throw DatabaseError("TW PK zero companion Database source changed or reentered");
        }
    };
    const std::thread::id pk_learning_companion_thread=std::this_thread::get_id();
    bool pk_learning_companion_reading=false,pk_learning_companion_reentered=false;
    struct PkLearningCompanionReadScope {
        Impl& owner;
        sqlite3* const connection;
        sqlite3_int64 changes=0;
        explicit PkLearningCompanionReadScope(Impl& value):owner(value),connection(value.connection.get()) {
            if(owner.pk_learning_companion_thread!=std::this_thread::get_id())
                throw DatabaseError("TW PK learned companion Database game owner mismatch");
            if(owner.pk_learning_companion_reading) {
                owner.pk_learning_companion_reentered=true;
                throw DatabaseError("TW PK learned companion Database source reentered");
            }
            if(!connection||!sqlite3_get_autocommit(connection))
                throw DatabaseError("TW PK learned companion Database source requires closed outer transaction");
            changes=sqlite3_total_changes64(connection); // Before any source observer.
            owner.pk_learning_companion_reading=true;owner.pk_learning_companion_reentered=false;
        }
        ~PkLearningCompanionReadScope(){owner.pk_learning_companion_reading=false;}
        void fence()const {
            if(owner.pk_learning_companion_thread!=std::this_thread::get_id()||!owner.pk_learning_companion_reading||
               owner.pk_learning_companion_reentered||owner.connection.get()!=connection||
               !sqlite3_get_autocommit(connection)||sqlite3_total_changes64(connection)!=changes)
                throw DatabaseError("TW PK learned companion Database source changed or reentered");
        }
    };
    // Last member dies before every borrowed repository and the connection.
    // Sources retain only a weak reference; no database/source ownership cycle.
    std::shared_ptr<const void> return_actor_saved_lifetime;
};
SqliteDatabase::SqliteDatabase(std::filesystem::path path, std::vector<Migration> migrations,
    NativeTaiwanSkillProfile taiwan_skill_profile)
    : path_(std::move(path)), migrations_(std::move(migrations)), taiwan_skill_profile_(taiwan_skill_profile) {
    if(!native_taiwan_skill_dataset_id(taiwan_skill_profile_))
        throw DatabaseError("Invalid Taiwan skill source profile");
}
SqliteDatabase::~SqliteDatabase() = default;
void SqliteDatabase::initialize() {
    if(impl_ && impl_->taiwan_skill_import_only)
        throw DatabaseError("Import-only database cannot initialize gameplay owners");
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
    candidate->native_skill_catalog = std::make_unique<NativeSkillCatalog>(raw,taiwan_skill_profile_);
    // Constructor binds identity/thread only; it performs no SQL or import.
    candidate->taiwan_installed_skill_import = std::make_unique<TaiwanInstalledSkillCatalogImport>(raw);
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
void SqliteDatabase::initialize_existing_for_taiwan_skill_import() {
    if(impl_ || migrated_)throw DatabaseError("Existing skill import requires a fresh Database object");
    if(path_.empty())throw DatabaseError("Existing skill import database path is empty");
    const auto original_utf8=path_.u8string();
    if(original_utf8.find(u8'\0')!=std::u8string::npos)
        throw DatabaseError("Existing skill import database path contains NUL");
    // Reject SQLite URI syntax even if a global SQLite URI option is enabled.
    if(original_utf8.size()>=5 && (original_utf8[0]==u8'f'||original_utf8[0]==u8'F') &&
       (original_utf8[1]==u8'i'||original_utf8[1]==u8'I') &&
       (original_utf8[2]==u8'l'||original_utf8[2]==u8'L') &&
       (original_utf8[3]==u8'e'||original_utf8[3]==u8'E') && original_utf8[4]==u8':')
        throw DatabaseError("Existing skill import database must not be a SQLite URI");
    std::error_code error;
    if(!std::filesystem::is_regular_file(path_,error) || error)
        throw DatabaseError("Existing skill import database must be an existing regular file");
    const auto opened_path=std::filesystem::canonical(path_,error);
    if(error || !std::filesystem::is_regular_file(opened_path,error) || error)
        throw DatabaseError("Existing skill import database cannot be resolved");
    const auto utf8=opened_path.u8string();
    if(utf8.empty() || utf8.find(u8'\0')!=std::u8string::npos)
        throw DatabaseError("Existing skill import resolved path is invalid");
    auto candidate=std::make_unique<Impl>();candidate->taiwan_skill_import_only=true;
    sqlite3* raw=nullptr;
    const int result=sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()),&raw,
        SQLITE_OPEN_READWRITE|SQLITE_OPEN_FULLMUTEX,nullptr); // Deliberately no CREATE/URI.
    candidate->connection.reset(raw);
    if(result!=SQLITE_OK)throw DatabaseError(raw?sqlite3_errmsg(raw):"Unable to open existing skill import DB");
    const char* actual_name=sqlite3_db_filename(raw,"main");
    if(!actual_name || !*actual_name)throw DatabaseError("Existing skill import DB filename is unavailable");
    const auto actual_path=std::filesystem::canonical(std::filesystem::u8path(actual_name),error);
    if(error || !std::filesystem::is_regular_file(actual_path,error) || error)
        throw DatabaseError("Existing skill import opened filename is not an existing regular file");
    // Equivalent canonical spellings permit native Windows case/path handling;
    // this metadata join is not a private file-handle incarnation attestation.
    if(!std::filesystem::equivalent(opened_path,actual_path,error) || error)
        throw DatabaseError("Existing skill import opened a different database path");
    sqlite_detail::check(raw,sqlite3_busy_timeout(raw,5000));
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON"); // Connection setting only, no schema change.
    {
        sqlite_detail::Statement keys(raw,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())
            throw DatabaseError("Existing skill import requires foreign keys");
    }
    candidate->taiwan_installed_skill_import=std::make_unique<TaiwanInstalledSkillCatalogImport>(raw);
    // No gameplay readers/writers, default guild selector or migration is constructed.
    // migrated_ stays false; schema4/5 is qualified by the actual importer before DML.
    impl_=std::move(candidate);
}
void SqliteDatabase::migrate() {
    if (!impl_) throw DatabaseError("Initialize database before migrating");
    if(impl_->taiwan_skill_import_only)
        throw DatabaseError("Import-only database cannot run migrations");
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
SqliteOrdinaryMovementPolicyRepository& SqliteDatabase::ordinary_movement_policies() {
    if(!migrated_||!impl_||impl_->taiwan_skill_import_only||!impl_->connection||
       !impl_->accounts||!impl_->recovered_characters)
        throw DatabaseError("Movement policy requires migrated same-Database owners");
    auto* const db=impl_->connection.get();
    if(!impl_->accounts->uses_connection(db)||!impl_->recovered_characters->uses_connection(db))
        throw DatabaseError("Movement policy common identity connection mismatch");
    if(!impl_->ordinary_movement_policies)
        impl_->ordinary_movement_policies=std::make_unique<SqliteOrdinaryMovementPolicyRepository>(db);
    auto& repository=*impl_->ordinary_movement_policies;
    if(!repository.uses_connection(db)||!repository.lifetime()->available())
        throw DatabaseError("Movement policy repository connection or lifetime mismatch");
    return repository;
}
void SqliteDatabase::install_ordinary_movement_policy_schema() {
    (void)ordinary_movement_policies(); // Pure actual-owner/same-connection gate.
    SqliteOrdinaryMovementPolicyRepository::install_schema(impl_->connection.get());
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
std::shared_ptr<OwnedTaiwanReturnActorSavedSource>
SqliteDatabase::make_owned_taiwan_return_actor_saved_source(std::shared_ptr<SharedWorldPresence> presence) {
    if(!migrated_||!impl_||impl_->taiwan_skill_import_only||!impl_->accounts||!impl_->recovered_characters||
       impl_->pk_player_thread!=std::this_thread::get_id())
        throw DatabaseError("TW return actor saved source requires migrated private game owners");
    auto* const owner=impl_.get();auto* const db=owner->connection.get();
    if(!db||!sqlite3_get_autocommit(db))
        throw DatabaseError("TW return actor saved factory requires closed transaction");
    const auto changes=sqlite3_total_changes64(db);
    const auto fence=[&] {
        if(impl_.get()!=owner||owner->connection.get()!=db||owner->pk_player_thread!=std::this_thread::get_id()||
           !sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes||
           !owner->accounts->uses_connection(db)||!owner->recovered_characters->uses_connection(db))
            throw DatabaseError("TW return actor saved factory changed private owners or rows");
    };
    fence();
    if(!presence||!presence->owns_repository(*owner->recovered_characters))
        throw DatabaseError("TW return actor saved factory requires exact Presence repository");
    fence();
    auto& world=native_world_entry_writer();fence();
    auto& equipment=native_equipment_snapshot_writer();fence();
    auto& inventory=owned_inventory_writer();fence();
    if(!owner->return_actor_saved_lifetime)owner->return_actor_saved_lifetime=std::make_shared<const std::uint8_t>(0);
    fence();
    auto result=std::shared_ptr<OwnedTaiwanReturnActorSavedSource>(new OwnedTaiwanReturnActorSavedSource(
        db,*owner->accounts,*owner->recovered_characters,world,equipment,inventory,
        std::move(presence),owner->return_actor_saved_lifetime));
    fence();return result;
}
std::shared_ptr<OwnedTaiwanReturnActorSavedSource::InitialIssuer>
SqliteDatabase::make_owned_taiwan_initial_actor_input_source(std::shared_ptr<SharedWorldPresence> presence) {
    auto saved=make_owned_taiwan_return_actor_saved_source(presence);
    auto* const owner=impl_.get();auto* const db=owner->connection.get();
    const auto changes=sqlite3_total_changes64(db);
    const auto fence=[&] {
        if(impl_.get()!=owner||owner->connection.get()!=db||owner->pk_player_thread!=std::this_thread::get_id()||
           !sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes||
           !owner->role_text||!owner->guilds||!saved->owns_presence(presence)||
           !owner->role_text->uses_connection(db)||!owner->guilds->uses_connection(db))
            throw DatabaseError("TW initial actor input factory changed private owners or rows");
    };
    fence();
    auto role=std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>(new OwnedTaiwanPkReturnRoleTextSource(
        db,*owner->role_text,*owner->guilds,*owner->recovered_characters,presence));
    fence();
    auto result=std::shared_ptr<OwnedTaiwanReturnActorSavedSource::InitialIssuer>(
        new OwnedTaiwanReturnActorSavedSource::InitialIssuer(saved,std::move(role)));
    fence();
    if(!result->owns_presence(presence))throw DatabaseError("TW initial actor issuer lost its actual Presence");
    fence();return result;
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
    return std::make_unique<SqliteOwnedPkRoomRepository>(raw,taiwan_skill_profile_);
}
void SqliteDatabase::install_owned_pk_terminal_resource_schema(){
    if(!migrated_)throw DatabaseError("Migrate before explicit PK terminal resource extension");
    SqliteOwnedPkRoomRepository::install_terminal_resource_schema(impl_->connection.get());
}
void SqliteDatabase::install_owned_pk_finished_return_schema(){
    if(!migrated_)throw DatabaseError("Migrate before explicit PK finished return extension");
    SqliteOwnedPkRoomRepository::install_finished_return_schema(impl_->connection.get());
}
std::shared_ptr<OwnedTaiwanPkEntryPreparation> SqliteDatabase::make_owned_taiwan_pk_entry_preparation(
    SqliteOwnedPkRoomRepository& rooms,std::shared_ptr<SharedWorldPresence> presence,
    TaiwanNativeFightCatalog catalog,OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkEntryPreparation::Companions companions,OwnedTaiwanPkEntryPreparation::Players players){
    if(!migrated_||!impl_||!presence||!presence->owns_repository(*impl_->recovered_characters)||
       !rooms.uses_connection(impl_->connection.get())||rooms.taiwan_profile()!=taiwan_skill_profile_)
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
        std::move(sessions),std::move(initializations),std::move(peers),std::move(seed),std::move(companions),std::move(players));
}
std::shared_ptr<OwnedTaiwanPkEntryPreparation> SqliteDatabase::make_owned_taiwan_pk_entry_preparation_from_archive(
    SqliteOwnedPkRoomRepository& rooms,std::shared_ptr<SharedWorldPresence> presence,
    const std::filesystem::path& archive_path,OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkEntryPreparation::Companions companions,OwnedTaiwanPkEntryPreparation::Players players){
    // CUSTOM-0120 fail invalid owner composition before file I/O or reader
    // assembly. These checks are identities, never SQL/schema qualification.
    if(!migrated_||!impl_||!presence||!presence->owns_repository(*impl_->recovered_characters)||
       !rooms.uses_connection(impl_->connection.get())||rooms.taiwan_profile()!=taiwan_skill_profile_||
       !sessions||!initializations||!peers||!seed)
        throw DatabaseError("TW PK archive preparation requires actual sources and resolver owners");
    auto catalog=TaiwanNativeFightCatalog::from_archive_file(archive_path);
    // Full immutable catalog owns its bytes. Only the established same-DB
    // factory assembles borrowed writers; loading never reserves a room.
    return make_owned_taiwan_pk_entry_preparation(rooms,std::move(presence),std::move(catalog),
        std::move(sessions),std::move(initializations),std::move(peers),std::move(seed),std::move(companions),std::move(players));
}
std::unique_ptr<OwnedTaiwanPkRoomBackend> SqliteDatabase::make_owned_taiwan_pk_room_backend(
    asio::any_io_executor game,LuaEngine& lua,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<shared::SharedActorVisibility> visibility,const std::filesystem::path& archive_path,
    OwnedTaiwanPkEntryPreparation::Sessions sessions,
    OwnedTaiwanPkEntryPreparation::Initializations initializations,
    OwnedTaiwanPkEntryPreparation::Resolve peers,OwnedTaiwanPkEntryPreparation::Seed seed,
    OwnedTaiwanPkRoomBackend::Parameters parameters,std::array<std::uint8_t,2> order,
    std::chrono::milliseconds retry,OwnedTaiwanPkEntryPreparation::Companions companions,
    OwnedTaiwanPkRoomBackend::ReturnSceneSource return_scene,OwnedTaiwanPkEntryPreparation::Players players){
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
    if(return_scene)SqliteOwnedPkRoomRepository::require_finished_return_schema(impl_->connection.get());
    // Historical preparation-only callers still have no return supplier and
    // require no new extension. A configured full return never installs on read.
    const auto path=archive_path; // Stable explicit path, no default/current-directory substitution.
    auto resolvers=std::make_shared<OwnedTaiwanPkRoomBackend::Resolvers>(
        OwnedTaiwanPkRoomBackend::Resolvers{std::move(sessions),std::move(initializations),
                                          std::move(peers),std::move(seed),std::move(companions),std::move(return_scene),std::move(players)});
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
    OwnedTaiwanPkEntryPreparation::Players player_source;
    if(resolvers->players)player_source=[resolvers](const std::shared_ptr<Session>& session,
            const Session::NormalWorldInitialization& initialization)
            ->std::optional<OwnedTaiwanPkPlayerEntrySource::Observation>{
        if(resolvers->stopped)return {};
        auto value=resolvers->players(session,initialization);
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
        std::move(companion_source),std::move(player_source));
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
        // The hosted backend issues the full population and saved-row witnesses
        // from its actual common owners. The mandatory supplier still owns the
        // complete actor/profile/resource/selection data; these witnesses do
        // not construct missing actors or turn an empty fallback into a scene.
        auto actor_saved_source=make_owned_taiwan_return_actor_saved_source(presence);
        return_source=[resolvers,role_text_source,actor_saved_source,presence](const OwnedPkOutboxPublication::ReturnSceneRequest& request)
            ->std::optional<shared::SharedActorVisibility::TaiwanReturnScene>{
        if(resolvers->stopped||request.actor_input)return {}; // Backend alone issues it.
        auto supplied=request; // Own the complete request before any observer.
        const auto population=presence->observe_ready_population();
        if(resolvers->stopped||!population||!presence->retained_population_current(*population))return {};
        const auto saved_rows=actor_saved_source->observe_population(population->characters());
        if(resolvers->stopped||!saved_rows||!presence->retained_population_current(*population)||
           !saved_rows->matches_population(population->characters()))return {};
        const auto actor_input=std::shared_ptr<const OwnedTaiwanReturnActorSavedSource::PopulationInput>(
            new OwnedTaiwanReturnActorSavedSource::PopulationInput(actor_saved_source,*population,*saved_rows,role_text_source));
        supplied.actor_input=actor_input;
        auto value=resolvers->return_scene(supplied);
        if(resolvers->stopped||!value||!value->current||
           (value->role_text_source&&value->role_text_source!=role_text_source))return {};
        const bool typed=bool(value->actor_input);
        if(typed){
            if(value->actor_input!=actor_input||!value->ready_population||!value->actor_saved_rows||
               value->actor_saved_source!=actor_saved_source||*value->ready_population!=*population||
               *value->actor_saved_rows!=*saved_rows)return {};
        }else if(value->ready_population||value->actor_saved_source||value->actor_saved_rows||
                 !value->actor_profile_equipment.empty()||value->actor_profile_equipment_required)return {};
        if(!actor_saved_source->current(*saved_rows)||resolvers->stopped||
           !presence->retained_population_current(*population))return {};
        value->role_text_source=role_text_source;
        value->ready_population=*population;
        value->actor_saved_source=actor_saved_source;
        value->actor_saved_rows=*saved_rows;
        value->actor_input=actor_input;
        value->actor_profile_equipment_required=typed;
        const auto current=value->current;
        value->current=[resolvers,current,presence,actor_saved_source,population=*population,saved_rows=*saved_rows]
                (shared::SharedActorVisibility::TaiwanReturnCheck check){
            const auto retained=[&] {
                return !resolvers->stopped&&actor_saved_source->owns_presence(presence)&&
                    actor_saved_source->owns_readset(saved_rows)&&
                    saved_rows.matches_population(population.characters())&&
                    presence->retained_population_current(population);
            };
            if(!retained())return false;
            const bool accepted=current(check);return accepted&&retained();
        };
        return value;
        };
    }
    auto return_lifecycle=std::make_shared<OwnedTaiwanPkRoomBackend::ReturnLifecycleCoordinator>();
    auto driver=std::make_unique<OwnedTaiwanPkBasicDriver>(std::move(game),*rooms,lua,parameters,order,retry,
        std::move(return_source),std::weak_ptr<OwnedPkOutboxPublication::ReturnLifecycleOwner>(return_lifecycle));
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
            const shared::SharedActorVisibility::TaiwanPkDeparture& departure){
            return owner->bind(ticket,bound,holds,
                OwnedTaiwanPkBasicDriver::WorldDeparture{departure_visibility,departure_presence,departure});});
    // The private constructor only moves already assembled owners; no callback
    // captures a partly constructed backend. On exceptions local reverse-order
    // destruction also retires Admission before driver/state/repository.
    return std::unique_ptr<OwnedTaiwanPkRoomBackend>(new OwnedTaiwanPkRoomBackend(std::move(resolvers),
        std::move(return_lifecycle),std::move(repository),std::move(rooms),std::move(preparation),
        std::move(driver),std::move(admission)));
}
std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> SqliteDatabase::observe_owned_taiwan_pk_player(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,SharedWorldPresence::Lease lease,
        TaiwanWorldEntryIdentity identity){
    if(!migrated_||!impl_)throw DatabaseError("TW PK player source requires actual Database");
    auto* const owner=impl_.get();Impl::PkPlayerReadScope read(*owner);
    if(!owner->accounts||!owner->recovered_characters||!owner->role_auxiliary||!owner->role_text||
       !presence||!session||!valid_taiwan_world_entry_identity(identity))return {};
    auto* const accounts=owner->accounts.get();auto* const characters=owner->recovered_characters.get();
    auto* const auxiliary=owner->role_auxiliary.get();auto* const texts=owner->role_text.get();
    const auto fence=[&] {
        read.fence();
        if(!migrated_||impl_.get()!=owner||owner->accounts.get()!=accounts||
           owner->recovered_characters.get()!=characters||owner->role_auxiliary.get()!=auxiliary||
           owner->role_text.get()!=texts||!accounts->uses_connection(read.connection)||
           !characters->uses_connection(read.connection)||!auxiliary->uses_connection(read.connection)||
           !texts->uses_connection(read.connection))
            throw DatabaseError("TW PK player source lost actual Database owners");
    };
    fence();
    if(!presence->owns_repository(*characters)||
       !session->normal_world_initialization_current_on_game(initialization)||!initialization.entry_written())return {};
    const auto phase=session->state();const auto battle=session->battle_generation();
    const auto local=[&] {
        fence();
        return (phase==SessionState::CharacterSelected||phase==SessionState::InWorld)&&
            session->normal_world_initialization_current_on_game(initialization)&&initialization.entry_written()&&
            !session->closing()&&session->state()==phase&&session->id()==lease.session&&
            session->account_id==lease.account&&session->character_id==lease.character&&
            session->battle_generation()==battle&&presence->owns_repository(*characters)&&
            presence->retained_ready_current(lease);
    };
    if(!local())return {};
    auto& inventory=owned_inventory_writer();fence();
    auto& equipment=native_equipment_snapshot_writer();fence();
    auto& worlds=native_world_entry_writer();fence();
    auto joint=std::make_shared<SqliteOwnedEquipmentTransaction>(inventory,equipment);fence();
    const auto sources=[&] {
        fence();
        return owner->owned_inventory.get()==&inventory&&owner->native_equipment_snapshots.get()==&equipment&&
            owner->native_world_entries.get()==&worlds&&inventory.owns_sources(*accounts,*characters)&&
            equipment.owns_sources(*accounts,*characters)&&worlds.owns_sources(*accounts,*characters)&&
            joint->owns_sources(*accounts,*characters);
    };
    if(!sources()||!local())return {};
    auto committed=joint->observe_committed(lease.account,lease.character);fence();
    if(!committed||!sources()||!local())return {};
    auto appearance=OwnedTaiwanPkAppearanceSource::observe(joint,*accounts,*characters,worlds,presence,
        session,initialization,lease,std::move(*committed));fence();
    if(!appearance||!sources()||!local())return {};
    auto combat=OwnedTaiwanPkCombatSource::observe(read.connection,*characters,*auxiliary,std::move(*appearance));fence();
    if(!combat||!sources()||!local())return {};
    auto result=OwnedTaiwanPkPlayerEntrySource::observe(read.connection,*texts,std::move(*combat),identity);fence();
    if(!result||!sources()||!local())return {};
    const bool current=result->current();fence();
    // Last saved observer is complete Player Current. Only private/pure cuts
    // follow it; this method never wraps live Current in an outer SQL scope.
    return current&&result->uses_connection(read.connection)&&result->identity_profile()==identity&&
        result->combat().appearance().owns_characters(*characters)&&
        result->combat().appearance().owns_presence(presence)&&
        result->combat().appearance().owns_initialization(initialization)&&
        result->combat().appearance().material().lease==lease&&sources()&&local()?
        std::move(result):std::nullopt;
}
std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> SqliteDatabase::observe_owned_taiwan_pk_learning_player(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,SharedWorldPresence::Lease lease,
        const OwnedTaiwanPkPlayerEntrySource::Observation& predecessor,
        OwnedSkillBookLearningService::WrittenLearningSource source){
    const auto identity=predecessor.identity_profile();
    if(!migrated_||!impl_)throw DatabaseError("TW PK player source requires actual Database");
    auto* const owner=impl_.get();Impl::PkPlayerReadScope read(*owner);
    if(!owner->accounts||!owner->recovered_characters||!owner->role_auxiliary||!owner->role_text||
       !presence||!session||!valid_taiwan_world_entry_identity(identity))return {};
    auto* const accounts=owner->accounts.get();auto* const characters=owner->recovered_characters.get();
    auto* const auxiliary=owner->role_auxiliary.get();auto* const texts=owner->role_text.get();
    const auto fence=[&] {
        read.fence();
        if(!migrated_||impl_.get()!=owner||owner->accounts.get()!=accounts||
           owner->recovered_characters.get()!=characters||owner->role_auxiliary.get()!=auxiliary||
           owner->role_text.get()!=texts||!accounts->uses_connection(read.connection)||
           !characters->uses_connection(read.connection)||!auxiliary->uses_connection(read.connection)||
           !texts->uses_connection(read.connection))
            throw DatabaseError("TW PK player source lost actual Database owners");
    };
    fence();
    if(!presence->owns_repository(*characters)||
       !session->normal_world_initialization_current_on_game(initialization)||!initialization.entry_written())return {};
    const auto phase=session->state();const auto battle=session->battle_generation();
    const auto local=[&] {
        fence();
        return (phase==SessionState::CharacterSelected||phase==SessionState::InWorld)&&
            session->normal_world_initialization_current_on_game(initialization)&&initialization.entry_written()&&
            !session->closing()&&session->state()==phase&&session->id()==lease.session&&
            session->account_id==lease.account&&session->character_id==lease.character&&
            session->battle_generation()==battle&&presence->owns_repository(*characters)&&
            presence->retained_ready_current(lease);
    };
    if(!local()||!predecessor.uses_connection(read.connection)||!source.current(*session))return {};
    auto& inventory=owned_inventory_writer();fence();
    auto& equipment=native_equipment_snapshot_writer();fence();
    auto& worlds=native_world_entry_writer();fence();
    auto joint=std::make_shared<SqliteOwnedEquipmentTransaction>(inventory,equipment);fence();
    const auto sources=[&] {
        fence();
        return owner->owned_inventory.get()==&inventory&&owner->native_equipment_snapshots.get()==&equipment&&
            owner->native_world_entries.get()==&worlds&&inventory.owns_sources(*accounts,*characters)&&
            equipment.owns_sources(*accounts,*characters)&&worlds.owns_sources(*accounts,*characters)&&
            joint->owns_sources(*accounts,*characters);
    };
    if(!sources()||!local())return {};
    auto committed=joint->observe_committed(lease.account,lease.character);fence();
    if(!committed||!sources()||!local())return {};
    auto appearance=OwnedTaiwanPkAppearanceSource::observe(joint,*accounts,*characters,worlds,presence,
        session,initialization,lease,std::move(*committed));fence();
    if(!appearance||!sources()||!local())return {};
    auto combat=OwnedTaiwanPkCombatSource::observe(read.connection,*characters,*auxiliary,std::move(*appearance));fence();
    if(!combat||!sources()||!local())return {};
    auto result=OwnedTaiwanPkPlayerEntrySource::observe_after_learning(read.connection,*texts,
        std::move(*combat),predecessor,source,session);fence();
    if(!result||!sources()||!local())return {};
    const bool current=result->current();fence();
    // Last saved observer is complete Player Current. Only private/pure cuts
    // follow it; this method never wraps live Current in an outer SQL scope.
    return current&&result->matches_learning_source(source)&&result->uses_connection(read.connection)&&result->identity_profile()==identity&&
        result->combat().appearance().owns_characters(*characters)&&
        result->combat().appearance().owns_presence(presence)&&
        result->combat().appearance().owns_initialization(initialization)&&
        result->combat().appearance().material().lease==lease&&sources()&&local()?
        std::move(result):std::nullopt;
}
std::optional<OwnedTaiwanPkCompanionSource::Observation> SqliteDatabase::observe_owned_taiwan_pk_learning_companions(
        RecoveredOwnedCompanions& helper,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,const OwnedTaiwanPkCompanionSource::Observation& predecessor,
        const OwnedTaiwanPkPlayerEntrySource::Observation& player,
        OwnedSkillBookLearningService::WrittenLearningSource source){
    if(!migrated_||!impl_)throw DatabaseError("TW learned companion source requires actual Database");
    auto* const owner=impl_.get();Impl::PkLearningCompanionReadScope read(*owner);
    auto* const companions=owner->companions.get();auto* const catalog=owner->native_skill_catalog.get();
    auto* const characters=owner->recovered_characters.get();
    const auto local=[&] {
        read.fence();
        return migrated_&&impl_.get()==owner&&companions&&catalog&&characters&&
            owner->companions.get()==companions&&owner->native_skill_catalog.get()==catalog&&
            owner->recovered_characters.get()==characters&&companions->uses_connection(read.connection)&&
            catalog->uses_connection(read.connection)&&characters->uses_connection(read.connection)&&
            helper.owns_repository(*companions)&&predecessor.uses_connection(read.connection)&&
            player.uses_connection(read.connection)&&player.matches_learning_source(source)&&
            player.combat().appearance().owns_characters(*characters);
    };
    if(!session||!local()||!source.current(*session))return {};
    auto result=OwnedTaiwanPkCompanionSource::observe_learning(read.connection,*companions,helper,*catalog,
        session,initialization,predecessor,player,source);read.fence();
    if(!result||!local())return {};
    const bool current=result->current();read.fence();
    return current&&result->uses_connection(read.connection)&&result->learning_player_matches(player)&&local()?
        std::move(result):std::nullopt;
}
std::optional<OwnedTaiwanPkPlayerEntrySource::Observation> SqliteDatabase::observe_owned_taiwan_pk_selection_player(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,SharedWorldPresence::Lease lease,
        const OwnedTaiwanPkPlayerEntrySource::Observation& predecessor,
        SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource source){
    const auto identity=predecessor.identity_profile();
    if(!migrated_||!impl_)throw DatabaseError("TW PK player source requires actual Database");
    auto* const owner=impl_.get();Impl::PkPlayerReadScope read(*owner);
    if(!owner->accounts||!owner->recovered_characters||!owner->role_auxiliary||!owner->role_text||
       !presence||!session||!valid_taiwan_world_entry_identity(identity))return {};
    auto* const accounts=owner->accounts.get();auto* const characters=owner->recovered_characters.get();
    auto* const auxiliary=owner->role_auxiliary.get();auto* const texts=owner->role_text.get();
    const auto fence=[&] {
        read.fence();
        if(!migrated_||impl_.get()!=owner||owner->accounts.get()!=accounts||
           owner->recovered_characters.get()!=characters||owner->role_auxiliary.get()!=auxiliary||
           owner->role_text.get()!=texts||!accounts->uses_connection(read.connection)||
           !characters->uses_connection(read.connection)||!auxiliary->uses_connection(read.connection)||
           !texts->uses_connection(read.connection))
            throw DatabaseError("TW PK player source lost actual Database owners");
    };
    fence();
    if(!presence->owns_repository(*characters)||
       !session->normal_world_initialization_current_on_game(initialization)||!initialization.entry_written())return {};
    const auto phase=session->state();const auto battle=session->battle_generation();
    const auto local=[&] {
        fence();
        return (phase==SessionState::CharacterSelected||phase==SessionState::InWorld)&&
            session->normal_world_initialization_current_on_game(initialization)&&initialization.entry_written()&&
            !session->closing()&&session->state()==phase&&session->id()==lease.session&&
            session->account_id==lease.account&&session->character_id==lease.character&&
            session->battle_generation()==battle&&presence->owns_repository(*characters)&&
            presence->retained_ready_current(lease);
    };
    if(!local()||!predecessor.uses_connection(read.connection)||!source.current(*session))return {};
    auto& inventory=owned_inventory_writer();fence();
    auto& equipment=native_equipment_snapshot_writer();fence();
    auto& worlds=native_world_entry_writer();fence();
    auto joint=std::make_shared<SqliteOwnedEquipmentTransaction>(inventory,equipment);fence();
    const auto sources=[&] {
        fence();
        return owner->owned_inventory.get()==&inventory&&owner->native_equipment_snapshots.get()==&equipment&&
            owner->native_world_entries.get()==&worlds&&inventory.owns_sources(*accounts,*characters)&&
            equipment.owns_sources(*accounts,*characters)&&worlds.owns_sources(*accounts,*characters)&&
            joint->owns_sources(*accounts,*characters);
    };
    if(!sources()||!local())return {};
    auto committed=joint->observe_committed(lease.account,lease.character);fence();
    if(!committed||!sources()||!local())return {};
    auto appearance=OwnedTaiwanPkAppearanceSource::observe(joint,*accounts,*characters,worlds,presence,
        session,initialization,lease,std::move(*committed));fence();
    if(!appearance||!sources()||!local())return {};
    auto combat=OwnedTaiwanPkCombatSource::observe(read.connection,*characters,*auxiliary,std::move(*appearance));fence();
    if(!combat||!sources()||!local())return {};
    auto result=OwnedTaiwanPkPlayerEntrySource::observe_after_selection(read.connection,*texts,
        std::move(*combat),predecessor,source,session);fence();
    if(!result||!sources()||!local())return {};
    const bool current=result->current();fence();
    // Last saved observer is complete Player Current. Only private/pure cuts
    // follow it; this method never wraps live Current in an outer SQL scope.
    return current&&result->matches_selection_source(source)&&result->uses_connection(read.connection)&&result->identity_profile()==identity&&
        result->combat().appearance().owns_characters(*characters)&&
        result->combat().appearance().owns_presence(presence)&&
        result->combat().appearance().owns_initialization(initialization)&&
        result->combat().appearance().material().lease==lease&&sources()&&local()?
        std::move(result):std::nullopt;
}
std::optional<OwnedTaiwanPkCompanionSource::Observation> SqliteDatabase::observe_owned_taiwan_pk_selection_companions(
        RecoveredOwnedCompanions& helper,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,const OwnedTaiwanPkCompanionSource::Observation& predecessor,
        const OwnedTaiwanPkPlayerEntrySource::Observation& player,
        SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource source){
    if(!migrated_||!impl_)throw DatabaseError("TW selected companion source requires actual Database");
    auto* const owner=impl_.get();Impl::PkLearningCompanionReadScope read(*owner);
    auto* const companions=owner->companions.get();auto* const catalog=owner->native_skill_catalog.get();
    auto* const characters=owner->recovered_characters.get();
    const auto local=[&] {
        read.fence();
        return migrated_&&impl_.get()==owner&&companions&&catalog&&characters&&
            owner->companions.get()==companions&&owner->native_skill_catalog.get()==catalog&&
            owner->recovered_characters.get()==characters&&companions->uses_connection(read.connection)&&
            catalog->uses_connection(read.connection)&&characters->uses_connection(read.connection)&&
            helper.owns_repository(*companions)&&predecessor.uses_connection(read.connection)&&
            player.uses_connection(read.connection)&&player.matches_selection_source(source)&&
            player.combat().appearance().owns_characters(*characters);
    };
    if(!session||!local()||!source.current(*session))return {};
    auto result=OwnedTaiwanPkCompanionSource::observe_selection(read.connection,*companions,helper,*catalog,
        session,initialization,predecessor,player,source);read.fence();
    if(!result||!local())return {};
    const bool current=result->current();read.fence();
    return current&&result->uses_connection(read.connection)&&result->learning_player_matches(player)&&local()?
        std::move(result):std::nullopt;
}
bool SqliteDatabase::owned_taiwan_pk_player_current(const OwnedTaiwanPkPlayerEntrySource::Observation& source){
    if(!migrated_||!impl_)throw DatabaseError("TW PK player Current requires actual Database");
    auto* const owner=impl_.get();Impl::PkPlayerReadScope read(*owner);
    const auto owned=source;auto* const characters=owner->recovered_characters.get();
    const auto local=[&] {
        read.fence();
        return migrated_&&impl_.get()==owner&&characters&&owner->recovered_characters.get()==characters&&
            characters->uses_connection(read.connection)&&owned.uses_connection(read.connection)&&
            owned.combat().appearance().owns_characters(*characters);
    };
    if(!local())return false;
    const bool current=owned.current();read.fence();
    return current&&local();
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
std::optional<OwnedTaiwanPkCompanionSource::Observation> SqliteDatabase::observe_owned_taiwan_pk_companions(
        RecoveredOwnedCompanions& helper,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        Session::WorldResponseWrite whole_response,std::vector<std::uint8_t> original_whole_wire){
    if(!migrated_||!impl_)throw DatabaseError("TW PK whole companion source requires actual Database");
    return OwnedTaiwanPkCompanionSource::observe(impl_->connection.get(),*impl_->companions,helper,
        *impl_->native_skill_catalog,std::move(session),std::move(initialization),
        std::move(restoration),std::move(whole_response),std::move(original_whole_wire));
}
std::optional<OwnedTaiwanPkCompanionSource::Observation> SqliteDatabase::observe_owned_taiwan_pk_zero_companions(
        RecoveredOwnedCompanions& helper,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        OwnedTaiwanPkCompanionSource::ZeroPublication publication){
    if(!migrated_||!impl_)throw DatabaseError("TW PK zero companion source requires actual Database");
    auto* const owner=impl_.get();Impl::PkZeroCompanionReadScope read(*owner);
    auto* const companions=owner->companions.get();auto* const catalog=owner->native_skill_catalog.get();
    auto* const characters=owner->recovered_characters.get();
    const auto local=[&] {
        read.fence();
        return migrated_&&impl_.get()==owner&&companions&&catalog&&characters&&
            owner->companions.get()==companions&&owner->native_skill_catalog.get()==catalog&&
            owner->recovered_characters.get()==characters&&companions->uses_connection(read.connection)&&
            catalog->uses_connection(read.connection)&&characters->uses_connection(read.connection)&&
            helper.owns_repository(*companions)&&publication.player().uses_connection(read.connection)&&
            publication.player().combat().appearance().owns_characters(*characters);
    };
    if(!local())return {};
    // The original player's live source is observed outside SQL. The issuer's
    // Current can separately use PlayerReadScope, while zero reentry poisons us.
    const bool player_current=publication.player().current();read.fence();
    if(!player_current||!local())return {};
    auto result=OwnedTaiwanPkCompanionSource::observe_zero(read.connection,*companions,helper,*catalog,
        std::move(session),std::move(initialization),std::move(restoration),publication);
    read.fence();
    if(!result||!local())return {};
    const bool current=result->current();read.fence();
    return current&&result->uses_connection(read.connection)&&local()?std::move(result):std::nullopt;
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
TaiwanInstalledSkillCatalogImport::Outcome SqliteDatabase::import_taiwan_installed_skill_catalog(
    std::shared_ptr<const TaiwanInstalledSkillCatalogSource> source) {
    if(!impl_ || (!migrated_ && !impl_->taiwan_skill_import_only) || !source || !impl_->taiwan_installed_skill_import ||
       !impl_->taiwan_installed_skill_import->uses_connection(impl_->connection.get()))
        throw DatabaseError("TW installed skill import requires the actual initialized common Database and qualified source");
    // Forward the same owning proof. This never changes the selected catalog
    // profile, installs schemas, populates old448 or creates learned skills.
    return impl_->taiwan_installed_skill_import->import_source(source);
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
