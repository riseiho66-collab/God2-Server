#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteCompanionRepository.h"
#include "game/ShunyingSanshazhan.h"
#include "game/ThousandBulls.h"
#include "game/RevivalRecoveryCodec.h"
#include "game/ExtendedExperienceAmount.h"
#include <algorithm>
#include <limits>
#include <utility>
#include <nlohmann/json.hpp>

namespace god2 {
bool SqliteRecoveredCharacterRepository::erase_owned(std::uint64_t account,std::uint64_t character,
    std::span<const std::uint8_t> expected_name) {
    if(!account || !character || expected_name.empty() || expected_name.size()>14)return false;
    sqlite_detail::Transaction transaction(db_);
    {
        sqlite_detail::Statement owned(db_,"SELECT id FROM recovered_characters WHERE id=? AND account_id=? AND name_bytes=?");
        owned.bind_id(1,character);owned.bind_id(2,account);owned.bind_blob(3,expected_name);
        if(!owned.row())return false;
    }
    // Existing non-cascading battle FKs and composite inventory/deity FKs
    // require leaves before roots. Deferred checks keep the whole delete atomic.
    sqlite_detail::execute(db_,"PRAGMA defer_foreign_keys=ON");
    for(const auto* table:{"battle_settlements","battle_checkpoints"}) {
        const auto sql=std::string("DELETE FROM ")+table+
            " WHERE battle_id IN (SELECT id FROM battle_reservations WHERE character_id=?)";
        sqlite_detail::Statement remove(db_,sql.c_str());remove.bind_id(1,character);remove.done();
    }
    // Enumerate the recovered-character FK graph, including runtime-created
    // owned quest tables. Unrelated legacy character IDs stay outside this graph.
    std::vector<std::string> tables;
    {
        sqlite_detail::Statement schema(db_,"SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'");
        while(schema.row())tables.push_back(schema.text(0));
    }
    const auto quote=[](const std::string& identifier) {
        std::string result="\"";for(char c:identifier){result+=c;if(c=='\"')result+=c;}return result+'\"';
    };
    std::vector<std::string> descendants{"recovered_characters"};
    bool extended=true;
    while(extended) {
        extended=false;
        for(const auto& table:tables) {
            if(std::find(descendants.begin(),descendants.end(),table)!=descendants.end())continue;
            const auto fk="PRAGMA foreign_key_list("+quote(table)+")";
            sqlite_detail::Statement references(db_,fk.c_str());
            while(references.row()) {
                const auto parent=references.text(2);
                if(std::find(descendants.begin(),descendants.end(),parent)!=descendants.end()) {
                    descendants.push_back(table);extended=true;break;
                }
            }
        }
    }
    for(const auto& table:tables) {
        if(std::find(descendants.begin(),descendants.end(),table)==descendants.end())continue;
        const auto info="PRAGMA table_info("+quote(table)+")";
        sqlite_detail::Statement columns(db_,info.c_str());bool has_character=false;
        while(columns.row())if(columns.text(1)=="character_id")has_character=true;
        if(!has_character)continue;
        const auto sql="DELETE FROM "+quote(table)+" WHERE character_id=?";
        sqlite_detail::Statement remove(db_,sql.c_str());remove.bind_id(1,character);remove.done();
    }
    sqlite_detail::Statement remove(db_,"DELETE FROM recovered_characters WHERE id=? AND account_id=? AND name_bytes=?");
    remove.bind_id(1,character);remove.bind_id(2,account);remove.bind_blob(3,expected_name);remove.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Character deletion ownership conflict");
    transaction.commit();return true;
}
namespace {
std::size_t name_size(const std::array<std::uint8_t, 40>& profile) {
    const auto end = std::find(profile.begin(), profile.begin() + 15, 0);
    if (end == profile.begin() || end == profile.begin() + 15)
        throw DatabaseError("Invalid recovered character profile");
    return static_cast<std::size_t>(end - profile.begin());
}
void require_account(sqlite3* db, std::uint64_t account_id) {
    if (account_id == 0) throw DatabaseError("Invalid recovered character account");
    sqlite_detail::Statement account(db, "SELECT id FROM accounts WHERE id=?");
    account.bind_id(1, account_id);
    if (!account.row()) throw DatabaseError("Invalid recovered character account");
}
StoredInventorySlot read_inventory_row(sqlite_detail::Statement& query,int offset) {
    StoredInventorySlot value{query.number<std::uint16_t>(offset),
        query.number<std::uint8_t>(offset+1),query.number<std::uint64_t>(offset+2),
        query.text(offset+3)};
    if(value.count>127 || !value.revision || (value.count==0)!=(value.item_id==0) ||
       query.text(offset+4)!="CUSTOM-0015" || value.source_sha256.size()!=64 ||
       value.source_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos)
        throw DatabaseError("Invalid inventory row");
    return value;
}
RecoveredCharacter read_character(sqlite_detail::Statement& statement) {
    RecoveredCharacter result;
    result.id = statement.number<std::uint64_t>(0);
    result.account_id = statement.number<std::uint64_t>(1);
    result.slot = statement.number<std::uint8_t>(2);
    if (result.id == 0 || result.account_id == 0 || result.slot > 1)
        throw DatabaseError("Invalid recovered character row");
    const auto profile = statement.blob(3, result.profile.size(), result.profile.size());
    std::copy(profile.begin(), profile.end(), result.profile.begin());
    const auto name = statement.blob(4, 1, 14);
    if (name.size() != name_size(result.profile) ||
        !std::equal(name.begin(), name.end(), result.profile.begin()))
        throw DatabaseError("Invalid recovered character name data");
    result.created_at = statement.text(5);
    result.name_codepage=statement.number<std::uint16_t>(6);
    if(result.name_codepage!=0 && result.name_codepage!=936 && result.name_codepage!=950)
        throw DatabaseError("Invalid character name encoding");
    result.streamer_privilege=statement.number<std::uint8_t>(7);
    if(result.streamer_privilege>3)throw DatabaseError("Invalid character chat style privilege");
    if (result.created_at.empty()) throw DatabaseError("Invalid recovered character creation time");
    return result;
}
}

std::optional<StoredTownGuideProgress> SqliteRecoveredCharacterRepository::load_town_guide_progress(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement query(db_,
        "SELECT q.character_id IS NOT NULL,q.stage,q.journal_description,q.revision,q.source_sha256,q.design_id,"
        "r.character_id IS NOT NULL,r.progress_revision,r.slot,r.slot_revision,r.item_id,r.count,r.source_sha256,r.design_id "
        "FROM recovered_characters c LEFT JOIN diagnostic_town_guide_progress q ON q.character_id=c.id "
        "LEFT JOIN diagnostic_town_guide_reward r ON r.character_id=c.id "
        "WHERE c.id=? AND c.account_id=?");
    query.bind_id(1,character);query.bind_id(2,account);
    if(!account || !character || !query.row()) throw DatabaseError("Invalid town guide owner");
    if(!query.integer(0)) {
        if(query.integer(6)) throw DatabaseError("Town reward without progress");
        return std::nullopt;
    }
    StoredTownGuideProgress value{query.number<std::uint32_t>(1),query.number<std::uint32_t>(2),
                                  query.number<std::uint64_t>(3)};
    if(value.stage<1 || value.stage>3 || value.journal_description!=(value.stage==3?0:value.stage) || !value.revision ||
       query.text(4)!=town_guide_source_sha256 || query.text(5)!="CUSTOM-0021")
        throw DatabaseError("Invalid town guide progress or provenance");
    if(value.stage==3) {
        if(!query.integer(6) || query.number<std::uint64_t>(7)!=value.revision ||
           query.number<std::uint32_t>(8)>=50 || !query.number<std::uint64_t>(9) ||
           query.integer(10)!=5569 || query.integer(11)!=1 ||
           query.text(12)!=town_reward_item_source_sha256 || query.text(13)!="CUSTOM-0022")
            throw DatabaseError("Town completion without matching reward receipt");
    } else if(query.integer(6)) throw DatabaseError("Town reward before completion");
    return value;
}

StoredTownGuideProgress SqliteRecoveredCharacterRepository::commit_town_guide_progress(
    std::uint64_t account,std::uint64_t character,const std::optional<StoredTownGuideProgress>& expected,
    std::uint32_t next_stage) {
    // Completion must use the separate atomic reward transaction.
    if(next_stage<1 || next_stage>2 || next_stage!=(expected?expected->stage+1:1) ||
       (expected && (expected->stage!=1 || expected->journal_description!=1 || !expected->revision ||
        expected->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))))
        throw DatabaseError("Invalid incomplete town guide transition");
    sqlite_detail::Transaction transaction(db_);
    if(load_town_guide_progress(account,character)!=expected)
        throw DatabaseError("Town guide snapshot conflict");
    const StoredTownGuideProgress next{next_stage,next_stage,expected?expected->revision+1:1};
    sqlite_detail::Statement write(db_,expected ?
        "UPDATE diagnostic_town_guide_progress SET stage=?,journal_description=?,revision=? "
        "WHERE character_id=? AND revision=?" :
        "INSERT INTO diagnostic_town_guide_progress(stage,journal_description,revision,character_id,source_sha256,design_id) "
        "VALUES(?,?,?,?,?,'CUSTOM-0021')");
    write.bind_id(1,next.stage);write.bind_id(2,next.journal_description);
    write.bind_id(3,next.revision);write.bind_id(4,character);
    if(expected) write.bind_id(5,expected->revision);
    else write.bind(5,town_guide_source_sha256);
    write.done();
    if(sqlite3_changes(db_)!=1 || load_town_guide_progress(account,character)!=std::optional{next})
        throw DatabaseError("Town guide write verification failed");
    transaction.commit();return next;
}

