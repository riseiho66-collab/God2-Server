#include "db/NativeEnemyDisplayCatalog.h"
#include "db/SqliteSupport.h"

#include <algorithm>
#include <limits>
#include <array>
#include <span>
#include <set>
#include <string_view>
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
struct CatalogReadScope {
    sqlite3* db;bool owned,committed=false;
    explicit CatalogReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0){if(owned)sqlite_detail::execute(db,"BEGIN");}
    ~CatalogReadScope(){if(owned&&!committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");committed=true;}
};
void append_catalog(std::vector<std::uint8_t>& output,std::span<const std::uint8_t> value) {
    if(value.size()>4096 || output.size()>16*1024*1024)throw DatabaseError("Enemy catalog fingerprint bound");
    for(unsigned b=0;b<4;++b)output.push_back(static_cast<std::uint8_t>(value.size()>>(8*b)));
    output.insert(output.end(),value.begin(),value.end());
}
void append_catalog(std::vector<std::uint8_t>& output,std::string_view value){append_catalog(output,std::span(reinterpret_cast<const std::uint8_t*>(value.data()),value.size()));}
void catalog_number(std::vector<std::uint8_t>& output,std::uint64_t value){append_catalog(output,std::to_string(value));}
std::string catalog_sha(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))throw DatabaseError("Enemy catalog SHA256 provider unavailable");
    DWORD size=0,returned=0;auto status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))throw DatabaseError("Enemy catalog SHA256 failed");
    std::string value;for(const auto byte:result){value+="0123456789abcdef"[byte>>4];value+="0123456789abcdef"[byte&15];}return value;
#else
    (void)bytes;throw DatabaseError("Qualified enemy catalog SHA256 backend unavailable");
#endif
}
bool valid_text(const std::string& value) {
    return !value.empty() && value.find('\0')==std::string::npos;
}
std::string required_text(sqlite_detail::Statement& row,int column) {
    auto value=row.text(column);
    if(!valid_text(value)) throw DatabaseError("Invalid enemy display provenance text");
    return value;
}
std::string required_sha(sqlite_detail::Statement& row,int column) {
    auto value=row.text(column);
    const auto hex=[](unsigned char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    };
    if(value.size()!=64 || !std::all_of(value.begin(),value.end(),hex))
        throw DatabaseError("Invalid enemy display SHA-256");
    return value;
}
}

NativeEnemyDisplayCatalog::NativeEnemyDisplayCatalog(sqlite3* db):db_(db) {
    if(!db_) throw DatabaseError("Null enemy display catalog connection");
}

NativeEnemyDisplayCatalog::Counts NativeEnemyDisplayCatalog::counts() const {
    using sqlite_detail::Statement;
    CatalogReadScope scope(db_);
    Statement total(db_,"SELECT count(*) FROM native_enemy_display_catalog");
    if(!total.row())throw DatabaseError("Enemy catalog count unavailable");
    const auto all=total.number<std::uint32_t>(0);
    Statement source(db_,"SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
        "source_section,loader_rva,lookup_rva,row_count FROM native_data_sources WHERE dataset_id=?");
    source.bind(1,std::string(current_dataset_id));
    if(!source.row()) {
        if(all)throw DatabaseError("Orphaned or renamed enemy display catalog");
        scope.finish();return {};
    }
    if(all!=7815 || source.number<std::uint32_t>(8)!=7815)throw DatabaseError("Incomplete enemy display catalog");
    std::vector<std::uint8_t> fingerprint;
    for(int c=0;c<8;++c)append_catalog(fingerprint,required_text(source,c));
    catalog_number(fingerprint,source.number<std::uint32_t>(8));
    if(source.row())throw DatabaseError("Duplicate enemy catalog source");
    Statement rows(db_,"SELECT dataset_id,source_record_index,source_line,source_offset,record_sha256,"
        "raw_record,area_generation,area,scene,ordinal,lookup_visible,source_label,name_bytes "
        "FROM native_enemy_display_catalog ORDER BY source_record_index");
    Counts out;std::set<std::pair<std::uint32_t,std::uint32_t>> groups;
    while(rows.row()) {
        if(out.records>=7815 || required_text(rows,0)!=current_dataset_id || rows.number<std::uint32_t>(1)!=out.records)
            throw DatabaseError("Enemy catalog sequence/dataset mismatch");
        const auto area=rows.number<std::uint32_t>(7),scene=rows.number<std::uint32_t>(8),visible=rows.number<std::uint32_t>(10);
        if(area>16 || scene>65535 || visible>1)throw DatabaseError("Enemy catalog namespace/visibility bounds");
        append_catalog(fingerprint,rows.text(0));
        for(int c=1;c<=3;++c)catalog_number(fingerprint,rows.number<std::uint64_t>(c));
        append_catalog(fingerprint,required_sha(rows,4));append_catalog(fingerprint,rows.blob(5,1,2047));
        for(int c=6;c<=11;++c)catalog_number(fingerprint,rows.number<std::uint64_t>(c));
        append_catalog(fingerprint,rows.blob(12,1,15));
        ++out.records;if(visible){++out.lookup_visible;groups.emplace(area,scene);}
    }
    out.groups=static_cast<std::uint32_t>(groups.size());
    if(out!=Counts{7815,7791,96} || catalog_sha(fingerprint)!=current_catalog_sha256)
        throw DatabaseError("Native enemy full catalog fingerprint mismatch");
    scope.finish();return out;
}

