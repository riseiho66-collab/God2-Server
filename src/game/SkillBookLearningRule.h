#pragma once
#include <cstdint>
namespace god2 {
// CUSTOM-0148: owner-authorized shared learning policy, not recovered native
// eligibility/debit. Caller owns exact book, selected subject and catalog.
struct SkillBookLearningInput {
    std::uint32_t book_count{};
    std::uint32_t skill_count{};
    bool already_learned=false;
    bool display_valid=false;
};
struct SkillBookLearningResult {
    bool allowed=false;
    bool duplicate=false;
    std::uint8_t consume=0;
};
}
