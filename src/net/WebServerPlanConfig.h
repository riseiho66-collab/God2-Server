#pragma once
#include "net/WebServerPlan.h"
#include <filesystem>
#include <nlohmann/json_fwd.hpp>

namespace god2 {
// Explicit transport configuration only. No source factory, native destination,
// DB access, bind, migration or gameplay permission is provided by this parser.
struct WebServerPlanConfig {
    // CUSTOM host-input budget, not a native packet/resource limit.
    static constexpr std::size_t max_file_bytes=64*1024;
    static WebServerPlan from_json(const nlohmann::json&);
    static WebServerPlan load(const std::filesystem::path&);
};
}
