#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <set>

namespace god2 {
namespace {
bool same_creation_row(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
}
std::optional<RecoveredCharacter> SqliteRecoveredCharacterRepository::create_owned_snapshot(
    std::uint64_t account,std::span<const RecoveredCharacter> expected,
    NewOwnedCharacter proposed,CurrentCreation current) {
    if(!account || !current || expected.size()>=2 || proposed.slot>1 ||
       (proposed.name_codepage!=0 && proposed.name_codepage!=936 && proposed.name_codepage!=950) ||
       proposed.streamer_privilege>3)return std::nullopt;
    const auto end=std::find(proposed.profile.begin(),proposed.profile.begin()+15,0);
    if(end==proposed.profile.begin() || end==proposed.profile.begin()+15)return std::nullopt;
    std::set<std::uint64_t> ids;
    std::set<std::uint8_t> slots;
    for(const auto& row:expected)
        if(!row.id || row.account_id!=account || row.slot>1 || row.slot==proposed.slot ||
           !ids.insert(row.id).second || !slots.insert(row.slot).second)return std::nullopt;
    {
        sqlite_detail::Statement foreign_keys(db_,"PRAGMA foreign_keys");
        if(!foreign_keys.row() || foreign_keys.integer(0)!=1)
            throw DatabaseError("Owned character creation requires foreign keys");
    }
    sqlite_detail::Transaction transaction(db_);
    const auto existing=list_for_account(account); // Actual account existence and stored raw-name checks.
    if(existing.size()!=expected.size())return std::nullopt;
    for(const auto& row:existing) {
        const auto found=std::find_if(expected.begin(),expected.end(),[&](const auto& e){return e.id==row.id;});
        if(found==expected.end() || !same_creation_row(row,*found))return std::nullopt;
    }
    if(!current(CreationPhase::BeforeInsert))return std::nullopt;
    {
        sqlite_detail::Statement insert(db_,"INSERT INTO recovered_characters "
            "(account_id,slot,profile,name_bytes,name_codepage,streamer_privilege) VALUES(?,?,?,?,?,?)");
        insert.bind_id(1,account);insert.bind(2,proposed.slot);insert.bind_blob(3,proposed.profile);
        insert.bind_blob(4,std::span<const std::uint8_t>{proposed.profile.begin(),end});
        insert.bind(5,proposed.name_codepage);insert.bind(6,proposed.streamer_privilege);insert.done();
        if(sqlite3_changes(db_)!=1)throw DatabaseError("Owned character insert conflict");
    }
    const auto inserted=sqlite3_last_insert_rowid(db_);
    if(inserted<=0)throw DatabaseError("Owned character creation missing identity");
    // Allocate/read the returned row before COMMIT; false/throw rolls back.
    const auto staged=list_for_account(account);
    if(staged.size()!=expected.size()+1)throw DatabaseError("Owned character row-set conflict");
    std::optional<RecoveredCharacter> created;
    for(const auto& row:staged) {
        if(row.id==static_cast<std::uint64_t>(inserted)) {
            if(created || row.account_id!=account || row.slot!=proposed.slot ||
               row.profile!=proposed.profile || row.name_codepage!=proposed.name_codepage ||
               row.streamer_privilege!=proposed.streamer_privilege)
                throw DatabaseError("Owned character created snapshot differs");
            created=row;
        }else {
            const auto found=std::find_if(expected.begin(),expected.end(),[&](const auto& e){return e.id==row.id;});
            if(found==expected.end() || !same_creation_row(row,*found))
                throw DatabaseError("Owned character existing snapshot differs");
        }
    }
    if(!created)throw DatabaseError("Owned character inserted row absent");
    if(!current(CreationPhase::BeforeCommit))return std::nullopt;
    transaction.commit();return created;
}
}
