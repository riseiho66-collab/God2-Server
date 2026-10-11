#pragma once

#include <sol/sol.hpp>
#include <array>
#include <cstring>

namespace god2::detail {

// Lives outside lua_pcall: Lua's hook error must never longjmp across this guard.
class LuaInstructionBudget {
public:
    static constexpr int instruction_limit = 1'000'000;
    static constexpr int hook_interval = 1'000;
    static constexpr const char* error_message = "Lua instruction budget exceeded";

    explicit LuaInstructionBudget(lua_State* state) noexcept
        : state_(state), previous_hook_(lua_gethook(state)),
          previous_mask_(lua_gethookmask(state)), previous_count_(lua_gethookcount(state)) {
        static_assert(LUA_EXTRASPACE >= sizeof(remaining_));
        if (previous_hook_ == count_hook) {
            // Nested require must retain both the budget and the partial hook count.
            std::memcpy(&remaining_, lua_getextraspace(state_), sizeof(remaining_));
        } else {
            installed_ = true;
            std::memcpy(previous_extra_.data(), lua_getextraspace(state_), LUA_EXTRASPACE);
            std::memcpy(lua_getextraspace(state_), &remaining_, sizeof(remaining_));
            lua_sethook(state_, count_hook, LUA_MASKCOUNT, hook_interval);
        }
    }

    ~LuaInstructionBudget() noexcept {
        if (installed_) {
            lua_sethook(state_, previous_hook_, previous_mask_, previous_count_);
            std::memcpy(lua_getextraspace(state_), previous_extra_.data(), LUA_EXTRASPACE);
        }
    }
    LuaInstructionBudget(const LuaInstructionBudget&) = delete;
    LuaInstructionBudget& operator=(const LuaInstructionBudget&) = delete;

    bool exhausted() const noexcept { return *remaining_ == 0; }

private:
    static void count_hook(lua_State* state, lua_Debug*) {
        // Only trivial locals here: luaL_error unwinds through Lua's C longjmp.
        int* remaining;
        std::memcpy(&remaining, lua_getextraspace(state), sizeof(remaining));
        if (*remaining <= hook_interval) {
            *remaining = 0;
            luaL_error(state, "%s", error_message);
            return;
        }
        *remaining -= hook_interval;
    }

    lua_State* state_;
    lua_Hook previous_hook_;
    int previous_mask_;
    int previous_count_;
    int own_remaining_ = instruction_limit;
    int* remaining_ = &own_remaining_;
    std::array<unsigned char, LUA_EXTRASPACE> previous_extra_{};
    bool installed_ = false;
};

} // namespace god2::detail
