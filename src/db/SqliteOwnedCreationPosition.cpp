#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>

namespace god2 {
std::optional<RecoveredPosition> SqliteRecoveredCharacterRepository::insert_owned_creation_position(
    const RecoveredCharacter& expected,InitialOwnedPosition proposed,CurrentCreationPosition current) {
    if(!expected.id || !expected.account_id || !current || proposed.area>63 || proposed.scene>1023)
        return std::nullopt;
    {
        sqlite_detail::Statement foreign_keys(db_,"PRAGMA foreign_keys");
        if(!foreign_keys.row() || foreign_keys.integer(0)!=1)
            throw DatabaseError("Creation position requires foreign keys");
    }
    sqlite_detail::Transaction transaction(db_);
    const auto root_current=[&]() {
        const auto rows=list_for_account(expected.account_id);
        unsigned matches=0;
        for(const auto& row:rows)if(row.id==expected.id) {
            ++matches;
            if(row.account_id!=expected.account_id || row.slot!=expected.slot || row.profile!=expected.profile ||
               row.created_at!=expected.created_at || row.name_codepage!=expected.name_codepage ||
               row.streamer_privilege!=expected.streamer_privilege)return false;
        }
        return matches==1;
    };
    if(!root_current() || load_position(expected.account_id,expected.id))return std::nullopt;
    if(!current(CreationPositionPhase::BeforeInsert))return std::nullopt;
    // Revision1 is existing shared persistence semantics, not a native18 byte.
    const RecoveredPosition next{proposed.area,proposed.scene,proposed.x,proposed.y,1};
    {
        sqlite_detail::Statement insert(db_,"INSERT INTO recovered_positions "
            "(character_id,area,scene,x,y,revision) VALUES(?,?,?,?,?,?)");
        insert.bind_id(1,expected.id);insert.bind(2,next.area);insert.bind(3,next.scene);
        insert.bind(4,next.x);insert.bind(5,next.y);insert.bind_id(6,next.revision);insert.done();
        if(sqlite3_changes(db_)!=1)throw DatabaseError("Creation position insert conflict");
    }
    if(!root_current() || load_position(expected.account_id,expected.id)!=std::optional<RecoveredPosition>{next})
        throw DatabaseError("Creation position staged snapshot differs");
    if(!current(CreationPositionPhase::BeforeCommit))return std::nullopt;
    transaction.commit();return next;
}
}
