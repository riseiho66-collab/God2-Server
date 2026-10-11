#pragma once
#include "cn/protocol/CnSubjectDeclaration30.h"
#include "cn/protocol/CnSubjectStatus31.h"
#include "cn/protocol/CnSelectedSubjectTitle32.h"
#include "cn/world/CnWorldSubjectSkillUpdateSource.h"
#include "cn/world/CnPrebornSkillReferences.h"
#include <variant>

namespace god2::cn {
// Explicit actual before-images in the original mixed sequence. Never strip
//30/31/32/33/39 and simulate all34/35 against one obsolete selected roster.
class CnRosterSkillCheckpointSource final {
public:
    using NativeSource=god2cn::CnWorldSubjectSkillUpdateSource;
    using Record=std::variant<god2cn::CnSubjectDeclaration30,god2cn::CnSubjectStatus31,
        god2cn::CnWorldSubjectSkillUpdate::Record,god2cn::CnSelectedSubjectUpdate,
        god2cn::CnSelectedSubjectTitle32>;
    using Definitions=std::vector<std::optional<NativeSkillRecord>>;
    struct Checkpoint {
        std::size_t first_record,record_count;
        std::shared_ptr<const NativeSource> actual_source;
    };
    struct Segment {
        std::size_t first_record,record_count;
        NativeSource::Projection data;
    };
    struct Projection {
        std::vector<Segment> segments;
        std::size_t total_skill_records=0;
    };
    // Every skill record is covered once, in order. A checkpoint may subdivide
    //a contiguous skill run, but cannot cross any intervening non-skill record.
    //All borrowed sequences are owned before any external Current observer.
    static std::optional<Projection> project_actual_sequence(std::span<const Record>,
        std::span<const std::optional<NativeSkillRecord>>,std::span<const Checkpoint>);
    static bool actual_sources_current(std::span<const Checkpoint>);
    // This is NOT qualification of the intervening native/common mutations.
    //Actual post-commit owner must qualify each before-image, revisions, rows,
    //selection and all unknown log/UI callbacks, including conditional stages
    //inside NativeSource::Projection. Sources need not be live client memory;
    //an actual prepared immutable event-owned checkpoint owner is still needed.
};
}