std::optional<NativeEnemyDisplayRecord> NativeEnemyDisplayCatalog::lookup(
    const std::string& dataset_id,std::int64_t area,std::int64_t scene,std::int64_t ordinal) const {
    if(!valid_text(dataset_id) ||
       dataset_id.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
       area<0 || area>16 || scene<0 || scene>65535 || ordinal<1 || ordinal>7815)
        throw DatabaseError("Invalid enemy display selector");
    sqlite_detail::Statement row(db_,
        "SELECT c.dataset_id,c.source_record_index,c.source_line,c.source_offset,"
        "c.record_sha256,c.raw_record,c.area_generation,c.area,c.scene,c.ordinal,"
        "c.lookup_visible,c.source_label,c.name_bytes,"
        "s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,s.native_image_sha256,"
        "s.source_section,s.loader_rva,s.lookup_rva,s.row_count "
        "FROM native_enemy_display_catalog c LEFT JOIN native_data_sources s ON s.dataset_id=c.dataset_id "
        "WHERE c.dataset_id=? AND c.area=? AND c.scene=? AND c.ordinal=? AND c.lookup_visible=1 LIMIT 2");
    row.bind(1,dataset_id);row.bind(2,area);row.bind(3,scene);row.bind(4,ordinal);
    if(!row.row()) return std::nullopt;
    NativeEnemyDisplayRecord result;
    if(required_text(row,0)!=dataset_id) throw DatabaseError("Enemy display dataset mismatch");
    result.source_record_index=row.integer(1);
    result.source_line=row.integer(2);
    result.source_offset=row.integer(3);
    result.record_sha256=required_sha(row,4);
    const auto raw=row.blob(5,1,2047);
    result.raw_record.assign(raw.begin(),raw.end());
    result.area_generation=row.integer(6);
    result.area=row.integer(7);
    result.scene=row.integer(8);
    result.ordinal=row.integer(9);
    if(row.integer(10)!=1) throw DatabaseError("Enemy display lookup visibility mismatch");
    result.source_label=row.integer(11);
    const auto name=row.blob(12,1,15);
    result.name_bytes.assign(name.begin(),name.end());
    if(result.source_record_index<0 || result.source_record_index>7814 ||
       result.source_line<1 || result.source_offset<0 ||
       result.area_generation<1 || result.area_generation>16 ||
       result.area!=area || result.scene!=scene || result.ordinal!=ordinal ||
       result.source_label<0 || result.source_label>2147483647)
        throw DatabaseError("Invalid enemy display record bounds");
    auto& source=result.source;
    source.dataset_id=required_text(row,13);
    source.source_path=required_text(row,14);
    source.source_sha256=required_sha(row,15);
    source.decoded_sha256=required_sha(row,16);
    source.native_image_sha256=required_sha(row,17);
    source.source_section=required_text(row,18);
    source.loader_rva=required_text(row,19);
    source.lookup_rva=required_text(row,20);
    source.row_count=row.integer(21);
    if(source.dataset_id!=dataset_id || source.row_count!=7815 ||
       result.source_record_index>=source.row_count || source.source_section!="EnyName")
        throw DatabaseError("Invalid enemy display source");
    if(row.row()) throw DatabaseError("Duplicate enemy display lookup");
    return result;
}

