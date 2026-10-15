#pragma once
#include "game/TaiwanNativeResourceSelection.h"
#include "game/TaiwanNativeRomAsset.h"
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
// Own supplied decoded bytes; request/ROM bindings below retain supplied
// selection/parsed values without executing file reads, resource codec or DB.
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
    // Dedicated463AD0 direct-loader context. There is NO Hero/model+1C prefix:
    // actual row filename already carries its full relative path to52F550.
    struct NativeRomContext {
        std::vector<std::uint8_t> actual_52f550_root;
        std::filesystem::path actual_working_directory;
        std::uint32_t actual_manager_bank_operand;
    };
    class NativeRomRequest final {
    public:
        const TaiwanNativeResourceSelection::Request& request() const noexcept{return request_;}
        const NativeRomContext& context() const noexcept{return context_;}
        const TaiwanNativeDrvDoll& bank() const noexcept{return *bank_;}
        std::size_t row_ordinal() const noexcept{return ordinal_;}
    private:
        friend class TaiwanNativeDrvDoll;
        NativeRomRequest(std::shared_ptr<const TaiwanNativeDrvDoll>,std::size_t,
            NativeRomContext,TaiwanNativeResourceSelection::Request);
        const std::shared_ptr<const TaiwanNativeDrvDoll> bank_;
        const std::size_t ordinal_;
        const NativeRomContext context_;
        const TaiwanNativeResourceSelection::Request request_;
    };
    class ResolvedRom final {
    public:
        const TaiwanNativeDrvDoll& bank() const noexcept{return request_->bank();}
        std::size_t row_ordinal() const noexcept{return request_->row_ordinal();}
        const TaiwanNativeResourceSelection& selection() const noexcept{return selected_;}
        const TaiwanNativeRomAsset& rom() const noexcept{return *rom_;}
        std::uint32_t full_action_operand() const noexcept{return action_operand_;}
        const TaiwanNativeRomAsset::Action& action() const{return *rom_->find_action(action_operand_);}
        const std::shared_ptr<const NativeRomRequest>& native_request() const noexcept{return request_;}
    private:
        friend class TaiwanNativeDrvDoll;
        ResolvedRom(std::shared_ptr<const NativeRomRequest>,TaiwanNativeResourceSelection,
            std::shared_ptr<const TaiwanNativeRomAsset>,std::uint32_t);
        const std::shared_ptr<const NativeRomRequest> request_;
        const TaiwanNativeResourceSelection selected_;
        const std::shared_ptr<const TaiwanNativeRomAsset> rom_;
        const std::uint32_t action_operand_;
    };
    // Actual first-selector/source ordinal only, never cacheWORD/word0/scale.
    static std::shared_ptr<const NativeRomRequest> native_rom_request(
        std::shared_ptr<const TaiwanNativeDrvDoll>,std::uint32_t full_source_ordinal,const NativeRomContext&);
    // Explicit CUSTOM full action remains separate from original source fields.
    // Same private bank/request, complete selected bytes and immutable ROM VALUE.
    static std::shared_ptr<const ResolvedRom> bind_native_rom(
        std::shared_ptr<const NativeRomRequest>,const TaiwanNativeResourceSelection&,
        std::shared_ptr<const TaiwanNativeRomAsset>,std::uint32_t actual_full_action_operand);
private:
    TaiwanNativeDrvDoll(std::filesystem::path,std::vector<std::uint8_t>,
        std::vector<std::uint8_t>,std::vector<Record>);
    const std::filesystem::path origin_;
    const std::vector<std::uint8_t> plain_,header_;
    const std::vector<Record> records_;
};
}
