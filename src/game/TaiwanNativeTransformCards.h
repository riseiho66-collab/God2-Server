#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// Native149c45BB10 indexed ChangeDollCard resource source, not monster stats.
// Requires supplied exact decoded bytes; performs no file read or decoding.
class TaiwanNativeTransformCards final {
public:
    static constexpr std::string_view native_image_sha256=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr std::string_view decoded_sha256=
        "0f04cc27292e4b3bc08c030dce8b2564e2fad52bf0d87f227414d63f4ca6acef";
    // Encoded provenance only; this factory does not attest encoded currentness.
    static constexpr std::string_view encoded_sha256=
        "4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2";
    struct SourceRow {
        std::size_t source_record_index,source_line,source_offset;
        std::vector<std::uint8_t> raw_record;
        std::array<std::vector<std::uint8_t>,39> fields;
        // Only actually selected numeric columns. Text/skipped fields stay raw.
        std::array<std::optional<std::int32_t>,39> selected_numbers;
    };
    struct Target {
        std::uint8_t area;
        std::uint16_t scene,ordinal; // ordinal is one-based; zero is not a lookup.
        bool operator==(const Target&) const = default;
    };
    struct Record {
        std::uint16_t key,source_word1;
        Target target;
        // Source columns8..22 -> native WORDs12..2E. No stat authority labels.
        std::array<std::uint16_t,15> selected_words;
        SourceRow source;
    };
    // Bounded strict integer/delimiter subset of the pinned101-row source.
    // Native duplicate overwrites/unchecked parsing are not reproduced.
    static std::shared_ptr<const TaiwanNativeTransformCards> from_pinned_decoded(
        std::filesystem::path actual_decoded_origin,std::span<const std::uint8_t>);
    const std::filesystem::path& decoded_origin() const noexcept {return origin_;}
    std::span<const std::uint8_t> decoded_bytes() const noexcept {return plain_;}
    std::span<const std::uint8_t> section_header() const noexcept {return header_;}
    std::span<const Record> records() const noexcept {return records_;}
    // Exact row-key match, not45C100's inclusive bound-only eligibility.
    // Key101 is not promoted from the additional calloc slot into a source row.
    const Record* find(std::uint16_t key) const noexcept;
private:
    TaiwanNativeTransformCards(std::filesystem::path,std::vector<std::uint8_t>,
        std::vector<std::uint8_t>,std::vector<Record>);
    const std::filesystem::path origin_;
    const std::vector<std::uint8_t> plain_,header_;
    const std::vector<Record> records_;
};
}
