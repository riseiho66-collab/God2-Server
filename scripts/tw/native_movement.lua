-- TW native RVA102700..1027B2: ordinary adjacent step direction.
-- CN00539150 independently has the same table. This TW source does not
-- adopt legacy TW timing/index/echo policies as CN native authority.
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
-- TW102F20's eight-direction probe calls46FF0 at102FCB and rejects zero
-- at102FD2; every direction reaches that raw-cell predicate.
-- This is a necessary raw-cell predicate, not all path/corner/entity/server
-- permission rules. Real map/direction/timing/pending context is mandatory.
function rules.native_cell_qualifies(native_cell)
    return native_cell ~= 0
end
return rules