bool SqliteRecoveredCharacterRepository::provision_town_reward_slot(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);
    const auto progress=load_town_guide_progress(account,character);
    const auto existing=load_inventory_slot(account,character,0);
    if(existing) {
        if(!existing->item_id && existing->source_sha256!=town_reward_item_source_sha256)
            throw DatabaseError("Town empty slot source mismatch");
        transaction.commit();
        return false;
    }
    if(progress && progress->stage==3)
        throw DatabaseError("Completed town reward has no inventory slot");
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);
    if(pending.row()) throw DatabaseError("Town slot provision during pending battle");
    sqlite_detail::Statement insert(db_,
        "INSERT INTO diagnostic_inventory_slots(item_id,count,revision,source_sha256,character_id,slot,design_id) "
        "VALUES(0,0,1,?,?,0,'CUSTOM-0015')");
    insert.bind(1,town_reward_item_source_sha256);
    insert.bind_id(2,character);
    insert.done();
    const StoredInventorySlot empty{0,0,1,town_reward_item_source_sha256};
    if(sqlite3_changes(db_)!=1 || load_inventory_slot(account,character,0)!=std::optional{empty})
        throw DatabaseError("Town empty slot provision failed");
    transaction.commit();
    return true;
}

TownGuideRewardCommit SqliteRecoveredCharacterRepository::complete_town_guide(
    std::uint64_t account,std::uint64_t character,const StoredTownGuideProgress& expected,
    std::uint8_t slot,const StoredInventorySlot& expected_slot) {
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(expected.stage!=2 || expected.journal_description!=2 || !expected.revision || expected.revision>=limit ||
       slot>=50 || expected_slot.item_id || expected_slot.count || !expected_slot.revision ||
       expected_slot.revision>=limit || expected_slot.source_sha256!=town_reward_item_source_sha256)
        throw DatabaseError("Invalid town reward preconditions");
    sqlite_detail::Transaction transaction(db_);
    if(load_town_guide_progress(account,character)!=std::optional{expected} ||
       load_inventory_slot(account,character,slot)!=std::optional{expected_slot})
        throw DatabaseError("Town reward snapshot conflict");
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);
    if(pending.row()) throw DatabaseError("Town reward during pending battle");
    const StoredTownGuideProgress next{3,0,expected.revision+1};
    const StoredInventorySlot granted{5569,1,expected_slot.revision+1,town_reward_item_source_sha256};
    sqlite_detail::Statement progress(db_,"UPDATE diagnostic_town_guide_progress SET stage=3,journal_description=0,revision=? WHERE character_id=? AND revision=? AND stage=2");
    progress.bind_id(1,next.revision);progress.bind_id(2,character);progress.bind_id(3,expected.revision);
    progress.done();
    if(sqlite3_changes(db_)!=1) throw DatabaseError("Town completion update conflict");
    sqlite_detail::Statement inventory(db_,"UPDATE diagnostic_inventory_slots SET item_id=5569,count=1,revision=? WHERE character_id=? AND slot=? AND revision=? AND item_id=0 AND count=0");
    inventory.bind_id(1,granted.revision);inventory.bind_id(2,character);inventory.bind(3,slot);
    inventory.bind_id(4,expected_slot.revision);inventory.done();
    if(sqlite3_changes(db_)!=1) throw DatabaseError("Town reward slot conflict");
    sqlite_detail::Statement receipt(db_,"INSERT INTO diagnostic_town_guide_reward(character_id,progress_revision,slot,slot_revision,item_id,count,source_sha256,design_id) VALUES(?,?,?,?,5569,1,?,'CUSTOM-0022')");
    receipt.bind_id(1,character);receipt.bind_id(2,next.revision);receipt.bind(3,slot);
    receipt.bind_id(4,granted.revision);receipt.bind(5,town_reward_item_source_sha256);receipt.done();
    if(load_town_guide_progress(account,character)!=std::optional{next} ||
       load_inventory_slot(account,character,slot)!=std::optional{granted})
        throw DatabaseError("Town reward readback mismatch");
    transaction.commit();return {next,granted};
}

std::array<std::uint16_t,418> SqliteRecoveredCharacterRepository::load_quest_description_counts() {
    // One SELECT keeps source identity and all rows in a consistent SQL snapshot.
    sqlite_detail::Statement rows(db_,
        "SELECT q.mission_index,q.description_index,q.description_count,"
        "s.source_sha256,s.decoded_sha256,s.native_image_sha256,s.source_path,s.row_count,"
        "s.source_section,s.loader_rva,s.lookup_rva "
        "FROM native_quest_descriptions q LEFT JOIN native_data_sources s ON s.dataset_id=q.dataset_id "
        "WHERE q.dataset_id='current-quest-descriptions-v1' ORDER BY q.mission_index,q.description_index");
    std::array<std::uint16_t,418> counts{};
    std::uint32_t mission=1,index=0,total=0;
    while(rows.row()) {
        if(rows.text(3)!=quest_source_sha256 ||
           rows.text(4)!="f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0" ||
           rows.text(5)!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
           rows.text(6)!="Data2/Patch/Comm/Mission_data.csvZ" || rows.integer(7)!=418 ||
           rows.text(8)!="Mission_data" || rows.text(9)!="0x584ae" || rows.text(10)!="0xc9581")
            throw DatabaseError("Quest catalog source mismatch");
        const auto count=rows.number<std::uint16_t>(2);
        if(mission>counts.size() || !count || count>32767 ||
           rows.number<std::uint32_t>(0)!=mission || rows.number<std::uint32_t>(1)!=index ||
           (index && counts[mission-1]!=count))
            throw DatabaseError("Quest catalog order/count mismatch");
        counts[mission-1]=count;++total;
        if(++index==count) { ++mission;index=0; }
    }
    if(mission!=419 || index || total!=2014) throw DatabaseError("Incomplete quest catalog");
    return counts;
}

