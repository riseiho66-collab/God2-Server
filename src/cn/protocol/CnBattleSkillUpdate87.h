#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582f S2C87, battle-connection-2: actual queued consumer5523F6
// calls554750 directly with owner+A97181 and listcomponent+A89658.
// 54DEF0 is a retained equivalent body+1 adapter; its live caller is not
// established here. The native writer routes bit14, preserves bit15 state,
// and computes a raw bank-relative address from the six-bit kind/low-byte ID.
// This record only owns exact supplied native bytes. It creates no message,
// epoch, catalog identity, learned/cast grant or default flag value.
struct CnBattleSkillUpdate87 {
    static constexpr std::uint8_t opcode=0x87;
    // Actual native567B50 table87 branch returns3. The generic deferred
    // consumer retains its original table and asserts equality separately.
    static constexpr std::size_t logical_size=3;
    enum class List {Primary,Secondary};
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
        std::span<const std::uint8_t> body() const noexcept {return {bytes_.data()+1,2};}
        std::uint16_t raw_word() const noexcept {
            return std::uint16_t(bytes_[1])|(std::uint16_t(bytes_[2])<<8);
        }
        std::uint8_t definition_id() const noexcept {return bytes_[1];}
        std::uint8_t kind() const noexcept {return std::uint8_t(bytes_[2]&0x3f);}
        List list() const noexcept {return (raw_word()&0x4000)?List::Secondary:List::Primary;}
        bool state_bit15() const noexcept {return (raw_word()&0x8000)!=0;}
        bool operator==(const Record&) const=default;
    private:
        friend struct CnBattleSkillUpdate87;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        LogicalRecord bytes_;
    };
    // Preserve all kind/ID/flag values, including unknown declarations. The
    // actual publisher/catalog/game owner must qualify those separate domains.
    static std::optional<Record> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());
        return Record(retained);
    }
};
}
