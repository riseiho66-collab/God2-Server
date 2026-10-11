register_event("server_start", function()
    log("World content is ready")
end)

register_event("server_stop", function()
    log("World content is stopping")
end)
