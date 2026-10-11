#include "cn/world/CnPrebornSkillReferences.h"
#include <algorithm>
#include <limits>
#include <utility>

namespace god2::cn {
std::optional<CnPrebornSkillReferences::Resolved> CnPrebornSkillReferences::resolve_actual_primary_source(
    const god2cn::CnWorldPrimarySkillSource& primary,const CnSharedSkillCatalog& catalog) {
    if(!primary.current() || !catalog.current())return std::nullopt;
    const auto& subject=primary.retained_subject();
    Resolved result{subject.scope(),subject.retained_skill_bank_pointer(),{}};
    for(const auto& entry:primary.retained_entries()) {
        if(!primary.current() || !catalog.current())return std::nullopt;
        const auto& native=entry.definition;
        auto actual=catalog.lookup(native.kind,native.definition_id);
        if(!actual || !primary.current() || !catalog.current() ||
           actual->source!=CnSharedSkillCatalog::expected_source() ||
           actual->source_offset!=native.file_offset || actual->record_sha256!=native.record_sha256 ||
           actual->raw_record.size()!=native.raw.size() ||
           !std::equal(actual->raw_record.begin(),actual->raw_record.end(),native.raw.begin()))return std::nullopt;
        result.entries.push_back({entry.reference,std::move(*actual)});
    }
    if(!primary.current() || !catalog.current())return std::nullopt;return result;
}
std::optional<NativeSkillRecord> CnPrebornSkillReferences::resolve_update_definition(
    const god2cn::CnWorldSubjectSkillUpdate::Record& update,const CnSharedSkillCatalog& catalog) {
    return catalog.lookup(update.kind(),update.definition_id());
}
std::optional<CnPrebornSkillReferences::Resolved> CnPrebornSkillReferences::resolve_actual_snapshot(
    const god2cn::CnPrebornSubjectState::Snapshot& subject,const CnSharedSkillCatalog& catalog) {
    // Geometry-only recovery provenance when no actual bank source supplied.
    // It does not attest to bytes stored at the captured native pointer.
    using Native=god2cn::CnNativeSkillCatalog;
    const auto bank=subject.retained_skill_bank_pointer();
    if(!subject.current() || !catalog.current() || !subject.retained_selection() || !bank ||
       bank>std::numeric_limits<std::uint32_t>::max()-(Native::resource_bytes-4))return std::nullopt;
    Resolved result{subject.scope(),bank,{}};
    for(const auto reference:subject.retained_selection()->skills) {
        const auto pointer=reference.actual_native_pointer_word;
        if(pointer<bank+4)return std::nullopt;
        const auto delta=std::size_t(pointer-bank-4);
        const auto kind=delta/Native::group_bytes,within=delta%Native::group_bytes;
        if(kind>=Native::declared_counts.size() || within%Native::record_bytes)return std::nullopt;
        const auto id=within/Native::record_bytes+1;
        if(id>Native::declared_counts[kind])return std::nullopt;
        auto definition=catalog.lookup(static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(id));
        if(!definition || definition->source_offset-4!=std::int64_t(pointer-bank))return std::nullopt;
        // Preserve every flag byte/order/duplicate. Native writers set0/3 in
        // specific UI branches; neither value establishes server entitlement.
        result.entries.push_back(Entry{reference,std::move(*definition)});
    }
    if(!subject.current() || !catalog.current())return std::nullopt;return result;
}
}