std::optional<StoredQuestJournal> SqliteRecoveredCharacterRepository::load_quest_journal(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement query(db_,
        "SELECT j.character_id IS NOT NULL,j.slots,j.revision,j.source_sha256,j.design_id "
        "FROM recovered_characters c LEFT JOIN diagnostic_quest_journal j ON j.character_id=c.id "
        "WHERE c.id=? AND c.account_id=?");
    query.bind_id(1,character);query.bind_id(2,account);
    if(!account || !character || !query.row()) throw DatabaseError("Invalid journal owner");
    if(!query.integer(0)) return std::nullopt;
    StoredQuestJournal value{};
    const auto bytes=query.blob(1,60,60);
    for(std::size_t slot=0;slot<value.slots.size();++slot)
        for(unsigned byte=0;byte<4;++byte)
            value.slots[slot]|=std::uint32_t{bytes[slot*4+byte]}<<(byte*8);
    value.revision=query.number<std::uint64_t>(2);value.source_sha256=query.text(3);
    if(!value.revision || query.text(4)!="CUSTOM-0018" || value.source_sha256.size()!=64 ||
       value.source_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos)
        throw DatabaseError("Invalid journal provenance");
    return value;
}

StoredQuestJournal SqliteRecoveredCharacterRepository::commit_quest_journal(
    std::uint64_t account,std::uint64_t character,const std::optional<StoredQuestJournal>& expected,
    StoredQuestJournal next,std::span<const std::uint16_t> description_counts) {
    if(!RecoveredQuestSync::encodeJournalLogical(next.slots,description_counts) ||
       next.source_sha256.size()!=64 || next.source_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos)
        throw DatabaseError("Invalid journal projection");
    sqlite_detail::Transaction transaction(db_);
    if(load_quest_journal(account,character)!=expected) throw DatabaseError("Journal snapshot conflict");
    if(expected && (expected->source_sha256!=next.source_sha256 ||
       expected->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())))
        throw DatabaseError("Journal source changed or revision overflow");
    next.revision=expected ? expected->revision+1 : 1;
    std::array<std::uint8_t,60> bytes{};
    for(std::size_t slot=0;slot<next.slots.size();++slot)
        for(unsigned byte=0;byte<4;++byte)
            bytes[slot*4+byte]=static_cast<std::uint8_t>(next.slots[slot]>>(byte*8));
    sqlite_detail::Statement write(db_,expected ?
        "UPDATE diagnostic_quest_journal SET slots=?,revision=?,source_sha256=? WHERE character_id=? AND revision=?" :
        "INSERT INTO diagnostic_quest_journal(slots,revision,source_sha256,character_id,design_id) VALUES(?,?,?,?,'CUSTOM-0018')");
    write.bind_blob(1,bytes);write.bind_id(2,next.revision);write.bind(3,next.source_sha256);write.bind_id(4,character);
    if(expected) write.bind_id(5,expected->revision);
    write.done();
    if(sqlite3_changes(db_)!=1 || load_quest_journal(account,character)!=std::optional<StoredQuestJournal>{next})
        throw DatabaseError("Journal write verification failed");
    transaction.commit();return next;
}

std::optional<CharacterRoleSnapshot> SqliteRecoveredCharacterRepository::load_role(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement query(db_,
        "SELECT r.character_id IS NOT NULL,r.logical,r.revision,r.design_id FROM recovered_characters c "
        "LEFT JOIN character_role_snapshots r ON r.character_id=c.id WHERE c.id=? AND c.account_id=?");
    query.bind_id(1,character);query.bind_id(2,account);
    if(!account || !character || !query.row()) throw DatabaseError("Invalid role owner");
    if(!query.integer(0)) return std::nullopt;
    CharacterRoleSnapshot result{};
    const auto bytes=query.blob(1,25,25);
    std::copy(bytes.begin(),bytes.end(),result.logical.begin());
    result.revision=query.number<std::uint64_t>(2);result.design_id=query.text(3);
    const auto parsed=RecoveredRoleLevel::parse(result.logical);
    if(!parsed || !parsed->level() || !parsed->max_hp() || !result.revision || result.design_id!="CUSTOM-0013")
        throw DatabaseError("Invalid diagnostic role snapshot");
    return result;
}

RoleResourceCommit SqliteRecoveredCharacterRepository::commit_role_resources(
    std::uint64_t account,std::uint64_t character,
    const std::optional<CharacterRoleSnapshot>& expected_role,const CharacterResources& expected_resources,
    CharacterRoleSnapshot next_role,CharacterResources next_resources) {
    sqlite_detail::Transaction transaction(db_);
    auto result=commit_role_resources_in_transaction(account,character,expected_role,expected_resources,
        std::move(next_role),std::move(next_resources));
    transaction.commit();
    return result;
}

