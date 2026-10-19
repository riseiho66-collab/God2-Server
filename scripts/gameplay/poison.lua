-- CUSTOM-0157: owner-directed one tenth of CURRENT maximum HP.
-- Owner-confirmed floor: maximum123 costs12HP. No tick, expiry or HP mutation.
-- C++ passes a nonnegative Lua5.4 signed64 integer, never a floating value.
local M = {}
function M.share(p)
    local maximum = p.target_current_max_hp
    local whole = maximum // 10
    return {
        whole_hp = whole,
        damage_hp = whole, -- Fractional tenths are discarded, with no minimum1.
        remainder_tenths = maximum % 10 -- Diagnostics only; never accumulated.
    }
end
return M
