#include "db/NativeSkillCatalog.h"
#include "db/SqliteSupport.h"

#include <algorithm>
#include <array>
#include <limits>
#include <utility>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
bool valid_text(const std::string& text) {
    return !text.empty() && text.find('\0') == std::string::npos;
}

std::string required_text(sqlite_detail::Statement& statement, int column) {
    auto text = statement.text(column);
    if (!valid_text(text)) throw DatabaseError("Invalid native skill provenance text");
    return text;
}

std::string sha256_text(sqlite_detail::Statement& statement, int column) {
    auto text = statement.text(column);
    const auto hex = [](unsigned char value) {
        return (value >= '0' && value <= '9') || (value >= 'a' && value <= 'f');
    };
    if (text.size() != 64 || !std::all_of(text.begin(), text.end(), hex))
        throw DatabaseError("Invalid native skill SHA-256 text");
    return text;
}

bool record_digest_matches(const NativeSkillRecord& record) {
#ifdef _WIN32
    if(record.raw_record.size()!=110)return false;
    struct Algorithm {
        BCRYPT_ALG_HANDLE value=nullptr;
        ~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}
    } algorithm;
    struct Hash {
        BCRYPT_HASH_HANDLE value=nullptr;
        ~Hash(){if(value)BCryptDestroyHash(value);}
    };
    if(BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
    DWORD length=0,returned=0;
    if(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),
        sizeof(length),&returned,0)<0 || returned!=sizeof(length) || !length)return false;
    std::vector<std::uint8_t> object(length);
    Hash hash; // Destroy the hash before its backing object and algorithm.
    if(BCryptCreateHash(algorithm.value,&hash.value,object.data(),length,nullptr,0,0)<0)return false;
    std::array<std::uint8_t,32> result{};
    if(BCryptHashData(hash.value,const_cast<PUCHAR>(record.raw_record.data()),110,0)<0 ||
       BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)<0)return false;
    constexpr char hex[]="0123456789abcdef";
    std::string digest;digest.reserve(64);
    for(const auto byte:result){digest.push_back(hex[byte>>4]);digest.push_back(hex[byte&15]);}
    return digest==record.record_sha256;
#else
    (void)record;return false;
