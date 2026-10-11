#pragma once
#include "cn/world/CnPrebornSkillReferences.h"
#include "cn/world/CnWorldSubjectSkillUpdateSource.h"
#include "cn/net/SharedCredentialConnection.h"
#include "game/SharedWorldPresence.h"
#include <functional>
#include <thread>

namespace god2::cn {
// Actual post-commit WORLD34/35 output path on the SAME common game owner.
// No rule/save/learning mutation, invented reply, default issuer or native memory.
class SharedSubjectSkillPublication final:public std::enable_shared_from_this<SharedSubjectSkillPublication> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Wire=god2cn::CnWorldSubjectSkillUpdate;
    using NativeSource=god2cn::CnWorldSubjectSkillUpdateSource;
    struct Plan {
        Lease recipient;
        std::uint64_t actual_event_id,actual_committed_revision;
        std::vector<Wire::Record> actual_records; // Actual order and recipient-native subject identities.
        // Optional actual recipient-native BEFORE-event data source, distinct
        // from actual_committed_revision. Absence leaves native delta unknown.
        std::shared_ptr<const NativeSource> optional_native_source;
    };
    enum class Check {BeforeQueue,QueueAccepted};
    // Required readonly/non-yielding actual POST-COMMIT owner observation.
    // Qualifies recipient-native subjects/common skills, rules/save/persistent
    // replay/event/order/new revision. A matching source row is not permission.
    using Qualify=std::function<bool(const Plan&,const std::vector<NativeSkillRecord>&,Check)>;
    // Explicit opt-in, mandatory with the actual source. Qualifies ALL native
    // matching rows, ordered primary/aux stages and remaining diagnostic/UI/
    // pending-table/rebinding effects from the real common event owner. The
    // retained projection alone does not complete those effects or grant rights.
    // If requires_unchanged_unmodeled_call_roster is true, this owner must
    // qualify that conditional same-row/count/role continuation explicitly;
    // source Current is not evidence for unknown native callback effects.
    using QualifyNative=std::function<bool(const Plan&,const std::vector<NativeSkillRecord>&,
        const NativeSource::Projection&,Check)>;
    static std::shared_ptr<SharedSubjectSkillPublication> create(
        std::shared_ptr<const CnSharedSkillCatalog>,Qualify,QualifyNative optional_native_qualifier={});
    // Bind once inside actual1C gameplay publication. Binding emits nothing;
    // only a qualified committed common event may later call publish().
    bool bind(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&);
    void publish(Plan,Connection::Transport::Completion);
private:
    SharedSubjectSkillPublication(std::shared_ptr<const CnSharedSkillCatalog>,Qualify,QualifyNative);
    void owner() const;
    bool current() const;
    std::shared_ptr<const CnSharedSkillCatalog> catalog_;
    Qualify qualify_;
    QualifyNative qualify_native_;
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_{};
    bool bound_=false,active_=false;
    std::optional<std::uint64_t> last_attempt_; // Local same-event fence, not persisted replay.
};
}
