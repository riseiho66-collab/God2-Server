#include "db/NativeDeliverySnapshotSchema.h"
#include "db/SqliteNativeAccountSnapshotRepository.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace god2 {
namespace {
constexpr std::array<std::string_view,4> names{
    "account_native_snapshots","account_native_character_summaries",
    "account_native_character_summary_rows","native_delivery_snapshot_schema"};
constexpr const char* ledger_sql=R"SQL(CREATE TABLE native_delivery_snapshot_schema (
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=1),
 sql_text TEXT NOT NULL CHECK(typeof(sql_text)='text' AND length(sql_text)>0)
);
)SQL";
constexpr const char* owned_where=
    "name IN('account_native_snapshots','account_native_character_summaries',"
    "'account_native_character_summary_rows','native_delivery_snapshot_schema') OR "
    "tbl_name IN('account_native_snapshots','account_native_character_summaries',"
    "'account_native_character_summary_rows','native_delivery_snapshot_schema')";
void require(bool condition,const char* message) {
    if(!condition)throw DatabaseError(message);
}
struct Cell {
    int type;
    std::string bytes;
    bool operator==(const Cell&) const=default;
    bool operator<(const Cell& other) const {
        return type<other.type || (type==other.type && bytes<other.bytes);
    }
};
using Row=std::vector<Cell>;
using Rows=std::vector<Row>;
using Statement=std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)>;
Statement prepare(sqlite3* db,const std::string& sql) {
    require(sql.size()<=static_cast<std::size_t>(std::numeric_limits<int>::max()),
        "Native delivery metadata query too large");
    sqlite3_stmt* raw=nullptr;
    const auto code=sqlite3_prepare_v2(db,sql.data(),static_cast<int>(sql.size()),&raw,nullptr);
    Statement result(raw,sqlite3_finalize);
    sqlite_detail::check(db,code);
    return result;
}
Rows rows(sqlite3* db,const std::string& sql) {
    auto statement=prepare(db,sql);
    Rows result;
    for(;;) {
        const auto code=sqlite3_step(statement.get());
        if(code==SQLITE_DONE)break;
        if(code!=SQLITE_ROW)throw DatabaseError("Unable to read native delivery schema metadata");
        Row value;
        for(int column=0;column<sqlite3_column_count(statement.get());++column) {
            Cell cell{sqlite3_column_type(statement.get(),column),{}};
            if(cell.type==SQLITE_INTEGER)cell.bytes=std::to_string(sqlite3_column_int64(statement.get(),column));
            else if(cell.type==SQLITE_FLOAT)
                cell.bytes=std::to_string(std::bit_cast<std::uint64_t>(sqlite3_column_double(statement.get(),column)));
            else if(cell.type==SQLITE_TEXT || cell.type==SQLITE_BLOB) {
                const auto* bytes=cell.type==SQLITE_TEXT?
                    static_cast<const void*>(sqlite3_column_text(statement.get(),column)):
                    sqlite3_column_blob(statement.get(),column);
                const auto size=sqlite3_column_bytes(statement.get(),column);
                require(size>=0 && (bytes || (cell.type==SQLITE_BLOB && size==0)),
                    "Unable to copy native delivery schema metadata");
                if(size)cell.bytes.assign(static_cast<const char*>(bytes),static_cast<std::size_t>(size));
            } else require(cell.type==SQLITE_NULL,"Invalid native delivery metadata type");
            value.push_back(std::move(cell));
        }
        result.push_back(std::move(value));
    }
    return result;
}
bool has_row(sqlite3* db,const std::string& sql) {
    auto statement=prepare(db,sql);
    const auto code=sqlite3_step(statement.get());
    require(code==SQLITE_ROW || code==SQLITE_DONE,"Unable to check native delivery schema metadata");
    return code==SQLITE_ROW;
}
std::string identifier(std::string_view name) {
    require(name.find('\0')==name.npos,"Invalid native delivery metadata identifier");
    std::string result="\"";
    for(char c:name){result.push_back(c);if(c=='\"')result.push_back(c);}
    result.push_back('\"');return result;
}
std::string literal(std::string_view value) {
    require(value.find('\0')==value.npos,"Invalid native delivery metadata literal");
    std::string result="'";
    for(char c:value){result.push_back(c);if(c=='\'')result.push_back(c);}
    result.push_back('\'');return result;
}
Rows objects(sqlite3* db,bool owned) {
    return rows(db,std::string("SELECT type,name,tbl_name,COALESCE(sql,'') FROM main.sqlite_master WHERE ")+
        (owned?"(":"NOT (")+owned_where+") ORDER BY type,name");
}
Rows sorted(Rows value) {std::sort(value.begin(),value.end());return value;}
void flags(sqlite3* db,bool entry) {
    require(db && (sqlite3_get_autocommit(db)!=0)==entry,
        "Native delivery schema requires its own transaction");
    const auto enabled=[&](const char* sql,std::int64_t value) {
        sqlite_detail::Statement query(db,sql);
        return query.row() && query.integer(0)==value && !query.row();
    };
    require(enabled("PRAGMA foreign_keys",1) && enabled("PRAGMA defer_foreign_keys",0),
        "Native delivery schema requires immediate foreign keys");
    require(!has_row(db,std::string("SELECT 1 FROM temp.sqlite_master WHERE (")+owned_where+") OR "
        "name IN('accounts','recovered_characters','schema_migrations') OR "
        "tbl_name IN('accounts','recovered_characters','schema_migrations')"),
        "Native delivery schema has a temporary-object collision");
}
Rows history(sqlite3* db,const std::vector<Migration>& migrations) {
    // Same configured already-migrated Database vector, not a reconstructed53
    // recipe. Current Database supports complete installed prefixes32..53.
    require(migrations.size()>=32 && migrations.size()<=53,
        "Native delivery schema requires a supported migrated base profile");
    const auto actual=rows(db,"SELECT version,name,sql_text,applied_at FROM main.schema_migrations ORDER BY version");
    require(actual.size()==migrations.size(),"Native delivery base history cardinality differs");
    for(std::size_t index=0;index<migrations.size();++index) {
        const auto& migration=migrations[index];const auto& row=actual[index];
        require(migration.version==static_cast<int>(index+1) && !migration.name.empty() && !migration.sql.empty() &&
            row.size()==4 && row[0]==Cell{SQLITE_INTEGER,std::to_string(migration.version)} &&
            row[1]==Cell{SQLITE_TEXT,migration.name} && row[2]==Cell{SQLITE_TEXT,migration.sql} && row[3].type==SQLITE_TEXT,
            "Native delivery base history differs from exact configured migrations");
    }
    return actual;
}
using Database=std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)>;
Database expected(const std::vector<Migration>& migrations,const std::string& ddl) {
    sqlite3* raw=nullptr;const auto code=sqlite3_open(":memory:",&raw);
    Database result(raw,sqlite3_close_v2);
    require(code==SQLITE_OK && raw,"Unable to create native delivery metadata reference");
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    // Only this separate metadata reference runs the original source recipes.
    // No base DDL or base data is replayed on the actual supplied connection.
    for(const auto& migration:migrations)sqlite_detail::execute(raw,migration.sql);
    sqlite_detail::execute(raw,ddl);
    return result;
}
void table_metadata(sqlite3* db,sqlite3* reference,std::string_view table) {
    const auto name=identifier(table);
    for(const auto* pragma: {"table_xinfo","foreign_key_list","index_list"}) {
        const auto query=std::string("PRAGMA main.")+pragma+"("+name+")";
        require(sorted(rows(db,query))==sorted(rows(reference,query)),
            "Native delivery table/foreign-key/index metadata differs");
    }
    const auto indexes=rows(reference,"SELECT name FROM main.sqlite_master WHERE type='index' AND tbl_name="+
        literal(table)+" ORDER BY name");
    for(const auto& index:indexes) {
        require(index.size()==1 && index[0].type==SQLITE_TEXT,"Invalid native delivery reference index");
        const auto query="PRAGMA main.index_xinfo("+identifier(index[0].bytes)+")";
        require(sorted(rows(db,query))==sorted(rows(reference,query)),
            "Native delivery index column/collation contract differs");
    }
}
void parents(sqlite3* db,sqlite3* reference) {
    // Canonical parent table contracts; unknown changed parent definitions are
    // rejected, never rewritten. Unrelated objects and data are left untouched.
    for(const auto* table: {"accounts","recovered_characters"}) {
        const auto query=std::string("SELECT type,name,tbl_name,sql FROM main.sqlite_master WHERE type='table' AND name=")+
            literal(table);
        const auto wanted=rows(reference,query);
        require(wanted.size()==1 && rows(db,query)==wanted,"Native delivery parent table contract differs");
        const auto name=identifier(table);
        for(const auto* pragma: {"table_xinfo","foreign_key_list"}) {
            const auto metadata=std::string("PRAGMA main.")+pragma+"("+name+")";
            require(sorted(rows(db,metadata))==sorted(rows(reference,metadata)),
                "Native delivery parent column/key contract differs");
        }
        // Additional unrelated indexes/triggers remain outside our owned scope.
        const auto indexes=rows(reference,std::string("SELECT type,name,tbl_name,COALESCE(sql,'') FROM main.sqlite_master ")+
            "WHERE type='index' AND tbl_name="+literal(table)+" ORDER BY name");
        for(const auto& index:indexes) {
            const auto actual=rows(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM main.sqlite_master WHERE name="+
                literal(index[1].bytes));
            require(actual==Rows{index},"Native delivery parent uniqueness/index contract differs");
            const auto metadata="PRAGMA main.index_xinfo("+identifier(index[1].bytes)+")";
            require(sorted(rows(db,metadata))==sorted(rows(reference,metadata)),
                "Native delivery parent index columns differ");
        }
    }
}
std::string contract() {
    return SqliteNativeAccountSnapshotRepository::schema()+
        SqliteNativeCharacterSummarySnapshotRepository::schema()+ledger_sql;
}
void qualify(sqlite3* db,sqlite3* reference,const std::vector<Migration>& migrations,const std::string& ddl) {
    flags(db,false);(void)history(db,migrations);parents(db,reference);
    require(objects(db,true)==objects(reference,true),"Native delivery owned objects are incomplete or altered");
    for(const auto table:names) {
        table_metadata(db,reference,table);
        require(!has_row(db,"PRAGMA main.foreign_key_check("+identifier(table)+")"),
            "Native delivery stored ownership foreign key differs");
    }
    sqlite_detail::Statement ledger(db,"SELECT version,sql_text FROM main.native_delivery_snapshot_schema");
    require(ledger.row() && ledger.integer(0)==1 && ledger.text(1)==ddl && !ledger.row(),
        "Native delivery exact v1 complete DDL ledger differs");
    flags(db,false);
}
void run(sqlite3* db,const std::vector<Migration>& migrations,bool install) {
    flags(db,true);
    sqlite_detail::Transaction transaction(db);
    const auto original_history=history(db,migrations);
    const auto outside=objects(db,false);
    const auto ddl=contract();auto reference=expected(migrations,ddl);
    parents(db,reference.get());
    const auto existing=objects(db,true);
    if(existing.empty()) {
        require(install,"Native delivery schema has not been explicitly installed");
        // The whole owned scope must be absent. No IF NOT EXISTS adoption,
        // base DML, ALTER, DROP or actual snapshot/native data is permitted.
        flags(db,false);
        sqlite_detail::execute(db,ddl);
        sqlite_detail::Statement ledger(db,"INSERT INTO main.native_delivery_snapshot_schema(version,sql_text) VALUES(1,?)");
        ledger.bind(1,ddl);ledger.done();
        require(sqlite3_changes(db)==1,"Native delivery schema ledger insert differs");
    }
    qualify(db,reference.get(),migrations,ddl);
    require(history(db,migrations)==original_history && objects(db,false)==outside,
        "Native delivery installation changed external schema or base history");
    // Only fresh owned CREATEs and one fresh ledger INSERT can mutate this
    // connection. No account/password/gameplay/native row values were selected
    // or copied. Existing owned snapshot rows are never rewritten.
    flags(db,false);
    transaction.commit();
}
}
void NativeDeliverySnapshotSchema::install(sqlite3* db,const std::vector<Migration>& migrations) {
    run(db,migrations,true);
}
void NativeDeliverySnapshotSchema::require_existing(sqlite3* db,const std::vector<Migration>& migrations) {
    run(db,migrations,false);
}
}
