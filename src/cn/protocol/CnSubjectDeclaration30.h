#pragma once
#include "cn/protocol/CnWorldConsumerRecords.h"

namespace god2cn {
// Pinned WORLD30 ->004D5B20, logical19. C2S30 is an independent request.
// Preserve the native append/reset/select branches, not shared identity rules.
class CnSubjectDeclaration30 final {
public:
    static constexpr std::size_t record_size=19;
    static constexpr std::size_t native_row_capacity=16;
    enum class Action {NoIdentifier,CapacityReturn,ResetExistingSkillCount,Append};
    struct Effect {
        Action action;
        std::uint8_t actual_active_count;
        std::optional<std::uint8_t> existing_reset_ordinal;
        // The inactive count-indexed slot's identity/name/5B are written BEFORE
        // the duplicate reset search. That slot must not be zero-fabricated.
        bool stages_inactive_slot;
        bool selects_appended_row;
        std::uint8_t native_row_byte5B;
    };
    static std::optional<CnSubjectDeclaration30> read(std::span<const std::uint8_t> record) {
        if(!CnWorldConsumerRecord<0x30,record_size>::parse_logical(record))return std::nullopt;
        std::array<std::uint8_t,record_size> bytes;
        std::copy(record.begin(),record.end(),bytes.begin());return CnSubjectDeclaration30(bytes);
    }
    std::array<std::uint8_t,record_size> record_bytes() const noexcept {return bytes_;}
    std::int8_t native_signed_identifier() const noexcept {return std::bit_cast<std::int8_t>(bytes_[1]);}
    std::uint16_t native_absolute_identifier() const noexcept {
        const int id=native_signed_identifier();return static_cast<std::uint16_t>(id<0?-id:id);
    }
    std::uint8_t native_control_byte17() const noexcept {return bytes_[18];}
    bool uses_template_name() const noexcept {return native_absolute_identifier()<100;}
    // Native high-ID strcpy can read beyond a malformed record. Report that
    // boundary as unknown; never emulate the overread or append a guessed NUL.
    // Includes the terminator, which may be the retained final control byte.
    std::optional<std::span<const std::uint8_t>> inline_c_string_in_record() const noexcept {
        const auto start=bytes_.begin()+2;
        const auto end=std::find(start,bytes_.end(),0);
        if(end==bytes_.end())return std::nullopt;
        return std::span<const std::uint8_t>{bytes_.data()+2,static_cast<std::size_t>(end-start+1)};
    }
    std::uint8_t native_row_byte5B() const noexcept {
        switch(native_absolute_identifier()) {
        case 4:case 8:case 10:case 31:case 32:case 33:case 34:return 1;
        default:return 0;
        }
    }
    // Actual ordered roster IDs only; pointers/process memory are optional
    // research, not own-server operation prerequisites. No gameplay mutation.
    std::optional<Effect> native_effect(std::span<const std::uint16_t> actual_roster) const noexcept {
        if(actual_roster.size()>255)return std::nullopt; //Cannot represent actual BYTE count.
        const auto count=static_cast<std::uint8_t>(actual_roster.size());
        const auto id=native_absolute_identifier();const auto flag=native_row_byte5B();
        if(!id)return Effect{Action::NoIdentifier,count,std::nullopt,false,false,flag};
        if(count>=native_row_capacity)return Effect{Action::CapacityReturn,count,std::nullopt,false,false,flag};
        if(!uses_template_name() && native_control_byte17()==1)
            for(std::size_t i=0;i<actual_roster.size();++i)
                if(actual_roster[i]==id)
                    return Effect{Action::ResetExistingSkillCount,count,static_cast<std::uint8_t>(i),true,false,flag};
        return Effect{Action::Append,count,std::nullopt,true,native_signed_identifier()<0,flag};
    }
private:
    explicit CnSubjectDeclaration30(std::array<std::uint8_t,record_size> bytes):bytes_(bytes) {}
    std::array<std::uint8_t,record_size> bytes_;
};
}
