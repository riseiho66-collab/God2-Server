-- Content hooks only. The host owns quest persistence and reward validation.
register_quest(2001, {
    name = "Welcome to GOD2",
    on_accept = function(player)
        log(player.name .. " accepted the welcome quest")
    end,
    on_complete = function(player)
        log(player.name .. " completed the welcome quest")
    end
})
