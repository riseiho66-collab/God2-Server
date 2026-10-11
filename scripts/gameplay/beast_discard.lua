-- CUSTOM-0085: destroy exactly one already owned ordinary-bag PET instance.
-- Native27 supplies item/slot/quantity but no server bind/drop policy or nonce.
-- This custom policy excludes equipped37 and saved exploring/alternate-control
-- states; it does not claim original activity, riding or binding semantics.
local M = {}
function M.allowed(snapshot)
    return snapshot.source_slot >= 0 and snapshot.source_slot < 30
        and snapshot.quantity == 1
        and not snapshot.native_exploring
        and not snapshot.alternate_control7
        and not snapshot.alternate_control8
end
return M
