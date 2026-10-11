#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include <array>
#include <functional>
#include <optional>
#include <vector>

namespace god2 {
// CUSTOM-0066: owned whole armor instances, not native generation or stat rules.
// Scalar occupancy remains in diagnostic_inventory_slots; no acquisition API.
struct StoredArmorSlot {
    std::uint8_t slot{};
    std::uint16_t item_id{};
    std::uint8_t count{};
    std::uint64_t revision{};
    std::array<std::uint8_t,20> logical20{};
    std::string origin,provenance;
    bool metadata_present{};
    bool operator==(const StoredArmorSlot&) const=default;
};
struct ArmorForeignOverlay {
    std::uint8_t slot{};
    std::array<std::uint8_t,20> logical20{};
    std::uint64_t revision{};
    std::string origin,provenance,source_sha256,client_sha256,design_id;
    bool operator==(const ArmorForeignOverlay&) const=default;
};
struct ArmorSnapshot {
    std::uint64_t account{},character{};
    // Missing cells remain absent, never implicit free capacity. Observe the
    // protected34..49 domain without allocating, projecting or changing it.
    std::array<std::optional<StoredInventorySlot>,50> scalar;
    std::vector<StoredArmorSlot> armor;
    std::vector<ArmorForeignOverlay> weapons,gems;
    bool operator==(const ArmorSnapshot&) const=default;
};
struct ArmorSlotMove {
    StoredArmorSlot source,destination;
    ArmorSnapshot after;
};
class SqliteArmorSlotRepository {
public:
    using QualifyArmor=std::function<std::optional<std::uint8_t>(std::uint16_t)>;
    using QualifyInstance=std::function<bool(std::uint16_t,const std::array<std::uint8_t,20>&)>;
    using Prepare=std::function<void(const ArmorSlotMove&)>;
    static constexpr const char* source_sha256="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr const char* client_sha256="c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575";
    static constexpr const char* design_id="CUSTOM-0066";
    // Explicit schema installation by the caller only. Requires existing scalar,
    // weapon and gem tables; adds no inventory/instance/player rows.
    static std::string schema();
    SqliteArmorSlotRepository(sqlite3* db,QualifyArmor qualify,QualifyInstance qualify_instance={});
    bool shares_connection(sqlite3* db) const noexcept{return db_==db;}
    ArmorSnapshot load_snapshot(std::uint64_t account,std::uint64_t character);
    std::optional<StoredArmorSlot> load(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
    std::vector<StoredArmorSlot> load_saved(std::uint64_t account,std::uint64_t character);
    // nullopt means absent/nonarmor occupied cell, not an empty destination.
    std::optional<StoredArmorSlot> inspect(const ArmorSnapshot&,std::uint8_t slot) const;
    std::optional<std::uint8_t> target(std::uint16_t item) const;
    ArmorSlotMove plan(const ArmorSnapshot&,std::uint8_t source,std::uint8_t destination) const;
    // Full owner50-slot/three-overlay snapshot CAS, two physical revisions,
    // pending-battle denial, preparation and complete readback before COMMIT.
    ArmorSlotMove move(const ArmorSnapshot& expected,std::uint8_t source,std::uint8_t destination,const Prepare& prepare);
private:
    void owner(std::uint64_t account,std::uint64_t character);
    void validate(const ArmorSnapshot&) const;
    sqlite3* db_;
    QualifyArmor qualify_;
    QualifyInstance qualify_instance_;
};
}
