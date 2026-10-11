#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// Same149c NPCList resources, NOT NPCAppearData, positions or monster stats.
// Own immutable decoded source. No codec, file search, database or native VM.
class TaiwanNativeNpcSceneGroups final {
public:
    static constexpr std::string_view native_image_sha256=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr std::string_view decoded_sha256=
        "75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815";
    // Historical encoded provenance only; this factory does not attest that
    // an encoded file is currently present or that decoding was performed.
    static constexpr std::string_view historical_encoded_sha256=
        "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    struct SourceRow {
        std::size_t source_record_index,source_line,source_offset;
        std::vector<std::uint8_t> raw_record; // Exact CR/CR/LF and offsets.
    };
    struct Resource {
        std::int32_t source_code;
        std::size_t source_record_index,source_field_index;
        // Native45A91D division by1000, quotient then remainder LOW BYTE.
        // A remainder256..999 narrows here; preserve original code separately.
        std::uint8_t category,ordinal;
    };
    struct Group {
        std::uint8_t scene;
        std::vector<Resource> resources;
        std::vector<std::size_t> source_record_indices;
    };
    // Actual absolute origin of supplied decoded bytes; no implicit filesystem
    // read or assertion of encoded origin. Full4MiB bound and exact SHA pin.
    // Rejects unsafe/malformed inputs rather than reproducing native unchecked
    // signed area/scene access, token failure0 or saturated bank writes.
    static std::shared_ptr<const TaiwanNativeNpcSceneGroups> from_pinned_decoded(
        std::filesystem::path actual_decoded_origin,std::span<const std::uint8_t>);
    const std::filesystem::path& decoded_origin() const noexcept {return origin_;}
    std::span<const std::uint8_t> decoded_bytes() const noexcept {return plain_;}
    const SourceRow& section_header() const noexcept {return header_;}
    std::span<const SourceRow> source_rows() const noexcept {return rows_;}
    // First-seen group order and source-row append order, including empty groups.
    // Out-of-domain area throws; a missing in-domain scene returns nullptr.
    std::span<const Group> area_groups(std::uint8_t area) const;
    // Native query's scene is WORD; do not silently alias scene>255 to BYTE.
    const Group* find(std::uint8_t area,std::uint16_t scene) const;
private:
    TaiwanNativeNpcSceneGroups(std::filesystem::path,std::vector<std::uint8_t>,
        SourceRow,std::vector<SourceRow>,std::array<std::vector<Group>,17>);
    const std::filesystem::path origin_;
    const std::vector<std::uint8_t> plain_;
    const SourceRow header_;
    const std::vector<SourceRow> rows_;
    const std::array<std::vector<Group>,17> groups_;
};
}
