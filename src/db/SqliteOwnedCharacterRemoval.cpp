#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <string>
#include <vector>
#include <set>
#include <utility>

namespace god2 {
bool SqliteRecoveredCharacterRepository::erase_owned_snapshot(
    const RecoveredCharacter expected,CurrentRemoval current) {
    return erase_owned_snapshot_impl(expected,std::move(current),nullptr,{},{});
}
bool SqliteRecoveredCharacterRepository::erase_owned_snapshot_with_native_summaries(
    RecoveredCharacter expected,SqliteNativeCharacterSummarySnapshotRepository& summaries,
    std::vector<NativeCharacterSummarySnapshot> complete_expected,CurrentNativeSummaryRemoval current) {
    return erase_owned_snapshot_impl(expected,{},&summaries,std::move(complete_expected),std::move(current));
}
bool SqliteRecoveredCharacterRepository::erase_owned_snapshot_impl(
    const RecoveredCharacter expected,CurrentRemoval current,SqliteNativeCharacterSummarySnapshotRepository* summaries,
    std::vector<NativeCharacterSummarySnapshot> complete_expected,CurrentNativeSummaryRemoval summary_current) {
    if(!expected.id || !expected.account_id || expected.slot>1 || expected.created_at.empty() ||
       (summaries?(!summary_current || bool(current)):(!current || bool(summary_current))) ||
       (expected.name_codepage!=0 && expected.name_codepage!=936 && expected.name_codepage!=950) ||
       expected.streamer_privilege>3)return false;
    // This is the existing common root's actual storage format, not a CN19
    // producer limit or conversion. The expected row comes from shared storage.
    const auto end=std::find(expected.profile.begin(),expected.profile.begin()+15,0);
    if(end==expected.profile.begin() || end==expected.profile.begin()+15)return false;
    const auto stored_name=std::span<const std::uint8_t>{expected.profile.begin(),end};
    struct SummaryLease {
        bool* writing=nullptr;
        ~SummaryLease(){if(writing)*writing=false;}
    } lease;
    if(summaries) {
        summaries->owner();
        if(summaries->writing_ || &summaries->characters_!=this || summaries->db_!=db_ ||
           !summaries->owns_sources(summaries->accounts_,*this) || !sqlite3_get_autocommit(db_))
            throw DatabaseError("Summary removal requires same backend, owner and own transaction");
        summaries->writing_=true;lease.writing=&summaries->writing_;
    }
    {
        sqlite_detail::Statement foreign_keys(db_,"PRAGMA foreign_keys");
        if(!foreign_keys.row() || foreign_keys.integer(0)!=1)
            throw DatabaseError("Owned character removal requires foreign key enforcement");
    }
    sqlite_detail::Transaction transaction(db_);
    std::vector<RecoveredCharacter> complete_roots;
    if(summaries) {
        complete_roots=list_for_account(expected.account_id);std::set<std::uint64_t> ids;
        for(const auto& row:complete_roots)
            if(!row.id || row.account_id!=expected.account_id || !ids.insert(row.id).second)
                throw DatabaseError("Summary removal invalid common roots");
    }
    const auto roots_current=[&](bool removed) {
        if(!summaries)return true;
        const auto actual=list_for_account(expected.account_id);
        if(actual.size()+static_cast<std::size_t>(removed)!=complete_roots.size())return false;
        std::set<std::uint64_t> seen;
        for(const auto& row:actual) {
            const auto old=std::find_if(complete_roots.begin(),complete_roots.end(),[&](const auto& value){return value.id==row.id;});
            if(old==complete_roots.end() || (removed && row.id==expected.id) || !seen.insert(row.id).second ||
               row.account_id!=old->account_id || row.slot!=old->slot || row.profile!=old->profile ||
               row.created_at!=old->created_at || row.name_codepage!=old->name_codepage ||
               row.streamer_privilege!=old->streamer_privilege)return false;
        }
        return true;
    };
    const auto coherent=[&](bool removed) {
        if(!summaries)return;
        if(!roots_current(removed))throw DatabaseError("Summary removal common roots conflict");
        if(removed)summaries->check_removal_inventory(expected.account_id,expected.id,{});
        else summaries->check_removal_inventory(expected.account_id,expected.id,complete_expected);
        if(!roots_current(removed))throw DatabaseError("Summary removal common roots changed");
    };
    {
        sqlite_detail::Statement row(db_,"SELECT slot,profile,name_bytes,created_at,name_codepage,streamer_privilege "
            "FROM recovered_characters WHERE id=? AND account_id=?");
        row.bind_id(1,expected.id);row.bind_id(2,expected.account_id);
        if(!row.row())return false;
        const auto profile=row.blob(1,40,40),name=row.blob(2,1,14);
        if(row.number<std::uint8_t>(0)!=expected.slot ||
           !std::equal(profile.begin(),profile.end(),expected.profile.begin()) ||
           name.size()!=stored_name.size() || !std::equal(name.begin(),name.end(),stored_name.begin()) ||
           row.text(3)!=expected.created_at || row.number<std::uint16_t>(4)!=expected.name_codepage ||
           row.number<std::uint8_t>(5)!=expected.streamer_privilege)return false;
    }
    coherent(false);
    if(!(summaries?summary_current(RemovalPhase::BeforeErase,complete_expected,complete_roots):current(RemovalPhase::BeforeErase)))return false;
    coherent(false);
    if(summaries) {
        summaries->invalidate_for_removal(expected.account_id,expected.id,complete_expected);
        if(!roots_current(false))throw DatabaseError("Summary invalidation changed common roots");
        summaries->check_removal_inventory(expected.account_id,expected.id,{});
    }
    // Preserve the existing root FK-graph cleanup semantics in an additive
    // writer. Existing erase_owned and TW Application handlers are untouched.
    sqlite_detail::execute(db_,"PRAGMA defer_foreign_keys=ON");
    for(const auto* table:{"battle_settlements","battle_checkpoints"}) {
        const auto sql=std::string("DELETE FROM ")+table+
            " WHERE battle_id IN (SELECT id FROM battle_reservations WHERE character_id=?)";
        sqlite_detail::Statement remove(db_,sql.c_str());remove.bind_id(1,expected.id);remove.done();
    }
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
            const auto sql="PRAGMA foreign_key_list("+quote(table)+")";
            sqlite_detail::Statement references(db_,sql.c_str());
            while(references.row())
                if(std::find(descendants.begin(),descendants.end(),references.text(2))!=descendants.end()) {
                    descendants.push_back(table);extended=true;break;
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
        sqlite_detail::Statement remove(db_,sql.c_str());remove.bind_id(1,expected.id);remove.done();
    }
    sqlite_detail::Statement remove(db_,"DELETE FROM recovered_characters WHERE id=? AND account_id=? AND slot=? "
        "AND profile=? AND name_bytes=? AND created_at=? AND name_codepage=? AND streamer_privilege=?");
    remove.bind_id(1,expected.id);remove.bind_id(2,expected.account_id);remove.bind(3,expected.slot);
    remove.bind_blob(4,expected.profile);remove.bind_blob(5,stored_name);remove.bind(6,expected.created_at);
    remove.bind(7,expected.name_codepage);remove.bind(8,expected.streamer_privilege);remove.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Character removal snapshot conflict");
    coherent(true);
    if(!(summaries?summary_current(RemovalPhase::BeforeCommit,complete_expected,complete_roots):current(RemovalPhase::BeforeCommit)))return false;
    coherent(true);
    transaction.commit();return true;
}
}
