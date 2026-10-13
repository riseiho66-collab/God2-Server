#pragma once
#include "db/NativeSkillCatalog.h"
#include "db/SharedSkillDefinition.h"
#include "game/SharedTaiwanWorldRecordSource.h"
#include "game/SharedTaiwanIssuedSkillSource.h"
#include "protocol/TaiwanNativeSkillCommand.h"
#include <cstddef>
#include <memory>
#include <optional>
#include <span>

namespace god2 {
// Conditional actual catalog/grammar/action source, not a learned-skill,
// grant, native charge, battle settlement or full-reply producer by itself.
// Concrete issued-list checks select actual primary/side0 or explicitly held
// secondary/side1. Secondary key-to-ordinal is a bounded owned projection,
// not a recovered native key-search or permission. Missing secondary cannot
// borrow primary membership. Main does not select this source; a real
// WorldOwner remains mandatory.
// The raw command and WorldOwner qualification must both match the actual
// issued control's BYTE+51/52 actor and matching side. This is consistency,
// not proof that an actor belongs to the selected saved deity or may act.
class SharedTaiwanNativeSkillCommandSource final {
public:
    using WireRecord=TaiwanNativeSkillCommand::WireRecord;
    using Command=TaiwanNativeSkillCommand::Command;
    using Qualification=TaiwanNativeSkillCommand::Qualification;
    using Reply=SharedTaiwanWorldRecordSource::Reply;
    using Binding=SharedTaiwanWorldRecordSource::SkillBinding;
    struct Scope {
        SharedWorldPresence::Lease lease;
        RecoveredPosition saved_position;
        std::uint64_t battle_generation;
        // CUSTOM-0143: owning common definition for the same requested TW row.
        // Source composition is not learned/cost/actor/native grant authority.
        std::optional<SharedSkillDefinition> common_definition{};
    };
    enum class Check {Qualified,BeforeAction};
    struct Budgets {std::size_t max_records,max_output_bytes,max_output_frames;};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Pure current native actor/selector/context/candidate/formation state.
        // This is neither a grant nor permission to charge a client threshold.
        // Do not yield, pump, mutate, send or retain borrowed arguments here.
        virtual std::optional<Qualification> qualification(Session&,const Scope&,
            std::span<const WireRecord>,const NativeSkillRecord&)=0;
        // Actual full learned/controlled actor/grant incarnation/MP/resources,
        // target state/rules/definition source must still authorize this exact
        // operation. Catalog membership and grammar never substitute for them.
        virtual bool current(Session&,const Scope&,Check,const Command&,const Qualification&)=0;
        // The real owner performs the complete action and once-settlement CAS,
        // supplies native cost/rules and prebuilds the COMPLETE encrypted reply
        // before durable mutation. No default Battle::act/PK/charge/reply here.
        // No yield/pump or borrowing beyond this call. A durable prefix cannot
        // be rolled back or retried because later publication is refused.
        virtual std::optional<Reply> action(Session&,const Scope&,const Command&,const Qualification&)=0;
        // Pure qualification of the actual NEXT durable receipt and full reply.
        // Never ask whether the consumed old grant/MP/learned snapshot is still
        // current, and never reverse or retry an already committed action.
        virtual bool after_action(Session&,const Scope&,const Command&,const Qualification&,const Reply&)=0;
        virtual void release(Session&)=0;
        virtual void invalidate_active()=0;
    };
    // Construct inside the real game Context with its actual shared presence
    // and native_skills reader. The borrowed catalog/DB must outlive this owner
    // and the Application game drain. This API does not certify an arbitrary
    // reader as same-connection or manufacture a concrete WorldOwner.
    static Binding create(std::shared_ptr<SharedWorldPresence>,const NativeSkillCatalog&,
        std::shared_ptr<SharedTaiwanIssuedSkillSource>,std::shared_ptr<WorldOwner>,Budgets);
};
}
