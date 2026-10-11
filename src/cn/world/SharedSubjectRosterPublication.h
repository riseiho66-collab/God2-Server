#pragma once
#include "cn/protocol/CnSubjectDeclaration30.h"
#include "cn/protocol/CnSubjectStatus31.h"
#include "cn/protocol/CnSelectedSubjectUpdate.h"
#include "cn/protocol/CnSelectedSubjectTitle32.h"
#include "cn/assets/CnSubjectTemplateNames.h"
#include "cn/world/CnPrebornSkillReferences.h"
#include "cn/world/CnRosterSkillCheckpointSource.h"
#include "cn/net/SharedCredentialConnection.h"
#include "game/SharedWorldPresence.h"
#include <functional>
#include <thread>
#include <variant>

namespace god2::cn {
// One actual common committed event's ordered native roster/status/skill bytes
// behind one held publication. Never invent initialization, IDs, rows or rules.
class SharedSubjectRosterPublication final:public std::enable_shared_from_this<SharedSubjectRosterPublication> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using CheckpointSource=CnRosterSkillCheckpointSource;
    using Record=CheckpointSource::Record;
    struct Plan {
        Lease recipient;
        std::uint64_t actual_event_id,actual_committed_revision;
        std::vector<Record> actual_records; // Exact real order, including native reset/select effects.
        bool use_actual_native_skill_checkpoints=false;
        std::vector<CheckpointSource::Checkpoint> actual_native_skill_checkpoints;
    };
    enum class Check {BeforeQueue,QueueAccepted};
    using Definitions=std::vector<std::optional<NativeSkillRecord>>; //Aligned with Plan records.
    using TemplateNames=std::vector<std::optional<god2cn::CnSubjectTemplateNames::Lookup>>;
    using LevelNames=std::vector<std::optional<god2cn::CnSubjectTemplateNames::LevelLookup>>;
    struct Framing {
        //Existing transport operational budgets, not native gameplay limits.
        static constexpr std::size_t max_frames=256;
        static constexpr std::size_t max_logical_per_frame=god2cn::CnTransport::max_logical;
        static constexpr std::size_t max_batch_logical_bytes=max_frames*max_logical_per_frame;
        static constexpr std::size_t min_record_bytes=2; //New actual33, not an invented game cap.
        struct Frame {
            std::size_t first_record,record_count,logical_bytes;
        };
        std::vector<Frame> frames; //Contiguous original record ranges, never split records.
        std::size_t total_logical_bytes=0;
    };
    // Required readonly/non-yielding post-commit owner qualifies common
    // ownership/recipient, actual pre-event roster and staged inactive row/name,
    // capacity/reset/selection, evolving record order, all fields/skills,
    // rules/save/durable replay/new revision. No native-memory prerequisite.
    //32/33/39 have no subject ID: qualify the actual current selected row (or
    //native null-selection no-op) at EACH record, including preceding30 changes.
    //Same owned framing is observed at both publication stages. Queue capacity
    //and encoding still belong to the actual existing socket strand.
    //32 also requires actual resource/retained row string bounds and rendering
    //branch; unresolved accepted index4 cannot be a fabricated empty title.
    using Qualify=std::function<bool(const Plan&,const Definitions&,const TemplateNames&,const LevelNames&,const Framing&,Check)>;
    // Additive actual owner, never a replacement for Qualify. Qualifies each
    //actual before-image at its original record index, intervening reset/select
    //effects and conditional unknown diagnostic/UI calls within each segment.
    //Source Current alone cannot establish evolving native/common state. The
    //same immutable projection and actual source lifetimes span both checks.
    using QualifyNative=std::function<bool(const Plan&,const Definitions&,const TemplateNames&,
        const LevelNames&,const Framing&,const CheckpointSource::Projection&,Check)>;
    static std::shared_ptr<SharedSubjectRosterPublication> create(Qualify,
        std::shared_ptr<const CnSharedSkillCatalog> actual_skill_catalog={},
        std::shared_ptr<const god2cn::CnSubjectTemplateNames> actual_template_names={},
        QualifyNative actual_native_checkpoint_owner={});
    bool bind(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&);
    void publish(Plan,Connection::Transport::Completion);
private:
    SharedSubjectRosterPublication(Qualify,std::shared_ptr<const CnSharedSkillCatalog>,
        std::shared_ptr<const god2cn::CnSubjectTemplateNames>,QualifyNative);
    void owner() const;
    bool current() const;
    Qualify qualify_;
    QualifyNative qualify_native_;
    std::shared_ptr<const CnSharedSkillCatalog> skills_; //Required for every actual34/35, not fabricated.
    std::shared_ptr<const god2cn::CnSubjectTemplateNames> names_; //Required for nonzero low-ID30 and every32.
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_{};
    bool bound_=false,active_=false;
    std::optional<std::uint64_t> last_attempt_; //Local fence only; actual persisted replay owner required.
};
}
