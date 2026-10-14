#include "db/NativeSkillBookCatalog.h"
#include "db/SqliteSupport.h"

#include <algorithm>
#include <array>
#include <limits>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
std::string text(sqlite_detail::Statement& row, int column) {
    auto value = row.text(column);
    if (value.empty() || value.find('\0') != std::string::npos)
        throw DatabaseError("Invalid native skill book provenance text");
    return value;
}
std::string sha(sqlite_detail::Statement& row, int column) {
    auto value = text(row, column);
    if (value.size() != 64 || !std::all_of(value.begin(), value.end(), [](unsigned char c) {
            return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
        })) throw DatabaseError("Invalid native skill book SHA-256 text");
    return value;
}
bool digest_matches(const std::vector<std::uint8_t>& bytes,const std::string& expected) {
#ifdef _WIN32
    if(bytes.empty()||bytes.size()>std::numeric_limits<ULONG>::max())return false;
    struct Algorithm {BCRYPT_ALG_HANDLE value=nullptr;~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}} algorithm;
    struct Hash {BCRYPT_HASH_HANDLE value=nullptr;~Hash(){if(value)BCryptDestroyHash(value);}};
    if(BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
    DWORD length=0,returned=0;
    if(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),
        sizeof(length),&returned,0)<0||returned!=sizeof(length)||!length)return false;
    std::vector<std::uint8_t> object(length);Hash hash;
    if(BCryptCreateHash(algorithm.value,&hash.value,object.data(),length,nullptr,0,0)<0)return false;
    std::array<std::uint8_t,32> result{};
    if(BCryptHashData(hash.value,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)<0||
       BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)<0)return false;
    constexpr char hex[]="0123456789abcdef";std::string digest;digest.reserve(64);
    for(const auto byte:result){digest.push_back(hex[byte>>4]);digest.push_back(hex[byte&15]);}
    return digest==expected;
#else
    (void)bytes;(void)expected;return false;
#endif
}
}

NativeSkillBookCatalog::NativeSkillBookCatalog(sqlite3* db) : db_(db) {
    if (!db_) throw DatabaseError("Null native skill book connection");
}

