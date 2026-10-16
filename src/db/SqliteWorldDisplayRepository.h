#pragma once
#include "db/NativeNpcDisplayCatalog.h"
#include "db/NativeEnemyDisplayCatalog.h"
#include <array>
#include <atomic>
#include <memory>
#include <thread>
#include <utility>
#include <cstdint>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Explicit server-owned scene records. A consumer address never supplies rows.
// Importers must establish complete map/record evidence before native admission.
struct StoredWorldDisplay {
    std::uint16_t area{},scene{};
    std::array<std::uint8_t,21> logical{};
    std::string origin,provenance;
    bool operator==(const StoredWorldDisplay&) const=default;
};
struct StoredMonsterLevel {
    std::uint16_t area{},scene{},identity{},level{};
    std::string origin,provenance;
    bool operator==(const StoredMonsterLevel&) const=default;
};
class SqliteWorldDisplayRepository {
    struct Identity {};
    struct Operation;
    struct ReadScope;
public:
    explicit SqliteWorldDisplayRepository(sqlite3* db):db_(db){}
    SqliteWorldDisplayRepository(const SqliteWorldDisplayRepository&)=delete;
    SqliteWorldDisplayRepository& operator=(const SqliteWorldDisplayRepository&)=delete;
    // Pure same-connection qualification; no SQL, schema access or row grant.
    bool uses_catalogs(const NativeNpcDisplayCatalog& npcs,const NativeEnemyDisplayCatalog& enemies) const noexcept {
        return db_&&npcs.uses_connection(db_)&&enemies.uses_connection(db_);
    }
    // Pure owning VALUE observation from this exact issuer. No DB/repository,
    // callbacks, game state, full-scene coverage or empty-world proof retained.
    class SceneReadset final {
    public:
        SceneReadset(const SceneReadset&)=default;
        SceneReadset& operator=(const SceneReadset&)=default;
        std::uint16_t area() const noexcept;
        std::uint16_t scene() const noexcept;
        bool isolated_test() const noexcept;
        const std::vector<StoredWorldDisplay>& rows() const noexcept;
        const std::vector<StoredMonsterLevel>& levels() const noexcept;
        const NativeNpcDisplayCatalog::References& npc_references() const noexcept;
        const NativeEnemyDisplayCatalog::References& enemy_references() const noexcept;
    private:
        friend class SqliteWorldDisplayRepository;
        struct Data;
        explicit SceneReadset(std::shared_ptr<const Data> value) noexcept:data_(std::move(value)){}
        std::shared_ptr<const Data> data_;
    };
    // Same actual connection; one owned read snapshot or the caller's existing
    // transaction. A borrowed transaction is never committed or rolled back.
    SceneReadset observe_scene(const NativeNpcDisplayCatalog&,const NativeEnemyDisplayCatalog&,
        std::uint16_t area,std::uint16_t scene,bool isolated_test=false) const;
    // Fresh full value comparison only; no transaction/instance ABA receipt,
    // native cache generation, world completeness or gameplay authority.
    bool current_scene(const SceneReadset&,const NativeNpcDisplayCatalog&,
        const NativeEnemyDisplayCatalog&) const noexcept;
    // Strictly borrow the caller's already active same-connection snapshot.
    // Never begin, commit or roll back a transaction on this path.
    bool current_scene_in_scope(sqlite3*,const SceneReadset&,const NativeNpcDisplayCatalog&,
        const NativeEnemyDisplayCatalog&) const noexcept;
    static const char* schema() noexcept;
    static const char* level_schema() noexcept;
    // Immutable insert: conflicting instance records are rejected, never replaced.
    void insert(const StoredWorldDisplay& record);
    void insert_level(const StoredMonsterLevel& record);
    std::vector<StoredMonsterLevel> load_levels(std::uint16_t area,std::uint16_t scene,bool isolated_test=false) const;
    std::vector<StoredWorldDisplay> load(std::uint16_t area,std::uint16_t scene,bool isolated_test=false) const;
private:
    void reject_scene_reentry() const;
    std::vector<StoredWorldDisplay> load_rows_impl(std::uint16_t,std::uint16_t,bool,bool main) const;
    std::vector<StoredMonsterLevel> load_levels_impl(std::uint16_t,std::uint16_t,bool,bool main) const;
    std::shared_ptr<const SceneReadset::Data> capture_scene(const NativeNpcDisplayCatalog&,
        const NativeEnemyDisplayCatalog&,std::uint16_t,std::uint16_t,bool,bool require_borrowed=false) const;
    sqlite3* db_;
    // Application constructs this repository inside its serial game thread.
    // Legacy public reads/writes keep their old thread behavior when no new
    // scene observation is active; active reentry is explicitly rejected.
    const std::thread::id thread_=std::this_thread::get_id();
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    mutable std::atomic<bool> busy_{false},poisoned_{false};
};
}
