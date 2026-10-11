#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <set>

namespace god2 {
namespace {
bool digest(std::string_view value) {
    return value.size()==64 && std::all_of(value.begin(),value.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    });
}
bool origin(std::string_view value) {
    return !value.empty() && value.size()<=2048 && value.find('\0')==value.npos;
}
}
SqliteNativeCharacterSummarySnapshotRepository::SqliteNativeCharacterSummarySnapshotRepository(
    sqlite3* db,const SqliteAccountRepository& accounts,SqliteRecoveredCharacterRepository& characters)
    :db_(db),accounts_(accounts),characters_(characters) {
    if(!db || !accounts.uses_connection(db) || !characters.uses_connection(db))
        throw DatabaseError("Native summary requires same account and character connection");
}
void SqliteNativeCharacterSummarySnapshotRepository::owner() const {
    if(owner_!=std::this_thread::get_id())throw DatabaseError("Native summary database owner mismatch");
}
bool SqliteNativeCharacterSummarySnapshotRepository::owns_sources(const AccountRepository& accounts,
    const RecoveredCharacterRepository& characters) const noexcept {
    return &accounts==&accounts_ && &characters==&characters_ &&
        accounts_.uses_connection(db_) && characters_.uses_connection(db_);
}
std::optional<NativeCharacterSummarySnapshot> SqliteNativeCharacterSummarySnapshotRepository::load(
    std::uint64_t account,std::uint16_t group,std::uint16_t server,std::string_view profile) {
    owner();
    if(!account || account>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) || !digest(profile))
        throw DatabaseError("Invalid native summary scope");
    // One SELECT cursor covers header, all ordered bindings and actual common
    // account ownership. No split reads, BEGIN/DDL/write or schema-on-read.
    sqlite_detail::Statement query(db_,
        "SELECT s.account_id,s.group_id,s.server_id,s.client_sha256,s.record,s.row_count,s.revision,s.source_sha256,s.source_record,"
        "COALESCE(m.ordinal,-1),m.character_id,m.name_source,CASE WHEN c.id IS NULL THEN 0 ELSE 1 END,"
        "CASE WHEN m.role_record IS NULL AND m.role_revision IS NULL AND m.role_source_sha256 IS NULL AND m.role_source_record IS NULL THEN 0 "
        "WHEN m.role_record IS NOT NULL AND m.role_revision IS NOT NULL AND m.role_source_sha256 IS NOT NULL AND m.role_source_record IS NOT NULL THEN 1 ELSE -1 END,"
        "m.role_record,m.role_revision,m.role_source_sha256,m.role_source_record "
        "FROM main.accounts a JOIN main.account_native_character_summaries s ON s.account_id=a.id "
        "LEFT JOIN main.account_native_character_summary_rows m ON m.account_id=s.account_id AND m.group_id=s.group_id "
        "AND m.server_id=s.server_id AND m.client_sha256=s.client_sha256 "
        "LEFT JOIN main.recovered_characters c ON c.id=m.character_id AND c.account_id=s.account_id "
        "WHERE a.id=? AND s.group_id=? AND s.server_id=? AND s.client_sha256=? ORDER BY m.ordinal");
    query.bind_id(1,account);query.bind(2,group);query.bind(3,server);query.bind(4,std::string(profile));
    std::optional<NativeCharacterSummarySnapshot> header;
    std::vector<NativeCharacterSummarySnapshot::Row> rows;
    std::set<std::uint64_t> ids;
    std::size_t declared=0;
    bool empty_binding_seen=false;
    while(query.row()) {
        NativeCharacterSummarySnapshot actual;
        actual.account=query.number<std::uint64_t>(0);actual.group=query.number<std::uint16_t>(1);
        actual.server=query.number<std::uint16_t>(2);actual.client_sha256=query.text(3);
        const auto bytes=query.blob(4,1,4096);actual.record.assign(bytes.begin(),bytes.end());
        const auto count=query.number<std::uint32_t>(5);actual.revision=query.number<std::uint64_t>(6);
        actual.source_sha256=query.text(7);actual.source_record=query.text(8);
        // Bounds are raw-storage budgets, not recovered native gameplay caps.
        if(actual.account!=account || actual.group!=group || actual.server!=server || actual.client_sha256!=profile ||
           !actual.revision || count>4096 || !digest(actual.source_sha256) || !origin(actual.source_record))
            throw DatabaseError("Invalid native summary header");
        if(!header) {header=std::move(actual);declared=count;}
        else if(actual!=*header || count!=declared)throw DatabaseError("Duplicate or inconsistent native summary header");
        const auto ordinal=query.number<int>(9);
        if(ordinal==-1) {
            if(declared || !rows.empty() || empty_binding_seen)throw DatabaseError("Missing or duplicate native summary binding");
            empty_binding_seen=true;
            continue; //Only an actual stored full record with explicit zero rows.
        }
        if(empty_binding_seen || ordinal<0 || static_cast<std::size_t>(ordinal)!=rows.size() || rows.size()>=declared || query.integer(12)!=1)
            throw DatabaseError("Invalid native summary ordinal or character ownership");
        NativeCharacterSummarySnapshot::Row row;
        row.character=query.number<std::uint64_t>(10);
        const auto mode=query.number<std::uint8_t>(11);
        if(!row.character || !ids.insert(row.character).second || mode>1)
            throw DatabaseError("Invalid native summary identity or name source");
        row.name_source=static_cast<NativeCharacterSummarySnapshot::NameSource>(mode);
        const auto role=query.number<int>(13);
        if(role==1) {
            NativeCharacterSummarySnapshot::Role value;
            const auto bytes=query.blob(14,1,4096);value.record.assign(bytes.begin(),bytes.end());
            value.revision=query.number<std::uint64_t>(15);value.source_sha256=query.text(16);value.source_record=query.text(17);
            if(!value.revision || !digest(value.source_sha256) || !origin(value.source_record))
                throw DatabaseError("Invalid native summary role source");
            row.role=std::move(value);
        }else if(role!=0)throw DatabaseError("Incomplete native summary role source");
        rows.push_back(std::move(row));
    }
    if(!header)return std::nullopt;
    if(rows.size()!=declared)throw DatabaseError("Native summary row count differs");
    header->rows=std::move(rows);return header;
}
std::optional<SqliteNativeCharacterSummarySnapshotRepository::Snapshot>
SqliteNativeCharacterSummarySnapshotRepository::replace_from_issuer(
    std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    owner();
    if(writing_) {reentered_=true;throw DatabaseError("Native summary writer reentered");}
    if(!issuer || !owns_sources(accounts_,characters_) || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Native summary writer requires same owner/sources, real issuer and own transaction");
    const auto positive=[](std::uint64_t value) {
        return value && value<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    };
    const auto valid=[&](const Snapshot& value) {
        if(!positive(value.account) || !positive(value.revision) || !digest(value.client_sha256) ||
           !digest(value.source_sha256) || !origin(value.source_record) || value.record.empty() ||
           value.record.size()>4096 || value.rows.size()>4096)return false;
        std::set<std::uint64_t> ids;
        for(const auto& row:value.rows) {
            if(!positive(row.character) || !ids.insert(row.character).second ||
               (row.name_source!=Snapshot::NameSource::CommonIdentity && row.name_source!=Snapshot::NameSource::NativePromptMarker))return false;
            if(row.role && (!positive(row.role->revision) || row.role->record.empty() || row.role->record.size()>4096 ||
                !digest(row.role->source_sha256) || !origin(row.role->source_record)))return false;
        }
        return true;
    };
    if(!valid(next) || (expected && (!valid(*expected) || expected->account!=next.account ||
        expected->group!=next.group || expected->server!=next.server || expected->client_sha256!=next.client_sha256 ||
        expected->revision>=next.revision)))throw DatabaseError("Invalid native summary issuer/CAS scope or revision");
    struct Writing {
        bool& active;bool& reentered;
        Writing(bool& value,bool& poison):active(value),reentered(poison){active=true;reentered=false;}
        ~Writing(){active=false;reentered=false;}
    } writing(writing_,reentered_);
    {
        sqlite_detail::Statement keys(db_,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())throw DatabaseError("Native summary writer requires foreign keys");
    }
    sqlite_detail::Transaction transaction(db_);
    const auto roots=characters_.list_for_account(next.account);
    std::set<std::uint64_t> root_ids;
    for(const auto& row:roots)
        if(!positive(row.id) || row.account_id!=next.account || !root_ids.insert(row.id).second)
            throw DatabaseError("Invalid native summary common roots");
    for(const auto& row:next.rows)
        if(!root_ids.contains(row.character))throw DatabaseError("Native summary issuer character not owned");
    const auto same_roots=[&] {
        const auto actual=characters_.list_for_account(next.account);
        if(actual.size()!=roots.size())return false;
        std::set<std::uint64_t> seen;
        for(const auto& row:actual) {
            const auto old=std::find_if(roots.begin(),roots.end(),[&](const auto& value){return value.id==row.id;});
            if(old==roots.end() || !seen.insert(row.id).second || row.account_id!=old->account_id || row.slot!=old->slot ||
               row.profile!=old->profile || row.created_at!=old->created_at || row.name_codepage!=old->name_codepage ||
               row.streamer_privilege!=old->streamer_privilege)return false;
        }
        return true;
    };
    const auto verify=[&](const std::optional<Snapshot>& wanted) {
        if(reentered_ || !same_roots() || load(next.account,next.group,next.server,next.client_sha256)!=wanted ||
           !same_roots() || reentered_)throw DatabaseError("Native summary fulltuple or common roots conflict");
    };
    verify(expected);
    if(!issuer(expected,next,WriteCheck::Prepared,roots))return std::nullopt;
    verify(expected);
    if(!issuer(expected,next,WriteCheck::BeforeWrite,roots))return std::nullopt;
    verify(expected);
    {
        sqlite_detail::Statement header(db_,expected?
            "UPDATE main.account_native_character_summaries SET record=?,row_count=?,revision=?,source_sha256=?,source_record=? "
            "WHERE account_id=? AND group_id=? AND server_id=? AND client_sha256=? AND revision=?":
            "INSERT INTO main.account_native_character_summaries(record,row_count,revision,source_sha256,source_record,account_id,group_id,server_id,client_sha256) "
            "VALUES(?,?,?,?,?,?,?,?,?)");
        header.bind_blob(1,next.record);header.bind(2,static_cast<std::int64_t>(next.rows.size()));header.bind_id(3,next.revision);
        header.bind(4,next.source_sha256);header.bind(5,next.source_record);header.bind_id(6,next.account);
        header.bind(7,next.group);header.bind(8,next.server);header.bind(9,next.client_sha256);
        if(expected)header.bind_id(10,expected->revision);
        header.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Native summary header CAS failed");
    }
    {
        sqlite_detail::Statement remove(db_,"DELETE FROM main.account_native_character_summary_rows "
            "WHERE account_id=? AND group_id=? AND server_id=? AND client_sha256=?");
        remove.bind_id(1,next.account);remove.bind(2,next.group);remove.bind(3,next.server);remove.bind(4,next.client_sha256);remove.done();
        const auto previous=expected?expected->rows.size():0;
        if(sqlite3_changes(db_)!=static_cast<int>(previous))throw DatabaseError("Native summary binding CAS differs");
    }
    for(std::size_t ordinal=0;ordinal<next.rows.size();++ordinal) {
        const auto& value=next.rows[ordinal];
        sqlite_detail::Statement row(db_,value.role?
            "INSERT INTO main.account_native_character_summary_rows(account_id,group_id,server_id,client_sha256,ordinal,character_id,name_source,"
            "role_record,role_revision,role_source_sha256,role_source_record) VALUES(?,?,?,?,?,?,?,?,?,?,?)":
            "INSERT INTO main.account_native_character_summary_rows(account_id,group_id,server_id,client_sha256,ordinal,character_id,name_source,"
            "role_record,role_revision,role_source_sha256,role_source_record) VALUES(?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)");
        row.bind_id(1,next.account);row.bind(2,next.group);row.bind(3,next.server);row.bind(4,next.client_sha256);
        row.bind(5,static_cast<std::int64_t>(ordinal));row.bind_id(6,value.character);row.bind(7,static_cast<std::int64_t>(value.name_source));
        if(value.role) {
            row.bind_blob(8,value.role->record);row.bind_id(9,value.role->revision);
            row.bind(10,value.role->source_sha256);row.bind(11,value.role->source_record);
        }
        row.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Native summary binding insert failed");
    }
    // Allocate/own readback BEFORE durable commit; no callback or reload after it.
    auto result=load(next.account,next.group,next.server,next.client_sha256);
    if(result!=std::optional{next})throw DatabaseError("Native summary staged readback differs");
    verify(result);
    if(!issuer(expected,next,WriteCheck::BeforeCommit,roots))return std::nullopt;
    verify(result);
    transaction.commit();return result;
}
std::string SqliteNativeCharacterSummarySnapshotRepository::schema() {
    // Shared opaque delivery storage keyed by build, account and destination.
    // Gameplay/identity/name stay in existing common tables; no default values.
    return R"SQL(CREATE TABLE account_native_character_summaries (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 group_id INTEGER NOT NULL CHECK(typeof(group_id)='integer' AND group_id BETWEEN 0 AND 65535),
 server_id INTEGER NOT NULL CHECK(typeof(server_id)='integer' AND server_id BETWEEN 0 AND 65535),
 client_sha256 TEXT NOT NULL CHECK(typeof(client_sha256)='text' AND length(client_sha256)=64 AND client_sha256 NOT GLOB '*[^0-9a-f]*'),
 record BLOB NOT NULL CHECK(typeof(record)='blob' AND length(record) BETWEEN 1 AND 4096),
 row_count INTEGER NOT NULL CHECK(typeof(row_count)='integer' AND row_count BETWEEN 0 AND 4096),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(typeof(source_sha256)='text' AND length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_record TEXT NOT NULL CHECK(typeof(source_record)='text' AND length(CAST(source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(source_record,char(0))=0),
 PRIMARY KEY(account_id,group_id,server_id,client_sha256),
 FOREIGN KEY(account_id) REFERENCES accounts(id)
) WITHOUT ROWID;
CREATE TABLE account_native_character_summary_rows (
 account_id INTEGER NOT NULL,
 group_id INTEGER NOT NULL,
 server_id INTEGER NOT NULL,
 client_sha256 TEXT NOT NULL,
 ordinal INTEGER NOT NULL CHECK(typeof(ordinal)='integer' AND ordinal BETWEEN 0 AND 4095),
 character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
 name_source INTEGER NOT NULL CHECK(typeof(name_source)='integer' AND name_source IN (0,1)),
 role_record BLOB,
 role_revision INTEGER,
 role_source_sha256 TEXT,
 role_source_record TEXT,
 CHECK((role_record IS NULL AND role_revision IS NULL AND role_source_sha256 IS NULL AND role_source_record IS NULL) OR
 (typeof(role_record)='blob' AND length(role_record) BETWEEN 1 AND 4096 AND typeof(role_revision)='integer' AND role_revision>0
 AND typeof(role_source_sha256)='text' AND length(role_source_sha256)=64 AND role_source_sha256 NOT GLOB '*[^0-9a-f]*'
 AND typeof(role_source_record)='text' AND length(CAST(role_source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(role_source_record,char(0))=0)),
 PRIMARY KEY(account_id,group_id,server_id,client_sha256,ordinal),
 UNIQUE(account_id,group_id,server_id,client_sha256,character_id),
 FOREIGN KEY(account_id,group_id,server_id,client_sha256) REFERENCES account_native_character_summaries(account_id,group_id,server_id,client_sha256) ON DELETE CASCADE,
 FOREIGN KEY(character_id) REFERENCES recovered_characters(id) ON DELETE CASCADE
) WITHOUT ROWID;
)SQL";
}
}
