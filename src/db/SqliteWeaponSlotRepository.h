#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
struct StoredWeaponSlot {
    std::uint8_t slot{};
    std::uint16_t item_id{};
    std::uint8_t count{};
    std::uint64_t revision{};
    std::array<std::uint8_t,20> logical20{};
    std::string origin,provenance;
    bool metadata_present{};
    bool operator==(const StoredWeaponSlot&) const = default;
};
struct WeaponSlotMove {StoredWeaponSlot source,destination;};
// CUSTOM-0046: persistence/whole-instance transfer policy, not native item stats.
// Scalar occupancy remains in diagnostic_inventory_slots. No acquisition API.
class SqliteWeaponSlotRepository {
public:
    using QualifyWeapon=std::function<bool(std::uint16_t)>;
    using Prepare=std::function<void(const WeaponSlotMove&)>;
    static constexpr const char* source_sha256="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr const char* client_sha256="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
    explicit SqliteWeaponSlotRepository(sqlite3* db,QualifyWeapon qualify);
    // Missing scalar -> absent. Occupied nonweapon without metadata -> absent.
    // Qualified occupied weapon without metadata, or any corrupt metadata -> error.
    std::optional<StoredWeaponSlot> load(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
    std::vector<StoredWeaponSlot> load_saved(std::uint64_t account,std::uint64_t character);
    // Both slots must already exist; no grants/allocation/stack merge. prepare
    // encodes the candidate projection before COMMIT; throwing rolls back all rows.
    WeaponSlotMove move(std::uint64_t account,std::uint64_t character,
        const StoredWeaponSlot& expected_source,const StoredWeaponSlot& expected_destination,
        const Prepare& prepare);
private:
    void owner(std::uint64_t account,std::uint64_t character);
    std::optional<StoredWeaponSlot> read(std::uint64_t character,std::uint8_t slot);
    void write(std::uint64_t character,const StoredWeaponSlot& before,const StoredWeaponSlot& after);
    sqlite3* db_;
    QualifyWeapon qualify_;
};
}
