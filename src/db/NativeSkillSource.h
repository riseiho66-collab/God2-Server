#pragma once
#include <array>
#include <cstdint>
#include <string>

namespace god2 {
struct NativeSkillSource {
    std::string dataset_id;
    std::string source_path;
    std::string source_sha256;
    std::string decoded_sha256;
    std::string native_image_sha256;
    std::string source_section;
    std::string loader_rva;
    std::string lookup_rva;
    std::int64_t row_count = 0;

    bool operator==(const NativeSkillSource&) const = default;
};
// Explicit retained source epochs. Selection is definition provenance, never
// learned rights, casting permission, file activation or observed native banks.
enum class NativeTaiwanSkillProfile { Historical448, Installed453 };
inline constexpr char native_taiwan_historical_dataset_id[]="current-skill-catalog-v1";
inline constexpr char native_taiwan_installed_dataset_id[]="tw-installed-cbspec2-3adcda70-149c1b45-453-v1";
inline constexpr const char* native_taiwan_skill_dataset_id(NativeTaiwanSkillProfile profile) noexcept {
    switch(profile) {
    case NativeTaiwanSkillProfile::Historical448:return native_taiwan_historical_dataset_id;
    case NativeTaiwanSkillProfile::Installed453:return native_taiwan_installed_dataset_id;
    default:return nullptr;
    }
}
inline constexpr std::array<std::int64_t,4> native_taiwan_skill_bank_counts(
    NativeTaiwanSkillProfile profile) noexcept {
    switch(profile) {
    case NativeTaiwanSkillProfile::Historical448:return {121,129,87,111};
    case NativeTaiwanSkillProfile::Installed453:return {126,129,87,111};
    default:return {};
    }
}
// Exact declared source epoch plus retained nonempty descriptor shape. Existing
// source_section/RVA evidence is retained; no new loader or lookup is invented.
// This does not attest on-disk files, loaded banks or recompute any row digest.
inline bool native_taiwan_skill_source_matches(const NativeSkillSource& source,
    NativeTaiwanSkillProfile profile) noexcept {
    const auto dataset=native_taiwan_skill_dataset_id(profile);
    if(!dataset)return false;
    const auto text=[](const std::string& value) noexcept {
        return !value.empty() && value.find(char(0))==std::string::npos;
    };
    const auto digest=profile==NativeTaiwanSkillProfile::Historical448?
        "7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51":
        "3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7";
    return source.dataset_id==dataset && source.source_sha256==digest &&
        source.decoded_sha256==digest && source.native_image_sha256==
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" &&
        source.row_count==(profile==NativeTaiwanSkillProfile::Historical448?448:453) &&
        text(source.source_path) && text(source.source_section) &&
        text(source.loader_rva) && text(source.lookup_rva);
}
}
