#include "db/SqliteRoleAuxiliaryRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <utility>
namespace god2 {
namespace {
constexpr auto current_client="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
void validate(const RoleAuxiliarySnapshot& row) {
    if(!RecoveredRoleAuxiliary::parse(row.logical) || !row.revision || row.revision>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       (row.origin!="NATIVE_CAPTURE_VERIFIED" && row.origin!="CUSTOM_TEST_NOT_NATIVE") ||
       row.provenance.empty() || row.provenance.size()>255 || row.provenance.find('\0')!=std::string::npos)
        throw DatabaseError("Invalid owned auxiliary snapshot");
}
}
SqliteRoleAuxiliaryRepository::SqliteRoleAuxiliaryRepository(sqlite3* db):db_(db){if(!db_)throw DatabaseError("Null auxiliary snapshot connection");}
std::optional<RoleAuxiliarySnapshot> SqliteRoleAuxiliaryRepository::load(std::uint64_t account,std::uint64_t character) {
    if(!account || !character)throw DatabaseError("Invalid auxiliary owner");
    sqlite_detail::Statement query(db_,
        "SELECT s.character_id IS NOT NULL,s.logical,s.revision,s.origin,s.provenance,s.client_sha256,s.design_id "
        "FROM recovered_characters c LEFT JOIN character_role_auxiliary_snapshots s ON s.character_id=c.id WHERE c.account_id=? AND c.id=?");
    query.bind_id(1,account);query.bind_id(2,character);
    if(!query.row())throw DatabaseError("Invalid auxiliary owner");
    if(!query.integer(0))return std::nullopt;
    const auto bytes=query.blob(1,61,61);const auto raw=RecoveredRoleAuxiliary::parse(bytes);
    if(!raw || query.text(5)!=current_client || query.text(6)!="CUSTOM-0045")throw DatabaseError("Owned auxiliary source/codec mismatch");
    RoleAuxiliarySnapshot result{*raw,query.number<std::uint64_t>(2),query.text(3),query.text(4)};
    validate(result);return result;
}
RoleAuxiliarySnapshot SqliteRoleAuxiliaryRepository::save(std::uint64_t account,std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,const RecoveredRoleAuxiliary::Logical& raw,
        std::string origin,std::string provenance) {
    if(expected_revision && (!*expected_revision || *expected_revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())))throw DatabaseError("Auxiliary revision bound");
    sqlite_detail::Transaction transaction(db_);
    const auto before=load(account,character);
    if(before.has_value()!=expected_revision.has_value() || (before && before->revision!=*expected_revision))throw DatabaseError("Auxiliary snapshot revision conflict");
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON r.id=s.battle_id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);if(pending.row())throw DatabaseError("Auxiliary change during pending battle");
    RoleAuxiliarySnapshot next{raw,expected_revision?*expected_revision+1:1,std::move(origin),std::move(provenance)};validate(next);
    sqlite_detail::Statement write(db_,before?
        "UPDATE character_role_auxiliary_snapshots SET logical=?,revision=?,origin=?,provenance=? WHERE character_id=? AND revision=?":
        "INSERT INTO character_role_auxiliary_snapshots(logical,revision,origin,provenance,character_id,client_sha256,design_id) VALUES(?,?,?,?,?,'6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98','CUSTOM-0045')");
    write.bind_blob(1,raw);write.bind_id(2,next.revision);write.bind(3,next.origin);write.bind(4,next.provenance);write.bind_id(5,character);if(before)write.bind_id(6,*expected_revision);write.done();
    if(sqlite3_changes(db_)!=1 || load(account,character)!=std::optional(next))throw DatabaseError("Auxiliary snapshot write/readback failed");
    transaction.commit();return next;
}
}
