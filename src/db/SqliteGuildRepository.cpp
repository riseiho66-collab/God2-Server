#include "db/SqliteGuildRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <limits>

namespace god2 {
namespace {
constexpr auto source_sha256="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void positive(std::uint64_t value,const char* message) {
    if(!value || value>maximum)throw DatabaseError(message);
}
void name_valid(const std::string& name) {
    // Native4E7180 passes this name as the5077C0 format argument. Reject
    // percent signs in new maintenance names; no client rewrite is needed.
    if(name.empty() || name.size()>60 || name.find('\0')!=std::string::npos || name.find('%')!=std::string::npos)
        throw DatabaseError("Invalid guild name");
    try {
        for(const auto simplified:{false,true}) {
            const auto legacy=LegacyChineseCodec::encode(name,simplified);
            if(legacy.empty() || legacy.size()>15 || legacy.find('\0')!=std::string::npos ||
               LegacyChineseCodec::decode(legacy,simplified)!=name)
                throw DatabaseError("Guild name is not lossless in both client languages");
        }
    }catch(const std::exception&) {throw DatabaseError("Invalid or unrepresentable guild name");}
}
void provenance(const sqlite_detail::Statement& row,int offset) {
    if(row.text(offset)!="CUSTOM_DESIGNED" || row.text(offset+1)!="CUSTOM-0075" ||
       row.text(offset+2)!=source_sha256)
        throw DatabaseError("Guild storage provenance mismatch");
}
struct Guild {std::uint64_t id;std::string name;std::uint64_t revision;};
Guild load_guild(sqlite3* db,std::uint64_t identity) {
    positive(identity,"Invalid guild identity");
    sqlite_detail::Statement query(db,"SELECT id,name_utf8,revision,origin,design_id,source_sha256 FROM owned_guilds WHERE id=?");
    query.bind_id(1,identity);
    if(!query.row())throw DatabaseError("Guild does not exist");
    Guild result{query.number<std::uint64_t>(0),query.text(1),query.number<std::uint64_t>(2)};
    positive(result.id,"Invalid stored guild identity");positive(result.revision,"Invalid guild revision");
    name_valid(result.name);provenance(query,3);return result;
}
std::uint64_t next_revision(sqlite3* db) {
    // CUSTOM-0075: globally monotonic maintenance generations. Guild rows are
    // retained; remove/rejoin or transferring between guilds cannot reuse a
    // deleted membership's CAS revision. This is not a gameplay formula.
    sqlite_detail::Statement query(db,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");
    if(!query.row())throw DatabaseError("Missing guild revision clock");
    const auto current=query.number<std::uint64_t>(0);
    if(current>=maximum)throw DatabaseError("Guild revision exhausted");
    return current+1;
}
void bump(sqlite3* db,const Guild& before,std::uint64_t revision) {
    sqlite_detail::Statement update(db,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=?");
    update.bind_id(1,revision);update.bind_id(2,before.id);update.bind_id(3,before.revision);update.done();
    const auto after=load_guild(db,before.id);
    if(sqlite3_changes(db)!=1 || after.revision!=revision || after.name!=before.name)
        throw DatabaseError("Guild revision CAS/readback failed");
}
}

SqliteGuildRepository::SqliteGuildRepository(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null guild connection");
}
std::string SqliteGuildRepository::schema() {
    return R"SQL(
-- CUSTOM-0075: maintenance membership only; no native guild economics claimed.
CREATE TABLE owned_guilds (
 id INTEGER PRIMARY KEY CHECK(typeof(id)='integer' AND id>0),
 name_utf8 TEXT NOT NULL UNIQUE COLLATE BINARY CHECK(typeof(name_utf8)='text' AND length(CAST(name_utf8 AS BLOB)) BETWEEN 1 AND 60 AND instr(name_utf8,char(0))=0 AND instr(name_utf8,'%')=0),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0075'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE TABLE owned_guild_members (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE CHECK(typeof(character_id)='integer' AND character_id>0),
 guild_id INTEGER NOT NULL REFERENCES owned_guilds(id) CHECK(typeof(guild_id)='integer' AND guild_id>0),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0075'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE INDEX owned_guild_member_audience ON owned_guild_members(guild_id,character_id);
-- Retain the monotonic revision clock even when the last member leaves.
CREATE TRIGGER retain_owned_guild_generation BEFORE DELETE ON owned_guilds
 BEGIN SELECT RAISE(ABORT,'CUSTOM-0075 guild generation must be retained'); END;
)SQL";
}
std::optional<StoredGuildMembership> SqliteGuildRepository::load(std::uint64_t account,std::uint64_t character) {
    positive(account,"Invalid guild owner");positive(character,"Invalid guild owner");
    sqlite_detail::Statement query(db_,
        "SELECT m.character_id IS NOT NULL,m.guild_id,m.revision,m.origin,m.design_id,m.source_sha256 "
        "FROM recovered_characters c LEFT JOIN owned_guild_members m ON m.character_id=c.id WHERE c.account_id=? AND c.id=?");
    query.bind_id(1,account);query.bind_id(2,character);
    if(!query.row())throw DatabaseError("Invalid guild owner");
    if(!query.integer(0))return std::nullopt;
    provenance(query,3);
    const auto guild=load_guild(db_,query.number<std::uint64_t>(1));
    const auto membership_revision=query.number<std::uint64_t>(2);
    positive(membership_revision,"Invalid guild membership revision");
    if(membership_revision>guild.revision)throw DatabaseError("Guild membership generation exceeds guild revision");
    return StoredGuildMembership{guild.id,guild.name,guild.revision,membership_revision};
}
std::uint64_t SqliteGuildRepository::admin_create(const std::string& name_utf8) {
    name_valid(name_utf8);
    sqlite_detail::Transaction transaction(db_);
    const auto revision=next_revision(db_);
    sqlite_detail::Statement insert(db_,
        "INSERT INTO owned_guilds(name_utf8,revision,origin,design_id,source_sha256) "
        "VALUES(?,?,'CUSTOM_DESIGNED','CUSTOM-0075','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')");
    insert.bind(1,name_utf8);insert.bind_id(2,revision);insert.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Guild creation write failed");
    const auto identity=static_cast<std::uint64_t>(sqlite3_last_insert_rowid(db_));
    const auto created=load_guild(db_,identity);
    if(created.name!=name_utf8 || created.revision!=revision)throw DatabaseError("Guild creation readback failed");
    transaction.commit();return identity;
}
StoredGuildMembership SqliteGuildRepository::admin_assign(std::uint64_t account,std::uint64_t character,
    std::uint64_t guild,std::optional<std::uint64_t> expected_revision) {
    if(expected_revision)positive(*expected_revision,"Invalid guild membership expected revision");
    sqlite_detail::Transaction transaction(db_);
    const auto before=load(account,character);
    if(before.has_value()!=expected_revision.has_value() || (before && before->membership_revision!=*expected_revision))
        throw DatabaseError("Guild membership revision conflict");
    const auto destination=load_guild(db_,guild);
    if(before && before->guild_id==guild) {transaction.commit();return *before;}
    const auto revision=next_revision(db_);
    if(before)bump(db_,load_guild(db_,before->guild_id),revision);
    bump(db_,destination,revision);
    sqlite_detail::Statement write(db_,before?
        "UPDATE owned_guild_members SET guild_id=?,revision=? WHERE character_id=? AND revision=?":
        "INSERT INTO owned_guild_members(guild_id,revision,character_id,origin,design_id,source_sha256) "
        "VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')");
    write.bind_id(1,guild);write.bind_id(2,revision);write.bind_id(3,character);
    if(before)write.bind_id(4,*expected_revision);write.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Guild membership CAS write failed");
    const StoredGuildMembership after{guild,destination.name,revision,revision};
    if(load(account,character)!=std::optional(after))throw DatabaseError("Guild membership readback failed");
    transaction.commit();return after;
}
void SqliteGuildRepository::admin_remove(std::uint64_t account,std::uint64_t character,std::uint64_t expected_revision) {
    positive(expected_revision,"Invalid guild membership expected revision");
    sqlite_detail::Transaction transaction(db_);
    const auto before=load(account,character);
    if(!before || before->membership_revision!=expected_revision)throw DatabaseError("Guild membership revision conflict");
    const auto guild=load_guild(db_,before->guild_id);
    bump(db_,guild,next_revision(db_));
    sqlite_detail::Statement erase(db_,"DELETE FROM owned_guild_members WHERE character_id=? AND revision=?");
    erase.bind_id(1,character);erase.bind_id(2,expected_revision);erase.done();
    if(sqlite3_changes(db_)!=1 || load(account,character))throw DatabaseError("Guild membership remove/readback failed");
    transaction.commit();
}
}
