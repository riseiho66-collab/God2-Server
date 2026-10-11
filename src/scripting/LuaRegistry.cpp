#include "scripting/LuaRegistry.h"
#include <cmath>
#include <limits>
#include <stdexcept>

namespace god2 {
std::uint32_t script_id(const sol::object& value) {
    if (value.get_type() != sol::type::number)
        throw std::runtime_error("script id must be a positive uint32");
    const double id = value.as<double>();
    if (!std::isfinite(id) || id < 1 || id > std::numeric_limits<std::uint32_t>::max()
        || std::floor(id) != id)
        throw std::runtime_error("script id must be a positive uint32");
    return static_cast<std::uint32_t>(id);
}

std::string script_name(const sol::object& value) {
    if (value.get_type() != sol::type::string)
        throw std::runtime_error("script name must be a string");
    auto name = value.as<std::string>();
    if (name.empty() || name.size() > 256)
        throw std::runtime_error("script name must contain 1 to 256 bytes");
    return name;
}

sol::protected_function script_function(const sol::object& value) {
    if (value.get_type() != sol::type::function)
        throw std::runtime_error("script callback must be a function");
    return value.as<sol::protected_function>();
}
} // namespace god2
