-- CUSTOM-0078: historical Bahamut8591 reference, not build-matched server rules.
-- Original current ProgramMsg181 independently displays the same 50000 fee.
-- No implicit joining, money creation, level mutation or database access.
-- See docs/research/native-guild-membership-balance-20261003.md.
return {
    policy = function(input)
        return {
            creation_fee = 50000,
            minimum_level = 30,
            initial_capacity = 20,
            may_create = input.level >= 30 and input.wallet >= 50000,
        }
    end,
}