RoleResourceCommit SqliteRecoveredCharacterRepository::commit_role_resources_in_transaction(
    std::uint64_t account,std::uint64_t character,
    const std::optional<CharacterRoleSnapshot>& expected_role,const CharacterResources& expected_resources,
    CharacterRoleSnapshot next_role,CharacterResources next_resources) {
    const auto parsed=RecoveredRoleLevel::parse(next_role.logical);
    if(!parsed || !parsed->level() || !parsed->max_hp() || next_role.design_id!="CUSTOM-0013" ||
       parsed->max_hp()!=next_resources.max_hp || parsed->max_mp()!=next_resources.max_mp)
        throw DatabaseError("Role snapshot/resource maxima mismatch");
    if(load_role(account,character)!=expected_role ||
       load_resources(account,character)!=std::optional<CharacterResources>{expected_resources})
        throw DatabaseError("Role/resource snapshot conflict");
    if(expected_role && expected_role->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
        throw DatabaseError("Role revision overflow");
    next_role.revision=expected_role ? expected_role->revision+1 : 1;
    {
        sqlite_detail::Statement write(db_,expected_role ?
            "UPDATE character_role_snapshots SET logical=?,revision=?,design_id=? WHERE character_id=? AND revision=?" :
            "INSERT INTO character_role_snapshots(logical,revision,design_id,character_id) VALUES(?,?,?,?)");
        write.bind_blob(1,next_role.logical);write.bind_id(2,next_role.revision);write.bind(3,next_role.design_id);write.bind_id(4,character);
        if(expected_role) write.bind_id(5,expected_role->revision);
        write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Role snapshot write rejected");
    }
    next_resources=commit_resources_in_transaction(account,character,expected_resources,std::move(next_resources));
    if(load_role(account,character)!=std::optional<CharacterRoleSnapshot>{next_role} ||
       load_resources(account,character)!=std::optional<CharacterResources>{next_resources})
        throw DatabaseError("Role/resource readback mismatch");
    return {std::move(next_role),std::move(next_resources)};
}

std::optional<CharacterExperience> SqliteRecoveredCharacterRepository::load_experience(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement query(db_,
        "SELECT c.id,e.character_id IS NOT NULL,e.total,e.design_id "
        "FROM recovered_characters c LEFT JOIN character_experience e ON e.character_id=c.id "
        "WHERE c.id=? AND c.account_id=?");
    query.bind_id(1,character);query.bind_id(2,account);
    if(!account || !character || !query.row()) throw DatabaseError("Invalid experience owner");
    if(query.integer(1)==0) return std::nullopt;
    CharacterExperience result{query.number<std::uint64_t>(2),query.text(3)};
    if(result.design_id!="CUSTOM-0012") throw DatabaseError("Invalid experience provenance");
    return result;
}

std::optional<CharacterResources> SqliteRecoveredCharacterRepository::load_resources(
    std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement owner(db_,"SELECT id FROM recovered_characters WHERE id=? AND account_id=?");
    owner.bind_id(1,character);owner.bind_id(2,account);
    if(!account || !character || !owner.row()) throw DatabaseError("Invalid resource owner");
    sqlite_detail::Statement query(db_,"SELECT hp,max_hp,mp,max_mp,revision,design_id FROM character_resources WHERE character_id=?");
    query.bind_id(1,character);
    if(!query.row()) return std::nullopt;
    CharacterResources value{query.number<std::uint64_t>(0),query.number<std::uint64_t>(1),
        query.number<std::uint32_t>(2),query.number<std::uint32_t>(3),query.number<std::uint64_t>(4),query.text(5)};
    if(!ExtendedHealthAmount::from(value.hp) || !ExtendedHealthAmount::from(value.max_hp) ||
       !value.max_hp || value.hp>value.max_hp || value.mp>value.max_mp || !value.revision ||
       value.design_id!="CUSTOM-0012") throw DatabaseError("Invalid resource row");
    return value;
}

bool SqliteRecoveredCharacterRepository::has_settled_diagnostic_battle(
    std::uint64_t account,std::uint64_t character) {
    if(!account || !character) return false;
    sqlite_detail::Statement query(db_,
        "SELECT s.battle_id FROM recovered_characters c "
        "JOIN battle_reservations r ON r.character_id=c.id "
        "JOIN battle_settlements s ON s.battle_id=r.id "
        "WHERE c.id=? AND c.account_id=? AND r.design_id='CUSTOM-0012' "
        "AND s.design_id='CUSTOM-0012' LIMIT 1");
    query.bind_id(1,character);query.bind_id(2,account);
    return query.row();
}

std::uint64_t SqliteRecoveredCharacterRepository::reserve_battle(
    std::uint64_t account,std::uint64_t character,const CharacterResources& expected) {
    sqlite_detail::Transaction transaction(db_);
    const auto current=load_resources(account,character);
    if(!current || *current!=expected || !current->hp)
        throw DatabaseError("Battle reservation resource conflict or dead character");
    {
        // Resource revisions advance during combat; they do not authorize a new encounter.
        sqlite_detail::Statement active(db_,
            "SELECT r.id,r.resource_revision,r.design_id FROM battle_reservations r "
            "LEFT JOIN battle_settlements s ON s.battle_id=r.id "
            "WHERE r.character_id=? AND s.battle_id IS NULL");
        active.bind_id(1,character);
        if(active.row()) {
            const auto id=active.number<std::uint64_t>(0);
            const auto revision=active.number<std::uint64_t>(1);
            const auto design=active.text(2);
            if(!id || design!="CUSTOM-0012" || active.row())
                throw DatabaseError("Inconsistent active battle reservations");
            if(revision!=current->revision)
                throw DatabaseError("Unsettled battle requires recovery before another reservation");
            transaction.commit();
            return id;
        }
    }
    {
        sqlite_detail::Statement insert(db_,
            "INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(?,?,'CUSTOM-0012') "
            "ON CONFLICT(character_id,resource_revision) DO NOTHING");
        insert.bind_id(1,character);insert.bind_id(2,current->revision);insert.done();
    }
    sqlite_detail::Statement query(db_,
        "SELECT id,design_id FROM battle_reservations WHERE character_id=? AND resource_revision=?");
    query.bind_id(1,character);query.bind_id(2,current->revision);
    if(!query.row() || query.text(1)!="CUSTOM-0012")
        throw DatabaseError("Battle reservation readback failed");
    const auto id=query.number<std::uint64_t>(0);
    if(!id || query.row()) throw DatabaseError("Invalid battle reservation identity");
    transaction.commit();
    return id;
}

std::optional<StoredBattleCheckpoint> SqliteRecoveredCharacterRepository::load_pending_checkpoint(
        std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);
    const auto resources=load_resources(account,character);
    std::uint64_t battle{};
    {
        sqlite_detail::Statement pending(db_,
            "SELECT r.id,r.design_id FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id "
            "WHERE r.character_id=? AND s.battle_id IS NULL");
        pending.bind_id(1,character);
        if(!pending.row()) {transaction.commit();return std::nullopt;}
        battle=pending.number<std::uint64_t>(0);
        if(!battle || pending.text(1)!="CUSTOM-0012" || pending.row())
            throw DatabaseError("Ambiguous pending battle reservation");
    }
    const auto saved=load_checkpoint(account,character,battle);
    if(!saved || !resources || resources->design_id!="CUSTOM-0012" ||
       saved->resource_revision!=resources->revision || saved->checkpoint.snapshot.state!=BattleState::Active)
        throw DatabaseError("Pending battle is missing a consistent active checkpoint");
    unsigned controlled=0;
    for(const auto& slot:saved->checkpoint.snapshot.actors) if(slot && slot->controller==character) {
        ++controlled;
        if(slot->hp!=resources->hp || slot->max_hp!=resources->max_hp || slot->mp!=resources->mp || slot->max_mp!=resources->max_mp)
            throw DatabaseError("Pending battle resources diverged");
    }
    if(controlled!=1) throw DatabaseError("Pending battle actor ownership mismatch");
    transaction.commit();return saved;
}

std::optional<StoredBattleCheckpoint> SqliteRecoveredCharacterRepository::load_checkpoint(
        std::uint64_t account,std::uint64_t character,std::uint64_t battle) {
    // Ownership is checked even when no checkpoint exists.
    (void)load_resources(account,character);
    sqlite_detail::Statement owner(db_,"SELECT character_id FROM battle_reservations WHERE id=?");
    owner.bind_id(1,battle);
    if(!owner.row() || owner.number<std::uint64_t>(0)!=character) throw DatabaseError("Checkpoint reservation ownership mismatch");
    sqlite_detail::Statement read(db_,"SELECT document,resource_revision,policy_id,COALESCE(revival_document,'') FROM battle_checkpoints WHERE battle_id=?");
    read.bind_id(1,battle);
    if(!read.row()) return std::nullopt;
    StoredBattleCheckpoint value{};
    try {value.checkpoint=BattleCheckpointCodec::decode(read.text(0));}
    catch(const std::exception&) {throw DatabaseError("Invalid stored checkpoint document");}
    value.resource_revision=read.number<std::uint64_t>(1);value.policy_id=read.text(2);
    if(value.checkpoint.snapshot.id!=battle || !value.resource_revision || value.policy_id!="CUSTOM-0012/diagnostic-v1" ||
       value.checkpoint.version!=1 || value.checkpoint.snapshot.numeric_profile!=BattleNumericProfile::LegacyCustom)
        throw DatabaseError("Invalid stored checkpoint identity");
    const auto phase=read.text(3);
    if(!phase.empty()) {
        try {value.revival=RevivalRecoveryCodec::decode(phase);}
        catch(const std::exception&) {throw DatabaseError("Invalid stored revival phase");}
        if(value.revival->account!=account || value.revival->character!=character || value.revival->battle!=value.checkpoint)
            throw DatabaseError("Stored revival phase identity mismatch");
    }
    return value;
}

