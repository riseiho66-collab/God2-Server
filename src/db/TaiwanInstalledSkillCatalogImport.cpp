#include "db/TaiwanInstalledSkillCatalogImport.h"
#include "db/DbTypes.h"
#include <sqlite3.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

namespace god2 {
namespace {
// Preserve literal quoted values while canonicalising insignificant SQL spaces.
std::string schema_text(std::string_view value) {
    std::string result;result.reserve(value.size());char quote=0;bool gap=false;
    for(std::size_t i=0;i<value.size();++i) {
        const char c=value[i];
        if(quote) {
            result.push_back(c);
            if(c==quote) {
                if(i+1<value.size() && value[i+1]==quote)result.push_back(value[++i]);
                else quote=0;
            }
        } else if(c=='\'' || c=='"') {
            if(gap && !result.empty())result.push_back(' ');gap=false;
            quote=c;result.push_back(c);
        } else if(c==' ' || c=='\r' || c=='\n' || c=='\t')gap=true;
        else {if(gap && !result.empty())result.push_back(' ');gap=false;result.push_back(c);}
    }
    if(quote)throw DatabaseError("Malformed installed skill schema text");
    if(!result.empty() && result.back()==';')result.pop_back();
    return result;
}
constexpr const char* source_schema=R"SQL(CREATE TABLE native_data_sources (
 dataset_id TEXT PRIMARY KEY NOT NULL CHECK(length(dataset_id) > 0),
 source_path TEXT NOT NULL CHECK(length(source_path) > 0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256) = 64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256) = 64 AND decoded_sha256 NOT GLOB '*[^0-9a-f]*'),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256) = 64 AND native_image_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_section TEXT NOT NULL CHECK(length(source_section) > 0),
 loader_rva TEXT NOT NULL CHECK(length(loader_rva) > 0),
 lookup_rva TEXT NOT NULL CHECK(length(lookup_rva) > 0),
 row_count INTEGER NOT NULL CHECK(typeof(row_count) = 'integer' AND row_count BETWEEN 1 AND 32767)
))SQL";
constexpr const char* record_schema=R"SQL(CREATE TABLE native_skill_catalog (
 dataset_id TEXT NOT NULL REFERENCES native_data_sources(dataset_id),
 source_record_index INTEGER NOT NULL CHECK(typeof(source_record_index) = 'integer' AND source_record_index BETWEEN 0 AND 1019),
 source_offset INTEGER NOT NULL CHECK(typeof(source_offset) = 'integer' AND source_offset = 8 + kind * 28164 + (definition_id - 1) * 110),
 record_sha256 TEXT NOT NULL CHECK(typeof(record_sha256) = 'text' AND length(record_sha256) = 64 AND record_sha256 NOT GLOB '*[^0-9a-f]*'),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record) = 'blob' AND length(raw_record) = 110),
 kind INTEGER NOT NULL CHECK(typeof(kind) = 'integer' AND kind BETWEEN 0 AND 3),
 definition_id INTEGER NOT NULL CHECK(typeof(definition_id) = 'integer' AND definition_id BETWEEN 1 AND 255),
 PRIMARY KEY(dataset_id, source_record_index),
 UNIQUE(dataset_id, kind, definition_id),
 CHECK(hex(substr(raw_record, 1, 2)) = printf('%02X%02X', definition_id, kind))
))SQL";
}

struct TaiwanInstalledSkillCatalogImport::Operation {
    TaiwanInstalledSkillCatalogImport& writer;
    sqlite3_int64 changes;
    bool transaction=false,commit_confirmed=false;
    explicit Operation(TaiwanInstalledSkillCatalogImport& value):writer(value),changes(0) {
        writer.owner(); // Wrong thread never reads/writes the plain guard fields.
        if(writer.busy_) {writer.poisoned_=true;throw DatabaseError("Installed skill import reentered");}
        if(writer.poisoned_)throw DatabaseError("Installed skill import connection poisoned");
        if(!sqlite3_get_autocommit(writer.db_))throw DatabaseError("Installed skill import requires its own transaction");
        changes=sqlite3_total_changes64(writer.db_);writer.busy_=true;
    }
    ~Operation() {
        // Retire observed ended ownership before any fallible cleanup observer.
        (void)current();
        if(transaction && !commit_confirmed) {
            // Best-effort error cleanup only; never retry or undo a confirmed COMMIT.
            if(!sqlite3_get_autocommit(writer.db_)) {
                const int code=sqlite3_exec(writer.db_,"ROLLBACK",nullptr,nullptr,nullptr);
                if(code!=SQLITE_OK)writer.poisoned_=true;
            }
            transaction=false;
        }
        if(!current())writer.poisoned_=true;
        writer.busy_=false;
    }
    bool current() noexcept {
        if(std::this_thread::get_id()!=writer.thread_)return false;
        // Always observe this boundary, including when already poisoned. Once
        // our transaction visibly ended, finalize may begin a foreign successor;
        // ownership stays retired and no later cleanup may roll it back.
        const bool autocommit=bool(sqlite3_get_autocommit(writer.db_));
        if(transaction && autocommit) {transaction=false;writer.poisoned_=true;}
        return !writer.poisoned_ && writer.busy_ && autocommit==!transaction &&
            sqlite3_total_changes64(writer.db_)==changes;
    }
    void check() {
        if(!current()) {writer.poisoned_=true;throw DatabaseError("Installed skill import observation changed connection");}
    }
};

