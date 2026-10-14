#pragma once
#include "game/TaiwanNativeResourceSelection.h"
#include "game/TaiwanNativeRomAsset.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// TW ordinary world Drv32B/HeroDoll44B banks. Neither DrvDoll136B nor Fight.
// Own complete pinned plaintext, physical row identity and opaque CP950 bytes.
// Source qualification alone grants no actor, native cache slot or world rights.
class TaiwanNativeActorResourceBank final {
public:
    static constexpr std::string_view native_image_sha256=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr std::string_view drv_decoded_sha256=
        "72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0";
    static constexpr std::string_view hero_decoded_sha256=
        "0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2";
    static constexpr std::size_t drv_native_stride=32,hero_native_stride=44;
    static constexpr std::uint16_t native_initial_cache_marker=0xffff;
    struct SourceRow {
        std::size_t ordinal,line,offset;
        std::vector<std::uint8_t> raw_record; // Includes original CRLF.
        std::vector<std::vector<std::uint8_t>> fields; // All trailing comments.
    };
    struct Drv {
        std::uint16_t ordinal,act_type,preload;
        std::array<std::uint16_t,4> component_values;
        std::vector<std::uint8_t> filename;
        SourceRow source;
    };
    struct Hero {
        std::size_t ordinal;
        std::string key; // Native ASCII-lower concatenation of columns0 and1.
        std::vector<std::uint8_t> filename; // Native lowercased ASCII filename.
        // Preserve numeric columns without assigning unrecovered semantics.
        std::array<std::int32_t,3> source_numeric_columns_2_4_5;
        std::uint8_t component_modifier; // Native row+2A, lowBYTE of column5.
        SourceRow source;
    };
    static std::shared_ptr<const TaiwanNativeActorResourceBank> from_pinned_decoded(
        std::filesystem::path drv_origin,std::span<const std::uint8_t> drv,
        std::filesystem::path hero_origin,std::span<const std::uint8_t> hero);
    const Drv* find_drv(std::uint32_t full_native_ordinal) const noexcept;
    const Hero* find_hero(std::string_view exact_native_key) const noexcept;
    std::span<const Drv> drv_rows() const noexcept {return drv_;}
    std::span<const Hero> hero_rows() const noexcept {return hero_;}
    std::span<const std::uint8_t> drv_plaintext() const noexcept {return drv_plain_;}
    std::span<const std::uint8_t> hero_plaintext() const noexcept {return hero_plain_;}
    const std::filesystem::path& drv_origin() const noexcept {return drv_origin_;}
    const std::filesystem::path& hero_origin() const noexcept {return hero_origin_;}
    // Exact source-row -> already selected original -> already parsed ROM ->
    // actual full action operand. This qualified direct-filename subset does
    // not yet produce native caller wrapper paths or cache-manager operands.
    // No file selection/codec is executed here.
    // Full resource/window/actor lifecycle Current remains the hosting owner.
    class ResolvedRom final {
    public:
        enum class Family {Drv,Hero};
        Family family() const noexcept {return family_;}
        std::size_t row_ordinal() const noexcept {return ordinal_;}
        const TaiwanNativeActorResourceBank& bank() const noexcept {return *bank_;}
        const TaiwanNativeResourceSelection& selection() const noexcept {return selected_;}
        const TaiwanNativeRomAsset& rom() const noexcept {return *rom_;}
        std::uint32_t full_action_operand() const noexcept {return action_operand_;}
        const TaiwanNativeRomAsset::Action& action() const {return *rom_->find_action(action_operand_);}
    private:
        friend class TaiwanNativeActorResourceBank;
        ResolvedRom(std::shared_ptr<const TaiwanNativeActorResourceBank>,Family,std::size_t,
            TaiwanNativeResourceSelection,std::shared_ptr<const TaiwanNativeRomAsset>,std::uint32_t);
        const std::shared_ptr<const TaiwanNativeActorResourceBank> bank_;
        const Family family_;
        const std::size_t ordinal_;
        const TaiwanNativeResourceSelection selected_;
        const std::shared_ptr<const TaiwanNativeRomAsset> rom_;
        const std::uint32_t action_operand_;
    };
    static std::shared_ptr<const ResolvedRom> bind_drv_rom(
        std::shared_ptr<const TaiwanNativeActorResourceBank>,std::uint32_t full_native_ordinal,
        const TaiwanNativeResourceSelection&,std::shared_ptr<const TaiwanNativeRomAsset>,
        std::uint32_t actual_full_action_operand);
    static std::shared_ptr<const ResolvedRom> bind_hero_rom(
        std::shared_ptr<const TaiwanNativeActorResourceBank>,std::string_view exact_native_key,
        const TaiwanNativeResourceSelection&,std::shared_ptr<const TaiwanNativeRomAsset>,
        std::uint32_t actual_full_action_operand);
private:
    TaiwanNativeActorResourceBank(std::filesystem::path,std::vector<std::uint8_t>,std::vector<Drv>,
        std::filesystem::path,std::vector<std::uint8_t>,std::vector<Hero>);
    const std::filesystem::path drv_origin_,hero_origin_;
    const std::vector<std::uint8_t> drv_plain_,hero_plain_;
    const std::vector<Drv> drv_;
    const std::vector<Hero> hero_;
};
}
