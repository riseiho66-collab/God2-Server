#include "db/NativeArmorCatalog.h"
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteOwnedArmorBankRepository.h"
#include "db/SqliteOwnedForeignBankRepository.h"
#include "db/SqliteOwnedInstanceTradeRepository.h"
#include "db/SqliteOwnedMixedBankRepository.h"
#include "db/SqliteOwnedInstanceDiscardRepository.h"
#include "db/Migration.h"
#include "db/SqliteWorldDisplayRepository.h"
#include "db/SqliteFruitQuestRepository.h"
#include "db/NativeFruitQuestSources.h"
#include "db/NativeNpcDisplayCatalog.h"
#include "db/SqlitePlayerAppearanceRepository.h"
#include "db/NativePet2CategoryCatalog.h"
#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteGuildRepository.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteTeleportGemRepository.h"
namespace god2 {
std::vector<Migration> default_sqlite_migrations() {
    return {{1, "accounts_and_characters", R"SQL(
CREATE TABLE accounts (
 id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(id > 0),
 username TEXT NOT NULL UNIQUE CHECK(length(username) > 0),
 password_hash TEXT NOT NULL CHECK(length(password_hash) > 0),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now'))
);
CREATE TABLE characters (
 id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(id > 0),
 account_id INTEGER NOT NULL REFERENCES accounts(id),
 name TEXT NOT NULL CHECK(length(name) > 0),
 level INTEGER NOT NULL DEFAULT 1 CHECK(level BETWEEN 0 AND 4294967295),
 job INTEGER NOT NULL DEFAULT 1 CHECK(job BETWEEN 0 AND 4294967295),
 hp INTEGER NOT NULL DEFAULT 100 CHECK(hp BETWEEN 0 AND 4294967295),
 mp INTEGER NOT NULL DEFAULT 50 CHECK(mp BETWEEN 0 AND 4294967295),
 map_id INTEGER NOT NULL DEFAULT 1 CHECK(map_id BETWEEN 0 AND 4294967295),
 x INTEGER NOT NULL DEFAULT 100 CHECK(x BETWEEN -2147483648 AND 2147483647),
 y INTEGER NOT NULL DEFAULT 100 CHECK(y BETWEEN -2147483648 AND 2147483647),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now'))
);
CREATE INDEX idx_characters_account_id ON characters(account_id);
)SQL"}, {2, "recovered_characters", R"SQL(
CREATE TABLE recovered_characters (
 id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(id > 0),
 account_id INTEGER NOT NULL REFERENCES accounts(id) CHECK(account_id > 0),
 slot INTEGER NOT NULL CHECK(typeof(slot) = 'integer' AND slot BETWEEN 0 AND 1),
 profile BLOB NOT NULL CHECK(typeof(profile) = 'blob' AND length(profile) = 40),
 name_bytes BLOB NOT NULL UNIQUE CHECK(typeof(name_bytes) = 'blob' AND length(name_bytes) BETWEEN 1 AND 14),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now')),
 UNIQUE(account_id, slot),
 CHECK(instr(name_bytes, X'00') = 0 AND substr(profile, 1, length(name_bytes)) = name_bytes
       AND substr(profile, length(name_bytes) + 1, 1) = X'00')
);
)SQL"}, {3, "recovered_positions", R"SQL(
CREATE TABLE recovered_positions (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id > 0),
 area INTEGER NOT NULL CHECK(typeof(area) = 'integer' AND area BETWEEN 0 AND 63),
 scene INTEGER NOT NULL CHECK(typeof(scene) = 'integer' AND scene BETWEEN 0 AND 1023),
 x INTEGER NOT NULL CHECK(typeof(x) = 'integer' AND x BETWEEN 0 AND 65535),
 y INTEGER NOT NULL CHECK(typeof(y) = 'integer' AND y BETWEEN 0 AND 65535),
 revision INTEGER NOT NULL CHECK(typeof(revision) = 'integer' AND revision BETWEEN 1 AND 9223372036854775807)
);
)SQL"}, {4, "native_map_catalog", R"SQL(
CREATE TABLE native_data_sources (
 dataset_id TEXT PRIMARY KEY NOT NULL CHECK(length(dataset_id) > 0),
 source_path TEXT NOT NULL CHECK(length(source_path) > 0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256) = 64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256) = 64 AND decoded_sha256 NOT GLOB '*[^0-9a-f]*'),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256) = 64 AND native_image_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_section TEXT NOT NULL CHECK(length(source_section) > 0),
 loader_rva TEXT NOT NULL CHECK(length(loader_rva) > 0),
 lookup_rva TEXT NOT NULL CHECK(length(lookup_rva) > 0),
 row_count INTEGER NOT NULL CHECK(typeof(row_count) = 'integer' AND row_count BETWEEN 1 AND 32767)
);
CREATE TABLE native_map_catalog (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index) = 'integer' AND source_record_index BETWEEN 0 AND 32766),
 source_line INTEGER NOT NULL CHECK(typeof(source_line) = 'integer' AND source_line > 0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256) = 64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record) = 'blob' AND length(raw_record) BETWEEN 1 AND 4095),
 area INTEGER NOT NULL CHECK(typeof(area) = 'integer' AND area BETWEEN 1 AND 16),
 scene INTEGER NOT NULL CHECK(typeof(scene) = 'integer' AND scene BETWEEN 0 AND 1023),
 kind INTEGER NOT NULL CHECK(typeof(kind) = 'integer' AND kind BETWEEN 0 AND 3),
 PRIMARY KEY(dataset_id, source_record_index),
 UNIQUE(dataset_id, area, scene)
);
)SQL"}, {5, "native_skill_catalog", R"SQL(
CREATE TABLE native_skill_catalog (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index) = 'integer' AND source_record_index BETWEEN 0 AND 1019),
 source_offset INTEGER NOT NULL CHECK(typeof(source_offset) = 'integer' AND source_offset = 8 + kind * 28164 + (definition_id - 1) * 110),
 record_sha256 TEXT NOT NULL CHECK(typeof(record_sha256) = 'text' AND length(record_sha256) = 64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record) = 'blob' AND length(raw_record) = 110),
 kind INTEGER NOT NULL CHECK(typeof(kind) = 'integer' AND kind BETWEEN 0 AND 3),
 definition_id INTEGER NOT NULL CHECK(typeof(definition_id) = 'integer' AND definition_id BETWEEN 1 AND 255),
 PRIMARY KEY(dataset_id, source_record_index),
 UNIQUE(dataset_id, kind, definition_id),
 CHECK(hex(substr(raw_record, 1, 2)) = printf('%02X%02X', definition_id, kind))
);
)SQL"}, {6, "character_resources", R"SQL(
CREATE TABLE character_resources (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id > 0),
 hp INTEGER NOT NULL CHECK(typeof(hp)='integer' AND hp BETWEEN 0 AND 4294967295),
 max_hp INTEGER NOT NULL CHECK(typeof(max_hp)='integer' AND max_hp BETWEEN 1 AND 4294967295 AND hp<=max_hp),
 mp INTEGER NOT NULL CHECK(typeof(mp)='integer' AND mp BETWEEN 0 AND 4294967295),
 max_mp INTEGER NOT NULL CHECK(typeof(max_mp)='integer' AND max_mp BETWEEN 0 AND 4294967295 AND mp<=max_mp),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 9223372036854775807),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0012')
);
)SQL"}, {7, "battle_reservations", R"SQL(
CREATE TABLE battle_reservations (
 id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(id>0),
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) CHECK(character_id>0),
 resource_revision INTEGER NOT NULL CHECK(typeof(resource_revision)='integer' AND resource_revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0012'),
 UNIQUE(character_id,resource_revision)
);
)SQL"}, {8, "diagnostic_battle_settlements", R"SQL(
CREATE TABLE character_experience (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 total INTEGER NOT NULL CHECK(typeof(total)='integer' AND total BETWEEN 0 AND 9223372036854775807),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0012')
);
CREATE TABLE battle_settlements (
 battle_id INTEGER PRIMARY KEY REFERENCES battle_reservations(id) CHECK(battle_id>0),
 request TEXT NOT NULL CHECK(length(request)>0),
 resource_revision INTEGER NOT NULL CHECK(typeof(resource_revision)='integer' AND resource_revision>0),
 total_experience INTEGER NOT NULL CHECK(typeof(total_experience)='integer' AND total_experience BETWEEN 0 AND 9223372036854775807),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0012')
);
)SQL"}, {9, "diagnostic_role_snapshots", R"SQL(
CREATE TABLE character_role_snapshots (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=25 AND substr(logical,1,1)=X'22'),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0013')
);
)SQL"}, {10, "diagnostic_battle_checkpoints", R"SQL(
CREATE TABLE battle_checkpoints (
 battle_id INTEGER PRIMARY KEY REFERENCES battle_reservations(id) CHECK(battle_id>0),
 document TEXT NOT NULL CHECK(typeof(document)='text' AND length(document) BETWEEN 1 AND 32768),
 resource_revision INTEGER NOT NULL CHECK(typeof(resource_revision)='integer' AND resource_revision>0),
 policy_id TEXT NOT NULL CHECK(policy_id='CUSTOM-0012/diagnostic-v1')
);
)SQL"}, {11, "diagnostic_inventory_slots", R"SQL(
CREATE TABLE diagnostic_inventory_slots (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) CHECK(character_id>0),
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 49),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 0 AND 65535),
 count INTEGER NOT NULL CHECK(typeof(count)='integer' AND count BETWEEN 0 AND 127),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0015'),
 CHECK((count=0 AND item_id=0) OR (count>0 AND item_id>0)),
 PRIMARY KEY(character_id,slot)
);
)SQL"}, {12, "diagnostic_revival_recovery", R"SQL(
ALTER TABLE battle_checkpoints ADD COLUMN revival_document TEXT
 CHECK(revival_document IS NULL OR (typeof(revival_document)='text' AND length(revival_document) BETWEEN 1 AND 65536));
)SQL"}, {13, "diagnostic_quest_journal", R"SQL(
CREATE TABLE diagnostic_quest_journal (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 slots BLOB NOT NULL CHECK(typeof(slots)='blob' AND length(slots)=60),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0018')
);
)SQL"}, {14, "native_quest_descriptions", R"SQL(
CREATE TABLE native_quest_descriptions (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 mission_index INTEGER NOT NULL CHECK(typeof(mission_index)='integer' AND mission_index BETWEEN 1 AND 32767),
 description_index INTEGER NOT NULL CHECK(typeof(description_index)='integer' AND description_index BETWEEN 0 AND 32766),
 description_count INTEGER NOT NULL CHECK(typeof(description_count)='integer' AND description_count BETWEEN 1 AND 32767),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 CHECK(description_index<description_count),
 PRIMARY KEY(dataset_id,mission_index,description_index)
);
)SQL"}, {15, "native_quest_requirement_display", R"SQL(
CREATE TABLE native_quest_requirement_display (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 serial INTEGER NOT NULL CHECK(typeof(serial)='integer' AND serial BETWEEN 1 AND 32767),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 item_quantity_pairs BLOB NOT NULL CHECK(typeof(item_quantity_pairs)='blob' AND length(item_quantity_pairs)=12),
 PRIMARY KEY(dataset_id,serial)
);
)SQL"}, {16, "diagnostic_town_guide_progress", R"SQL(
CREATE TABLE diagnostic_town_guide_progress (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 stage INTEGER NOT NULL CHECK(typeof(stage)='integer' AND stage BETWEEN 1 AND 2),
 journal_description INTEGER NOT NULL CHECK(typeof(journal_description)='integer' AND journal_description=stage),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0021')
);
)SQL"}, {17, "diagnostic_town_guide_reward", R"SQL(
ALTER TABLE diagnostic_town_guide_progress RENAME TO diagnostic_town_guide_progress_v16;
CREATE TABLE diagnostic_town_guide_progress (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 stage INTEGER NOT NULL CHECK(typeof(stage)='integer' AND stage BETWEEN 1 AND 3),
 journal_description INTEGER NOT NULL CHECK(typeof(journal_description)='integer' AND
   journal_description=CASE WHEN stage=3 THEN 0 ELSE stage END),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0021')
);
INSERT INTO diagnostic_town_guide_progress SELECT * FROM diagnostic_town_guide_progress_v16;
DROP TABLE diagnostic_town_guide_progress_v16;
CREATE TABLE diagnostic_town_guide_reward (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) CHECK(character_id>0),
 progress_revision INTEGER NOT NULL CHECK(typeof(progress_revision)='integer' AND progress_revision>0),
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 49),
 slot_revision INTEGER NOT NULL CHECK(typeof(slot_revision)='integer' AND slot_revision>0),
 item_id INTEGER NOT NULL CHECK(item_id=5569),
 count INTEGER NOT NULL CHECK(count=1),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0022')
);
)SQL"}, {18, "native_skill_books", R"SQL(
CREATE TABLE native_skill_books (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index)='integer' AND source_record_index BETWEEN 0 AND 380),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(typeof(decoded_offset)='integer' AND decoded_offset>=0),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 6501 AND 7199),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 parsed_sha256 TEXT NOT NULL CHECK(length(parsed_sha256)=64 AND parsed_sha256 NOT GLOB '*[^0-9a-f]*'),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 PRIMARY KEY(dataset_id,source_record_index),
 UNIQUE(dataset_id,item_id)
);
CREATE TABLE native_skill_book_bindings (
 book_dataset_id TEXT NOT NULL,
 skill_dataset_id TEXT NOT NULL,
 kind INTEGER NOT NULL CHECK(typeof(kind)='integer' AND kind BETWEEN 0 AND 3),
 definition_id INTEGER NOT NULL CHECK(typeof(definition_id)='integer' AND definition_id BETWEEN 1 AND 255),
 item_id INTEGER NOT NULL,
 PRIMARY KEY(book_dataset_id,kind,definition_id),
 UNIQUE(book_dataset_id,item_id),
 FOREIGN KEY(book_dataset_id,item_id) REFERENCES native_skill_books(dataset_id,item_id),
 FOREIGN KEY(skill_dataset_id,kind,definition_id) REFERENCES native_skill_catalog(dataset_id,kind,definition_id)
);
)SQL"}, {19, "recovered_character_name_encoding", R"SQL(
ALTER TABLE recovered_characters ADD COLUMN name_codepage INTEGER NOT NULL DEFAULT 950
 CHECK(typeof(name_codepage)='integer' AND name_codepage IN (0,936,950));
)SQL"}, {20, "native_enemy_display_catalog", R"SQL(
CREATE TABLE native_enemy_display_catalog (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index)='integer' AND source_record_index BETWEEN 0 AND 7814),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 source_offset INTEGER NOT NULL CHECK(typeof(source_offset)='integer' AND source_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 2047),
 area_generation INTEGER NOT NULL CHECK(typeof(area_generation)='integer' AND area_generation BETWEEN 1 AND 16),
 area INTEGER NOT NULL CHECK(typeof(area)='integer' AND area BETWEEN 0 AND 16),
 scene INTEGER NOT NULL CHECK(typeof(scene)='integer' AND scene BETWEEN 0 AND 65535),
 ordinal INTEGER NOT NULL CHECK(typeof(ordinal)='integer' AND ordinal BETWEEN 1 AND 7815),
 lookup_visible INTEGER NOT NULL CHECK(typeof(lookup_visible)='integer' AND lookup_visible IN (0,1)),
 source_label INTEGER NOT NULL CHECK(typeof(source_label)='integer' AND source_label BETWEEN 0 AND 2147483647),
 name_bytes BLOB NOT NULL CHECK(typeof(name_bytes)='blob' AND length(name_bytes) BETWEEN 1 AND 15),
 PRIMARY KEY(dataset_id,source_record_index)
);
CREATE UNIQUE INDEX native_enemy_display_lookup ON native_enemy_display_catalog(dataset_id,area,scene,ordinal)
 WHERE lookup_visible=1;
)SQL"}, {21, "native_med02_recovery_declarations", R"SQL(
CREATE TABLE native_med02_recovery_declarations (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index)='integer' AND source_record_index BETWEEN 0 AND 99),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 1 AND 65535),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 tooltip_bytes BLOB NOT NULL CHECK(typeof(tooltip_bytes)='blob' AND length(tooltip_bytes) BETWEEN 1 AND 255),
 declared_hp INTEGER NOT NULL CHECK(typeof(declared_hp)='integer' AND declared_hp BETWEEN 0 AND 2147483647),
 declared_mp INTEGER NOT NULL CHECK(typeof(declared_mp)='integer' AND declared_mp BETWEEN 0 AND 2147483647),
 normal_use INTEGER NOT NULL CHECK(normal_use=1),
 hotkey_allowed INTEGER NOT NULL CHECK(hotkey_allowed=1),
 PRIMARY KEY(dataset_id,source_record_index),
 UNIQUE(dataset_id,item_id),
 CHECK(declared_hp>0 OR declared_mp>0)
);
)SQL"}, {22, "owned_deity_and_pet2_snapshots", R"SQL(
CREATE TABLE native_companion_metadata (
 family TEXT NOT NULL CHECK(family IN ('GOD','NCP')),
 metadata_key INTEGER NOT NULL CHECK(typeof(metadata_key)='integer' AND
  ((family='GOD' AND metadata_key BETWEEN 2801 AND 2834) OR
   (family='NCP' AND metadata_key BETWEEN 28001 AND 32599))),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 PRIMARY KEY(family,metadata_key)
);
CREATE TABLE character_deities (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 row_key INTEGER NOT NULL CHECK(typeof(row_key)='integer' AND row_key BETWEEN 1 AND 127),
 declaration BLOB NOT NULL CHECK(typeof(declaration)='blob' AND length(declaration)=19 AND substr(declaration,1,1)=X'30'),
 status BLOB NOT NULL CHECK(typeof(status)='blob' AND length(status)=29 AND substr(status,1,1)=X'31'),
 skills BLOB NOT NULL CHECK(typeof(skills)='blob' AND length(skills)<=400 AND length(skills)%4=0),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 authority TEXT NOT NULL CHECK(authority IN ('NATIVE_VERIFIED','CUSTOM_DESIGNED','CUSTOM_TEST_NOT_NATIVE')),
 evidence_id TEXT NOT NULL CHECK(length(evidence_id) BETWEEN 1 AND 512),
 PRIMARY KEY(character_id,row_key)
);
CREATE TABLE character_deity_selection (
 character_id INTEGER PRIMARY KEY,
 row_key INTEGER NOT NULL,
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 FOREIGN KEY(character_id,row_key) REFERENCES character_deities(character_id,row_key)
);
CREATE TABLE character_pet2_slots (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 42 AND 44),
 metadata BLOB NOT NULL CHECK(typeof(metadata)='blob'),
 stats BLOB NOT NULL CHECK(typeof(stats)='blob'),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 authority TEXT NOT NULL CHECK(authority IN ('NATIVE_VERIFIED','CUSTOM_DESIGNED','CUSTOM_TEST_NOT_NATIVE')),
 evidence_id TEXT NOT NULL CHECK(length(evidence_id) BETWEEN 1 AND 512),
 PRIMARY KEY(character_id,slot),
 CHECK((length(metadata)=0 AND length(stats)=0) OR
       (length(metadata)=20 AND length(stats)=73 AND substr(stats,1,1)=X'FB'))
);
)SQL"}, {23, "native_quest_source_catalog", R"SQL(
CREATE TABLE native_quest_definitions (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 mission_index INTEGER NOT NULL CHECK(mission_index BETWEEN 1 AND 418),
 description_count INTEGER NOT NULL CHECK(description_count BETWEEN 1 AND 32767),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 65535),
 title_bytes BLOB NOT NULL CHECK(typeof(title_bytes)='blob' AND length(title_bytes)>0),
 PRIMARY KEY(dataset_id,mission_index)
);
CREATE TABLE native_daily_quest_source (
 record_index INTEGER PRIMARY KEY CHECK(record_index BETWEEN 0 AND 84),
 source_path TEXT NOT NULL CHECK(source_path='Data2/Patch/Comm/DayMissionDesc.csvZ'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'),
 decoded_sha256 TEXT NOT NULL CHECK(decoded_sha256='2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf'),
 source_line INTEGER NOT NULL UNIQUE CHECK(source_line>0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 65535),
 field_count INTEGER NOT NULL CHECK(field_count IN (12,19)),
 authority TEXT NOT NULL CHECK(authority='SOURCE_FIELDS_ONLY')
);
)SQL"}, {24, "owned_quest_journal_snapshots", R"SQL(
-- CUSTOM-0041: display snapshots only, not quest progression/reward rules.
CREATE TABLE character_quest_journals (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 values_blob BLOB NOT NULL CHECK(typeof(values_blob)='blob' AND length(values_blob)=60),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 255),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0041')
);
)SQL"}, {25, "native_multi_message_source", R"SQL(
CREATE TABLE native_multi_message_sources (
 source_file TEXT PRIMARY KEY,
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 record_count INTEGER NOT NULL CHECK(record_count>0),
 line_count INTEGER NOT NULL CHECK(line_count>2),
 decoded_size INTEGER NOT NULL CHECK(decoded_size>0),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
);
CREATE TABLE native_multi_messages (
 message_key INTEGER PRIMARY KEY CHECK(message_key BETWEEN 1 AND 2995),
 source_file TEXT NOT NULL REFERENCES native_multi_message_sources(source_file),
 option_count INTEGER NOT NULL CHECK(option_count BETWEEN 1 AND 255),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
);
CREATE TABLE native_multi_message_rows (
 message_key INTEGER NOT NULL REFERENCES native_multi_messages(message_key),
 ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
 source_line INTEGER NOT NULL CHECK(source_line>=3),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 text_bytes BLOB NOT NULL CHECK(typeof(text_bytes)='blob' AND length(text_bytes)>0),
 PRIMARY KEY(message_key,ordinal)
);
)SQL"}, {26, "native_map_item_sources", R"SQL(
CREATE TABLE native_map_item_sources (
 source_file TEXT PRIMARY KEY,
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 source_section TEXT NOT NULL CHECK(source_section='SPI'),
 section_row_count INTEGER NOT NULL CHECK(section_row_count=737),
 row_desc_line INTEGER NOT NULL CHECK(row_desc_line=3),
 row_desc_sha256 TEXT NOT NULL CHECK(length(row_desc_sha256)=64),
 row_desc_raw BLOB NOT NULL CHECK(typeof(row_desc_raw)='blob'),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
);
CREATE TABLE native_map_item_rows (
 item_id INTEGER PRIMARY KEY CHECK(item_id IN (5569,5576)),
 source_file TEXT NOT NULL REFERENCES native_map_item_sources(source_file),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 category_code INTEGER NOT NULL,
 resource_name BLOB NOT NULL CHECK(typeof(resource_name)='blob'),
 icon_id INTEGER NOT NULL CHECK(icon_id BETWEEN 0 AND 65535),
 name_bytes BLOB NOT NULL CHECK(typeof(name_bytes)='blob'),
 description_bytes BLOB NOT NULL CHECK(typeof(description_bytes)='blob'),
 effect_code INTEGER NOT NULL CHECK(effect_code BETWEEN 0 AND 65535),
 source_flags BLOB NOT NULL CHECK(typeof(source_flags)='blob' AND length(source_flags)=12),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
);
)SQL"}, {27, "native_weapons_and_owned_auxiliary", R"SQL(
CREATE TABLE native_weapon_sources (
 family TEXT PRIMARY KEY CHECK(family IN ('WPN','TWP')),
 source_file TEXT NOT NULL CHECK(source_file='Data2/Patch/Comm/gamedata.csvZ'),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256)=64),
 loader_rva TEXT NOT NULL CHECK(loader_rva='0x59420'),
 lookup_rva TEXT NOT NULL CHECK(lookup_rva='0x59a60'),
 row_count INTEGER NOT NULL CHECK(row_count IN (629,630)),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY')
);
CREATE TABLE native_weapon_rows (
 family TEXT NOT NULL REFERENCES native_weapon_sources(family),
 item_id INTEGER NOT NULL CHECK(item_id BETWEEN 1 AND 32767),
 source_record_index INTEGER NOT NULL CHECK(source_record_index BETWEEN 0 AND 629),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 parsed_sha256 TEXT NOT NULL CHECK(length(parsed_sha256)=64),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY'),
 PRIMARY KEY(family,item_id),
 UNIQUE(item_id),
 UNIQUE(family,source_record_index)
);
CREATE TABLE character_role_auxiliary_snapshots (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=61 AND substr(logical,1,1)=X'2C'),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 255),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0045')
);
)SQL"}, {28, "owned_weapon_slot_metadata", R"SQL(
CREATE TABLE character_weapon_slot_metadata (
 character_id INTEGER NOT NULL,
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND (slot BETWEEN 0 AND 29 OR slot=34)),
 logical20 BLOB NOT NULL CHECK(typeof(logical20)='blob' AND length(logical20)=20),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE','EMPTY_SLOT_POLICY')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 512),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0046'),
 PRIMARY KEY(character_id,slot),
 FOREIGN KEY(character_id,slot) REFERENCES diagnostic_inventory_slots(character_id,slot)
);
-- CUSTOM-0046: another scalar policy may reuse an explicitly empty cell.
-- Retire only its inactive tail overlay; never delete an occupied instance.
CREATE TRIGGER retire_empty_weapon_overlay
AFTER UPDATE OF item_id,count,revision ON diagnostic_inventory_slots
BEGIN
 DELETE FROM character_weapon_slot_metadata
 WHERE character_id=NEW.character_id AND slot=NEW.slot AND origin='EMPTY_SLOT_POLICY';
