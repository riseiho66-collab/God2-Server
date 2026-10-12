#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// Exact149c DrvDoll source consumed by4637B0/463AD0, distinct from Drv.
// Own supplied decoded bytes; no file read, resource codec, ROM or DB access.
class TaiwanNativeDrvDoll final {
public:
    static constexpr std::string_view native_image_sha256=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr std::string_view decoded_sha256=
        "de9510e0c5b1171e164b407c931b41e7fc3c5a7b5ffa3aba9193a51063f2dd9f";
    // Historical encoded provenance only, not encoded file currentness.
    static constexpr std::string_view historical_encoded_sha256=
        "502df5822b376ac57c4bf8460bf6d646a3cb6d706b1be36396e73bf69ced1042";
    static constexpr std::size_t native_record_stride=136;
    static constexpr std::uint16_t initial_cache_marker=0xffff;
    // Mapped570CBC FLOAT32 source for the native FILD/FMUL/FSTP sequence.
    // The signed source integer below is not a computed/rounded native float.
    static constexpr std::uint32_t native_scale_multiplier_bits=0x3dcccccd;
    struct SourceRow {
        std::size_t source_record_index,source_line,source_offset;
        std::vector<std::uint8_t> raw_record;
        // Native consumes first5; retain the two trailing source comments too.
        std::array<std::vector<std::uint8_t>,7> fields;
    };
    struct Record {
        // Native bank index follows row order, not source column0's label.
        std::uint16_t ordinal;
        std::int32_t source_word_value,source_scale_value;
        std::uint16_t word0; // Native column1 lowWORD at row+0.
        bool source_word_was_empty;
        std::vector<std::uint8_t> filename; // Column4, without inventing a path.
        SourceRow source;
    };
    // Strict delimiter/integer subset of this exact120-row pinned plaintext.
    // Empty column1 ->0 is the observed451B50/451BA0/451B60 accessor chain;
    // malformed numbers are refused, not replaced with arbitrary zero.
    static std::shared_ptr<const TaiwanNativeDrvDoll> from_pinned_decoded(
        std::filesystem::path actual_decoded_origin,std::span<const std::uint8_t>);
    const std::filesystem::path& decoded_origin() const noexcept {return origin_;}
    std::span<const std::uint8_t> decoded_bytes() const noexcept {return plain_;}
    std::span<const std::uint8_t> section_header() const noexcept {return header_;}
    std::span<const Record> records() const noexcept {return records_;}
    // nullptr is an absent source ordinal, not an entry rejection. Empty row0
    // stays a real empty filename; no cache handle or load success is supplied.
    const Record* find(std::uint16_t ordinal) const noexcept;
private:
    TaiwanNativeDrvDoll(std::filesystem::path,std::vector<std::uint8_t>,
        std::vector<std::uint8_t>,std::vector<Record>);
    const std::filesystem::path origin_;
    const std::vector<std::uint8_t> plain_,header_;
    const std::vector<Record> records_;
};
}
