-- TW native RVA102700..1027B2: ordinary adjacent step direction.
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
-- CUSTOM-0150 explicit server policy. Sequence/timing/reset/5D token are
-- not recovered native-server facts. Required scalar policy is supplied by
-- the actual resource installation; this file supplies no gameplay defaults.
function rules.owned_ordinary_token(sequence, expected_sequence, dx, dy,
    allow_zero, block_players, occupied, forbid_corner_cut, sides_clear)
    if sequence ~= expected_sequence then return nil end
    if dx < -1 or dx > 1 or dy < -1 or dy > 1 then return nil end
    if dx == 0 and dy == 0 and not allow_zero then return nil end
    if block_players and occupied then return nil end
    if forbid_corner_cut and dx ~= 0 and dy ~= 0 and not sides_clear then return nil end
    -- Explicit CUSTOM echo. Original server5D value remains unrecovered.
    return sequence
end
return rules