END;
)SQL"}, {29,"owned_player_appearance_snapshots",SqlitePlayerAppearanceRepository::schema()},
{30,"native_daily_display_and_owned_lists",R"SQL(
CREATE TABLE native_daily_quest_parsed (
 ordinal INTEGER PRIMARY KEY CHECK(ordinal BETWEEN 0 AND 84) REFERENCES native_daily_quest_source(record_index),
 source_line INTEGER NOT NULL CHECK(source_line BETWEEN 6 AND 90),
 pair_index INTEGER NOT NULL CHECK(pair_index BETWEEN 0 AND 255),
 pair_branch INTEGER NOT NULL CHECK(pair_branch BETWEEN 0 AND 255),
 logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=316),
 source_record_sha256 TEXT NOT NULL CHECK(length(source_record_sha256)=64),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'),
 decoded_sha256 TEXT NOT NULL CHECK(decoded_sha256='2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf'),
 catalog_sha256 TEXT NOT NULL CHECK(catalog_sha256='df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a'),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DISPLAY_ONLY')
);
-- CUSTOM-0049: issued display fixture/state only. No automatic source-derived
-- availability, quest acceptance, teleport, item consumption or reward grant.
CREATE TABLE character_daily_quest_lists (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=172 AND substr(logical,1,4)=X'FDAC0002'),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 512),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0049')
);
)SQL"}, {31,"owned_fruit_quests",SqliteFruitQuestRepository::schema()},
{32,"qualified_fruit_sources",NativeFruitQuestSources::schema()},
{33,"native_npc_display_catalog",NativeNpcDisplayCatalog::schema()},
{34,"qualified_world_display_records",SqliteWorldDisplayRepository::schema()},
{35,"qualified_monster_level_records",SqliteWorldDisplayRepository::level_schema()},
{36,"native_pet2_display_categories",NativePet2CategoryCatalog::schema()},
{37,"owned_first_generation_pet_snapshots",R"SQL(
CREATE TABLE native_pet1_metadata (
 family TEXT NOT NULL CHECK(family='COM'),
 metadata_key INTEGER NOT NULL CHECK(typeof(metadata_key)='integer' AND metadata_key BETWEEN 24001 AND 26070),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 PRIMARY KEY(family,metadata_key)
);
-- Retain the historical table name and three shared cells; preserve all rows.
CREATE TABLE character_pet_slots_next (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 42 AND 44),
 metadata BLOB NOT NULL CHECK(typeof(metadata)='blob'),
 stats BLOB NOT NULL CHECK(typeof(stats)='blob'),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 authority TEXT NOT NULL CHECK(authority IN ('NATIVE_VERIFIED','CUSTOM_DESIGNED','CUSTOM_TEST_NOT_NATIVE')),
 evidence_id TEXT NOT NULL CHECK(length(evidence_id) BETWEEN 1 AND 512),
 PRIMARY KEY(character_id,slot),
 CHECK((length(metadata)=0 AND length(stats)=0) OR
       (length(metadata)=20 AND ((length(stats)=73 AND substr(stats,1,1)=X'FB') OR
                                (length(stats)=53 AND substr(stats,1,1)=X'E3'))))
);
INSERT INTO character_pet_slots_next SELECT * FROM character_pet2_slots;
DROP TABLE character_pet2_slots;
ALTER TABLE character_pet_slots_next RENAME TO character_pet2_slots;
)SQL"}, {38,"character_streamer_privilege",R"SQL(
-- CUSTOM-0054: owner-configured presentation privilege, never combat/admin authority.
ALTER TABLE recovered_characters ADD COLUMN streamer_privilege INTEGER NOT NULL DEFAULT 0
 CHECK(typeof(streamer_privilege)='integer' AND streamer_privilege BETWEEN 0 AND 3);
)SQL"}, {39,"owned_secondary_role_text",SqliteRoleTextRepository::schema()},
{40,"owned_teleport_gem_instances",SqliteTeleportGemRepository::schema()},
{41,"native_armor_definitions",NativeArmorCatalog::schema()},
{42,"owned_armor_instances",SqliteArmorSlotRepository::schema()},
{43,"owned_armor_bank_instances",R"SQL(
-- CUSTOM-0067: the legacy scalar bank tables were installed by Application,
-- not by migrations 1..42. Create the exact same empty dependencies on fresh
-- databases; IF NOT EXISTS preserves all already installed tables and rows.
-- This allocates no per-character capacity, instance, balance or banker lease.
CREATE TABLE IF NOT EXISTS character_bank_item_slots(
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 299),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 0 AND 65535),
 count INTEGER NOT NULL CHECK(typeof(count)='integer' AND count BETWEEN 0 AND 127),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 item_design_id TEXT NOT NULL CHECK(item_design_id='CUSTOM-0015'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0065'),
 CHECK((count=0 AND item_id=0) OR (count>0 AND item_id>0)),
 PRIMARY KEY(character_id,slot));
