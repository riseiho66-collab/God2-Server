-- CUSTOM-0085: whole ordinary-bag PET custody transfer between two consenting
-- live players. This custom rule is not original binding/activity policy.
-- No item generation, stat, EXP, lifespan, currency or appearance effect.
local M = {}
function M.allowed(snapshot)
    return snapshot.source_slot >= 0 and snapshot.source_slot < 30
        and snapshot.quantity == 1
        and not snapshot.native_exploring
        and not snapshot.alternate_control7
        and not snapshot.alternate_control8
end
return M
