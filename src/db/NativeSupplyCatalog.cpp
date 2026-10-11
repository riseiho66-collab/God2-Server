#include "db/NativeSupplyCatalog.h"
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
    if(value.size()>4096 || bytes.size()>16*1024*1024)throw DatabaseError("MED02 catalog fingerprint bound");
    for(unsigned i=0;i<4;++i)bytes.push_back(static_cast<std::uint8_t>(value.size()>>(i*8)));
    bytes.insert(bytes.end(),value.begin(),value.end());
}
void append(std::vector<std::uint8_t>& bytes,std::string_view value){append(bytes,std::span(reinterpret_cast<const std::uint8_t*>(value.data()),value.size()));}
void number(std::vector<std::uint8_t>& bytes,std::uint64_t value){append(bytes,std::to_string(value));}
std::string sha(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))throw DatabaseError("MED02 SHA256 provider unavailable");
    DWORD size=0,returned=0;NTSTATUS status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))throw DatabaseError("MED02 SHA256 failed");
    std::string value;for(const auto byte:result){value+="0123456789abcdef"[byte>>4];value+="0123456789abcdef"[byte&15];}return value;
#else
    (void)bytes;throw DatabaseError("Qualified MED02 SHA256 backend unavailable");
#endif
}
}
NativeSupplyCatalog::NativeSupplyCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null MED02 catalog connection");
}
std::vector<NativeSupplyDeclaration> NativeSupplyCatalog::read() const {
    using sqlite_detail::Statement;
    ReadScope scope(db_);
    // This specialized table has one qualified dataset. Renaming its dataset
    // must not make corrupt rows look absent and enable a diagnostic fallback.
    Statement count(db_,"SELECT count(*) FROM native_med02_recovery_declarations");
    if(!count.row())throw DatabaseError("MED02 source count unavailable");
    const auto total=count.number<std::uint32_t>(0);
    Statement source(db_,"SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
        "source_section,loader_rva,lookup_rva,row_count FROM native_data_sources WHERE dataset_id=?");
    source.bind(1,std::string(current_dataset_id));
    if(!source.row()) {
        if(total)throw DatabaseError("Orphaned MED02 recovery declarations");
        scope.finish();return {};
    }
    if(total!=71 || source.number<std::uint32_t>(8)!=100)throw DatabaseError("Incomplete MED02 recovery declarations");
    std::vector<std::uint8_t> fingerprint;
    for(int column=0;column<8;++column)append(fingerprint,source.text(column));
    number(fingerprint,source.number<std::uint32_t>(8));
    if(source.row())throw DatabaseError("Duplicate MED02 source");
    Statement rows(db_,"SELECT dataset_id,source_record_index,source_line,item_id,record_sha256,raw_record,"
        "tooltip_bytes,declared_hp,declared_mp,normal_use,hotkey_allowed FROM native_med02_recovery_declarations "
        "WHERE dataset_id=? ORDER BY source_record_index");
    rows.bind(1,std::string(current_dataset_id));
    std::vector<NativeSupplyDeclaration> result;
    while(rows.row()) {
        if(result.size()>=71)throw DatabaseError("Too many MED02 recovery declarations");
        NativeSupplyDeclaration row;
        row.source_record_index=rows.number<std::uint8_t>(1);
        row.source_line=rows.number<std::uint32_t>(2);
        row.item_id=rows.number<std::uint16_t>(3);
        row.record_sha256=rows.text(4);
        const auto raw=rows.blob(5,1,4095),tooltip=rows.blob(6,1,255);
        row.raw_record.assign(raw.begin(),raw.end());row.tooltip_bytes.assign(tooltip.begin(),tooltip.end());
        row.declared_hp=rows.number<std::uint32_t>(7);row.declared_mp=rows.number<std::uint32_t>(8);
        if(row.source_record_index>99 || row.source_line!=6354+row.source_record_index ||
           row.item_id!=3101+row.source_record_index || row.record_sha256.size()!=64 ||
           row.record_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos ||
           row.declared_hp>4000 || row.declared_mp>4000 || (!row.declared_hp && !row.declared_mp) ||
           rows.number<std::uint8_t>(9)!=1 || rows.number<std::uint8_t>(10)!=1)
            throw DatabaseError("Invalid MED02 recovery declaration");
        append(fingerprint,rows.text(0));number(fingerprint,static_cast<std::uint64_t>(row.source_record_index));
        number(fingerprint,static_cast<std::uint64_t>(row.source_line));number(fingerprint,row.item_id);
        append(fingerprint,row.record_sha256);append(fingerprint,raw);append(fingerprint,tooltip);
        number(fingerprint,row.declared_hp);number(fingerprint,row.declared_mp);
        number(fingerprint,rows.number<std::uint8_t>(9));number(fingerprint,rows.number<std::uint8_t>(10));
        result.push_back(std::move(row));
    }
    if(result.size()!=71 || sha(fingerprint)!=current_catalog_sha256)
        throw DatabaseError("Native MED02 full catalog fingerprint mismatch");
    scope.finish();return result;
}
bool NativeSupplyCatalog::is_imported() const {return !read().empty();}
std::optional<NativeSupplyDeclaration> NativeSupplyCatalog::lookup(std::uint16_t item_id) const {
    if(!item_id)throw DatabaseError("Invalid MED02 item selector");
    const auto rows=read();
    const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.item_id==item_id;});
    return found==rows.end()?std::nullopt:std::optional(*found);
}
}
