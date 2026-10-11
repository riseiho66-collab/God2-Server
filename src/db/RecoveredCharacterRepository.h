#pragma once
#include "game/RecoveredCharacter.h"
#include "game/RecoveredPosition.h"
#include "game/CharacterResources.h"
#include "protocol/RecoveredRoleLevel.h"
#include <optional>
#include <vector>

namespace god2 {
struct CharacterRoleSnapshot {
    RecoveredRoleLevel::Bytes logical;
    std::uint64_t revision{};
    std::string design_id;
    bool operator==(const CharacterRoleSnapshot&) const = default;
};
struct RoleResourceCommit {
    CharacterRoleSnapshot role;
    CharacterResources resources;
};
struct CharacterExperience {
    std::uint64_t total{};
    std::string design_id;
    bool operator==(const CharacterExperience&) const = default;
};
struct BattleSettlement {
    CharacterResources resources;
    std::uint64_t total_experience{};
    std::optional<CharacterRoleSnapshot> role;
    bool operator==(const BattleSettlement&) const = default;
};
struct BattleProgressionCommit {
    std::optional<CharacterExperience> expected_experience;
    std::optional<CharacterRoleSnapshot> expected_role;
    CharacterRoleSnapshot next_role;
};
class RecoveredCharacterRepository {
public:
    virtual ~RecoveredCharacterRepository() = default;
    virtual std::optional<CharacterRoleSnapshot> load_role(std::uint64_t account,std::uint64_t character)=0;
    virtual RoleResourceCommit commit_role_resources(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterRoleSnapshot>& expected_role,const CharacterResources& expected_resources,
        CharacterRoleSnapshot next_role,CharacterResources next_resources)=0;
    virtual std::optional<CharacterExperience> load_experience(std::uint64_t account,
        std::uint64_t character)=0;
    // Server-authorized terminal outcome only; CUSTOM-0012 diagnostic awards.
    virtual BattleSettlement settle_battle(std::uint64_t account,std::uint64_t character,
        std::uint64_t battle,const CharacterResources& expected,CharacterResources next,
        bool won,std::uint64_t experience,const std::optional<BattleProgressionCommit>& progression={})=0;
    virtual std::uint64_t reserve_battle(std::uint64_t account,std::uint64_t character,
        const CharacterResources& expected)=0;
    virtual std::optional<CharacterResources> load_resources(std::uint64_t account,std::uint64_t character)=0;
    virtual CharacterResources commit_resources(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterResources>& expected,CharacterResources next)=0;
    virtual RecoveredCharacter create(std::uint64_t account_id,
                                      const std::array<std::uint8_t, 40>& profile) = 0;
    virtual std::vector<RecoveredCharacter> list_for_account(std::uint64_t account_id) = 0;
    virtual std::optional<RecoveredPosition> load_position(std::uint64_t account_id,
                                                          std::uint64_t character_id) = 0;
    virtual RecoveredPosition commit_position(std::uint64_t account_id, std::uint64_t character_id,
                                              const std::optional<RecoveredPosition>& expected,
                                              std::uint16_t area, std::uint16_t scene,
                                              std::uint16_t x, std::uint16_t y) = 0;
};
}
