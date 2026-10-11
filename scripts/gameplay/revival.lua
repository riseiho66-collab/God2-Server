-- CUSTOM-0017: source book6808 says HP1 / MP66. Timing/eligibility remain custom.
-- Pure test rule, not installed in production battle dispatch.
return {
    project = function(input)
        assert(input.target_max_hp >= 1)
        return { hp = 1, mp_cost = 66 }
    end
}