std::optional<NativeSkillBookRecord> NativeSkillBookCatalog::lookup_item(std::int64_t item_id) const {
    if(item_id<6501||item_id>7199)return std::nullopt;
    const bool own=sqlite3_get_autocommit(db_)!=0;
    if(own)sqlite_detail::execute(db_,"BEGIN");
    struct Read {sqlite3* db;bool own,done=false;~Read(){if(own&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} read{db_,own};
    sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('native_skill_book_bindings','native_skill_books','native_data_sources','native_skill_catalog') OR tbl_name COLLATE NOCASE IN ('native_skill_book_bindings','native_skill_books','native_data_sources','native_skill_catalog')");
    if(shadow.row())throw DatabaseError("Skill book item lookup TEMP shadow rejected");
    sqlite_detail::Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('native_skill_book_bindings','native_skill_books','native_data_sources','native_skill_catalog')");
    if(!tables.row()||tables.integer(0)!=4||tables.row())throw DatabaseError("Skill book item lookup requires actual main tables");
    sqlite_detail::Statement rows(db_,"SELECT kind,definition_id FROM main.native_skill_book_bindings WHERE book_dataset_id='current-skill-books-v1' AND item_id=? ORDER BY kind,definition_id LIMIT 2");
    rows.bind(1,item_id);
    std::optional<NativeSkillBookRecord> result;
    if(rows.row()) {
        const auto kind=rows.integer(0),id=rows.integer(1);
        if(rows.row())throw DatabaseError("Ambiguous skill book item association");
        result=lookup(kind,id);
        if(!result||result->item_id!=item_id)throw DatabaseError("Skill book item association changed");
        if(!digest_matches(result->raw_record,result->record_sha256)||
           !digest_matches(result->parsed_record,result->parsed_sha256))result.reset();
    }
    if(own)sqlite_detail::execute(db_,"COMMIT");read.done=true;return result;
}

std::optional<NativeSkillBookRecord> NativeSkillBookCatalog::lookup(
    std::int64_t kind, std::int64_t definition_id) const {
    if (kind < 0 || kind > 3 || definition_id < 1 || definition_id > 255)
        throw DatabaseError("Invalid native skill book selector");
    sqlite_detail::Statement row(db_,
        "SELECT b.dataset_id,b.source_record_index,b.source_line,b.decoded_offset,b.item_id,"
        "b.record_sha256,b.raw_record,b.parsed_sha256,b.parsed_record,"
        "k.book_dataset_id,k.skill_dataset_id,k.kind,k.definition_id,k.item_id,"
        "s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,s.native_image_sha256,"
        "s.source_section,s.loader_rva,s.lookup_rva,s.row_count,"
        "c.dataset_id,c.kind,c.definition_id,c.raw_record "
        "FROM native_skill_book_bindings k "
        "LEFT JOIN native_skill_books b ON b.dataset_id=k.book_dataset_id AND b.item_id=k.item_id "
        "LEFT JOIN native_data_sources s ON s.dataset_id=k.book_dataset_id "
        "LEFT JOIN native_skill_catalog c ON c.dataset_id=k.skill_dataset_id "
        "AND c.kind=k.kind AND c.definition_id=k.definition_id "
        "WHERE k.book_dataset_id='current-skill-books-v1' AND k.kind=? AND k.definition_id=? LIMIT 2");
    row.bind(1, kind);
    row.bind(2, definition_id);
    if (!row.row()) return std::nullopt;
    NativeSkillBookRecord result;
    if (text(row, 0) != current_dataset_id || text(row, 9) != current_dataset_id ||
        text(row, 10) != NativeSkillCatalog::current_dataset_id ||
        text(row, 23) != NativeSkillCatalog::current_dataset_id)
        throw DatabaseError("Native skill book dataset mismatch");
    result.source_record_index = row.integer(1);
    result.source_line = row.integer(2);
    result.decoded_offset = row.integer(3);
    result.item_id = row.integer(4);
    result.record_sha256 = sha(row, 5);
    auto raw = row.blob(6, 1, 4095);
    result.raw_record.assign(raw.begin(), raw.end());
    result.parsed_sha256 = sha(row, 7);
    auto parsed = row.blob(8, 396, 396);
    result.parsed_record.assign(parsed.begin(), parsed.end());
    result.kind = row.integer(11);
    result.definition_id = row.integer(12);
    const auto linked_item = row.integer(13);
    const auto skill_kind = row.integer(24);
    const auto skill_id = row.integer(25);
    const auto skill_raw = row.blob(26, 110, 110);
    if (result.source_record_index < 0 || result.source_record_index >= 381 ||
        result.source_line <= 0 || result.decoded_offset < 0 ||
        result.item_id < 6501 || result.item_id > 7199 || linked_item != result.item_id ||
        result.kind != kind || result.definition_id != definition_id ||
        skill_kind != kind || skill_id != definition_id ||
        skill_raw[0] != definition_id || skill_raw[1] != kind)
        throw DatabaseError("Native skill book binding invalid");
    auto& source = result.source;
    source.dataset_id = text(row, 14);
    source.source_path = text(row, 15);
    source.source_sha256 = sha(row, 16);
    source.decoded_sha256 = sha(row, 17);
    source.native_image_sha256 = sha(row, 18);
    source.source_section = text(row, 19);
    source.loader_rva = text(row, 20);
    source.lookup_rva = text(row, 21);
    source.row_count = row.integer(22);
    if (source.dataset_id != current_dataset_id ||
        source.source_path != "Data2/Patch/Comm/gamedata.csvZ" ||
        source.source_sha256 != "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731" ||
        source.decoded_sha256 != "75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815" ||
        source.native_image_sha256 != "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
        source.source_section != "SKB" || source.loader_rva != "0x59420" ||
        source.lookup_rva != "0xA8E10" || source.row_count != 381)
        throw DatabaseError("Native skill book source identity changed");
    if (row.row()) throw DatabaseError("Duplicate native skill book lookup");
    return result;
}
}
