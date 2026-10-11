#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <limits>

namespace god2 {
namespace {
constexpr auto source_sha256="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
std::string decode(const RecoveredRoleText::Text& text,std::uint16_t codepage) {
    if((codepage!=936 && codepage!=950) || !RecoveredRoleText::update(text))
        throw DatabaseError("Invalid canonical role text/codepage");
    const auto end=std::find(text.begin(),text.end(),0);
    const std::string bytes(reinterpret_cast<const char*>(text.data()),
        static_cast<std::size_t>(end-text.begin()));
    try {
        const auto utf8=LegacyChineseCodec::decode(bytes,codepage==936);
        if(LegacyChineseCodec::encode(utf8,codepage==936)!=bytes)
            throw DatabaseError("Role text codepage roundtrip mismatch");
        return utf8;
    } catch(const std::exception&) {
        throw DatabaseError("Invalid or non-roundtripping role text encoding");
    }
}
void validate(const StoredRoleText& row) {
    if(!row.revision || row.revision>maximum_revision || decode(row.text,row.codepage)!=row.utf8)
        throw DatabaseError("Invalid owned role text row");
}
}

SqliteRoleTextRepository::SqliteRoleTextRepository(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null role text connection");
}
std::string SqliteRoleTextRepository::schema() {
    return R"SQL(
-- CUSTOM-0056: secondary display text only; primary identity remains unchanged.
CREATE TABLE character_role_text (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 legacy_text BLOB NOT NULL CHECK(typeof(legacy_text)='blob' AND length(legacy_text)=16 AND substr(legacy_text,16,1)=X'00'),
 utf8_text TEXT NOT NULL CHECK(typeof(utf8_text)='text' AND length(CAST(utf8_text AS BLOB))<=60 AND instr(utf8_text,char(0))=0),
 codepage INTEGER NOT NULL CHECK(typeof(codepage)='integer' AND codepage IN (936,950)),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0056')
);
)SQL";
}
std::optional<StoredRoleText> SqliteRoleTextRepository::load(std::uint64_t account,std::uint64_t character) {
    if(!account || !character)throw DatabaseError("Invalid role text owner");
    sqlite_detail::Statement query(db_,
        "SELECT t.character_id IS NOT NULL,t.legacy_text,t.utf8_text,t.codepage,t.revision,t.origin,t.source_sha256,t.design_id "
        "FROM recovered_characters c LEFT JOIN character_role_text t ON t.character_id=c.id WHERE c.account_id=? AND c.id=?");
    query.bind_id(1,account);query.bind_id(2,character);
    if(!query.row())throw DatabaseError("Invalid role text owner");
    if(!query.integer(0))return std::nullopt;
    if(query.text(5)!="CUSTOM_DESIGNED" || query.text(6)!=source_sha256 || query.text(7)!="CUSTOM-0056")
        throw DatabaseError("Owned role text provenance mismatch");
    StoredRoleText result;
    const auto bytes=query.blob(1,16,16);
    std::copy(bytes.begin(),bytes.end(),result.text.begin());
    result.utf8=query.text(2);result.codepage=query.number<std::uint16_t>(3);result.revision=query.number<std::uint64_t>(4);
    validate(result);return result;
}
std::optional<RecoveredRoleText::Text> SqliteRoleTextRepository::project(const StoredRoleText& row,std::uint16_t output_codepage) {
    try {
        validate(row);
        if(output_codepage!=936 && output_codepage!=950)return std::nullopt;
        if(output_codepage==row.codepage)return row.text;
        const auto bytes=LegacyChineseCodec::encode(row.utf8,output_codepage==936);
        if(bytes.size()>RecoveredRoleText::maximum_text_bytes || bytes.find('\0')!=std::string::npos ||
           LegacyChineseCodec::decode(bytes,output_codepage==936)!=row.utf8)return std::nullopt;
        RecoveredRoleText::Text result{};
        std::copy(bytes.begin(),bytes.end(),result.begin());return result;
    } catch(const std::exception&) {return std::nullopt;}
}
StoredRoleText SqliteRoleTextRepository::save(std::uint64_t account,std::uint64_t character,
    std::optional<std::uint64_t> expected_revision,const RecoveredRoleText::Text& canonical_text,std::uint16_t codepage,const Prepare& prepare) {
    if(expected_revision && (!*expected_revision || *expected_revision>maximum_revision))
        throw DatabaseError("Role text revision bound");
    const auto utf8=decode(canonical_text,codepage);
    sqlite_detail::Transaction transaction(db_);
    const auto before=load(account,character);
    if(before.has_value()!=expected_revision.has_value() || (before && before->revision!=*expected_revision))
        throw DatabaseError("Role text revision conflict");
    // A retry with the same canonical text is harmless even at the revision cap.
    if(before && before->text==canonical_text && before->codepage==codepage) {
        if(prepare)prepare(*before);
        if(load(account,character)!=before)throw DatabaseError("Role text prepare changed owned state");
        transaction.commit();return *before;
    }
    if(expected_revision && *expected_revision==maximum_revision)throw DatabaseError("Role text revision exhausted");
    StoredRoleText next{canonical_text,utf8,codepage,expected_revision?*expected_revision+1:1};
    validate(next);
    sqlite_detail::Statement write(db_,before?
        "UPDATE character_role_text SET legacy_text=?,utf8_text=?,codepage=?,revision=? WHERE character_id=? AND revision=?":
        "INSERT INTO character_role_text(legacy_text,utf8_text,codepage,revision,character_id,origin,source_sha256,design_id) "
        "VALUES(?,?,?,?,?,'CUSTOM_DESIGNED','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763','CUSTOM-0056')");
    write.bind_blob(1,next.text);write.bind(2,next.utf8);write.bind(3,static_cast<std::int64_t>(next.codepage));
    write.bind_id(4,next.revision);write.bind_id(5,character);if(before)write.bind_id(6,*expected_revision);write.done();
    if(sqlite3_changes(db_)!=1 || load(account,character)!=std::optional(next))
        throw DatabaseError("Role text write/readback failed");
    if(prepare)prepare(next);
    if(load(account,character)!=std::optional(next))throw DatabaseError("Role text prepare changed owned state");
    transaction.commit();return next;
}
}