StoredBattleCheckpoint SqliteRecoveredCharacterRepository::commit_checkpoint(
        std::uint64_t account,std::uint64_t character,const std::optional<StoredBattleCheckpoint>& expected,
        const CharacterResources& expected_resources,BattleCheckpoint next,CharacterResources resources,
        const std::string& policy_id,const std::optional<RevivalRecovery>& revival,
        const OwnedSkillCheckpointAuthority* owned_skill) {
    std::string document;
    std::string phase_document;
    if(revival) {
        if(revival->account!=account || revival->character!=character || revival->battle!=next)
            throw DatabaseError("Revival phase/checkpoint mismatch");
        try {phase_document=RevivalRecoveryCodec::encode(*revival);}
        catch(const std::exception&) {throw DatabaseError("Invalid revival phase");}
    }
    try {document=BattleCheckpointCodec::encode(next);}
    catch(const std::exception&) {throw DatabaseError("Invalid checkpoint state");}
    if(policy_id!="CUSTOM-0012/diagnostic-v1" || next.snapshot.state!=BattleState::Active ||
       next.version!=1 || next.snapshot.numeric_profile!=BattleNumericProfile::LegacyCustom)
        throw DatabaseError("Checkpoint requires isolated active battle policy");
    unsigned controlled=0;
    for(const auto& slot:next.snapshot.actors) if(slot && slot->controller==character) {
        ++controlled;
        if(slot->hp!=resources.hp || slot->max_hp!=resources.max_hp || slot->mp!=resources.mp || slot->max_mp!=resources.max_mp)
            throw DatabaseError("Checkpoint/resource values differ");
    }
    if(controlled!=1) throw DatabaseError("Checkpoint requires exactly one owned diagnostic actor");
    sqlite_detail::Transaction transaction(db_);
    require_owned_skill_current(account,character,owned_skill);
    const auto current=load_checkpoint(account,character,next.snapshot.id);
    if(current!=expected || load_resources(account,character)!=std::optional<CharacterResources>{expected_resources})
        throw DatabaseError("Checkpoint baseline conflict");
    sqlite_detail::Statement settled(db_,"SELECT 1 FROM battle_settlements WHERE battle_id=?");
    settled.bind_id(1,next.snapshot.id);
    if(settled.row()) throw DatabaseError("Settled battle cannot receive active checkpoint");
    if(current) {
        if(current->revival && !revival) throw DatabaseError("Checkpoint update would drop revival phase");
        if(current->resource_revision!=expected_resources.revision || current->policy_id!=policy_id ||
           next.version!=current->checkpoint.version ||
           next.snapshot.numeric_profile!=current->checkpoint.snapshot.numeric_profile ||
           next.snapshot.revision<=current->checkpoint.snapshot.revision)
            throw DatabaseError("Checkpoint revision or policy conflict");
    } else {
        sqlite_detail::Statement reservation(db_,"SELECT resource_revision FROM battle_reservations WHERE id=?");
        reservation.bind_id(1,next.snapshot.id);
        if(!reservation.row() || reservation.number<std::uint64_t>(0)!=expected_resources.revision || next.snapshot.revision!=1)
            throw DatabaseError("Initial checkpoint must match reserved baseline");
    }
    const auto saved=commit_resources_in_transaction(account,character,expected_resources,resources);
    {
        sqlite_detail::Statement write(db_,
            "INSERT INTO battle_checkpoints(battle_id,document,resource_revision,policy_id,revival_document) VALUES(?,?,?,?,NULLIF(?,'')) "
            "ON CONFLICT(battle_id) DO UPDATE SET document=excluded.document,resource_revision=excluded.resource_revision,policy_id=excluded.policy_id,revival_document=excluded.revival_document");
        write.bind_id(1,next.snapshot.id);write.bind(2,document);write.bind_id(3,saved.revision);write.bind(4,policy_id);
        write.bind(5,phase_document);write.done();
    }
    StoredBattleCheckpoint result{std::move(next),saved.revision,policy_id,revival};
    if(load_checkpoint(account,character,result.checkpoint.snapshot.id)!=std::optional<StoredBattleCheckpoint>{result} ||
       load_resources(account,character)!=std::optional<CharacterResources>{saved})
        throw DatabaseError("Checkpoint commit readback mismatch");
    require_owned_skill_current(account,character,owned_skill);
    transaction.commit();return result;
}

StoredBattleCheckpoint SqliteRecoveredCharacterRepository::commit_revival_phase(
        std::uint64_t account,std::uint64_t character,const StoredBattleCheckpoint& expected,
        const CharacterResources& resources,const RevivalRecovery& next) {
    if(!expected.revival || expected.checkpoint.snapshot.state!=BattleState::Active ||
       expected.resource_revision!=resources.revision)
        throw DatabaseError("Revival phase requires consistent active checkpoint");
    auto permitted=*expected.revival;
    if(permitted.action_received && !permitted.control_received) {
        permitted.control_received=true;
    } else if(permitted.action_received && permitted.control_received) {
        permitted.action_received=false;permitted.control_received=false;
    } else throw DatabaseError("Revival phase has no pending receipt or rearm");
    if(next!=permitted || next.account!=account || next.character!=character || next.battle!=expected.checkpoint)
        throw DatabaseError("Invalid revival phase transition");
    std::string document;
    try {document=RevivalRecoveryCodec::encode(next);}
    catch(const std::exception&) {throw DatabaseError("Invalid revival phase document");}
    sqlite_detail::Transaction transaction(db_);
    const auto battle=expected.checkpoint.snapshot.id;
    if(load_checkpoint(account,character,battle)!=std::optional<StoredBattleCheckpoint>{expected} ||
       load_resources(account,character)!=std::optional<CharacterResources>{resources})
        throw DatabaseError("Revival phase baseline conflict");
    sqlite_detail::Statement settled(db_,"SELECT 1 FROM battle_settlements WHERE battle_id=?");
    settled.bind_id(1,battle);
    if(settled.row()) throw DatabaseError("Settled battle cannot update revival phase");
    sqlite_detail::Statement write(db_,"UPDATE battle_checkpoints SET revival_document=? WHERE battle_id=? AND resource_revision=?");
    write.bind(1,document);write.bind_id(2,battle);write.bind_id(3,resources.revision);write.done();
    auto result=expected;result.revival=next;
    if(sqlite3_changes(db_)!=1 || load_checkpoint(account,character,battle)!=std::optional<StoredBattleCheckpoint>{result} ||
       load_resources(account,character)!=std::optional<CharacterResources>{resources})
        throw DatabaseError("Revival phase readback mismatch");
    transaction.commit();return result;
}

// CUSTOM-0139: only the actual private saved readset and same connection qualify.
void SqliteRecoveredCharacterRepository::require_owned_skill_current(std::uint64_t account,
        std::uint64_t character,const OwnedSkillCheckpointAuthority* authority) {
    if(!authority)return;
    const auto& saved=authority->readset;
    const bool supported=(saved.kind()==ShunyingSanshazhan::kind && saved.definition_id()==ShunyingSanshazhan::id) ||
        (saved.kind()==ThousandBulls::kind && saved.definition_id()==ThousandBulls::id);
    if(!supported || saved.account()!=account || saved.character()!=character ||
       !authority->repository.uses_connection(db_) ||
       !authority->repository.selected_deity_skill_current_in_transaction(saved))
        throw DatabaseError("Owned skill saved authority changed");
}
CharacterResources SqliteRecoveredCharacterRepository::commit_owned_skill_resources(
        std::uint64_t account,std::uint64_t character,const CharacterResources& expected,
        CharacterResources next,const OwnedSkillCheckpointAuthority& authority) {
    sqlite_detail::Transaction transaction(db_);
    require_owned_skill_current(account,character,&authority);
    next=commit_resources_in_transaction(account,character,expected,std::move(next));
    require_owned_skill_current(account,character,&authority);
    transaction.commit();return next;
}
BattleSettlement SqliteRecoveredCharacterRepository::settle_owned_skill_battle(
        std::uint64_t account,std::uint64_t character,std::uint64_t battle,
        const CharacterResources& expected,CharacterResources next,bool won,std::uint64_t experience,
        const std::optional<BattleProgressionCommit>& progression,const OwnedSkillCheckpointAuthority& authority) {
    return settle_battle_impl(account,character,battle,expected,std::move(next),won,experience,progression,nullptr,nullptr,&authority);
}
CharacterResources SqliteRecoveredCharacterRepository::commit_resources(
    std::uint64_t account,std::uint64_t character,
    const std::optional<CharacterResources>& expected,CharacterResources next) {
    sqlite_detail::Transaction transaction(db_);
    next=commit_resources_in_transaction(account,character,expected,std::move(next));
    transaction.commit();
    return next;
}

