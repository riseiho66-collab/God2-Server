-- Authorization and the actual reload are host responsibilities. Never replace
-- the active VM from inside a callback executing in that same VM.
register_gm_command("reload_scripts", function(admin, args)
    log("Reload requested by " .. admin.name)
end)
