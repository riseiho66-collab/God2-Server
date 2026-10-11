#include "db/SqliteOwnedGuildLeaveRepository.h"
#include "db/SqliteSupport.h"
#include <limits>

namespace god2 {
namespace {
constexpr auto source_sha256=
    "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void positive(std::uint64_t value) {
    if (!value || value>maximum) throw DatabaseError("Invalid owned guild leave identity/revision");
}
void verify_guild(sqlite3* db,const StoredGuildMembership& expected,std::uint64_t revision) {
    sqlite_detail::Statement query(db,
        "SELECT id,name_utf8,revision,origin,design_id,source_sha256 FROM owned_guilds WHERE id=?");
    query.bind_id(1,expected.guild_id);
    if (!query.row() || query.number<std::uint64_t>(0)!=expected.guild_id ||
        query.text(1)!=expected.name_utf8 || query.number<std::uint64_t>(2)!=revision ||
        query.text(3)!="CUSTOM_DESIGNED" || query.text(4)!="CUSTOM-0075" ||
        query.text(5)!=source_sha256)
        throw DatabaseError("Owned guild leave generation/readback conflict");
}
}

SqliteOwnedGuildLeaveRepository::SqliteOwnedGuildLeaveRepository(sqlite3* db):db_(db) {
    if (!db_) throw DatabaseError("Null owned guild leave connection");
}
void SqliteOwnedGuildLeaveRepository::leave(std::uint64_t account,std::uint64_t character,
                                         const StoredGuildMembership& expected) {
    positive(account);positive(character);positive(expected.guild_id);
    positive(expected.guild_revision);positive(expected.membership_revision);
    // Lock before checking ownership/snapshot; do not accept a partial CAS
    // generation, name alias, changed guild, or remove/rejoin replacement.
    sqlite_detail::Transaction transaction(db_); // BEGIN IMMEDIATE
    SqliteGuildRepository authority(db_);
    const auto before=authority.load(account,character);
    if (!before || *before!=expected)
        throw DatabaseError("Owned guild leave membership snapshot conflict");
    sqlite_detail::Statement clock(db_,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");
    if (!clock.row()) throw DatabaseError("Missing owned guild generation clock");
    const auto current=clock.number<std::uint64_t>(0);
    if (current>=maximum) throw DatabaseError("Owned guild revision exhausted");
    const auto revision=current+1;
    sqlite_detail::Statement bump(db_,
        "UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    bump.bind_id(1,revision);bump.bind_id(2,expected.guild_id);
    bump.bind_id(3,expected.guild_revision);bump.bind(4,expected.name_utf8);
    bump.bind(5,std::string(source_sha256));bump.done();
    if (sqlite3_changes(db_)!=1) throw DatabaseError("Owned guild leave generation CAS failed");
    verify_guild(db_,expected,revision);
    const StoredGuildMembership bumped{expected.guild_id,expected.name_utf8,revision,
                                      expected.membership_revision};
    if (authority.load(account,character)!=std::optional(bumped))
        throw DatabaseError("Owned guild leave membership changed during generation update");
    sqlite_detail::Statement erase(db_,
        "DELETE FROM owned_guild_members WHERE character_id=? AND guild_id=? AND revision=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? "
        "AND EXISTS (SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id "
        "AND c.account_id=?)");
    erase.bind_id(1,character);erase.bind_id(2,expected.guild_id);
    erase.bind_id(3,expected.membership_revision);erase.bind(4,std::string(source_sha256));
    erase.bind_id(5,account);erase.done();
    if (sqlite3_changes(db_)!=1 || authority.load(account,character))
        throw DatabaseError("Owned guild leave delete/readback failed");
    // Detect trigger rewriting of the retained guild row after the delete.
    verify_guild(db_,expected,revision);
    transaction.commit();
}
}
