#pragma once
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Native S2C0A consumer contract. No empty/default billing-success constructor.
// Source:0047FE30 completion and00443FA0 display, current CN resource labels.
class CnAccountBilling {
public:
    enum class PayType:std::uint8_t {
        MonthlyValueAdded=0,TimedValueAdded=1,HalfDayValueAdded=2,
        Free=3,FreeNoPointDeduction=4,ValueAddedInactive=5,
        PublicBetaValueAdded6=6,PublicBetaValueAdded7=7
    };
    static std::optional<CnAccountBilling> read(std::span<const std::uint8_t> record) {
        if(record.size()!=17 || record[0]!=0x0a)return std::nullopt;
        CnAccountBilling result;
        std::copy(record.begin()+1,record.end(),result.payload_.begin());
        return result;
    }
    std::uint8_t raw_pay_type() const {return payload_[0];}
    std::optional<PayType> named_pay_type() const {
        if(payload_[0]>7)return std::nullopt;
        return static_cast<PayType>(payload_[0]);
    }
    std::uint8_t month() const {return payload_[1];}
    std::uint8_t day() const {return payload_[2];}
    std::uint8_t hour() const {return payload_[3];}
    std::uint8_t minute() const {return payload_[4];}
    std::uint8_t opaque_byte_5() const {return payload_[5];}
    std::int16_t year() const {
        return std::bit_cast<std::int16_t>(static_cast<std::uint16_t>(payload_[6]|(std::uint16_t(payload_[7])<<8)));
    }
    std::int32_t game_points() const {return signed_word(8);}
    std::int32_t timed_service_points() const {return signed_word(12);}
    // This models native presentation only, not access rights or billing rules.
    std::uint8_t display_pay_type(std::uint8_t group_type) const {
        return group_type==6 || group_type==7?group_type:raw_pay_type();
    }
    enum class PresentationKind {
        DateAndPoints,LabelAndClearDetails,NoBillingRowWrites,
        AssertionThenUnqualifiedDispatch
    };
    struct Presentation {
        std::uint8_t effective_pay_type;
        PresentationKind kind;
        // ProgramMsg one-based IDs, NOT SystemMessage or text literals.
        // Actual resource owner/availability is separate from this operand view.
        std::optional<std::uint16_t> label,expiry_format,points_format;
        bool monthly_date_assertion_operand;
    };
    //00443FA0 eight-cell44445C switch, supplied actual group billing BYTE.
    // This describes UI rows9/10/11 only; never decides access, expiry or price.
    Presentation presentation(std::uint8_t group_type) const {
        const auto effective=display_pay_type(group_type);
        if(effective>=9)
            return {effective,PresentationKind::AssertionThenUnqualifiedDispatch,
                    std::nullopt,std::nullopt,std::nullopt,false};
        //8 skips all billing-row writes; it does NOT clear old rows or name a
        //ninth PayType. Assertion behavior for>=9 is not emulated here.
        if(effective==8)
            return {effective,PresentationKind::NoBillingRowWrites,
                    std::nullopt,std::nullopt,std::nullopt,false};
        constexpr std::array<std::uint16_t,8> labels{321,319,323,324,478,651,688,689};
        if(effective<=2) {
            // Only case0 checks these operands. Native accepts year0 here;
            // no calendar/hour/minute/expiry/backend validity is inferred.
            const auto month_minus_one=static_cast<std::uint8_t>(month()-1);
            const bool assertion=effective==0 &&
                (year()<0 || month_minus_one>11 || day()==0 || day()>31);
            return {effective,PresentationKind::DateAndPoints,labels[effective],322,320,assertion};
        }
        return {effective,PresentationKind::LabelAndClearDetails,labels[effective],
                std::nullopt,std::nullopt,false};
    }
private:
    CnAccountBilling()=default;
    std::int32_t signed_word(std::size_t at) const {
        std::uint32_t value=0;
        for(unsigned i=0;i<4;++i)value|=std::uint32_t(payload_[at+i])<<(8*i);
        return std::bit_cast<std::int32_t>(value);
    }
    std::array<std::uint8_t,16> payload_{};
};
}
