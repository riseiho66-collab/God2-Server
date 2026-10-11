#include "db/NativeMapItemCatalog.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <string_view>

namespace god2 {
namespace {
std::vector<std::uint8_t> hex(std::string_view text) {
    auto digit=[](char c)->unsigned {return c<='9' ? c-'0' : c-'a'+10;};
    std::vector<std::uint8_t> result;
    for(std::size_t i=0;i<text.size();i+=2)result.push_back(static_cast<std::uint8_t>((digit(text[i])<<4)|digit(text[i+1])));
    return result;
}
const auto row_desc=hex(
    "4954454d5f49442cc3fea74fa54ebd582cb944a8e3bd73b8b92cb9cfbd5828a650b9cfc0c9a657c0c9292ca657bad92ca874b2cebde6a558bbf9aee62ca874b2cea65ea6acbbf9aee62cb479ad7a28bba1a9fa31292cb944a8e3aec4aa4728bba1a9fa32292cb8cbb3c6af53a9ca28bba1a9fa33292cb944a8e3aec4aa4728bba1a9fa34292cb944a8e3aec4aa4728bba1a9fa35292cb944a8e3aec4aa4728bba1a9fa36292caf53aec4b9cfbd582ca440afeba8cfa5ce2cbed4b0aba8cfa5ce2ca569a75fb8cbb3c62cb9efa74fa448a8cfa5ce2ca569a75fb35da977686f746b65792ca569a75fa5e6a9f62ca569a75fa5e1b1bc2cac4fa75fa9f1a44aaddcae772cac4fa75fb0efc57c2ca658a6a8a457adb12ca658a6a8a455adb1");
const std::array<NativeMapItemSource,2> pinned{{
    {5569,8236,617594,"6aad4d59bbbd41192acfc375d538ca93f1c2e454975e44f57114e7aedbae172e",
     hex("353536392c332c53706930313036392c35353036392caaf7f7b4ae71a661b0cfa661b9cf2c3130302c31302ca661b9cfb944a8e32caaf7f7b4ae71a661b0cfa661a7ceb9cf2c2c2c2c2c383432382c312c302c302c302c312c312c312c312c312c302c302c30"),
     3,hex("5370693031303639"),55069,hex("aaf7f7b4ae71a661b0cfa661b9cf"),hex("aaf7f7b4ae71a661b0cfa661a7ceb9cf"),8428,{1,0,0,0,1,1,1,1,1,0,0,0}},
    {5576,8243,618386,"6877e19719a222a3ad7bf45d1f61526d7364eb3b822890f15845d6a8ca216404",
     hex("353537362c302c53706930313037362c35353037362cb158b15ba550acc9a661b9cf2c302c302ca661b9cfb944a8e32cb158b15ba550acc9a661a7ceb9cf2c2c2c2c2c383432382c312c302c302c302c312c312c312c312c312c302c302c30"),
     0,hex("5370693031303736"),55076,hex("b158b15ba550acc9a661b9cf"),hex("b158b15ba550acc9a661a7ceb9cf"),8428,{1,0,0,0,1,1,1,1,1,0,0,0}}
}};
std::vector<std::uint8_t> blob(sqlite_detail::Statement& row,int index,std::size_t maximum=4096) {
    const auto bytes=row.blob(index,1,maximum);return {bytes.begin(),bytes.end()};
}
}
NativeMapItemCatalog::NativeMapItemCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null map item catalog connection");
}
std::optional<std::array<NativeMapItemSource,2>> NativeMapItemCatalog::read() const {
    // One SELECT provides a coherent SQLite read snapshot, including counts,
    // even on a read-only connection and inside a caller's existing transaction.
    // A seed row exposes orphan rows when the source table is empty.
    sqlite_detail::Statement rows(db_,
        "SELECT (SELECT count(*) FROM native_map_item_sources),(SELECT count(*) FROM native_map_item_rows),"
        "s.source_file,s.source_sha256,s.decoded_sha256,s.source_section,s.section_row_count,s.row_desc_line,"
        "s.row_desc_sha256,s.row_desc_raw,s.encoding,s.authority,"
        "r.item_id,r.source_file,r.source_line,r.decoded_offset,r.record_sha256,r.raw_record,r.category_code,"
        "r.resource_name,r.icon_id,r.name_bytes,r.description_bytes,r.effect_code,r.source_flags,r.authority "
        "FROM (SELECT 1) seed LEFT JOIN native_map_item_sources s ON 1=1 "
        "LEFT JOIN native_map_item_rows r ON r.source_file=s.source_file ORDER BY r.item_id");
    std::array<NativeMapItemSource,2> result{};std::size_t index=0;
    while(rows.row()) {
        if(rows.integer(0)==0 && rows.integer(1)==0) {
            if(index || rows.row())throw DatabaseError("Ambiguous empty map item catalog");
            return std::nullopt;
        }
        if(rows.integer(0)!=1 || rows.integer(1)!=2 || index>=result.size() ||
           rows.text(2)!=source_file || rows.text(3)!=source_sha256 || rows.text(4)!=decoded_sha256 ||
           rows.text(5)!="SPI" || rows.integer(6)!=737 || rows.integer(7)!=3 ||
           rows.text(8)!="ab84cb5beb35b1a0f753f657993d881673b3b59351049cdedf91c2f7fab79e34" ||
           blob(rows,9)!=row_desc || rows.text(10)!="CP950" || rows.text(11)!=authority ||
           rows.text(13)!=source_file || rows.text(25)!=authority)
            throw DatabaseError("Map item source provenance mismatch");
        auto& value=result[index];
        value.item_id=rows.number<std::uint16_t>(12);value.source_line=rows.number<std::uint32_t>(14);
        value.decoded_offset=rows.number<std::uint32_t>(15);value.record_sha256=rows.text(16);
        value.raw_record=blob(rows,17);value.category_code=rows.number<std::uint32_t>(18);
        value.resource_name=blob(rows,19);value.icon_id=rows.number<std::uint16_t>(20);
        value.name_bytes=blob(rows,21);value.description_bytes=blob(rows,22);
        value.effect_code=rows.number<std::uint16_t>(23);
        const auto flags=rows.blob(24,12,12);std::copy(flags.begin(),flags.end(),value.source_flags.begin());
        if(value!=pinned[index++])throw DatabaseError("Map item source row differs from pin");
    }
    if(index!=2)throw DatabaseError("Incomplete map item catalog");
    return result;
}
bool NativeMapItemCatalog::is_imported() const {return read().has_value();}
bool NativeMapItemCatalog::populated() const {return read().has_value();}
bool NativeMapItemCatalog::contains(std::uint16_t item_id) const {return lookup(item_id).has_value();}
std::optional<NativeMapItemSource> NativeMapItemCatalog::lookup(std::uint16_t item_id) const {
    const auto records=read();
    if(records)for(const auto& row:*records)if(row.item_id==item_id)return row;
    return std::nullopt;
}
}
