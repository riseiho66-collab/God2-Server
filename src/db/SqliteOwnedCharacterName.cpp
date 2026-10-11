#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <set>

namespace god2 {
namespace {
bool same_name_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
}
std::optional<RecoveredCharacter> SqliteRecoveredCharacterRepository::replace_owned_name_snapshot(
    std::uint64_t account,std::vector<RecoveredCharacter> expected,std::uint64_t character,
    OwnedNameCandidate proposed,CurrentNameReplacement current) {
    if(!account || !character || !current || expected.empty() ||
       (proposed.name_codepage!=0 && proposed.name_codepage!=936 && proposed.name_codepage!=950))return std::nullopt;
    // Existing common storage name bound, not a whole-protocol domain or
    // inferred native name normalization/permission. Source must provide an
    // explicit common projection; never narrow an unqualified native name.
    const auto end=std::find(proposed.common_name_bytes.begin(),proposed.common_name_bytes.begin()+15,0);
    if(end==proposed.common_name_bytes.begin() || end==proposed.common_name_bytes.begin()+15)return std::nullopt;
    std::set<std::uint64_t> ids;
    for(const auto& row:expected)
        if(!row.id || row.account_id!=account || !ids.insert(row.id).second)return std::nullopt;
    const auto found=std::find_if(expected.begin(),expected.end(),[character](const auto& row){return row.id==character;});
    if(found==expected.end())return std::nullopt;
    const auto old=*found;
    const auto old_end=std::find(old.profile.begin(),old.profile.begin()+15,0);
    if(old_end==old.profile.begin() || old_end==old.profile.begin()+15)return std::nullopt;
    auto next=old;
    std::copy(proposed.common_name_bytes.begin(),proposed.common_name_bytes.end(),next.profile.begin());
    next.name_codepage=proposed.name_codepage;
    {
        sqlite_detail::Statement keys(db_,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1)throw DatabaseError("Owned name replacement requires foreign keys");
    }
    sqlite_detail::Transaction transaction(db_);
    const auto existing=list_for_account(account);
    if(existing.size()!=expected.size())return std::nullopt;
    for(const auto& row:existing) {
        const auto at=std::find_if(expected.begin(),expected.end(),[&](const auto& e){return e.id==row.id;});
        if(at==expected.end() || !same_name_root(row,*at))return std::nullopt;
    }
    if(!current(NameReplacementPhase::BeforeReplace))return std::nullopt;
    {
        sqlite_detail::Statement write(db_,"UPDATE recovered_characters SET profile=?,name_bytes=?,name_codepage=? "
            "WHERE id=? AND account_id=? AND slot=? AND profile=? AND name_bytes=? "
            "AND created_at=? AND name_codepage=? AND streamer_privilege=?");
        write.bind_blob(1,next.profile);
        write.bind_blob(2,std::span<const std::uint8_t>{proposed.common_name_bytes.begin(),end});
        write.bind(3,next.name_codepage);write.bind_id(4,old.id);write.bind_id(5,account);write.bind(6,old.slot);
        write.bind_blob(7,old.profile);write.bind_blob(8,std::span<const std::uint8_t>{old.profile.begin(),old_end});
        write.bind(9,old.created_at);write.bind(10,old.name_codepage);write.bind(11,old.streamer_privilege);write.done();
        if(sqlite3_changes(db_)!=1)throw DatabaseError("Owned name replacement snapshot conflict");
    }
    const auto staged=list_for_account(account);
    if(staged.size()!=expected.size())throw DatabaseError("Owned name replacement row-set conflict");
    std::optional<RecoveredCharacter> updated;
    for(const auto& row:staged) {
        if(row.id==character) {
            if(updated || !same_name_root(row,next))throw DatabaseError("Owned updated name snapshot differs");
            updated=row;
        }else {
            const auto at=std::find_if(expected.begin(),expected.end(),[&](const auto& e){return e.id==row.id;});
            if(at==expected.end() || !same_name_root(row,*at))throw DatabaseError("Owned other name snapshot differs");
        }
    }
    if(!updated)throw DatabaseError("Owned updated name row absent");
    if(!current(NameReplacementPhase::BeforeCommit))return std::nullopt;
    transaction.commit();return updated;
}
}
