-- CUSTOM-0013: explicit-table projection; no official thresholds or stat growth.
-- XP remains banked in C++ storage. A lock clamps display, never consumes XP.
local M = {}
function M.project(p)
    local thresholds = p.thresholds
    local level = 1
    while level < p.unlocked_level and p.total >= thresholds[level + 1] do
        level = level + 1
    end
    local progress = 10000
    if level < #thresholds then
        local span = thresholds[level + 1] - thresholds[level]
        local earned = math.min(p.total - thresholds[level], span)
        progress = (earned * 10000) // span
    end
    return { level = level, progress_display = progress }
end
return M
