#pragma once
#include <sol/sol.hpp>
#include <string>
namespace god2 {
struct ScriptNpc { std::string name; sol::protected_function on_talk; };
}
