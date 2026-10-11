-- Sample content is selected by the host's PLACEHOLDER runtime policy.
if not GOD2_FIXTURE_MODE then return end

require("npc.test_npc")
require("quests.test_quest")
require("monsters.test_ai")
require("events.test_event")
require("gm.gm_commands")

register_event("server_start", function()
    log("GOD2 server_start event fired")
end)
