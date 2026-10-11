-- CUSTOM-0016: isolated non-revival supply policy, not recovered native rules.
local M = {}
function M.project(p)
    if p.hp == 0 then
        return { hp = p.hp, mp = p.mp, consume = false }
    end
    local hp = p.hp + math.min(p.restore_hp, p.max_hp - p.hp)
    local mp = p.mp + math.min(p.restore_mp, p.max_mp - p.mp)
    return { hp = hp, mp = mp, consume = hp ~= p.hp or mp ~= p.mp }
end
return M
