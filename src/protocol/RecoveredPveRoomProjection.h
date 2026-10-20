#pragma once
#include "game/OwnedPveRoomTypes.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattleAttackPresentation.h"
#include "protocol/RecoveredBattleAction08Control.h"
#include "protocol/RecoveredBattleExperience.h"
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include "protocol/RecoveredBattleRowSwapResult.h"
#include <map>
#include <stdexcept>

namespace god2 {
// CUSTOM-0161/0162 pure projection of an actual room snapshot. Full native
// actor/resource/text/opaque/counter templates are mandatory host inputs.
// This API neither mints those sources nor sends/persists/qualifies a Session.
struct RecoveredPveRoomProjection {
    using Types=OwnedPveRoomTypes;
    class ProfileRequired final:public std::invalid_argument {
    public:explicit ProfileRequired(const char* why):std::invalid_argument(why){}
    };
    struct ActorProfile {
        RecoveredBattleIdentity::Record identity;
        std::optional<RecoveredBattlePlayerAppearance::Record> appearance;
        RecoveredBattleVitals::Record hp;
        std::optional<RecoveredBattleVitals::Record> mp;
    };
    struct RecipientProfile {
        std::uint64_t character{};
        // Entry82 only for a NEW entrant. context_a is the actual room-issued
        // command context; neither context is synthesized from the room ID.
        std::optional<RecoveredBattleEntry::Record> entry;
        // Complete current native profiles keyed by canonical actual position.
        std::map<std::uint8_t,ActorProfile> actors;
        std::optional<RecoveredBattleVitalsBatch::Record> bulk;
        std::optional<std::array<std::uint8_t,17>> grant;
        // One complete raw template per actual ordered hit, fresh group bytes.
        std::vector<RecoveredBattleAttackPresentation::Record> attacks;
        std::optional<std::uint16_t> action_skill;
        std::optional<RecoveredBattleAction08Control::Record> support;
        // Explicit native83/action6 successful-removal templates for every
        // departing actual primary/pet. No fabricated flag/group/tail bytes.
        std::vector<std::array<std::uint8_t,15>> withdrawal;
        // Actual complete native89 result. No awards/default padding inferred.
        // Client0B/context and return-WORLD barriers belong to the actual host.
        std::optional<RecoveredBattleExperience::Record> terminal;
        std::optional<RecoveredBattleRowSwapResult::Record> row_swap;
    };
    using Profiles=std::map<std::uint64_t,RecipientProfile>;
    // Each output contains whole records and is bounded by the native logical
    // frame limit; multiple outputs per recipient preserve original order.
    // Admission: newcomer full current roster; incumbents new actors only,
    // without82, old actor reset, bulk/counter or grant replacement.
    static std::vector<Types::Output> prepare(const Types::Snapshot&,const Types::Change&,const Profiles&);
};
}
