-- CUSTOM-0157: owner-directed one tenth of CURRENT maximum HP.
-- Exact unrounded share only. No tick, expiry, HP mutation or native claim.
-- C++ passes a nonnegative Lua5.4 signed64 integer, never a floating value.
local M = {}
function M.share(p)
    local maximum = p.target_current_max_hp
    return {
        whole_hp = maximum // 10,
        remainder_tenths = maximum % 10
    }
end
return M
