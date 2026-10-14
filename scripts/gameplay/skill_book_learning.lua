-- CUSTOM-0148: explicit shared learning policy, not a native recovered rule.
-- Numeric/boolean snapshots only; no Session, database, issuer or send objects.
local M = {}
function M.policy(p)
    local allowed = p.display_valid and p.book_count >= 1
        and (p.already_learned or p.skill_count < 100)
    return { allowed = allowed, duplicate = p.already_learned,
        consume = allowed and not p.already_learned and 1 or 0 }
end
return M
