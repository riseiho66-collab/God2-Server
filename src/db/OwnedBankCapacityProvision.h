#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include <nlohmann/json.hpp>
#include <string_view>
namespace god2 {
// Explicit operator CUSTOM capacity, never recovered unlock/economic rules.
// The planner has no connection and cannot write or create an owner/item.
class OwnedBankCapacityProvision final {
public:
    using Tx=SqliteOwnedEquipmentTransaction;
    struct Plan {Tx::Before expected;Tx::State next;std::string permit_id;};
    static nlohmann::json complete_material(const Tx::State&);
    static nlohmann::json draft(const Tx::State&,std::string_view database_identity);
    static void preflight(const nlohmann::json&);
    static Plan plan(const nlohmann::json&,const Tx::Before&,std::string_view database_identity);
    // Strict duplicate keys, floats, unknown top-level fields, size and depth
    // refused before any database owner/SQL is opened by the actual CLI.
    static nlohmann::json parse(std::string_view);
};
}
