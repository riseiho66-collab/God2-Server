-- OWNER_CONFIRMED 2026-09-27. Level 1 is a supplied baseline, never a growth step.
-- Catalog IDs are not client create-profile byte values. No EXP/HP/MP inference.
local rules = {
    [1] = {2,3,0,1}, -- Swordsman: constitution, strength, intelligence, speed
    [2] = {1,0,3,2}, -- Taoist
    [3] = {2,0,2,2}, -- Pharmacist
    [4] = {1,1,1,3}, -- Warlock
}
local M = {}
function M.project(p)
    local step = p.next_level - p.previous_level
    local output = {}
    for i=1,4 do output[i] = p.attributes[i] + rules[p.profession][i] * step end
    return {attributes=output, unspent_points=p.unspent_points + 4*step}
end
-- NATIVE_VERIFIED 4E8B2A..4E8C22: exactly one selected base point,
-- with remaining points decremented once. No derived combat/resource rule.
function M.allocate(p)
    local indices = {3,1,2,4} -- wire selector1=int,2=con,3=str,4=speed
    local selected = indices[p.selector]
    local output = {}
    for i=1,4 do output[i] = p.attributes[i] + (i==selected and 1 or 0) end
    return {attributes=output, unspent_points=p.unspent_points-1}
end
return M
