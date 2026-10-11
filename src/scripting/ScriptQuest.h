#pragma once
#include <sol/sol.hpp>
#include <string>
namespace god2 {
struct ScriptQuest {
    std::string name;
    sol::protected_function on_accept;
    sol::protected_function on_complete;
};
}
