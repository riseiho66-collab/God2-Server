-- CUSTOM-0085: placement policy for owned full PET instances. Native28 has
-- no destination. Bag -> native beast37;37 -> lowest explicitly owned empty
-- bag cell. This is not original server selection, riding or appearance.
local M = {}
function M.destination(snapshot)
    if snapshot.source_slot < 30 then return 37 end
    if snapshot.source_slot ~= 37 then return nil end
    local lowest = nil
    for _, slot in ipairs(snapshot.owned_empty_slots) do
        if lowest == nil or slot < lowest then lowest = slot end
    end
    return lowest
end
return M
