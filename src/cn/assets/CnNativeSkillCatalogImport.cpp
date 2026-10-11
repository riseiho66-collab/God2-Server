#include "cn/assets/CnNativeSkillCatalogImport.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include "db/SqliteSupport.h"
#include <utility>

namespace god2::cn {
namespace {
using Native=god2cn::CnNativeSkillCatalog;
using sqlite_detail::Statement;

void require_existing_schema(sqlite3* db) {
    Statement migration(db,"SELECT name FROM schema_migrations WHERE version=5 LIMIT 2");
    if(!migration.row() || migration.text(0)!="native_skill_catalog" || migration.row())
        throw DatabaseError("CN skill import requires the existing native skill catalog migration");
    Statement foreign_keys(db,"PRAGMA foreign_keys");
    if(!foreign_keys.row() || foreign_keys.integer(0)!=1 || foreign_keys.row())
        throw DatabaseError("CN skill import requires enforced foreign keys");
}

bool existing_source(sqlite3* db,const NativeSkillSource& expected) {
    Statement row(db,"SELECT dataset_id,source_path,source_sha256,decoded_sha256,"
        "native_image_sha256,source_section,loader_rva,lookup_rva,row_count "
        "FROM native_data_sources WHERE dataset_id=? LIMIT 2");
    row.bind(1,expected.dataset_id);
    if(!row.row())return false;
    const NativeSkillSource actual{row.text(0),row.text(1),row.text(2),row.text(3),
        row.text(4),row.text(5),row.text(6),row.text(7),row.integer(8)};
    if(actual!=expected || row.row())
        throw DatabaseError("CN skill import source metadata conflicts with retained data");
    return true;
}

std::int64_t row_count(sqlite3* db,const std::string& dataset) {
    Statement row(db,"SELECT COUNT(*) FROM native_skill_catalog WHERE dataset_id=?");
    row.bind(1,dataset);
    if(!row.row())throw DatabaseError("CN skill import row count unavailable");
    const auto count=row.integer(0);
    if(count<0 || row.row())throw DatabaseError("CN skill import invalid row count");
    return count;
}

void insert_source(sqlite3* db,const NativeSkillSource& source) {
    Statement row(db,"INSERT INTO native_data_sources(dataset_id,source_path,source_sha256,"
        "decoded_sha256,native_image_sha256,source_section,loader_rva,lookup_rva,row_count) "
        "VALUES(?,?,?,?,?,?,?,?,?)");
    row.bind(1,source.dataset_id);row.bind(2,source.source_path);
    row.bind(3,source.source_sha256);row.bind(4,source.decoded_sha256);
    row.bind(5,source.native_image_sha256);row.bind(6,source.source_section);
    row.bind(7,source.loader_rva);row.bind(8,source.lookup_rva);row.bind(9,source.row_count);
    row.done();
    if(sqlite3_changes(db)!=1)throw DatabaseError("CN skill import source was not inserted");
}

void insert_record(sqlite3* db,const NativeSkillRecord& record) {
    Statement row(db,"INSERT INTO native_skill_catalog(dataset_id,source_record_index,source_offset,"
        "record_sha256,raw_record,kind,definition_id) VALUES(?,?,?,?,?,?,?)");
    row.bind(1,record.source.dataset_id);row.bind(2,record.source_record_index);
    row.bind(3,record.source_offset);row.bind(4,record.record_sha256);
    row.bind_blob(5,record.raw_record);row.bind(6,record.kind);row.bind(7,record.definition_id);
    row.done();
    if(sqlite3_changes(db)!=1)throw DatabaseError("CN skill import definition was not inserted");
}
}

CnNativeSkillCatalogImport::Result CnNativeSkillCatalogImport::import_actual_source(
    sqlite3* db,std::shared_ptr<const Native> native) {
    if(!db || !native || !native->current())
        throw DatabaseError("CN skill import requires an actual current pinned source");
    if(!sqlite3_get_autocommit(db))
        throw DatabaseError("CN skill import cannot borrow an enclosing transaction");
    const auto source=CnSharedSkillCatalog::expected_source();
    // Own every definition/hash before touching SQLite. No JSON/import fixture,
    // same-number TW record or synthesized parsed-field projection is accepted.
    std::vector<NativeSkillRecord> records;
    records.reserve(static_cast<std::size_t>(source.row_count));
    for(std::size_t kind=0;kind<Native::declared_counts.size();++kind)
        for(std::uint32_t id=1;id<=Native::declared_counts[kind];++id) {
            auto record=native->lookup(static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(id));
            if(!record)throw DatabaseError("CN skill import native definition unavailable");
            records.push_back(NativeSkillRecord{source,static_cast<std::int64_t>(records.size()),
                record->file_offset,std::move(record->record_sha256),
                std::vector<std::uint8_t>(record->raw.begin(),record->raw.end()),
                record->kind,record->definition_id});
        }
    if(records.size()!=static_cast<std::size_t>(source.row_count) || !native->current())
        throw DatabaseError("CN skill import source changed during materialization");

    sqlite_detail::Transaction transaction(db);
    require_existing_schema(db);
    const bool present=existing_source(db,source);
    const auto count=row_count(db,source.dataset_id);
    if((present && count!=source.row_count) || (!present && count!=0))
        throw DatabaseError("CN skill import will not replace partial or orphan definitions");
    if(!native->current())throw DatabaseError("CN skill import source changed before insertion");
    if(!present) {
        insert_source(db,source);
        for(const auto& record:records)insert_record(db,record);
    }

    // Read back on THIS connection and transaction, including exact provenance,
    // ordinal, offset, hash, raw bytes and identities for every expected record.
    // Extra rows/duplicates/corrupt existing content cannot become an import ack.
    if(!existing_source(db,source) || row_count(db,source.dataset_id)!=source.row_count)
        throw DatabaseError("CN skill import stored source envelope differs");
    const NativeSkillCatalog reader(db);
    for(const auto& expected:records) {
        const auto actual=reader.lookup(source.dataset_id,expected.kind,expected.definition_id);
        if(!actual || *actual!=expected)
            throw DatabaseError("CN skill import stored definition differs");
    }
    if(!native->current())throw DatabaseError("CN skill import source changed before commit");
    transaction.commit();
    return present?Result::AlreadyPresent:Result::Inserted;
}
}
