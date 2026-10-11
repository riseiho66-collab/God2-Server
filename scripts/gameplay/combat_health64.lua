-- CUSTOM-0090: owner-authorized exact integer extension of CUSTOM-0006.
-- Same coefficients and floor order; no native formula/skill/balance claim.
-- C++ admits integer uint32 stats and bounded percentages before invocation.
-- Largest admitted integer product: 429496729500000, within signed64.
local M = {}
function M.damage(p)
    local scaled_attack = (p.attack * p.power_percent) // 100
    local scaled_defense = (p.defense * p.defense_percent) // 100
    local damage = math.max(1, scaled_attack - scaled_defense)
    local critical = p.roll < p.critical_chance_bp
    if critical then
        damage = (damage * p.critical_multiplier_percent) // 100
    end
    return { damage = damage, mp_cost = p.mp_cost, critical = critical }
end
return M