std::optional<StoredInventorySlot> SqliteRecoveredCharacterRepository::load_inventory_slot(
    std::uint64_t account,std::uint64_t character,std::uint8_t slot) {
    if(slot>=50) throw DatabaseError("Inventory slot outside qualified projection");
    (void)load_resources(account,character); // Owner check also applies to an absent slot.
    sqlite_detail::Statement query(db_,"SELECT item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");
    query.bind_id(1,character);query.bind(2,slot);
    if(!query.row()) return std::nullopt;
    return read_inventory_row(query,0);
}
bool SqliteRecoveredCharacterRepository::owned_pending_battle(std::uint64_t account,std::uint64_t character) {
    (void)load_resources(account,character); // Checks ownership even if absent.
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);return pending.row();
}

std::vector<std::pair<std::uint8_t,StoredInventorySlot>>
SqliteRecoveredCharacterRepository::load_saved_supply_slots(
        std::uint64_t account,std::uint64_t character) {
    (void)load_resources(account,character); // Check ownership even if no rows exist.
    sqlite_detail::Statement query(db_,
        "SELECT slot,item_id,count,revision,source_sha256,design_id "
        "FROM diagnostic_inventory_slots WHERE character_id=? AND slot<30 ORDER BY slot");
    query.bind_id(1,character);
    std::vector<std::pair<std::uint8_t,StoredInventorySlot>> result;
    result.reserve(30);
    while(query.row()) {
        const auto index=query.number<std::uint8_t>(0);
        if(index>=30 || (!result.empty() && index<=result.back().first))
            throw DatabaseError("Invalid saved supply slot order");
        result.emplace_back(index,read_inventory_row(query,1));
    }
    return result;
}

InventoryResourceCommit SqliteRecoveredCharacterRepository::commit_inventory_resources(
    std::uint64_t account,std::uint64_t character,std::uint8_t slot,
    const std::optional<StoredInventorySlot>& expected_slot,const CharacterResources& expected_resources,
    StoredInventorySlot next_slot,CharacterResources next_resources) {
    sqlite_detail::Transaction transaction(db_);
    const auto current=load_inventory_slot(account,character,slot);
    if(current!=expected_slot || load_resources(account,character)!=std::optional<CharacterResources>{expected_resources})
        throw DatabaseError("Inventory/resource version conflict");
    // Outside-battle transactions must not invalidate a pending combat checkpoint.
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);
    if(pending.row()) throw DatabaseError("Inventory resource change during pending battle");
    if(next_slot.count>127 || (next_slot.count==0)!=(next_slot.item_id==0) ||
       next_slot.source_sha256.size()!=64 || next_slot.source_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos ||
       (current && current->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())))
        throw DatabaseError("Invalid inventory update");
    next_slot.revision=current ? current->revision+1 : 1;
    next_resources=commit_resources_in_transaction(account,character,expected_resources,std::move(next_resources));
    sqlite_detail::Statement write(db_,current ?
        "UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND revision=?" :
        "INSERT INTO diagnostic_inventory_slots(item_id,count,revision,source_sha256,character_id,slot,design_id) VALUES(?,?,?,?,?,?,'CUSTOM-0015')");
    write.bind(1,next_slot.item_id);write.bind(2,next_slot.count);write.bind_id(3,next_slot.revision);
    write.bind(4,next_slot.source_sha256);write.bind_id(5,character);write.bind(6,slot);
    if(current) write.bind_id(7,current->revision);
    write.done();
    if(sqlite3_changes(db_)!=1 || load_inventory_slot(account,character,slot)!=std::optional<StoredInventorySlot>{next_slot} ||
       load_resources(account,character)!=std::optional<CharacterResources>{next_resources})
        throw DatabaseError("Inventory/resource readback mismatch");
    transaction.commit();
    return {std::move(next_slot),std::move(next_resources)};
}

