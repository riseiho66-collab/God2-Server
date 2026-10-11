#include "db/SqlitePlayerAppearanceRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <utility>

namespace god2 {
namespace {
constexpr auto maximum_revision = static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void owner_domain(std::uint64_t account, std::uint64_t character) {
    if (!account || account > maximum_revision || !character || character > 0x3fff)
        throw DatabaseError("Player appearance owner outside native world domain");
}
void validate(const StoredPlayerAppearance& row, std::uint64_t character) {
    if (!row.revision || row.revision > maximum_revision ||
        row.fields.actor_identity != character || row.fields.transform_key != 0 ||
        (row.origin != "NATIVE_CAPTURE_VERIFIED" && row.origin != "CUSTOM_TEST_NOT_NATIVE") ||
        row.provenance.empty() || row.provenance.size() > 255 || row.provenance.find('\0') != std::string::npos ||
        row.client_sha256 != SqlitePlayerAppearanceRepository::client_sha256 ||
        row.design_id != SqlitePlayerAppearanceRepository::design_id)
        throw DatabaseError("Invalid owned ordinary player appearance snapshot");
}
class AtomicSave {
public:
    explicit AtomicSave(sqlite3* db) : db_(db), owned_(sqlite3_get_autocommit(db) != 0) {
        sqlite_detail::execute(db_, owned_ ? "BEGIN IMMEDIATE" : "SAVEPOINT god2_player_appearance_save");
    }
    ~AtomicSave() {
        if (finished_) return;
        if (owned_) sqlite3_exec(db_, "ROLLBACK", nullptr, nullptr, nullptr);
        else {
            // Never issue a whole-transaction ROLLBACK for a borrowed connection.
            sqlite3_exec(db_, "ROLLBACK TO god2_player_appearance_save", nullptr, nullptr, nullptr);
            sqlite3_exec(db_, "RELEASE god2_player_appearance_save", nullptr, nullptr, nullptr);
        }
    }
    AtomicSave(const AtomicSave&) = delete;
    AtomicSave& operator=(const AtomicSave&) = delete;
    void commit() {
        sqlite_detail::execute(db_, owned_ ? "COMMIT" : "RELEASE god2_player_appearance_save");
        finished_ = true;
    }
private:
    sqlite3* db_;
    bool owned_, finished_ = false;
};
}

const char* SqlitePlayerAppearanceRepository::schema() noexcept {
    return R"SQL(CREATE TABLE character_player_appearance_snapshots(
        character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE
            CHECK(character_id BETWEEN 1 AND 16383),
        logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=15),
        base_components BLOB NOT NULL CHECK(typeof(base_components)='blob' AND length(base_components)=8),
        revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
        origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
        provenance TEXT NOT NULL CHECK(typeof(provenance)='text' AND length(CAST(provenance AS BLOB)) BETWEEN 1 AND 255 AND instr(provenance,char(0))=0),
        client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
        design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0047')
    ))SQL";
}

SqlitePlayerAppearanceRepository::SqlitePlayerAppearanceRepository(sqlite3* db) : db_(db) {
    if (!db_) throw DatabaseError("Null player appearance connection");
}
std::optional<StoredPlayerAppearance> SqlitePlayerAppearanceRepository::load(std::uint64_t account, std::uint64_t character) {
    owner_domain(account, character);
    sqlite_detail::Statement query(db_,
        "SELECT s.character_id IS NOT NULL,s.logical,s.revision,s.origin,s.provenance,s.client_sha256,s.design_id,s.base_components "
        "FROM recovered_characters c LEFT JOIN character_player_appearance_snapshots s ON s.character_id=c.id "
        "WHERE c.account_id=? AND c.id=?");
    query.bind_id(1, account); query.bind_id(2, character);
    if (!query.row()) throw DatabaseError("Player appearance owner mismatch");
    if (!query.integer(0)) return std::nullopt;
    const auto fields = RecoveredPlayerAppearanceUpdate::decode(query.blob(1, 15, 15));
    if (!fields) throw DatabaseError("Player appearance codec mismatch");
    RecoveredPlayerAppearanceUpdate::Components base{};
    const auto raw_base = query.blob(7, 8, 8);
    for (std::size_t i=0; i<base.size(); ++i) base[i]=raw_base[i];
    StoredPlayerAppearance row{query.number<std::uint64_t>(2), *fields, base, query.text(3),
        query.text(4), query.text(5), query.text(6)};
    validate(row, character);
    return row;
}
StoredPlayerAppearance SqlitePlayerAppearanceRepository::save(std::uint64_t account, std::uint64_t character,
    std::optional<std::uint64_t> expected_revision, const RecoveredPlayerAppearanceUpdate::Fields& fields,
    std::string origin, std::string provenance,
    std::optional<RecoveredPlayerAppearanceUpdate::Components> baseline) {
    owner_domain(account, character);
    if (expected_revision && (!*expected_revision || *expected_revision >= maximum_revision))
        throw DatabaseError("Player appearance revision bound");
    StoredPlayerAppearance next{expected_revision ? *expected_revision + 1 : 1, fields,
        baseline.value_or(fields.components),
        std::move(origin), std::move(provenance), client_sha256, design_id};
    validate(next, character);
    const auto logical = RecoveredPlayerAppearanceUpdate::encode(fields);
    AtomicSave transaction(db_);
    const auto before = load(account, character);
    if (before.has_value() != expected_revision.has_value() ||
        (before && before->revision != *expected_revision))
        throw DatabaseError("Player appearance revision conflict");
    if (before) {
        if (baseline && *baseline != before->base_components)
            throw DatabaseError("Player appearance baseline is immutable");
        next.base_components = before->base_components;
    }
    sqlite_detail::Statement pending(db_,
        "SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id "
        "WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1, character);
    if (pending.row()) throw DatabaseError("Player appearance change during pending battle");
    sqlite_detail::Statement write(db_, before ?
        "UPDATE character_player_appearance_snapshots SET logical=?,revision=?,origin=?,provenance=?,client_sha256=?,design_id=?,base_components=? WHERE character_id=? AND revision=?" :
        "INSERT INTO character_player_appearance_snapshots(logical,revision,origin,provenance,client_sha256,design_id,base_components,character_id) VALUES(?,?,?,?,?,?,?,?)");
    write.bind_blob(1, logical); write.bind_id(2, next.revision); write.bind(3, next.origin);
    write.bind(4, next.provenance); write.bind(5, next.client_sha256); write.bind(6, next.design_id);
    write.bind_blob(7, next.base_components); write.bind_id(8, character);
    if (before) write.bind_id(9, *expected_revision);
    write.done();
    if (sqlite3_changes(db_) != 1 || load(account, character) != std::optional(next))
        throw DatabaseError("Player appearance write/readback mismatch");
    transaction.commit();
    return next;
}
}
