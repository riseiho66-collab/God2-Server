-- CUSTOM-0085 inactive whole PET vault custody, not original binding policy.
-- Native63/64 quantities are amounts;65 quantity1 is the whole-cell marker.
-- No acquisition, timer, riding/stat/appearance or activity effect.
local M = {}
function M.allowed(snapshot)
    return snapshot.operation >= 99 and snapshot.operation <= 101
        and snapshot.page >= 0 and snapshot.page < 3
        and snapshot.quantity == 1
        and not snapshot.native_exploring
        and not snapshot.alternate_control7
        and not snapshot.alternate_control8
end
return M
