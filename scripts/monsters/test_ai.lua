register_monster_ai(3001, {
    on_spawn = function(monster)
        log("Monster spawned: " .. monster.id)
    end,
    on_update = function(monster, dt)
        if monster.hp <= 0 then return end
        -- A future validated host API can accept movement/combat intents here.
    end,
    on_death = function(monster, killer)
        log("Monster " .. monster.id .. " defeated by " .. killer.name)
    end
})