std::optional<NativeEnemyDisplayCatalog::Scene> NativeEnemyDisplayCatalog::read_scene(
        std::int64_t area,std::int64_t scene) const {
    if(area<0 || area>16 || scene<0 || scene>65535)
        throw DatabaseError("Invalid enemy scene selector");
    CatalogReadScope scope(db_);
    // counts() predates this additive main-only API. Reject shadows before its
    // unqualified reads so qualification and the selected rows share a source.
    sqlite_detail::Statement shadows(db_,
        "SELECT 1 FROM temp.sqlite_master WHERE name IN ('native_data_sources','native_enemy_display_catalog') "
        "OR tbl_name IN ('native_data_sources','native_enemy_display_catalog') LIMIT 1");
    if(shadows.row())throw DatabaseError("Enemy scene catalog temp shadow");
    // Missing main schema must fail, even if an attached database exposes
    // empty tables which the older unqualified counts() could otherwise use.
    sqlite_detail::Statement main_tables(db_,
        "SELECT 1 FROM main.native_enemy_display_catalog,main.native_data_sources LIMIT 0");
    if(main_tables.row())throw DatabaseError("Unexpected enemy scene schema row");
    const auto complete=counts();
    if(complete==Counts{}) {scope.finish();return std::nullopt;}
    if(complete!=Counts{7815,7791,96})throw DatabaseError("Enemy scene catalog incomplete");

    Scene result;
    result.area=area;result.scene=scene;result.catalog_sha256=current_catalog_sha256;
    sqlite_detail::Statement source(db_,
        "SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
        "source_section,loader_rva,lookup_rva,row_count FROM main.native_data_sources WHERE dataset_id=?");
    source.bind(1,std::string(current_dataset_id));
    if(!source.row())throw DatabaseError("Qualified enemy scene source missing");
    auto& origin=result.source;
    origin.dataset_id=required_text(source,0);origin.source_path=required_text(source,1);
    origin.source_sha256=required_sha(source,2);origin.decoded_sha256=required_sha(source,3);
    origin.native_image_sha256=required_sha(source,4);origin.source_section=required_text(source,5);
    origin.loader_rva=required_text(source,6);origin.lookup_rva=required_text(source,7);
    origin.row_count=source.integer(8);
    if(origin.dataset_id!=current_dataset_id || origin.source_path!="Data2/Patch/Comm/gamedata.csvZ" ||
       origin.source_sha256!="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731" ||
       origin.decoded_sha256!="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815" ||
       origin.native_image_sha256!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
       origin.source_section!="EnyName" || origin.loader_rva!="0x5a1a0" ||
       origin.lookup_rva!="0x5a0a0" || origin.row_count!=7815 || source.row())
        throw DatabaseError("Enemy scene source identity mismatch");
    sqlite_detail::Statement rows(db_,
        "SELECT dataset_id,source_record_index,source_line,source_offset,record_sha256,raw_record,"
        "area_generation,area,scene,ordinal,lookup_visible,source_label,name_bytes "
        "FROM main.native_enemy_display_catalog WHERE dataset_id=? AND area=? AND scene=? "
        "AND lookup_visible=1 ORDER BY ordinal");
    rows.bind(1,std::string(current_dataset_id));rows.bind(2,area);rows.bind(3,scene);
    while(rows.row()) {
        if(result.records.size()>=7815 || required_text(rows,0)!=current_dataset_id)
            throw DatabaseError("Enemy scene record count/dataset mismatch");
        NativeEnemyDisplayRecord record;
        record.source=origin;record.source_record_index=rows.integer(1);
        record.source_line=rows.integer(2);record.source_offset=rows.integer(3);
        record.record_sha256=required_sha(rows,4);
        const auto raw=rows.blob(5,1,2047);record.raw_record.assign(raw.begin(),raw.end());
        record.area_generation=rows.integer(6);record.area=rows.integer(7);
        record.scene=rows.integer(8);record.ordinal=rows.integer(9);
        if(rows.integer(10)!=1)throw DatabaseError("Enemy scene row is not lookup visible");
        record.source_label=rows.integer(11);
        const auto name=rows.blob(12,1,15);record.name_bytes.assign(name.begin(),name.end());
        if(record.source_record_index<0 || record.source_record_index>=origin.row_count ||
           record.source_line<1 || record.source_offset<0 || record.area_generation<1 || record.area_generation>16 ||
           record.area!=area || record.scene!=scene || record.ordinal!=static_cast<std::int64_t>(result.records.size()+1) ||
           record.source_label<0 || record.source_label>2147483647 ||
           (!result.records.empty() && (record.source_record_index<=result.records.back().source_record_index ||
               record.area_generation!=result.records.back().area_generation)))
            throw DatabaseError("Enemy scene record order/provenance mismatch");
        result.records.push_back(std::move(record));
    }
    scope.finish();return result;
}
}