CharacterResources SqliteRecoveredCharacterRepository::commit_resources_in_transaction(
    std::uint64_t account,std::uint64_t character,
    const std::optional<CharacterResources>& expected,CharacterResources next) {
    const auto hp=ExtendedHealthAmount::from(next.hp),max_hp=ExtendedHealthAmount::from(next.max_hp);
    if(!hp || !max_hp || !next.max_hp || next.hp>next.max_hp || next.mp>next.max_mp || next.design_id!="CUSTOM-0012")
        throw DatabaseError("Invalid resource values or provenance");
    if(const auto role=load_role(account,character)) {
        const auto parsed=RecoveredRoleLevel::parse(role->logical);
        if(parsed->max_hp()!=next.max_hp || parsed->max_mp()!=next.max_mp)
            throw DatabaseError("Resource write would diverge from stored role maxima");
    }
    const auto current=load_resources(account,character);
    if(current!=expected) throw DatabaseError("Resource version conflict");
    if(current && current->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
        throw DatabaseError("Resource revision overflow");
    next.revision=current ? current->revision+1 : 1;
    {
        sqlite_detail::Statement write(db_,current ?
            "UPDATE character_resources SET hp=?,max_hp=?,mp=?,max_mp=?,revision=?,design_id=? WHERE character_id=? AND revision=?" :
            "INSERT INTO character_resources(hp,max_hp,mp,max_mp,revision,design_id,character_id) VALUES(?,?,?,?,?,?,?)");
        write.bind(1,hp->sqlite_integer());write.bind(2,max_hp->sqlite_integer());write.bind(3,next.mp);write.bind(4,next.max_mp);
        write.bind_id(5,next.revision);write.bind(6,next.design_id);write.bind_id(7,character);
        if(current) write.bind_id(8,current->revision);
        write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Resource write rejected");
    }
    if(load_resources(account,character)!=std::optional<CharacterResources>{next})
        throw DatabaseError("Resource readback mismatch");
    return next;
}

BattleSettlement SqliteRecoveredCharacterRepository::settle_battle(
    std::uint64_t account,std::uint64_t character,std::uint64_t battle,
    const CharacterResources& expected,CharacterResources next,bool won,std::uint64_t experience,
    const std::optional<BattleProgressionCommit>& progression) {
    return settle_battle_impl(account,character,battle,expected,std::move(next),won,experience,progression);
}
BattleSettlement SqliteRecoveredCharacterRepository::settle_checkpoint(
    std::uint64_t account,std::uint64_t character,const StoredBattleCheckpoint& checkpoint,
    const CharacterResources& expected,const BattleCheckpoint& terminal,CharacterResources next,bool won,std::uint64_t experience,
    const std::optional<BattleProgressionCommit>& progression,const OwnedSkillCheckpointAuthority* owned_skill) {
    return settle_battle_impl(account,character,terminal.snapshot.id,expected,std::move(next),won,experience,progression,&checkpoint,&terminal,owned_skill);
}
BattleSettlement SqliteRecoveredCharacterRepository::settle_battle_impl(
    std::uint64_t account,std::uint64_t character,std::uint64_t battle,
    const CharacterResources& expected,CharacterResources next,bool won,std::uint64_t experience,
    const std::optional<BattleProgressionCommit>& progression,const StoredBattleCheckpoint* checkpoint,const BattleCheckpoint* terminal,
    const OwnedSkillCheckpointAuthority* owned_skill) {
    // Validate wide award and complete HP values BEFORE canonical replay.
    // It is still an actual server-authorized CUSTOM diagnostic outcome.
    if(!ExtendedExperienceAmount::from(experience) || !expected.valid_health() || !next.valid_health() ||
       expected.mp>expected.max_mp || next.mp>next.max_mp ||
       !battle || !expected.revision || expected.design_id!="CUSTOM-0012" ||
       next.design_id!="CUSTOM-0012" || (!won && experience))
        throw DatabaseError("Invalid diagnostic settlement");
    // Canonical structured request binds a retry to the complete original outcome.
    const auto resources_json=[](const CharacterResources& r) {
        return nlohmann::json::array({r.hp,r.max_hp,r.mp,r.max_mp,r.revision,r.design_id});
    };
    next.revision=0; // Assigned by the transaction, never trusted from the caller.
    auto request_data=nlohmann::json{{"version",1},{"account",account},{"character",character},
        {"battle",battle},{"before",resources_json(expected)},{"after",resources_json(next)},
        {"won",won},{"experience",experience},{"design_id","CUSTOM-0012"}};
    std::optional<CharacterRoleSnapshot> resulting_role;
    if(progression) {
        const auto role_json=[](const CharacterRoleSnapshot& r) {
            return nlohmann::json{{"logical",r.logical},{"revision",r.revision},{"design_id",r.design_id}};
        };
        auto proposed=progression->next_role;proposed.revision=0;
        request_data["version"]=2;
        request_data["progression"]={
            {"expected_xp",progression->expected_experience ? nlohmann::json{
                {"total",progression->expected_experience->total},{"design_id",progression->expected_experience->design_id}} : nlohmann::json(nullptr)},
            {"expected_role",progression->expected_role ? role_json(*progression->expected_role) : nlohmann::json(nullptr)},
            {"next_role",role_json(proposed)}};
        if(progression->expected_role && progression->expected_role->revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
            throw DatabaseError("Settlement role revision overflow");
        proposed.revision=progression->expected_role ? progression->expected_role->revision+1 : 1;
        resulting_role=std::move(proposed);
    }
    std::string terminal_document;
    if(checkpoint && terminal) {
        std::string before_document;
        try {
            before_document=BattleCheckpointCodec::encode(checkpoint->checkpoint);
            terminal_document=BattleCheckpointCodec::encode(*terminal);
        } catch(const std::exception&) {throw DatabaseError("Invalid terminal checkpoint");}
        if(checkpoint->policy_id!="CUSTOM-0012/diagnostic-v1" || checkpoint->resource_revision!=expected.revision ||
           checkpoint->checkpoint.version!=1 ||
           checkpoint->checkpoint.snapshot.numeric_profile!=BattleNumericProfile::LegacyCustom ||
           terminal->version!=checkpoint->checkpoint.version ||
           terminal->snapshot.numeric_profile!=checkpoint->checkpoint.snapshot.numeric_profile ||
           checkpoint->checkpoint.snapshot.id!=battle || checkpoint->checkpoint.snapshot.state!=BattleState::Active ||
           terminal->snapshot.state!=BattleState::Finished || terminal->snapshot.revision<=checkpoint->checkpoint.snapshot.revision)
            throw DatabaseError("Terminal checkpoint baseline mismatch");
        unsigned controlled=0;
        for(const auto& slot:terminal->snapshot.actors) if(slot && slot->controller==character) {
            ++controlled;
            if(slot->hp!=next.hp || slot->max_hp!=next.max_hp || slot->mp!=next.mp || slot->max_mp!=next.max_mp ||
               won!=(terminal->snapshot.victorious_side==slot->position/14))
                throw DatabaseError("Terminal checkpoint outcome/resource mismatch");
        }
        if(controlled!=1) throw DatabaseError("Terminal checkpoint requires one owned actor");
        request_data["version"]=3;
        request_data["checkpoint"]={{"before",before_document},{"after",terminal_document},
            {"resource_revision",checkpoint->resource_revision},{"policy_id",checkpoint->policy_id}};
    }
    // CUSTOM-0139: a durable retry retains the exact selected saved authority.
    // Old ordinary requests keep their original structured version and bytes.
    if(owned_skill) {
        const auto& saved=owned_skill->readset;
        std::vector<std::array<std::uint8_t,4>> skills;
        for(const auto& skill:saved.deity().snapshot.skills)skills.push_back(skill.encode());
        request_data["version"]=4;
        request_data["owned_skill_readset"]={
            {"design_id","CUSTOM-0139"},{"account",saved.account()},{"character",saved.character()},
            {"selection_key",saved.selection().key},{"selection_revision",saved.selection().revision},
            {"deity_revision",saved.deity().revision},{"declaration",saved.deity().snapshot.declaration.encode()},
            {"status",saved.deity().snapshot.status.encode()},{"skills",skills},{"selected_skill",saved.skill().encode()},
            {"source_sha256",saved.deity().provenance.source_sha256},
            {"authority",saved.deity().provenance.authority},{"evidence_id",saved.deity().provenance.evidence_id}};
    }
    const auto request=request_data.dump();
    sqlite_detail::Transaction transaction(db_);
    require_owned_skill_current(account,character,owned_skill);
    const auto current=load_resources(account,character); // Ownership applies to retries too.
    {
        sqlite_detail::Statement reservation(db_,
            "SELECT character_id,resource_revision,design_id FROM battle_reservations WHERE id=?");
        reservation.bind_id(1,battle);
        if(!reservation.row() || reservation.number<std::uint64_t>(0)!=character ||
           reservation.number<std::uint64_t>(1)>expected.revision || reservation.text(2)!="CUSTOM-0012")
            throw DatabaseError("Invalid settlement reservation");
    }
    {
        sqlite_detail::Statement replay(db_,
            "SELECT request,resource_revision,total_experience,design_id FROM battle_settlements WHERE battle_id=?");
        replay.bind_id(1,battle);
        if(replay.row()) {
            if(replay.text(0)!=request || replay.text(3)!="CUSTOM-0012")
                throw DatabaseError("Settlement retry differs");
            next.revision=replay.number<std::uint64_t>(1);
            BattleSettlement result{next,replay.number<std::uint64_t>(2),resulting_role};
            if(expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
               next.revision!=expected.revision+1)
                throw DatabaseError("Invalid settlement readback");
            require_owned_skill_current(account,character,owned_skill);
            transaction.commit();
            return result; // Do not restore old resources or XP over a later battle.
        }
    }
    if(current!=std::optional<CharacterResources>{expected})
        throw DatabaseError("Settlement resource conflict");
    const auto stored_checkpoint=load_checkpoint(account,character,battle);
    if(checkpoint ? stored_checkpoint!=std::optional<StoredBattleCheckpoint>{*checkpoint} : stored_checkpoint.has_value())
        throw DatabaseError("Settlement must include current checkpoint");
    const auto previous_experience=load_experience(account,character);
    if(progression && previous_experience!=progression->expected_experience)
        throw DatabaseError("Progression XP baseline conflict");
    const auto total_amount=ExtendedExperienceAmount::accumulate(previous_experience ? previous_experience->total : 0,experience);
    if(!total_amount)
        throw DatabaseError("Experience overflow");
    const auto total=total_amount->value();
    if(progression) {
        const auto committed=commit_role_resources_in_transaction(account,character,progression->expected_role,expected,
            progression->next_role,std::move(next));
        next=committed.resources;resulting_role=committed.role;
    } else next=commit_resources_in_transaction(account,character,expected,std::move(next));
    if(checkpoint) {
        sqlite_detail::Statement write(db_,"UPDATE battle_checkpoints SET document=?,resource_revision=?,revival_document=NULL WHERE battle_id=?");
        write.bind(1,terminal_document);write.bind_id(2,next.revision);write.bind_id(3,battle);write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Terminal checkpoint write rejected");
    }
    {
        sqlite_detail::Statement write(db_,
            "INSERT INTO character_experience(character_id,total,design_id) VALUES(?,?,'CUSTOM-0012') "
            "ON CONFLICT(character_id) DO UPDATE SET total=excluded.total");
        write.bind_id(1,character);write.bind(2,total_amount->sqlite_integer());write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Experience write rejected");
    }
    {
        sqlite_detail::Statement write(db_,
            "INSERT INTO battle_settlements(battle_id,request,resource_revision,total_experience,design_id) "
            "VALUES(?,?,?,?,'CUSTOM-0012')");
        write.bind_id(1,battle);write.bind(2,request);write.bind_id(3,next.revision);write.bind(4,total_amount->sqlite_integer());write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Settlement write rejected");
    }
    {
        sqlite_detail::Statement verify(db_,
            "SELECT s.request,s.resource_revision,s.total_experience,s.design_id,e.total,e.design_id "
            "FROM battle_settlements s JOIN character_experience e ON e.character_id=? WHERE s.battle_id=?");
        verify.bind_id(1,character);verify.bind_id(2,battle);
        if(!verify.row() || verify.text(0)!=request || verify.number<std::uint64_t>(1)!=next.revision ||
           verify.number<std::uint64_t>(2)!=total || verify.text(3)!="CUSTOM-0012" ||
           verify.number<std::uint64_t>(4)!=total || verify.text(5)!="CUSTOM-0012" ||
           load_resources(account,character)!=std::optional<CharacterResources>{next})
            throw DatabaseError("Settlement readback mismatch");
        if(progression && load_role(account,character)!=resulting_role)
            throw DatabaseError("Settlement role readback mismatch");
        if(checkpoint && load_checkpoint(account,character,battle)!=
           std::optional<StoredBattleCheckpoint>{{*terminal,next.revision,checkpoint->policy_id}})
            throw DatabaseError("Terminal checkpoint readback mismatch");
    }
    require_owned_skill_current(account,character,owned_skill);
    transaction.commit();
    return {next,total,resulting_role};
}

RecoveredCharacter SqliteRecoveredCharacterRepository::create(
    std::uint64_t account_id, const std::array<std::uint8_t, 40>& profile) {
    try {
        const auto length = name_size(profile);
        sqlite_detail::Transaction transaction(db_);
        const auto existing = list_for_account(account_id);
        std::array<bool, 2> occupied{};
        for (const auto& character : existing) occupied[character.slot] = true;
        // Two slots match the current wire capacity; allocation is local policy.
        const auto free = std::find(occupied.begin(), occupied.end(), false);
        if (free == occupied.end()) throw DatabaseError("Recovered character account is full");
        const auto slot = static_cast<std::uint8_t>(free - occupied.begin());
        {
            sqlite_detail::Statement insert(db_,
                "INSERT INTO recovered_characters(account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,?,?,0)");
            insert.bind_id(1, account_id);
            insert.bind(2, slot);
            insert.bind_blob(3, profile);
            insert.bind_blob(4, std::span<const std::uint8_t>(profile.data(), length));
            insert.done();
        }
        RecoveredCharacter created;
        {
            sqlite_detail::Statement select(db_,
                "SELECT id,account_id,slot,profile,name_bytes,created_at,name_codepage,streamer_privilege FROM recovered_characters WHERE id=?");
            select.bind(1, sqlite3_last_insert_rowid(db_));
            if (!select.row()) throw DatabaseError("Inserted recovered character missing");
            created = read_character(select);
            if (created.account_id != account_id || created.slot != slot || created.profile != profile)
                throw DatabaseError("Inserted recovered character differs");
        }
        transaction.commit();
        return created;
    } catch (const DatabaseError&) {
        throw DatabaseError("Unable to create recovered character");
    }
}

std::vector<RecoveredCharacter> SqliteRecoveredCharacterRepository::list_for_account(std::uint64_t account_id) {
    try {
        require_account(db_, account_id);
        sqlite_detail::Statement select(db_,
            "SELECT id,account_id,slot,profile,name_bytes,created_at,name_codepage,streamer_privilege FROM recovered_characters "
            "WHERE account_id=? ORDER BY slot LIMIT 3");
        select.bind_id(1, account_id);
        std::vector<RecoveredCharacter> result;
        result.reserve(2);
        std::array<bool, 2> occupied{};
        while (select.row()) {
            auto character = read_character(select);
            if (character.account_id != account_id || occupied[character.slot] || result.size() == 2)
                throw DatabaseError("Invalid recovered character slots");
            occupied[character.slot] = true;
            result.push_back(std::move(character));
        }
        return result;
    } catch (const DatabaseError&) {
        throw DatabaseError("Unable to list recovered characters");
    }
}

std::optional<RecoveredPosition> SqliteRecoveredCharacterRepository::load_position(
    std::uint64_t account_id, std::uint64_t character_id) {
    try {
        if (account_id == 0 || character_id == 0) throw DatabaseError("Invalid position owner");
        // One snapshot distinguishes an owned character without a position from an unknown owner.
        sqlite_detail::Statement select(db_,
            "SELECT c.id,c.account_id,p.character_id IS NOT NULL,p.area,p.scene,p.x,p.y,p.revision "
            "FROM recovered_characters c JOIN accounts a ON a.id=c.account_id "
            "LEFT JOIN recovered_positions p ON p.character_id=c.id WHERE c.id=? AND c.account_id=?");
        select.bind_id(1, character_id);
        select.bind_id(2, account_id);
        if (!select.row() || select.number<std::uint64_t>(0) != character_id ||
            select.number<std::uint64_t>(1) != account_id)
            throw DatabaseError("Invalid position owner");
        std::optional<RecoveredPosition> result;
        if (select.integer(2) != 0) {
            result = RecoveredPosition{select.number<std::uint16_t>(3), select.number<std::uint16_t>(4),
                                       select.number<std::uint16_t>(5), select.number<std::uint16_t>(6),
                                       select.number<std::uint64_t>(7)};
            if (result->area > 63 || result->scene > 1023 || result->revision == 0)
                throw DatabaseError("Invalid recovered position row");
        }
        if (select.row()) throw DatabaseError("Duplicate recovered position row");
        return result;
    } catch (const DatabaseError&) {
        throw DatabaseError("Unable to load recovered position");
    }
}

RecoveredPosition SqliteRecoveredCharacterRepository::commit_position(
    std::uint64_t account_id, std::uint64_t character_id, const std::optional<RecoveredPosition>& expected,
    std::uint16_t area, std::uint16_t scene, std::uint16_t x, std::uint16_t y) {
    try {
        if (area > 63 || scene > 1023) throw DatabaseError("Invalid recovered position bounds");
        sqlite_detail::Transaction transaction(db_);
        const auto current = load_position(account_id, character_id);
        if (current != expected) throw DatabaseError("Recovered position conflict");
        if (current && current->revision >= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
            throw DatabaseError("Recovered position revision overflow");
        const RecoveredPosition next{area, scene, x, y, current ? current->revision + 1 : 1};
        {
            sqlite_detail::Statement write(db_, current ?
                "UPDATE recovered_positions SET area=?,scene=?,x=?,y=?,revision=? "
                "WHERE character_id=? AND revision=? AND area=? AND scene=? AND x=? AND y=?" :
                "INSERT INTO recovered_positions(area,scene,x,y,revision,character_id) VALUES(?,?,?,?,?,?)");
            write.bind(1, next.area);
            write.bind(2, next.scene);
            write.bind(3, next.x);
            write.bind(4, next.y);
            write.bind_id(5, next.revision);
            write.bind_id(6, character_id);
            if (current) {
                write.bind_id(7, current->revision);
                write.bind(8, current->area);
                write.bind(9, current->scene);
                write.bind(10, current->x);
                write.bind(11, current->y);
            }
            write.done();
            if (sqlite3_changes(db_) != 1) throw DatabaseError("Recovered position was not written");
        }
        if (load_position(account_id, character_id) != std::optional<RecoveredPosition>{next})
            throw DatabaseError("Written recovered position differs");
        transaction.commit();
        return next;
    } catch (const DatabaseError&) {
        throw DatabaseError("Unable to commit recovered position");
    }
}
}

namespace god2 {
void SqliteRecoveredCharacterRepository::bind_name_encoding(
    std::uint64_t account,std::uint64_t character,bool simplified) {
    require_account(db_,account);
    sqlite_detail::Statement update(db_,
        "UPDATE recovered_characters SET name_codepage=? WHERE id=? AND account_id=? AND name_codepage=0");
    update.bind(1,simplified?936:950);update.bind_id(2,character);update.bind_id(3,account);update.done();
}
}
