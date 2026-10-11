#pragma once
#include "game/Battle.h"
#include "protocol/RecoveredBattleCommand.h"
#include <string_view>
namespace god2 {
// CUSTOM-0086 persistent two-owner input/notification/grant stages. Official
// round collection/order/receipt requirements are NOT recovered. C++ chooses
// this two-input policy; no numerical combat rule or skill ownership here.
class OwnedPkRound {
public:
    enum class Phase {InitialControl,Collect,Ready,ResultsControl,Grants,Terminal};
    struct Header {std::uint8_t actor,side;std::uint32_t context;bool operator==(const Header&)const=default;};
    using Masks=std::array<std::array<std::uint16_t,2>,2>;
    struct Intent {
        BattleAction action;
        std::optional<std::uint16_t> skill_key;
        // Canonical FULL NativeSkillRecord snapshot supplied by same DB reader;
        // membership is not server ownership. Empty for basic.
        std::string definition_readset;
    };
    static OwnedPkRound waiting(std::array<Header,2>,Masks,std::uint64_t battle_revision);
    // CUSTOM-0104 initial notification only; actual entry roster bounds.
    // waiting() retains exact expected-mask/version1 semantics.
    static OwnedPkRound waiting_notification(std::array<Header,2>,Masks allowed_bounds,std::uint64_t battle_revision);
    Phase phase()const noexcept{return phase_;}
    std::uint64_t revision()const noexcept{return revision_;}
    std::uint64_t battle_revision()const noexcept{return battle_revision_;}
    std::uint64_t round()const noexcept{return round_;}
    std::uint64_t grant_epoch()const noexcept{return grant_epoch_;}
    const std::array<Header,2>& headers()const noexcept{return headers_;}
    const Masks& masks()const noexcept{return expected_masks_;}
    const std::optional<Masks>& initial_notification_bounds()const noexcept{return notification_bounds_;}
    const std::array<std::optional<std::array<std::uint16_t,2>>,2>& initial_notification_observations()const noexcept{return notification_observations_;}
    const std::array<std::optional<Intent>,2>& intents()const noexcept{return intents_;}
    const std::array<bool,2>& grant_submissions()const noexcept{return grant_submissions_;}
    bool control(std::uint8_t viewer,const RecoveredBattleCommand::ControlRequest&);
    bool submit(std::uint8_t viewer,Intent);
    bool grant_submitted(std::uint64_t epoch,std::uint8_t viewer);
    // Trusted resolver must atomically pair this state transition with its
    // shared checkpoint/results. This function alone never settles a room.
    bool results_issued(std::uint64_t next_battle_revision,Masks,bool terminal);
    std::string document()const;
    static OwnedPkRound from_document(std::string_view);
    static bool masks_valid(const Masks&)noexcept;
private:
    Phase phase_{Phase::InitialControl};
    std::uint64_t revision_{1},battle_revision_{1},round_{1},grant_epoch_{};
    std::array<Header,2> headers_{};
    Masks expected_masks_{};
    std::optional<Masks> notification_bounds_;
    // Permanent first observations; null means unobserved, not a zero receipt.
    std::array<std::optional<std::array<std::uint16_t,2>>,2> notification_observations_{};
    std::array<bool,2> controls_{},grant_submissions_{};
    std::array<std::optional<Intent>,2> intents_{};
    void bump();
    void validate()const;
};
}
