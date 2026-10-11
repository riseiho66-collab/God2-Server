#pragma once
#include "cn/assets/CnResourceBytes.h"
#include <memory>
#include <string>
#include <string_view>
#include <utility>

namespace god2cn {
// Pinned CN0047C990/0047CBC0. Ordinals and slots come from the selected
// resource, not names, enable bits, node count or the native language preference.
class CnClientGroupConfiguration final {
public:
    struct Selection {
        std::string initial_host; // Actual0047C990 argument, prefix compared8.
        std::string address_operand; // Actual008AEEC0 operand, not Windows locale.
        Selection(std::string initial,std::string address)
            :initial_host(std::move(initial)),address_operand(std::move(address)) {}
    };
    struct Slot {
        std::string name_bytes; // Original narrow bytes, no conversion/ID join.
        std::string value_bytes; // Original first %s token; meaning not inferred.
    };
    struct Group {
        std::string name_bytes;
        std::vector<Slot> slots;
    };
    static std::shared_ptr<const CnClientGroupConfiguration> read(
        const std::filesystem::path& client_root,Selection,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    // Normal00405A60 startup only: complete argv[0] AFTER its native narrow
    // conversion, excluding NUL. WinMain's argument tail excludes the EXE.
    // No Windows quoting/ACP emulation or existing-cache/reinit claim.
    static std::shared_ptr<const CnClientGroupConfiguration> read_from_startup_argument(
        const std::filesystem::path& client_root,std::span<const std::uint8_t> first_argument,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    CnClientGroupConfiguration(const CnClientGroupConfiguration&)=delete;
    CnClientGroupConfiguration& operator=(const CnClientGroupConfiguration&)=delete;
    const Selection& selection() const noexcept {return selection_;}
    const CnSelectedResource& selected() const noexcept {return selected_;}
    std::span<const std::uint8_t> decoded_bytes() const noexcept {return plain_;}
    std::span<const Group> groups() const noexcept {return groups_;}
    std::optional<std::int32_t> network_version_integer() const noexcept {return version_;}
    //0047CBC0 stores the low BYTE, not the whole$ integer or UI version200.
    std::optional<std::uint8_t> network_version() const noexcept {
        if(!version_)return std::nullopt;
        return static_cast<std::uint8_t>(*version_);
    }
    std::optional<std::uint8_t> configured_slots(std::uint8_t ordinal) const noexcept;
private:
    CnClientGroupConfiguration(Selection,CnSelectedResource,std::vector<std::uint8_t>,std::vector<Group>,
        std::optional<std::int32_t>);
    const Selection selection_;
    const CnSelectedResource selected_;
    const std::vector<std::uint8_t> plain_;
    const std::vector<Group> groups_;
    const std::optional<std::int32_t> version_;
};
}
