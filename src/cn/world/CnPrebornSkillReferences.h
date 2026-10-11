#pragma once
#include "cn/world/CnPrebornSubjectState.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include "cn/protocol/CnWorldSubjectSkillUpdate.h"
#include "cn/world/CnWorldPrimarySkillSource.h"

namespace god2::cn {
// Optional native recovery evidence ->actual shared-store CN definitions.
// No process-memory access, dereference, common skill ID or cast permission.
struct CnPrebornSkillReferences {
    struct Entry {
        god2cn::CnPrebornSubjectState::SkillReference native_reference;
        NativeSkillRecord definition;
    };
    struct Resolved {
        god2cn::CnPrebornSubjectState::Scope scope;
        std::uint32_t bank_word;
        std::vector<Entry> entries;
    };
    static std::optional<Resolved> resolve_actual_snapshot(
        const god2cn::CnPrebornSubjectState::Snapshot&,const CnSharedSkillCatalog&);
    // Stronger optional source: actual complete bank/primary records are
    // already owned and byte-qualified; still no learned/common actor rights.
    static std::optional<Resolved> resolve_actual_primary_source(
        const god2cn::CnWorldPrimarySkillSource&,const CnSharedSkillCatalog&);
    // Format-to-definition source only. Common subject mapping, learning,
    // post-commit publication and WORLD recipient state remain caller authority.
    static std::optional<NativeSkillRecord> resolve_update_definition(
        const god2cn::CnWorldSubjectSkillUpdate::Record&,const CnSharedSkillCatalog&);
};
}
