#include "cn/assets/CnNativeSkillBookSourceImport.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <utility>

namespace god2::cn {
namespace {
using sqlite_detail::Statement;
using BookSource=CnNativeSkillBookBindings;
void require_base(sqlite3* db) {
    if(!db)throw DatabaseError("Null CN book source connection");
    Statement migration(db,"SELECT name FROM main.schema_migrations WHERE version=5 LIMIT 2");
    if(!migration.row() || migration.text(0)!="native_skill_catalog" || migration.row())
        throw DatabaseError("CN book source requires existing native source schema");
    Statement foreign_keys(db,"PRAGMA foreign_keys");
    if(!foreign_keys.row() || foreign_keys.integer(0)!=1 || foreign_keys.row())
        throw DatabaseError("CN book source requires enforced foreign keys");
}
std::string schema_identity(std::string text) {
    // SQLite omits the terminal delimiter in sqlite_master.sql. Only this
    // delimiter/terminal ASCII whitespace is ignored; constraints/formatting
    // of a preexisting different schema are never silently accepted.
    constexpr char whitespace[]=" \t\r\n";
    const auto trim=[&]{const auto last=text.find_last_not_of(whitespace);
        if(last==std::string::npos)text.clear();else text.resize(last+1);};
    trim();if(!text.empty() && text.back()==';'){text.pop_back();trim();}
    return text;
}
bool existing_schema(sqlite3* db) {
    Statement row(db,"SELECT type,sql FROM main.sqlite_master WHERE name='native_skill_book_source_records' LIMIT 2");
    if(!row.row())return false;
    if(row.text(0)!="table" || schema_identity(row.text(1))!=
       schema_identity(NativeSkillBookSourceCatalog::schema_sql()) || row.row())
        throw DatabaseError("Existing shared book source schema differs");
    return true;
}
bool existing_source(sqlite3* db,const NativeSkillSource& expected) {
    Statement row(db,"SELECT dataset_id,source_path,source_sha256,decoded_sha256,"
        "native_image_sha256,source_section,loader_rva,lookup_rva,row_count "
        "FROM main.native_data_sources WHERE dataset_id=? LIMIT 2");
    row.bind(1,expected.dataset_id);if(!row.row())return false;
    const NativeSkillSource actual{row.text(0),row.text(1),row.text(2),row.text(3),
        row.text(4),row.text(5),row.text(6),row.text(7),row.integer(8)};
    if(actual!=expected || row.row())throw DatabaseError("CN book source metadata conflicts");
    return true;
}
std::int64_t row_count(sqlite3* db,const std::string& dataset) {
    Statement row(db,"SELECT COUNT(*) FROM main.native_skill_book_source_records WHERE dataset_id=?");
    row.bind(1,dataset);if(!row.row())throw DatabaseError("CN book source row count unavailable");
    const auto count=row.integer(0);
    if(count<0 || row.row())throw DatabaseError("CN book source row count invalid");
    return count;
}
void insert_source(sqlite3* db,const NativeSkillSource& source) {
    Statement row(db,"INSERT INTO main.native_data_sources(dataset_id,source_path,source_sha256,"
        "decoded_sha256,native_image_sha256,source_section,loader_rva,lookup_rva,row_count) "
        "VALUES(?,?,?,?,?,?,?,?,?)");
    row.bind(1,source.dataset_id);row.bind(2,source.source_path);row.bind(3,source.source_sha256);
    row.bind(4,source.decoded_sha256);row.bind(5,source.native_image_sha256);
    row.bind(6,source.source_section);row.bind(7,source.loader_rva);row.bind(8,source.lookup_rva);
    row.bind(9,source.row_count);row.done();
    if(sqlite3_changes(db)!=1)throw DatabaseError("CN book source metadata was not inserted");
}
void insert_record(sqlite3* db,const NativeSkillBookSourceRecord& record) {
    Statement row(db,"INSERT INTO main.native_skill_book_source_records(dataset_id,source_record_index,"
        "source_line,decoded_offset,item_id,record_sha256,raw_record) VALUES(?,?,?,?,?,?,?)");
    row.bind(1,record.source.dataset_id);row.bind(2,record.source_record_index);
    row.bind(3,record.source_line);row.bind(4,record.decoded_offset);row.bind(5,record.item_id);
    row.bind(6,record.record_sha256);row.bind_blob(7,record.raw_record);row.done();
    if(sqlite3_changes(db)!=1)throw DatabaseError("CN book source record was not inserted");
}
}
NativeSkillSource CnNativeSkillBookSourceImport::expected_source() {
    // RVAs of the retained actual CN42CFB0 SKB parser and4D2BB0 selector
    // lookup. They qualify this raw source, not server learning eligibility.
    return NativeSkillSource{"cn-native-skill-books-582f-v1",BookSource::resource_path,
        BookSource::encoded_sha256,BookSource::decoded_sha256,BookSource::client_sha256,
        "SKB","0x2cfb0","0xd2bb0",static_cast<std::int64_t>(BookSource::book_count)};
}
void CnNativeSkillBookSourceImport::require_schema(sqlite3* db) {
    require_base(db);
    if(!existing_schema(db))throw DatabaseError("Explicit shared book source schema is absent");
}
void CnNativeSkillBookSourceImport::install_schema(sqlite3* db) {
    if(!db || !sqlite3_get_autocommit(db))
        throw DatabaseError("CN book source schema cannot borrow a transaction");
    sqlite_detail::Transaction transaction(db);require_base(db);
    if(!existing_schema(db))sqlite_detail::execute(db,NativeSkillBookSourceCatalog::schema_sql());
    require_schema(db);transaction.commit();
}
CnNativeSkillBookSourceImport::Result CnNativeSkillBookSourceImport::import_actual_source(
    sqlite3* db,std::shared_ptr<const BookSource> native) {
    if(!db || !native || !native->current() || !sqlite3_get_autocommit(db))
        throw DatabaseError("CN book source import requires current actual source and own transaction");
    const auto source=expected_source();
    // Fully materialize exact owned records BEFORE SQL. The factory pins full
    // encoded/decoded bytes and actual raw-line SHA, including original CRLF.
    // No JSON fixture, alias inversion or guessed native parsed image enters.
    std::array<std::optional<NativeSkillBookSourceRecord>,BookSource::book_count> records;
    std::optional<BookSource::Source> epoch;
    std::size_t count=0;
    for(std::uint16_t item=6501;item<=6900;++item) {
        auto book=native->lookup_item(item);
        if(!book){if(!native->current())throw DatabaseError("CN book source expired");continue;}
        const auto index=book->source_record_index;
        if(index>=records.size() || records[index] || book->item_id!=item ||
           book->source_line!=9442+index || !book->source.actual_revision ||
           book->source.actual_client_sha256!=BookSource::client_sha256 ||
           (epoch && *epoch!=book->source) || book->raw_line.size()<2 || book->raw_line.size()>4095 ||
           book->raw_line[book->raw_line.size()-2]!='\r' || book->raw_line.back()!='\n')
            throw DatabaseError("CN book source record qualification differs");
        if(!epoch)epoch=book->source;
        records[index]=NativeSkillBookSourceRecord{source,index,book->source_line,
            book->decoded_offset,item,std::move(book->record_sha256),std::move(book->raw_line)};
        ++count;
    }
    std::int64_t offset=739107; // Immediately after actual SKB,386 CRLF header.
    for(const auto& record:records) {
        if(!record || record->decoded_offset!=offset)
            throw DatabaseError("CN book source ordered raw block is incomplete");
        offset+=static_cast<std::int64_t>(record->raw_record.size());
    }
    if(count!=BookSource::book_count || offset!=806862 || !native->current())
        throw DatabaseError("CN book source changed during complete materialization");

    sqlite_detail::Transaction transaction(db);require_schema(db);
    const bool present=existing_source(db,source);
    const auto stored_count=row_count(db,source.dataset_id);
    if((present && stored_count!=source.row_count) || (!present && stored_count!=0))
        throw DatabaseError("CN book source will not overwrite partial or orphan data");
    if(!native->current())throw DatabaseError("CN book source changed before insertion");
    if(!present){insert_source(db,source);for(const auto& record:records)insert_record(db,*record);}
    if(!existing_source(db,source) || row_count(db,source.dataset_id)!=source.row_count)
        throw DatabaseError("CN book source stored envelope differs");
    const NativeSkillBookSourceCatalog reader(db);
    for(const auto& expected:records) {
        const auto by_item=reader.lookup(source.dataset_id,expected->item_id);
        const auto by_index=reader.lookup_by_index(source.dataset_id,expected->source_record_index);
        if(!by_item || !by_index || *by_item!=*expected || *by_index!=*expected)
            throw DatabaseError("CN book source exact stored record differs");
    }
    if(!native->current())throw DatabaseError("CN book source changed before commit");
    transaction.commit();return present?Result::AlreadyPresent:Result::Inserted;
}
}
