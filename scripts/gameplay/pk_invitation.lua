-- CUSTOM-0086 proposal eligibility. C++ owns both live identities, exact
-- wire context, transient lease, room reservation and all state/storage.
-- Original PK permissions/range/fees are unrecovered. No combat grant here.
local M = {}
function M.allowed(snapshot)
    return snapshot.challenger_ready and snapshot.recipient_ready
        and snapshot.same_scene and snapshot.distinct_characters
        and not snapshot.challenger_blocked and not snapshot.recipient_blocked
end
return M
