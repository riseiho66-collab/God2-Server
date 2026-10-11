-- CUSTOM-0021: source texts are native; selection/transition policy is custom.
-- No actor access, persistence, item grant, XP or reputation mutation.
local plans = {
    [0] = { [1606] = {894, 1, 1, false}, [1607] = {898, 0, 0, false} },
    [1] = { [1606] = {895, 1, 1, false}, [1607] = {899, 2, 2, false} },
    [2] = { [1606] = {896, 3, 0, true},  [1607] = {900, 2, 2, false} },
    [3] = { [1606] = {897, 3, 0, false}, [1607] = {901, 3, 0, false} },
}
return {
    plan = function(input)
        local stage = plans[input.stage]
        local row = stage and stage[input.npc]
        assert(row, "Unsupported town guide state/target")
        return {
            text_key = row[1], confirmed_stage = row[2],
            journal_description = row[3], requires_reward = row[4],
        }
    end,
}
