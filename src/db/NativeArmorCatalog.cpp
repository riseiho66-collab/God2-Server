#include "db/NativeArmorCatalog.h"
#include "protocol/RecoveredArmorSourceSlots.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <span>
#include <string_view>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif
namespace god2 {
namespace {
struct ReadScope {
    sqlite3* db;bool owned,committed=false;
    explicit ReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0){if(owned)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owned && !committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");committed=true;}
};
void append(std::vector<std::uint8_t>& bytes,std::span<const std::uint8_t> value) {
    if(value.size()>4096 || bytes.size()>16*1024*1024)throw DatabaseError("Armor catalog fingerprint bound");
    for(unsigned i=0;i<4;++i)bytes.push_back(static_cast<std::uint8_t>(value.size()>>(i*8)));
    bytes.insert(bytes.end(),value.begin(),value.end());
}
void append(std::vector<std::uint8_t>& bytes,std::string_view value){append(bytes,std::span(reinterpret_cast<const std::uint8_t*>(value.data()),value.size()));}
void number(std::vector<std::uint8_t>& bytes,std::uint64_t value){append(bytes,std::to_string(value));}
std::string sha(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))throw DatabaseError("Armor SHA256 provider unavailable");
    DWORD size=0,returned=0;NTSTATUS status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))throw DatabaseError("Armor SHA256 failed");
    std::string value;for(const auto byte:result){value+="0123456789abcdef"[byte>>4];value+="0123456789abcdef"[byte&15];}return value;
#else
    (void)bytes;throw DatabaseError("Qualified armor SHA256 backend unavailable");
#endif
}
}
std::string NativeArmorCatalog::schema() { return R"SQL(
CREATE TABLE native_armor_sources (
 family TEXT PRIMARY KEY CHECK(family IN ('EQU','TEQ')),
 source_file TEXT NOT NULL CHECK(source_file='Data2/Patch/Comm/gamedata.csvZ'),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256)=64),
 loader_rva TEXT NOT NULL CHECK(loader_rva='0x59420'),
 lookup_rva TEXT NOT NULL CHECK(lookup_rva='0x59a60'),
 row_count INTEGER NOT NULL CHECK(row_count IN (662,692)),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY')
);
CREATE TABLE native_armor_rows (
 family TEXT NOT NULL REFERENCES native_armor_sources(family),
 item_id INTEGER NOT NULL CHECK(item_id BETWEEN 1 AND 32767),
 source_record_index INTEGER NOT NULL CHECK(source_record_index BETWEEN 0 AND 691),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 parsed_sha256 TEXT NOT NULL CHECK(length(parsed_sha256)=64),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY'),
 PRIMARY KEY(family,item_id),
 UNIQUE(item_id),
 UNIQUE(family,source_record_index)
);
)SQL"; }
NativeArmorCatalog::NativeArmorCatalog(sqlite3* db):db_(db){if(!db_)throw DatabaseError("Null armor catalog connection");}
std::vector<NativeArmorRecord> NativeArmorCatalog::read() const {
    using sqlite_detail::Statement;ReadScope scope(db_);
    Statement counts(db_,"SELECT (SELECT count(*) FROM native_armor_sources),(SELECT count(*) FROM native_armor_rows)");
    if(!counts.row())throw DatabaseError("Armor source count unavailable");
    if(!counts.integer(0) && !counts.integer(1)){scope.finish();return {};}
    if(counts.integer(0)!=2 || counts.integer(1)!=1354)throw DatabaseError("Incomplete armor source catalog");
    std::vector<std::uint8_t> fingerprint;
    Statement sources(db_,"SELECT * FROM native_armor_sources ORDER BY family");
    for(const auto* family:{"EQU","TEQ"}) {
        if(!sources.row() || sources.text(0)!=family || sources.integer(7)!=(std::string_view(family)=="EQU"?692:662))throw DatabaseError("Armor source namespace/count mismatch");
        for(int i=0;i<10;++i) {if(i==7)number(fingerprint,sources.number<std::uint32_t>(i));else append(fingerprint,sources.text(i));}
    }
    if(sources.row())throw DatabaseError("Unexpected armor source");
    Statement rows(db_,"SELECT family,item_id,source_record_index,source_line,decoded_offset,record_sha256,raw_record,parsed_sha256,parsed_record,authority FROM native_armor_rows ORDER BY family,item_id");
    std::vector<NativeArmorRecord> result;
    while(rows.row()) {
        NativeArmorRecord row{rows.text(0),rows.number<std::uint16_t>(1),rows.number<std::uint32_t>(2),rows.number<std::uint32_t>(3),rows.number<std::uint32_t>(4),rows.text(5),rows.text(7),{}, {}};
        const auto raw=rows.blob(6,1,4095),parsed=rows.blob(8,396,396);
        row.raw_record.assign(raw.begin(),raw.end());row.parsed_record.assign(parsed.begin(),parsed.end());
        append(fingerprint,row.family);number(fingerprint,row.item_id);number(fingerprint,row.source_record_index);number(fingerprint,row.source_line);number(fingerprint,row.decoded_offset);
        append(fingerprint,row.record_sha256);append(fingerprint,raw);append(fingerprint,row.parsed_sha256);append(fingerprint,parsed);append(fingerprint,rows.text(9));
        result.push_back(std::move(row));
    }
    if(result.size()!=1354 || sha(fingerprint)!=catalog_sha256)throw DatabaseError("Native armor full catalog fingerprint mismatch");
    scope.finish();return result;
}
bool NativeArmorCatalog::populated() const {return !read().empty();}
std::optional<NativeArmorRecord> NativeArmorCatalog::lookup(std::uint16_t item) const {
    const auto rows=read();const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.item_id==item;});
    return found==rows.end()?std::nullopt:std::optional(*found);
}
std::optional<std::uint8_t> NativeArmorCatalog::equipment_slot(std::uint16_t item) const {
    const auto row=lookup(item);
    if(!row || row->parsed_record.size()!=396 || (row->parsed_record[0x11a]&4)==0)return {};
    return RecoveredArmorSourceSlots::find(item);
}

}
