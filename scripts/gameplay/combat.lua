-- CUSTOM-0006: designed formula, not recovered native combat.
-- C++ selects skill/stats, supplies the RNG roll and atomically commits HP/MP.
local M = {}
function M.damage(p)
    local scaled_attack = math.floor(p.attack * p.power_percent / 100)
    local scaled_defense = math.floor(p.defense * p.defense_percent / 100)
    local damage = math.max(1, scaled_attack - scaled_defense)
    local critical = p.roll < p.critical_chance_bp
    if critical then
        damage = math.floor(damage * p.critical_multiplier_percent / 100)
    end
    return { damage = math.min(1000000, damage), mp_cost = p.mp_cost, critical = critical }
end
return M