CREATE TABLE IF NOT EXISTS character_bank_item_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation IN (99,100,101)),
 page INTEGER NOT NULL CHECK(page BETWEEN 0 AND 5),
 source INTEGER NOT NULL CHECK(source BETWEEN 0 AND 49),
 destination INTEGER NOT NULL CHECK(destination BETWEEN 0 AND 49),
 quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 127),
 before_state TEXT NOT NULL CHECK(length(before_state)>0),
 after_state TEXT NOT NULL CHECK(length(after_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0065'));
)SQL"+SqliteOwnedArmorBankRepository::schema()},
{44,"owned_foreign_bank_instances",SqliteOwnedForeignBankRepository::schema()},
{45,"owned_instance_trade",SqliteOwnedInstanceTradeRepository::schema()},
{46,"owned_mixed_bank",SqliteOwnedMixedBankRepository::schema()},
{47,"owned_instance_discard",SqliteOwnedInstanceDiscardRepository::schema()},
{48,"owned_guild_chat_membership",SqliteGuildRepository::schema()},
// CUSTOM-0078: same immutable49 SQL/identity as the qualified candidate path.
{49,"owned_player_guild_membership_candidate",SqliteOwnedGuildMembershipRepository::schema()}};
}
// CUSTOM-0078: explicit candidate-only storage until native runtime/live acceptance.
// Ordinary server startup retains the qualified migration49 default.
std::vector<Migration> owned_guild_announcement_migrations() {
    auto candidate=default_sqlite_migrations();
    candidate.push_back({50,"owned_guild_announcements_candidate",SqliteOwnedGuildAnnouncementRepository::schema()});
    return candidate;
}
}
