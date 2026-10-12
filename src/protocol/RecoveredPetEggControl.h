#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c PetEgg primary4D6940 and later dialogs4DA730/4DC880
// ->4D6BA0 ->4132E0. Local UI open alone does not emit the later request.
// B1 logical2 carries a selector BYTE, without explicit slot/key/full20 fields.
// Qualified primary0..6/9 and later10/11,14..37/43 are distinct from options7/8.
// No original server operation, E5/E6 reply pairing or mutation is inferred.
struct RecoveredPetEggControl {
    static constexpr std::uint8_t opcode=0xb1;
    static constexpr std::size_t logical_size=2;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    enum class SourcePath {PrimaryAction, AlternateDialog, AlternateList};
    struct Request {
        std::uint8_t selector_raw;
        bool operator==(const Request&) const = default;
    };
    // These are qualified UI source branches, not authoritative state/phase
    // bindings or a prediction that an earlier event emits a later request.
    // The list branch additionally reads a current context WORD row; neither
    // that row nor the opening event is carried by this two-byte record.
    static constexpr std::optional<SourcePath> source_path(std::uint8_t selector) noexcept {
        if(selector<=6 || selector==9)return SourcePath::PrimaryAction;
        if(selector==10 || selector==11)return SourcePath::AlternateDialog;
        if((selector>=14 && selector<=37) || selector==43)return SourcePath::AlternateList;
        return {};
    }
    // Exact4DC880 selected-row operand projection after its unsigned WORD
    // range gate. Low-BYTE subtraction then WORD sign extension gives0..23;
    // only the final argument's low BYTE is queued. This supplies no current row,
    // control index, event/phase rights nor a server-owned item identity.
    static constexpr std::optional<std::uint8_t> alternate_list_selector_from_word(
        std::uint16_t row_word) noexcept {
        if(row_word<0x1821 || row_word>0x1838)return {};
        return static_cast<std::uint8_t>((row_word&0xff)-0x21+14);
    }
    // Scope is the recovered primary and later UI actions, not every caller
    // of the generic BYTE producer. Other B1 variants remain open.
    static constexpr bool qualified_selector(std::uint8_t selector) noexcept {
        return source_path(selector).has_value();
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=opcode ||
           !qualified_selector(logical[1]))return {};
        return Request{logical[1]};
    }
    static std::array<std::uint8_t,logical_size> encode(Request request) noexcept {
        return {opcode,request.selector_raw};
    }
};
}