class TaiwanInstalledSkillCatalogImport::Statement final {
public:
    Statement(Operation& op,const char* sql):operation_(op) {
        operation_.check();const int code=sqlite3_prepare_v2(db(),sql,-1,&statement_,nullptr);
        try {after(code);}catch(...) {finalize_noexcept();throw;}
    }
    ~Statement(){finalize_noexcept();}
    Statement(const Statement&)=delete;
    Statement& operator=(const Statement&)=delete;
    void bind(int index,const std::string& value) {
        operation_.check();
        if(value.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()))throw DatabaseError("Installed skill text too large");
        after(sqlite3_bind_text(statement_,index,value.data(),static_cast<int>(value.size()),SQLITE_TRANSIENT));
    }
    void bind(int index,std::int64_t value) {operation_.check();after(sqlite3_bind_int64(statement_,index,value));}
    void blob(int index,std::span<const std::uint8_t> value) {
        operation_.check();
        if(value.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()))throw DatabaseError("Installed skill blob too large");
        after(sqlite3_bind_blob(statement_,index,value.data(),static_cast<int>(value.size()),SQLITE_TRANSIENT));
    }
    bool row() {
        operation_.check();const int code=sqlite3_step(statement_);operation_.check();
        if(code==SQLITE_ROW)return true;
        if(code==SQLITE_DONE)return false;
        throw DatabaseError(sqlite3_errmsg(db()));
    }
    void insert_one() {
        operation_.check();const int code=sqlite3_step(statement_);
        if(code==SQLITE_DONE) {
            ++operation_.changes; // Only the one expected actual INSERT may change total_changes.
            operation_.check();
            if(sqlite3_changes(db())!=1)throw DatabaseError("Installed skill insert affected wrong count");
        } else {operation_.check();throw DatabaseError(sqlite3_errmsg(db()));}
    }
    void begin() {
        operation_.check();const int code=sqlite3_step(statement_);
        if(code==SQLITE_DONE)operation_.transaction=true;
        operation_.check();if(code!=SQLITE_DONE)throw DatabaseError(sqlite3_errmsg(db()));
    }
    void commit() {
        operation_.check();const int code=sqlite3_step(statement_);
        if(code==SQLITE_DONE) {
            // Actual successful COMMIT is recorded BEFORE every fallible post fence/finalize.
            operation_.commit_confirmed=true;operation_.transaction=false;
        }
        operation_.check();if(code!=SQLITE_DONE)throw DatabaseError(sqlite3_errmsg(db()));
    }
    std::int64_t integer(int column) const {
        operation_.check();if(sqlite3_column_type(statement_,column)!=SQLITE_INTEGER)throw DatabaseError("Installed skill expected integer");
        const auto value=sqlite3_column_int64(statement_,column);operation_.check();return value;
    }
    std::string text(int column) const {
        operation_.check();if(sqlite3_column_type(statement_,column)!=SQLITE_TEXT)throw DatabaseError("Installed skill expected text");
        const auto* value=sqlite3_column_text(statement_,column);operation_.check();
        const int size=sqlite3_column_bytes(statement_,column);operation_.check();
        if(!value || size<0)throw DatabaseError("Installed skill unreadable text");
        std::string result(reinterpret_cast<const char*>(value),static_cast<std::size_t>(size));operation_.check();return result;
    }
    bool blob_equals(int column,std::span<const std::uint8_t> expected) const {
        operation_.check();if(sqlite3_column_type(statement_,column)!=SQLITE_BLOB)return false;
        const int size=sqlite3_column_bytes(statement_,column);operation_.check();
        const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement_,column));operation_.check();
        const bool same=size>=0 && std::size_t(size)==expected.size() && bytes &&
            std::equal(expected.begin(),expected.end(),bytes);operation_.check();return same;
    }
    void finish() {
        operation_.check();auto* old=std::exchange(statement_,nullptr);
        const int code=sqlite3_finalize(old);after(code);
    }
