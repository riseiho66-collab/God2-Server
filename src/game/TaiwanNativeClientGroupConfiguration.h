#pragma once
#include "game/TaiwanNativeResourceSelection.h"
#include <span>
#include <string>
#include <string_view>
#include <utility>

namespace god2 {
// TW11BB0/12740 immutable first-load source. Physical rows include missing
// '=' entries. Neither configured ordinals nor label text grant server rights.
class TaiwanNativeClientGroupConfiguration final {
public:
    struct Selection {
        std::string initial_host;
        // Actual TW531C10 operands; no Windows/display-locale inference.
        std::uint16_t word_59dfd8,word_59dfda;
    };
    struct Slot {std::string name_bytes,value_bytes;};
    struct Group {std::string name_bytes;std::vector<Slot> slots;};
    static constexpr std::string_view client_sha256=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    // Explicit resolved client root, actual native operands and source bounds.
    // Own subset excludes malformed/chunk/cache/temp-reopen branches, without
    // simulating the native formatter, GUI, or implicitly selecting a locale.
    static std::shared_ptr<const TaiwanNativeClientGroupConfiguration> read(
        const std::filesystem::path& actual_client_root,Selection,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    const Selection& selection() const noexcept {return selection_;}
    const TaiwanNativeResourceSelection& selected_resource() const noexcept {return selected_;}
    std::span<const std::uint8_t> decoded_bytes() const noexcept {return plain_;}
    std::span<const Group> groups() const noexcept {return groups_;}
    // Missing '$' stays absent; malformed '$' is rejected, never assigned0.
    std::optional<std::int32_t> version_operand() const noexcept {return version_;}
    std::optional<std::uint8_t> configured_slots(std::uint8_t ordinal) const noexcept;
private:
    TaiwanNativeClientGroupConfiguration(Selection,TaiwanNativeResourceSelection,
        std::vector<std::uint8_t>,std::vector<Group>,std::optional<std::int32_t>);
    const Selection selection_;
    const TaiwanNativeResourceSelection selected_;
    const std::vector<std::uint8_t> plain_;
    const std::vector<Group> groups_;
    const std::optional<std::int32_t> version_;
};
}