#endif
}
struct SharedReadScope {
    sqlite3* db;bool owned,finished=false;
    explicit SharedReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0) {
        if(owned)sqlite_detail::execute(db,"BEGIN");
    }
    SharedReadScope(const SharedReadScope&)=delete;
    SharedReadScope& operator=(const SharedReadScope&)=delete;
    ~SharedReadScope(){if(owned && !finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
SharedSkillNativeBinding shared_binding(const NativeSkillRecord& r,SharedSkillRegion region) {
    if(r.raw_record.size()!=110)throw DatabaseError("Invalid shared skill raw record");
    SharedSkillNativeBinding b;b.region=region;b.source=r.source;
    b.source_record_index=r.source_record_index;b.source_offset=r.source_offset;
    b.record_sha256=r.record_sha256;std::copy(r.raw_record.begin(),r.raw_record.end(),b.raw.begin());
    b.row_digest_verified=record_digest_matches(r);return b;
}
}

NativeSkillCatalog::NativeSkillCatalog(sqlite3* db) : db_(db) {
    if (!db_) throw DatabaseError("Null native skill catalog connection");
}

std::uint16_t NativeSkillRecord::client_mp_threshold() const {
    if(raw_record.size()!=110) throw DatabaseError("Invalid native skill record for client MP threshold");
    return static_cast<std::uint16_t>(raw_record[0x42] | (static_cast<std::uint16_t>(raw_record[0x43])<<8));
}

std::optional<NativeSkillRecord> NativeSkillCatalog::lookup(
    const std::string& dataset_id, std::int64_t kind, std::int64_t definition_id) const {
    return lookup_impl(dataset_id,kind,definition_id,false);
}
std::optional<NativeSkillRecord> NativeSkillCatalog::lookup_main(
    const std::string& dataset_id, std::int64_t kind, std::int64_t definition_id) const {
    return lookup_impl(dataset_id,kind,definition_id,true);
}
std::optional<NativeSkillRecord> NativeSkillCatalog::lookup_main_digest_checked(
    const std::string& dataset_id, std::int64_t kind, std::int64_t definition_id) const {
    const auto owned_dataset=dataset_id; // Retain caller text across SQLite observers.
    auto record=lookup_main(owned_dataset,kind,definition_id);
    if(!record || !record_digest_matches(*record))return std::nullopt;
    return record;
}
std::optional<SharedSkillLookup> NativeSkillCatalog::lookup_shared_definition_main(
    std::int64_t kind,std::int64_t definition_id) const {
    // Existing joined reads validate selectors and corrupt rows even on this
    // explicit path. A missing CN counterpart never drops a valid TW snapshot.
    SharedReadScope scope(db_);
    auto tw=lookup_main(current_dataset_id,kind,definition_id);
    auto cn=lookup_main("cn-native-cbspec2-582f2695-857b52e3-v1",kind,definition_id);
    std::optional<SharedSkillNativeBinding> t,c;
    if(tw)t=shared_binding(*tw,SharedSkillRegion::Taiwan);
    if(cn)c=shared_binding(*cn,SharedSkillRegion::China);
    SharedSkillLookup value{tw,resolve_shared_skill_definition(
        static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(definition_id),std::move(t),std::move(c))};
    // Existing native absence stays visible. Only the two formal owner rule
    // keys can yield a common definition with no native source/raw profile.
    if(!tw && !cn && !value.definition.owner_rule){scope.finish();return std::nullopt;}
    scope.finish();return value;
}
std::optional<NativeSkillSource> NativeSkillCatalog::lookup_main_source(const std::string& dataset_id) const {
    const auto owned_dataset=dataset_id; // Own caller text before SQLite observers.
    if(!valid_text(owned_dataset) ||
       owned_dataset.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()))
        throw DatabaseError("Invalid native skill catalog dataset");
    sqlite_detail::Statement statement(db_,
        "SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
        "source_section,loader_rva,lookup_rva,row_count FROM main.native_data_sources WHERE dataset_id=? LIMIT 2");
    statement.bind(1,owned_dataset);
    if(!statement.row())return std::nullopt;
    NativeSkillSource source;
    source.dataset_id=required_text(statement,0);
    source.source_path=required_text(statement,1);
    source.source_sha256=sha256_text(statement,2);
    source.decoded_sha256=sha256_text(statement,3);
    source.native_image_sha256=sha256_text(statement,4);
    source.source_section=required_text(statement,5);
    source.loader_rva=required_text(statement,6);
    source.lookup_rva=required_text(statement,7);
    source.row_count=statement.integer(8);
    if(source.dataset_id!=owned_dataset || source.row_count<1 || source.row_count>1020 ||
       source.source_sha256!=source.decoded_sha256)
        throw DatabaseError("Invalid native skill catalog source");
    if(statement.row())throw DatabaseError("Duplicate native skill catalog source");
    return source;
}
std::optional<NativeSkillRecord> NativeSkillCatalog::lookup_impl(
    const std::string& dataset_id, std::int64_t kind, std::int64_t definition_id,bool main_schema) const {
    if (!valid_text(dataset_id) ||
        dataset_id.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        kind < 0 || kind > 3 || definition_id < 1 || definition_id > 255)
        throw DatabaseError("Invalid native skill catalog selector");

    // One snapshot exposes orphans through the outer join and duplicate matches
    // through the second row, even if database uniqueness constraints are damaged.
    const std::string tables=main_schema ?
        "FROM main.native_skill_catalog c LEFT JOIN main.native_data_sources s ON s.dataset_id=c.dataset_id " :
        "FROM native_skill_catalog c LEFT JOIN native_data_sources s ON s.dataset_id=c.dataset_id ";
    const std::string query=
        "SELECT c.dataset_id,c.source_record_index,c.source_offset,c.record_sha256,"
        "c.raw_record,c.kind,c.definition_id,"
        "s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,s.native_image_sha256,"
        "s.source_section,s.loader_rva,s.lookup_rva,s.row_count " + tables +
        "WHERE c.dataset_id=? AND c.kind=? AND c.definition_id=? LIMIT 2";
    sqlite_detail::Statement statement(db_,query.c_str());
    statement.bind(1, dataset_id);
    statement.bind(2, kind);
    statement.bind(3, definition_id);
    if (!statement.row()) return std::nullopt;

    if (required_text(statement, 0) != dataset_id)
        throw DatabaseError("Native skill catalog dataset mismatch");
    NativeSkillRecord result;
    result.source_record_index = statement.integer(1);
    result.source_offset = statement.integer(2);
    result.record_sha256 = sha256_text(statement, 3);
    const auto raw = statement.blob(4, 110, 110);
    result.raw_record.assign(raw.begin(), raw.end());
    result.kind = statement.integer(5);
    result.definition_id = statement.integer(6);
    if (result.source_record_index < 0 || result.source_record_index > 1019 ||
        result.kind < 0 || result.kind > 3 || result.definition_id < 1 || result.definition_id > 255 ||
        result.kind != kind || result.definition_id != definition_id)
        throw DatabaseError("Invalid native skill catalog record bounds");
    if (result.source_offset != 8 + result.kind * 0x6e04 + (result.definition_id - 1) * 110 ||
        result.raw_record[0] != result.definition_id || result.raw_record[1] != result.kind)
        throw DatabaseError("Native skill catalog source identity mismatch");

    auto& source = result.source;
    source.dataset_id = required_text(statement, 7);
    source.source_path = required_text(statement, 8);
    source.source_sha256 = sha256_text(statement, 9);
    source.decoded_sha256 = sha256_text(statement, 10);
    source.native_image_sha256 = sha256_text(statement, 11);
    source.source_section = required_text(statement, 12);
    source.loader_rva = required_text(statement, 13);
    source.lookup_rva = required_text(statement, 14);
    source.row_count = statement.integer(15);
    if (source.dataset_id != dataset_id || source.row_count < 1 || source.row_count > 1020 ||
        result.source_record_index >= source.row_count || source.source_sha256 != source.decoded_sha256)
        throw DatabaseError("Invalid native skill catalog source");
    if (statement.row()) throw DatabaseError("Duplicate native skill catalog lookup");
    return result;
}
}
