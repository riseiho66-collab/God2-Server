register_npc(1001, {
    name = "Test NPC",
    on_talk = function(player)
        log("Player " .. player.name .. " talked to Test NPC")
        return {
            text = "Hello, welcome to GOD2 rebuild server.",
            options = {
                { id = 1, text = "Who are you?" },
                { id = 2, text = "Goodbye." }
            }
        }
    end
})
