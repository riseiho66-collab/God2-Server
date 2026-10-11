#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Ordinary17's 0047DCC0 -> 0043D280 receive continuation only. This view
// requires a complete native02 record and retains every unresolved byte.
// Evidence: cn-create-status-resource-01. It cannot generate a native reply,
// authorize creation, or select a common name-comparison/storage policy.
class CnCharacterCreateStatus {
public:
    enum class UiBranch {
        LocationChoiceStage,
        NameCollisionUiBranch,
        OtherNonzeroUiBranch
    };
    static constexpr std::size_t record_size=23;
    static constexpr std::uint16_t name_collision_message_id=0x31;
    static std::optional<CnCharacterCreateStatus> read(
        std::span<const std::uint8_t> record) {
        if(record.size()!=record_size || record[0]!=0x02)return std::nullopt;
        CnCharacterCreateStatus value;
        std::copy(record.begin(),record.end(),value.record_.begin());
        return value;
    }
    std::uint16_t status() const {
        return static_cast<std::uint16_t>(record_[1]|(std::uint16_t(record_[2])<<8));
    }
    std::uint8_t raw_message_selector() const {return record_[21];}
    std::uint8_t message_field_selector() const {return record_[21]&0x7f;}
    UiBranch ordinary_ui_branch() const {
        if(status()==0)return UiBranch::LocationChoiceStage;
        if(status()==name_collision_message_id)return UiBranch::NameCollisionUiBranch;
        return UiBranch::OtherNonzeroUiBranch;
    }
    // A selector below3 only passes the native selector-domain check. A
    // missing/empty resource column still has no message pointer; do not turn
    // this predicate into permission to issue arbitrary status/selector pairs.
    bool within_native_message_selector_domain() const {
        return message_field_selector()<3;
    }
    std::span<const std::uint8_t,record_size> record_bytes() const {return record_;}
private:
    CnCharacterCreateStatus()=default;
    std::array<std::uint8_t,record_size> record_{};
};
}
