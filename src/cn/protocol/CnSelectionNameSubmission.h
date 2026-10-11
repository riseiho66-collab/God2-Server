#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// Read-only native D3 produced by0047F750 after the normal selection name
// prompt. Scoped callers use ACCOUNT UI+1617C, not world creation17/19.
// Evidence: cn-selection-name-submit-01. No native result/handler/permission
// or mutation is implied by this view; keep all24 supplied payload bytes.
class CnSelectionNameSubmission {
public:
    static constexpr std::size_t record_size=25;
    static std::optional<CnSelectionNameSubmission> read(std::span<const std::uint8_t> record) {
        if(record.size()!=record_size || record[0]!=0xd3)return std::nullopt;
        const auto name=record.subspan(5,16);
        if(std::find(name.begin(),name.end(),0)==name.end())return std::nullopt;
        CnSelectionNameSubmission value;
        std::copy(record.begin()+1,record.end(),value.payload_.begin());return value;
    }
    std::string_view submitted_name_bytes() const {
        const auto end=std::find(payload_.begin()+4,payload_.begin()+20,0);
        return {reinterpret_cast<const char*>(payload_.data()+4),static_cast<std::size_t>(end-(payload_.begin()+4))};
    }
    // Both scoped UI callers copy their selected summary row WORD1792D4.
    // A row ordinal, never a native slot, common ID or name-based authority.
    // Actual current offered07/order/common-ID/phase owner must qualify it.
    std::uint16_t native_selection_ordinal() const {return word16(20);}
    std::uint32_t unresolved_prefix() const {
        return std::uint32_t(payload_[0]) | (std::uint32_t(payload_[1])<<8) |
            (std::uint32_t(payload_[2])<<16) | (std::uint32_t(payload_[3])<<24);
    }
    std::uint16_t unresolved_tail() const {return word16(22);}
    // Primary scoped callers extract at most14 raw bytes with433B00, then
    // 47F750 strncpy15 into zero-initialized16-byte storage. Zero prefix/tail
    // and padding are observed producer values, not guessed server policies.
    bool matches_observed_ui_shape() const {
        const auto name=submitted_name_bytes();
        return !name.empty() && name.size()<=14 && unresolved_prefix()==0 && unresolved_tail()==0 &&
            std::all_of(payload_.begin()+4+name.size(),payload_.begin()+20,[](auto b){return b==0;});
    }
    std::array<std::uint8_t,record_size> record_bytes() const {
        std::array<std::uint8_t,record_size> bytes;
        bytes[0]=0xd3;std::copy(payload_.begin(),payload_.end(),bytes.begin()+1);return bytes;
    }
private:
    std::uint16_t word16(std::size_t offset) const {
        return static_cast<std::uint16_t>(payload_[offset]+256u*payload_[offset+1]);
    }
    std::array<std::uint8_t,24> payload_{};
};
}
