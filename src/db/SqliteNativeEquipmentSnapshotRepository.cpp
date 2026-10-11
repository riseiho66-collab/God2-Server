#include "db/SqliteNativeEquipmentSnapshotRepository.h"
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
struct ReadScope {
    sqlite3* db;bool finished=false;
    explicit ReadScope(sqlite3* value):db(value){sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){sqlite_detail::execute(db,"COMMIT");finished=true;}
};
bool valid(const NativeEquipmentSnapshot& value) {
    return positive(value.root.account_id) && positive(value.root.id) && value.root.slot<2 &&
        text(value.root.created_at,2048) &&
        (value.root.name_codepage==0 || value.root.name_codepage==936 || value.root.name_codepage==950) &&
        value.root.streamer_privilege<=3 && positive(value.position.revision) &&
        positive(value.revision) && digest(value.client_sha256) && digest(value.source_sha256) &&
        text(value.record_kind,64) && text(value.source_record,2048) &&
        value.client_sha256==NativeEquipmentSnapshot::client_pin &&
        value.record_kind==NativeEquipmentSnapshot::kind && value.actor_handle<=0x3fff &&
        value.record.size()==NativeEquipmentSnapshot::record_bytes &&
        value.appearance() && value.appearance()->actor_identity()==value.actor_handle;
}
}
SqliteNativeEquipmentSnapshotRepository::SqliteNativeEquipmentSnapshotRepository(
        sqlite3* db,const SqliteAccountRepository& accounts,SqliteRecoveredCharacterRepository& characters)
    :db_(db),accounts_(accounts),characters_(characters) {
    if(!db || !accounts.uses_connection(db) || !characters.uses_connection(db))
        throw DatabaseError("Native equipment requires the same common connection");
}
void SqliteNativeEquipmentSnapshotRepository::owner() const {
    if(owner_!=std::this_thread::get_id())throw DatabaseError("Native equipment owner mismatch");
}
bool SqliteNativeEquipmentSnapshotRepository::owns_sources(const AccountRepository& a,
        const RecoveredCharacterRepository& c) const noexcept {
    return &a==&accounts_ && &c==&characters_ && accounts_.uses_connection(db_) && characters_.uses_connection(db_);
}
bool SqliteNativeEquipmentSnapshotRepository::owns_characters(const RecoveredCharacterRepository& c) const noexcept {
    return owns_sources(accounts_,c);
}
std::optional<NativeEquipmentSnapshot> SqliteNativeEquipmentSnapshotRepository::load(
        std::uint64_t account,std::uint64_t character,std::string_view client,std::string_view kind) {
    owner();if(issuer_active_){reentered_=true;throw DatabaseError("Native equipment issuer reentered reader");}
    if(!positive(account) || !positive(character) || client!=Snapshot::client_pin || kind!=Snapshot::kind)
        throw DatabaseError("Invalid native equipment key");
    // The common repositories use their existing unqualified names. Reject
    // shadows of every borrowed common source before observing those readers;
    // main-qualified witness storage alone cannot qualify the full save root.
    sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name IN ('character_native_equipment_snapshots','accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements') OR tbl_name IN ('character_native_equipment_snapshots','accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements')");
    if(shadow.row())throw DatabaseError("Native equipment TEMP shadow rejected");
    // One cursor owns both the stored witness and actual account/character
    // ownership. Do not conflate stored old profile/position with current save.
    sqlite_detail::Statement q(db_,
        "SELECT s.account_id,s.character_id,s.client_sha256,s.record_kind,s.record,s.revision,s.source_sha256,s.source_record,"
        "s.root_slot,s.root_profile,s.root_created_at,s.root_name_codepage,s.root_streamer_privilege,"
        "s.area,s.scene,s.x,s.y,s.position_revision,s.actor_handle "
        "FROM main.character_native_equipment_snapshots s JOIN main.accounts a ON a.id=s.account_id "
        "JOIN main.recovered_characters c ON c.id=s.character_id AND c.account_id=s.account_id "
        "WHERE s.account_id=? AND s.character_id=? AND s.client_sha256=? AND s.record_kind=?");
    q.bind_id(1,account);q.bind_id(2,character);q.bind(3,std::string(client));q.bind(4,std::string(kind));
    if(!q.row())return std::nullopt;
    Snapshot v;
    v.root.account_id=q.number<std::uint64_t>(0);v.root.id=q.number<std::uint64_t>(1);
    v.client_sha256=q.text(2);v.record_kind=q.text(3);
    const auto raw=q.blob(4,Snapshot::record_bytes,Snapshot::record_bytes);v.record.assign(raw.begin(),raw.end());
    v.revision=q.number<std::uint64_t>(5);v.source_sha256=q.text(6);v.source_record=q.text(7);
    v.root.slot=q.number<std::uint8_t>(8);
    const auto profile=q.blob(9,40,40);std::copy(profile.begin(),profile.end(),v.root.profile.begin());
    v.root.created_at=q.text(10);v.root.name_codepage=q.number<std::uint16_t>(11);
    v.root.streamer_privilege=q.number<std::uint8_t>(12);
    v.position.area=q.number<std::uint16_t>(13);v.position.scene=q.number<std::uint16_t>(14);
    v.position.x=q.number<std::uint16_t>(15);v.position.y=q.number<std::uint16_t>(16);
    v.position.revision=q.number<std::uint64_t>(17);v.actor_handle=q.number<std::uint16_t>(18);
    if(!valid(v) || v.root.account_id!=account || v.root.id!=character ||
       v.client_sha256!=client || v.record_kind!=kind || q.row())
        throw DatabaseError("Invalid or ambiguous native equipment observation");
    return v;
}
void SqliteNativeEquipmentSnapshotRepository::validate_change(const std::optional<Snapshot>& expected,const Snapshot& next) const {
    if(!valid(next) || (expected && (!valid(*expected) ||
        expected->root.account_id!=next.root.account_id || expected->root.id!=next.root.id ||
        expected->client_sha256!=next.client_sha256 || expected->record_kind!=next.record_kind ||
        expected->revision>=next.revision)))throw DatabaseError("Invalid native equipment CAS");
}
void SqliteNativeEquipmentSnapshotRepository::stage_replace(const std::optional<Snapshot>& expected,const Snapshot& next) {
    owner();if(!writing_||issuer_active_||reentered_||sqlite3_get_autocommit(db_))
        throw DatabaseError("Native equipment stage needs its guarded outer transaction");
    validate_change(expected,next);
    sqlite_detail::Statement write(db_,expected?
        "UPDATE main.character_native_equipment_snapshots SET record=?,revision=?,source_sha256=?,source_record=?,root_slot=?,root_profile=?,"
        "root_created_at=?,root_name_codepage=?,root_streamer_privilege=?,area=?,scene=?,x=?,y=?,position_revision=?,actor_handle=? "
        "WHERE account_id=? AND character_id=? AND client_sha256=? AND record_kind=? AND revision=?":
        "INSERT INTO main.character_native_equipment_snapshots(record,revision,source_sha256,source_record,root_slot,root_profile,"
        "root_created_at,root_name_codepage,root_streamer_privilege,area,scene,x,y,position_revision,actor_handle,account_id,character_id,client_sha256,record_kind) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");
    write.bind_blob(1,next.record);write.bind_id(2,next.revision);write.bind(3,next.source_sha256);write.bind(4,next.source_record);
    write.bind(5,next.root.slot);write.bind_blob(6,next.root.profile);write.bind(7,next.root.created_at);
    write.bind(8,next.root.name_codepage);write.bind(9,next.root.streamer_privilege);
    write.bind(10,next.position.area);write.bind(11,next.position.scene);write.bind(12,next.position.x);write.bind(13,next.position.y);
    write.bind_id(14,next.position.revision);write.bind(15,next.actor_handle);
    write.bind_id(16,next.root.account_id);write.bind_id(17,next.root.id);
    write.bind(18,next.client_sha256);write.bind(19,next.record_kind);if(expected)write.bind_id(20,expected->revision);
    write.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Native equipment CAS write failed");
    auto result=load(next.root.account_id,next.root.id,next.client_sha256,next.record_kind);
    if(result!=std::optional{next})throw DatabaseError("Native equipment staged readback differs");
}
std::optional<SqliteNativeEquipmentSnapshotRepository::Committed>
SqliteNativeEquipmentSnapshotRepository::replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    owner();
    if(writing_) {reentered_=true;throw DatabaseError("Native equipment writer reentered");}
    if(!issuer || !owns_sources(accounts_,characters_) || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Native equipment needs actual issuer and its own transaction");
    validate_change(expected,next);
    writing_=true;reentered_=false;
    struct Exit {bool& active;bool& nested;~Exit(){active=false;nested=false;}} exit{writing_,reentered_};
    {
        sqlite_detail::Statement keys(db_,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())throw DatabaseError("Native equipment requires foreign keys");
    }
    sqlite_detail::Transaction tx(db_);
    const auto roots=characters_.list_for_account(next.root.account_id);
    const auto position=characters_.load_position(next.root.account_id,next.root.id);
    std::size_t found=0;
    for(const auto& root:roots)if(root.id==next.root.id) {
        if(!Snapshot::same_root(root,next.root))throw DatabaseError("Native equipment root witness is stale");
        ++found;
    }
    if(found!=1 || !position || *position!=next.position)
        throw DatabaseError("Native equipment requires actual owned root and saved position");
    const auto common_current=[&] {
        sqlite_detail::Statement battle(db_,"SELECT 1 FROM main.battle_reservations r LEFT JOIN main.battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
        battle.bind_id(1,next.root.id);if(battle.row())return false;
        const auto actual=characters_.list_for_account(next.root.account_id);
        if(actual.size()!=roots.size())return false;
        for(std::size_t i=0;i<roots.size();++i)if(!Snapshot::same_root(actual[i],roots[i]))return false;
        return characters_.load_position(next.root.account_id,next.root.id)==position;
    };
    const auto check=[&](const std::optional<Snapshot>& wanted) {
        if(reentered_ || sqlite3_get_autocommit(db_) || !common_current() ||
            load(next.root.account_id,next.root.id,next.client_sha256,next.record_kind)!=wanted ||
            !common_current() || reentered_)throw DatabaseError("Native equipment source changed");
    };
    const auto issue=[&](WriteCheck phase) {
        const auto changes=sqlite3_total_changes64(db_);
        issuer_active_=true;struct Leave {bool& active;~Leave(){active=false;}} leave{issuer_active_};
        const auto supplied=issuer(expected,next,phase);
        if(reentered_ || sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=changes)
            throw DatabaseError("Native equipment issuer changed transaction or wrote storage");
        return supplied && *supplied==next;
    };
    check(expected);
    if(!issue(WriteCheck::Prepared))return std::nullopt;
    check(expected);
    if(!issue(WriteCheck::BeforeWrite))return std::nullopt;
    check(expected);
    stage_replace(expected,next);
    check(std::optional{next});
    if(!issue(WriteCheck::BeforeCommit))return std::nullopt;
    check(std::optional{next});
    std::optional<Committed> committed{Committed(identity_,std::make_shared<const Snapshot>(next))};
    tx.commit();return committed; // No allocation/provider/reload/retry after durable COMMIT.
}
bool SqliteNativeEquipmentSnapshotRepository::committed_current(const Committed& token) {
    owner();if(writing_){reentered_=true;return false;}
    if(token.identity_!=identity_ || !token.snapshot_ || !sqlite3_get_autocommit(db_))return false;
    ReadScope read_scope(db_);
    const auto& wanted=*token.snapshot_;
    const auto stored=load(wanted.root.account_id,wanted.root.id,wanted.client_sha256,wanted.record_kind);
    const auto roots=characters_.list_for_account(wanted.root.account_id);
    std::size_t found=0;
    for(const auto& root:roots)if(root.id==wanted.root.id) {
        if(!Snapshot::same_root(root,wanted.root))return false;
        ++found;
    }
    sqlite_detail::Statement battle(db_,"SELECT 1 FROM main.battle_reservations r LEFT JOIN main.battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    battle.bind_id(1,wanted.root.id);
    const bool same=found==1 && !battle.row() && stored==std::optional{wanted} &&
        characters_.load_position(wanted.root.account_id,wanted.root.id)==std::optional{wanted.position};
    read_scope.finish();return same;
}
std::string SqliteNativeEquipmentSnapshotRepository::schema() {
    return R"SQL(CREATE TABLE main.character_native_equipment_snapshots (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
 client_sha256 TEXT NOT NULL CHECK(typeof(client_sha256)='text' AND length(client_sha256)=64 AND client_sha256 NOT GLOB '*[^0-9a-f]*'),
 record_kind TEXT NOT NULL CHECK(typeof(record_kind)='text' AND length(CAST(record_kind AS BLOB)) BETWEEN 1 AND 64 AND instr(record_kind,char(0))=0),
 record BLOB NOT NULL CHECK(typeof(record)='blob' AND length(record)=1215),
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
 actor_handle INTEGER NOT NULL CHECK(typeof(actor_handle)='integer' AND actor_handle BETWEEN 0 AND 16383),
 position_revision INTEGER NOT NULL CHECK(typeof(position_revision)='integer' AND position_revision>0),
 PRIMARY KEY(account_id,character_id,client_sha256,record_kind),
 FOREIGN KEY(account_id) REFERENCES accounts(id),
 FOREIGN KEY(character_id) REFERENCES recovered_characters(id) ON DELETE CASCADE
) WITHOUT ROWID;
)SQL";
}
}
