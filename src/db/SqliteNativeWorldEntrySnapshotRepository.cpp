#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>

namespace god2 {
namespace {
bool digest(std::string_view value) {
    return value.size()==64 && std::all_of(value.begin(),value.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    });
}
bool text(std::string_view value,std::size_t limit) {
    return !value.empty() && value.size()<=limit && value.find('\0')==value.npos;
}
bool positive(std::uint64_t value) {
    return value && value<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
}
bool valid(const NativeWorldEntrySnapshot& value) {
    return positive(value.root.account_id) && positive(value.root.id) && value.root.slot<2 &&
        text(value.root.created_at,2048) &&
        (value.root.name_codepage==0 || value.root.name_codepage==936 || value.root.name_codepage==950) &&
        value.root.streamer_privilege<=3 && positive(value.position.revision) &&
        positive(value.revision) && digest(value.client_sha256) && digest(value.source_sha256) &&
        text(value.record_kind,64) && text(value.source_record,2048) &&
        !value.record.empty() && value.record.size()<=4096;
}
}
SqliteNativeWorldEntrySnapshotRepository::SqliteNativeWorldEntrySnapshotRepository(
        sqlite3* db,const SqliteAccountRepository& accounts,SqliteRecoveredCharacterRepository& characters)
    :db_(db),accounts_(accounts),characters_(characters) {
    if(!db || !accounts.uses_connection(db) || !characters.uses_connection(db))
        throw DatabaseError("Native world entry requires the same common connection");
}
void SqliteNativeWorldEntrySnapshotRepository::owner() const {
    if(owner_!=std::this_thread::get_id())throw DatabaseError("Native world entry owner mismatch");
}
bool SqliteNativeWorldEntrySnapshotRepository::owns_sources(const AccountRepository& a,
        const RecoveredCharacterRepository& c) const noexcept {
    return &a==&accounts_ && &c==&characters_ && accounts_.uses_connection(db_) && characters_.uses_connection(db_);
}
bool SqliteNativeWorldEntrySnapshotRepository::owns_characters(const RecoveredCharacterRepository& c) const noexcept {
    return owns_sources(accounts_,c);
}
std::optional<NativeWorldEntrySnapshot> SqliteNativeWorldEntrySnapshotRepository::load(
        std::uint64_t account,std::uint64_t character,std::string_view client,std::string_view kind) {
    owner();
    if(!positive(account) || !positive(character) || !digest(client) || !text(kind,64))
        throw DatabaseError("Invalid native world entry key");
    // One cursor owns both the stored witness and actual account/character
    // ownership. Do not conflate stored old profile/position with current save.
    sqlite_detail::Statement q(db_,
        "SELECT s.account_id,s.character_id,s.client_sha256,s.record_kind,s.record,s.revision,s.source_sha256,s.source_record,"
        "s.root_slot,s.root_profile,s.root_created_at,s.root_name_codepage,s.root_streamer_privilege,"
        "s.area,s.scene,s.x,s.y,s.position_revision "
        "FROM main.character_native_world_entries s JOIN main.accounts a ON a.id=s.account_id "
        "JOIN main.recovered_characters c ON c.id=s.character_id AND c.account_id=s.account_id "
        "WHERE s.account_id=? AND s.character_id=? AND s.client_sha256=? AND s.record_kind=?");
    q.bind_id(1,account);q.bind_id(2,character);q.bind(3,std::string(client));q.bind(4,std::string(kind));
    if(!q.row())return std::nullopt;
    Snapshot v;
    v.root.account_id=q.number<std::uint64_t>(0);v.root.id=q.number<std::uint64_t>(1);
    v.client_sha256=q.text(2);v.record_kind=q.text(3);
    const auto raw=q.blob(4,1,4096);v.record.assign(raw.begin(),raw.end());
    v.revision=q.number<std::uint64_t>(5);v.source_sha256=q.text(6);v.source_record=q.text(7);
    v.root.slot=q.number<std::uint8_t>(8);
    const auto profile=q.blob(9,40,40);std::copy(profile.begin(),profile.end(),v.root.profile.begin());
    v.root.created_at=q.text(10);v.root.name_codepage=q.number<std::uint16_t>(11);
    v.root.streamer_privilege=q.number<std::uint8_t>(12);
    v.position.area=q.number<std::uint16_t>(13);v.position.scene=q.number<std::uint16_t>(14);
    v.position.x=q.number<std::uint16_t>(15);v.position.y=q.number<std::uint16_t>(16);
    v.position.revision=q.number<std::uint64_t>(17);
    if(!valid(v) || v.root.account_id!=account || v.root.id!=character ||
       v.client_sha256!=client || v.record_kind!=kind || q.row())
        throw DatabaseError("Invalid or ambiguous native world entry observation");
    return v;
}
std::optional<SqliteNativeWorldEntrySnapshotRepository::Snapshot>
SqliteNativeWorldEntrySnapshotRepository::replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    owner();
    if(writing_) {reentered_=true;throw DatabaseError("Native world entry writer reentered");}
    if(!issuer || !owns_sources(accounts_,characters_) || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Native world entry needs actual issuer and its own transaction");
    if(!valid(next) || (expected && (!valid(*expected) ||
        expected->root.account_id!=next.root.account_id || expected->root.id!=next.root.id ||
        expected->client_sha256!=next.client_sha256 || expected->record_kind!=next.record_kind ||
        expected->revision>=next.revision)))throw DatabaseError("Invalid native world entry CAS");
    writing_=true;reentered_=false;
    struct Exit {bool& active;bool& nested;~Exit(){active=false;nested=false;}} exit{writing_,reentered_};
    {
        sqlite_detail::Statement keys(db_,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())throw DatabaseError("Native world entry requires foreign keys");
    }
    sqlite_detail::Transaction tx(db_);
    const auto roots=characters_.list_for_account(next.root.account_id);
    const auto position=characters_.load_position(next.root.account_id,next.root.id);
    std::size_t found=0;
    for(const auto& root:roots)if(root.id==next.root.id) {
        if(!Snapshot::same_root(root,next.root))throw DatabaseError("Native world entry root witness is stale");
        ++found;
    }
    if(found!=1 || !position || *position!=next.position)
        throw DatabaseError("Native world entry requires actual owned root and saved position");
    const auto common_current=[&] {
        const auto actual=characters_.list_for_account(next.root.account_id);
        if(actual.size()!=roots.size())return false;
        for(std::size_t i=0;i<roots.size();++i)if(!Snapshot::same_root(actual[i],roots[i]))return false;
        return characters_.load_position(next.root.account_id,next.root.id)==position;
    };
    const auto check=[&](const std::optional<Snapshot>& wanted) {
        if(reentered_ || !common_current() ||
            load(next.root.account_id,next.root.id,next.client_sha256,next.record_kind)!=wanted ||
            !common_current() || reentered_)throw DatabaseError("Native world entry source changed");
    };
    check(expected);
    if(!issuer(expected,next,WriteCheck::Prepared))return std::nullopt;
    check(expected);
    if(!issuer(expected,next,WriteCheck::BeforeWrite))return std::nullopt;
    check(expected);
    sqlite_detail::Statement write(db_,expected?
        "UPDATE main.character_native_world_entries SET record=?,revision=?,source_sha256=?,source_record=?,root_slot=?,root_profile=?,"
        "root_created_at=?,root_name_codepage=?,root_streamer_privilege=?,area=?,scene=?,x=?,y=?,position_revision=? "
        "WHERE account_id=? AND character_id=? AND client_sha256=? AND record_kind=? AND revision=?":
        "INSERT INTO main.character_native_world_entries(record,revision,source_sha256,source_record,root_slot,root_profile,"
        "root_created_at,root_name_codepage,root_streamer_privilege,area,scene,x,y,position_revision,account_id,character_id,client_sha256,record_kind) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");
    write.bind_blob(1,next.record);write.bind_id(2,next.revision);write.bind(3,next.source_sha256);write.bind(4,next.source_record);
    write.bind(5,next.root.slot);write.bind_blob(6,next.root.profile);write.bind(7,next.root.created_at);
    write.bind(8,next.root.name_codepage);write.bind(9,next.root.streamer_privilege);
    write.bind(10,next.position.area);write.bind(11,next.position.scene);write.bind(12,next.position.x);write.bind(13,next.position.y);
    write.bind_id(14,next.position.revision);write.bind_id(15,next.root.account_id);write.bind_id(16,next.root.id);
    write.bind(17,next.client_sha256);write.bind(18,next.record_kind);if(expected)write.bind_id(19,expected->revision);
    write.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Native world entry CAS write failed");
    auto result=load(next.root.account_id,next.root.id,next.client_sha256,next.record_kind);
    if(result!=std::optional{next})throw DatabaseError("Native world entry staged readback differs");
    check(result);
    if(!issuer(expected,next,WriteCheck::BeforeCommit))return std::nullopt;
    check(result);
    tx.commit();return result;
}
std::string SqliteNativeWorldEntrySnapshotRepository::schema() {
    return R"SQL(CREATE TABLE main.character_native_world_entries (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
 client_sha256 TEXT NOT NULL CHECK(typeof(client_sha256)='text' AND length(client_sha256)=64 AND client_sha256 NOT GLOB '*[^0-9a-f]*'),
 record_kind TEXT NOT NULL CHECK(typeof(record_kind)='text' AND length(CAST(record_kind AS BLOB)) BETWEEN 1 AND 64 AND instr(record_kind,char(0))=0),
 record BLOB NOT NULL CHECK(typeof(record)='blob' AND length(record) BETWEEN 1 AND 4096),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(typeof(source_sha256)='text' AND length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_record TEXT NOT NULL CHECK(typeof(source_record)='text' AND length(CAST(source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(source_record,char(0))=0),
 root_slot INTEGER NOT NULL CHECK(typeof(root_slot)='integer' AND root_slot BETWEEN 0 AND 1),
 root_profile BLOB NOT NULL CHECK(typeof(root_profile)='blob' AND length(root_profile)=40),
 root_created_at TEXT NOT NULL CHECK(typeof(root_created_at)='text' AND length(CAST(root_created_at AS BLOB)) BETWEEN 1 AND 2048 AND instr(root_created_at,char(0))=0),
 root_name_codepage INTEGER NOT NULL CHECK(typeof(root_name_codepage)='integer' AND root_name_codepage IN (0,936,950)),
 root_streamer_privilege INTEGER NOT NULL CHECK(typeof(root_streamer_privilege)='integer' AND root_streamer_privilege BETWEEN 0 AND 3),
 area INTEGER NOT NULL CHECK(typeof(area)='integer' AND area BETWEEN 0 AND 65535),
 scene INTEGER NOT NULL CHECK(typeof(scene)='integer' AND scene BETWEEN 0 AND 65535),
 x INTEGER NOT NULL CHECK(typeof(x)='integer' AND x BETWEEN 0 AND 65535),
 y INTEGER NOT NULL CHECK(typeof(y)='integer' AND y BETWEEN 0 AND 65535),
 position_revision INTEGER NOT NULL CHECK(typeof(position_revision)='integer' AND position_revision>0),
 PRIMARY KEY(account_id,character_id,client_sha256,record_kind),
 FOREIGN KEY(account_id) REFERENCES accounts(id),
 FOREIGN KEY(character_id) REFERENCES recovered_characters(id) ON DELETE CASCADE
) WITHOUT ROWID;
)SQL";
}
}
