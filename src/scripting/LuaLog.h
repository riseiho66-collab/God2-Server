#pragma once

#include <spdlog/spdlog.h>

namespace god2::detail {
inline std::shared_ptr<spdlog::logger> lua_logger() {
    auto logger = spdlog::get("lua");
    return logger ? logger : spdlog::default_logger();
}
} // namespace god2::detail
