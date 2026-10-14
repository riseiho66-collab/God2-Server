#pragma once
#include "db/NativeSkillSource.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace god2 {
enum class SharedSkillRegion { Taiwan, China };
enum class SharedSkillRowQualification {
    MetadataSnapshotOnly, OriginalRowPinned, OwnerRowPinned, InstalledEquivalentRowPinned
};
enum class SharedSkillStatus {
    SingleProfile, VerifiedEqualPayload, BorrowedCNReserve, CNPopulatedTWEmpty,
    OwnerSelectedTWCompleteConflict, UnresolvedRegionalProfiles, OwnerCustom
};
// Owning definition data, never a native Current/learning/casting capability.
// row_digest_verified is an informational reader digest result, never proof
// supplied by the caller. Exact full110 bytes plus source/ordinal/offset pins
// promote row qualification even when a runtime digest provider is unavailable.
struct SharedSkillNativeBinding {
    SharedSkillRegion region;
    NativeSkillSource source;
    std::int64_t source_record_index=0,source_offset=0;
    std::string record_sha256;
    std::array<std::uint8_t,110> raw{};
    bool row_digest_verified=false;
    SharedSkillRowQualification qualification=SharedSkillRowQualification::MetadataSnapshotOnly;
    bool operator==(const SharedSkillNativeBinding&) const=default;
};
struct SharedSkillTextProjection {
    std::optional<std::size_t> profile_index;
    std::uint16_t offset=0,limit_exclusive=0;
    std::string encoding;
    std::vector<std::uint8_t> bounded_raw;
    std::string source_utf8,traditional_utf8;
    // A bounded pinned source literal, not a recovered native UI field width.
    bool pinned_literal=false;
    bool operator==(const SharedSkillTextProjection&) const=default;
};
// Formal owning specification of the existing owner rule classes. This is
// definition data, never installed Policy, learned rights or cast authority.
// Native raw bindings remain independent; no native110 bytes are synthesized.
struct OwnerSkillRule {
    std::string design_id;
    std::uint16_t key=0;
    std::uint32_t physical_power_percent=0,mp_cost=0;
    std::uint8_t max_targets=0;
    bool all_living_opponents=false;
    std::string traditional_name;
    bool operator==(const OwnerSkillRule&) const=default;
};
struct SharedSkillDefinition {
    // Stable registry/native-binding key. A common identity does not assert
    // equal native effects. Original regional keys and full records remain.
    std::uint16_t canonical_key=0;
    SharedSkillStatus status=SharedSkillStatus::UnresolvedRegionalProfiles;
    std::vector<SharedSkillNativeBinding> profiles;
    // Owner-selected complete parameter base only; not a damage formula,
    // native eligibility, server debit, bank population or entitlement.
    std::optional<std::size_t> chosen_profile;
    SharedSkillTextProjection name,short_text;
    // Engaged only for the existing CUSTOM-0058/0059 formal rule keys.
    // Presence never promotes any raw profile's pin/source qualification.
    std::optional<OwnerSkillRule> owner_rule;
    bool operator==(const SharedSkillDefinition&) const=default;
};
const char* shared_skill_status_name(SharedSkillStatus) noexcept;
const char* shared_skill_qualification_name(SharedSkillRowQualification) noexcept;
// Pure owning value composition. Selected-row pins do not attest a loaded
// whole file or observed native bank. Unknown source snapshots stay explicit.
SharedSkillDefinition resolve_shared_skill_definition(std::uint8_t kind,std::uint8_t id,
    std::optional<SharedSkillNativeBinding> taiwan,std::optional<SharedSkillNativeBinding> china);
}
