#include "db/NativeSkillBookSourceCatalog.h"
#include "db/SqliteSupport.h"
#include <algorithm>

namespace god2 {
namespace {
std::string text(sqlite_detail::Statement& row,int column) {
    auto value=row.text(column);
    if(value.empty() || value.find('\0')!=std::string::npos)
        throw DatabaseError("Invalid shared skill book source provenance text");
    return value;
}
std::string sha(sqlite_detail::Statement& row,int column) {
    auto value=text(row,column);
    if(value.size()!=64 || !std::all_of(value.begin(),value.end(),[](unsigned char c){
        return (c>='0' && c<='9') || (c>='a' && c<='f');}))
        throw DatabaseError("Invalid shared skill book source SHA-256 text");
    return value;
}
}
NativeSkillBookSourceCatalog::NativeSkillBookSourceCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null shared skill book source connection");
}
const char* NativeSkillBookSourceCatalog::schema_sql() noexcept {
    return R"SQL(CREATE TABLE native_skill_book_source_records (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index)='integer' AND source_record_index>=0),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(typeof(decoded_offset)='integer' AND decoded_offset>=0),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id>=0),
 record_sha256 TEXT NOT NULL CHECK(typeof(record_sha256)='text' AND length(record_sha256)=64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 PRIMARY KEY(dataset_id,source_record_index),
 UNIQUE(dataset_id,item_id)
);
)SQL";
}
std::optional<NativeSkillBookSourceRecord> NativeSkillBookSourceCatalog::lookup(
    const std::string& dataset,std::int64_t item_id) const {return read(dataset,item_id,false);}
std::optional<NativeSkillBookSourceRecord> NativeSkillBookSourceCatalog::lookup_by_index(
    const std::string& dataset,std::int64_t index) const {return read(dataset,index,true);}
std::optional<NativeSkillBookSourceRecord> NativeSkillBookSourceCatalog::read(
    const std::string& dataset,std::int64_t key,bool by_index) const {
    if(dataset.empty() || dataset.find('\0')!=std::string::npos || key<0)
        throw DatabaseError("Invalid shared skill book source selector");
    const char* select_item=
        "SELECT b.dataset_id,b.source_record_index,b.source_line,b.decoded_offset,b.item_id,"
        "b.record_sha256,b.raw_record,s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,"
        "s.native_image_sha256,s.source_section,s.loader_rva,s.lookup_rva,s.row_count "
        "FROM main.native_skill_book_source_records b LEFT JOIN main.native_data_sources s ON s.dataset_id=b.dataset_id "
        "WHERE b.dataset_id=? AND b.item_id=? LIMIT 2";
    const char* select_index=
        "SELECT b.dataset_id,b.source_record_index,b.source_line,b.decoded_offset,b.item_id,"
        "b.record_sha256,b.raw_record,s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,"
        "s.native_image_sha256,s.source_section,s.loader_rva,s.lookup_rva,s.row_count "
        "FROM main.native_skill_book_source_records b LEFT JOIN main.native_data_sources s ON s.dataset_id=b.dataset_id "
        "WHERE b.dataset_id=? AND b.source_record_index=? LIMIT 2";
    sqlite_detail::Statement row(db_,by_index?select_index:select_item);
    row.bind(1,dataset);row.bind(2,key);
    if(!row.row())return std::nullopt;
    NativeSkillBookSourceRecord result;
    const auto row_dataset=text(row,0);
    result.source_record_index=row.integer(1);result.source_line=row.integer(2);
    result.decoded_offset=row.integer(3);result.item_id=row.integer(4);
    result.record_sha256=sha(row,5);
    const auto raw=row.blob(6,1,4095);result.raw_record.assign(raw.begin(),raw.end());
    auto& source=result.source;
    source.dataset_id=text(row,7);source.source_path=text(row,8);
    source.source_sha256=sha(row,9);source.decoded_sha256=sha(row,10);source.native_image_sha256=sha(row,11);
    source.source_section=text(row,12);source.loader_rva=text(row,13);source.lookup_rva=text(row,14);
    source.row_count=row.integer(15);
    // Actual source count, not a hardcoded build count in the shared reader.
    // This does not pin a particular build/section or prove complete population:
    // the actual provider/import owner must compare all rows/provenance/hash.
    if(row_dataset!=dataset || source.dataset_id!=dataset || source.row_count<1 || source.row_count>32767 ||
       result.source_record_index<0 || result.source_record_index>=source.row_count || result.source_line<=0 ||
       result.decoded_offset<0 || result.item_id<0 ||
       (by_index?result.source_record_index:result.item_id)!=key)
        throw DatabaseError("Shared skill book source row/provenance mismatch");
    if(row.row())throw DatabaseError("Duplicate shared skill book source lookup");
    return result;
}
}
