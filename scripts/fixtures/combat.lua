-- Custom fixture-only formulas, not recovered native combat behavior.
-- CUSTOM-0001: docs/custom-designs.json; not a production/native balance model.
-- Inputs are bounded snapshots; the C++ service owns all HP/MP mutations.
local floor, max = math.floor, math.max
local rules = {
    [1] = { attack = "physical_attack", defense = "physical_defense", power = 100, cost = 0 },
    [2] = { attack = "magical_attack", defense = "magical_defense", power = 150, cost = 8 },
    [3] = { attack = "physical_attack", defense = "physical_defense", power = 200, cost = 20 },
}

return {
    damage = function(attacker, defender, skill, roll)
        local rule = assert(rules[skill], "invalid fixture skill")
        local damage = max(1, floor(attacker[rule.attack] * rule.power / 100) - defender[rule.defense])
        local critical = roll < 1000
        if critical then damage = floor(damage * 150 / 100) end
        return { damage = damage, mp_cost = rule.cost, critical = critical }
    end,
}
