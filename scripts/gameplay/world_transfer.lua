-- CUSTOM-0155: the host supplied this exact source-qualified immutable route.
-- Lua owns activation policy; C++ rechecks identity, movement witness and CAS.
return {
    plan = function(input)
        if input.before_x == input.x and input.before_y == input.y then return nil end
        return input.route_id
    end,
}
