-- CN native00539150 direction calculation for an ordinary adjacent path step.
-- This classifies geometry only. It grants no walkability, timing or ownership.
local rules = {}
function rules.step_direction(x, y, next_x, next_y, previous_direction)
    local dx, dy = next_x - x, next_y - y
    if dx < -1 or dx > 1 or dy < -1 or dy > 1 then return nil end
    if dx > 0 then
        if dy > 0 then return 3 end
        if dy == 0 then return 2 end
        return 1
    elseif dx == 0 then
        if dy > 0 then return 4 end
        if dy == 0 then return previous_direction end
        return 0
    else
        if dy > 0 then return 5 end
        if dy == 0 then return 6 end
        return 7
    end
end
-- 00486B80 filters each candidate by its raw cell, with no adjacent-cardinal
-- check in that function. This predicate alone is not the complete path search.
function rules.native_neighbor_passable(native_cell)
    return native_cell ~= 0
end
return rules