private:
    sqlite3* db() const noexcept {return operation_.writer.db_;}
    void after(int code) {operation_.check();if(code!=SQLITE_OK)throw DatabaseError(sqlite3_errmsg(db()));}
    void finalize_noexcept() noexcept {
        if(!statement_)return;
        const bool before=operation_.current(); // Drop ended ownership BEFORE finalize observers.
        auto* old=std::exchange(statement_,nullptr);
        const int code=sqlite3_finalize(old);
        const bool after=operation_.current(); // Never short-circuit this boundary on an error code.
        if(!before || code!=SQLITE_OK || !after)operation_.writer.poisoned_=true;
    }
    Operation& operation_;
    sqlite3_stmt* statement_=nullptr;
};

TaiwanInstalledSkillCatalogImport::TaiwanInstalledSkillCatalogImport(sqlite3* db)
    :db_(db),thread_(std::this_thread::get_id()) {
    if(!db_)throw DatabaseError("Installed skill import requires actual connection");
}
void TaiwanInstalledSkillCatalogImport::owner() const {
    if(thread_!=std::this_thread::get_id())throw DatabaseError("Installed skill import installation thread mismatch");
}
void TaiwanInstalledSkillCatalogImport::require_schema(Operation& op) {
    Statement shadows(op,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('schema_migrations','native_data_sources','native_skill_catalog') OR tbl_name COLLATE NOCASE IN ('schema_migrations','native_data_sources','native_skill_catalog') LIMIT 1");
    if(shadows.row())throw DatabaseError("Installed skill import rejects TEMP shadows/triggers");shadows.finish();
    Statement triggers(op,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE IN ('schema_migrations','native_data_sources','native_skill_catalog') LIMIT 1");
    if(triggers.row())throw DatabaseError("Installed skill import rejects main triggers");triggers.finish();
    for(const auto& [name,expected]:std::array<std::pair<const char*,const char*>,2>{{{"native_data_sources",source_schema},{"native_skill_catalog",record_schema}}}) {
        Statement table(op,"SELECT sql,rootpage FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE LIMIT 2");table.bind(1,std::string(name));
        if(!table.row() || table.integer(1)<=0 || schema_text(table.text(0))!=schema_text(expected) || table.row())
            throw DatabaseError("Installed skill import existing table shape differs");table.finish();
    }
    Statement history_table(op,"SELECT rootpage FROM main.sqlite_master WHERE type='table' AND name='schema_migrations' COLLATE NOCASE LIMIT 2");
    if(!history_table.row() || history_table.integer(0)<=0 || history_table.row())throw DatabaseError("Installed skill migration table missing");history_table.finish();
    Statement history_shape(op,"PRAGMA main.table_info('schema_migrations')");
    const std::array<const char*,4> column_names{"version","name","sql_text","applied_at"};
    const std::array<const char*,4> column_types{"INTEGER","TEXT","TEXT","TEXT"};
    for(std::size_t i=0;i<column_names.size();++i) {
        if(!history_shape.row() || history_shape.integer(0)!=static_cast<std::int64_t>(i) || history_shape.text(1)!=column_names[i] ||
           history_shape.text(2)!=column_types[i] || history_shape.integer(3)!=(i?1:0) || history_shape.integer(5)!=(i?0:1))
            throw DatabaseError("Installed skill migration columns differ");
    }
    if(history_shape.row())throw DatabaseError("Installed skill migration extra column");history_shape.finish();
    Statement migrations(op,"SELECT version,name FROM main.schema_migrations WHERE version IN (4,5) ORDER BY version");
    if(!migrations.row() || migrations.integer(0)!=4 || migrations.text(1)!="native_map_catalog" ||
       !migrations.row() || migrations.integer(0)!=5 || migrations.text(1)!="native_skill_catalog" || migrations.row())
        throw DatabaseError("Installed skill import requires existing migrations4/5");migrations.finish();
    Statement foreign_keys(op,"PRAGMA main.foreign_keys");
    if(!foreign_keys.row() || foreign_keys.integer(0)!=1 || foreign_keys.row())throw DatabaseError("Installed skill import requires foreign keys");foreign_keys.finish();
    op.check();
}

bool TaiwanInstalledSkillCatalogImport::source_present(Operation& op,const NativeSkillSource& expected) {
    Statement row(op,"SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,source_section,loader_rva,lookup_rva,row_count FROM main.native_data_sources WHERE dataset_id=? LIMIT 2");row.bind(1,expected.dataset_id);
    const bool present=row.row();
    if(present) {
        const NativeSkillSource actual{row.text(0),row.text(1),row.text(2),row.text(3),row.text(4),row.text(5),row.text(6),row.text(7),row.integer(8)};
        if(actual!=expected || row.row())throw DatabaseError("Installed skill source conflicts");
    }
    row.finish();return present;
}
void TaiwanInstalledSkillCatalogImport::require_records(Operation& op,std::span<const NativeSkillRecord> records) {
    Statement rows(op,"SELECT dataset_id,source_record_index,source_offset,record_sha256,raw_record,kind,definition_id FROM main.native_skill_catalog WHERE dataset_id=? ORDER BY source_record_index");
    rows.bind(1,records.front().source.dataset_id);
    for(const auto& expected:records) {
        if(!rows.row() || rows.text(0)!=expected.source.dataset_id || rows.integer(1)!=expected.source_record_index ||
           rows.integer(2)!=expected.source_offset || rows.text(3)!=expected.record_sha256 || !rows.blob_equals(4,expected.raw_record) ||
           rows.integer(5)!=expected.kind || rows.integer(6)!=expected.definition_id)
            throw DatabaseError("Installed skill complete ordered records differ");
    }
    if(rows.row())throw DatabaseError("Installed skill extra definition row");rows.finish();
}
void TaiwanInstalledSkillCatalogImport::insert_source(Operation& op,const NativeSkillSource& s) {
    Statement row(op,"INSERT INTO main.native_data_sources(dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,source_section,loader_rva,lookup_rva,row_count) VALUES(?,?,?,?,?,?,?,?,?)");
    row.bind(1,s.dataset_id);row.bind(2,s.source_path);row.bind(3,s.source_sha256);row.bind(4,s.decoded_sha256);row.bind(5,s.native_image_sha256);
    row.bind(6,s.source_section);row.bind(7,s.loader_rva);row.bind(8,s.lookup_rva);row.bind(9,s.row_count);row.insert_one();row.finish();
}
void TaiwanInstalledSkillCatalogImport::insert_record(Operation& op,const NativeSkillRecord& r) {
    Statement row(op,"INSERT INTO main.native_skill_catalog(dataset_id,source_record_index,source_offset,record_sha256,raw_record,kind,definition_id) VALUES(?,?,?,?,?,?,?)");
    row.bind(1,r.source.dataset_id);row.bind(2,r.source_record_index);row.bind(3,r.source_offset);row.bind(4,r.record_sha256);
    row.blob(5,r.raw_record);row.bind(6,r.kind);row.bind(7,r.definition_id);row.insert_one();row.finish();
}

TaiwanInstalledSkillCatalogImport::Outcome TaiwanInstalledSkillCatalogImport::import_source(
    const std::shared_ptr<const TaiwanInstalledSkillCatalogSource>& supplied) {
    owner();Operation operation(*this);
    const auto source=supplied; // Own the private immutable material before SQL observers.
    if(!source || source->records().size()!=TaiwanInstalledSkillCatalogSource::record_count ||
       source->retained_bytes().size()!=TaiwanInstalledSkillCatalogSource::file_bytes ||
       !native_taiwan_skill_source_matches(source->source(),NativeTaiwanSkillProfile::Installed453))
        throw DatabaseError("Installed skill import requires complete private qualified source");
    if(operation.changes>std::numeric_limits<sqlite3_int64>::max()-454)throw DatabaseError("Installed skill import change counter exhausted");
    Result result=Result::AlreadyPresent;
    try {
        {Statement begin(operation,"BEGIN IMMEDIATE");begin.begin();begin.finish();}
        require_schema(operation);
        const bool present=source_present(operation,source->source());
        if(present)require_records(operation,source->records());
        else {
            Statement orphan(operation,"SELECT 1 FROM main.native_skill_catalog WHERE dataset_id=? LIMIT 1");orphan.bind(1,source->source().dataset_id);
            if(orphan.row())throw DatabaseError("Installed skill import rejects orphan/partial rows");orphan.finish();
            result=Result::Inserted;insert_source(operation,source->source());
            for(const auto& record:source->records())insert_record(operation,record);
        }
        if(!source_present(operation,source->source()))throw DatabaseError("Installed skill source readback missing");
        require_records(operation,source->records());require_schema(operation);operation.check();
        Statement commit(operation,"COMMIT");
        // Re-check actual schema after COMMIT prepare observers; no user Current.
        require_schema(operation);operation.check();commit.commit();commit.finish();operation.check();
        return {result,true,true};
    } catch(...) {
        if(!operation.commit_confirmed)throw;
        // A successful local COMMIT cannot be relabelled rollback/retry when a
        // later finalize/observer poisons the connection. Only trivial value return.
        return {result,true,false};
    }
    // Public autocommit/totalchanges cannot identify silent COMMIT+BEGIN
    // replacement by arbitrary SQLite observers. No private transaction identity
    // or general observer convergence is claimed by these bounded fences.
}
}
