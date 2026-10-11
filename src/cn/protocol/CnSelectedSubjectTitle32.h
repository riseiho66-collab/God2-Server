#pragma once
#include "cn/assets/CnSubjectTemplateNames.h"
#include "cn/protocol/CnSelectedSubjectUpdate.h"

namespace god2cn {
//WORLD32 logical2, current selected row text+13 ->native control3 %s.
//No subject ID or server rank/progression/permission rule is supplied.
class CnSelectedSubjectTitle32 final {
public:
    using Row=CnSelectedSubjectUpdate::Row;
    using Lookup=CnSubjectTemplateNames::LevelLookup;
    using Projection=CnSelectedSubjectUpdate::Projection;
    static std::optional<CnSelectedSubjectTitle32> read(std::span<const std::uint8_t> bytes) {
        if(!CnWorldConsumerRecord<0x32,2>::parse_logical(bytes))return std::nullopt;
        return CnSelectedSubjectTitle32({bytes[0],bytes[1]});
    }
    std::array<std::uint8_t,2> record_bytes() const noexcept {return bytes_;}
    std::uint8_t native_selector() const noexcept {return bytes_[1];}
    //Caller supplies the actual NONNULL selected row and current resource
    //lookup; no zero row, missing native string or stale-source success.
    std::optional<Projection> project_actual_selected_row(const Row& actual_row,const Lookup& lookup) const {
        using Action=CnSubjectTemplateNames::LevelAction;
        if(lookup.native_packet_selector!=native_selector() || lookup.native_header_count!=4 ||
           lookup.action==Action::UnresolvedAcceptedString)return std::nullopt;
        Projection result{actual_row,actual_row};
        if(lookup.action==Action::CopyKnownSource) {
            const auto& name=lookup.native_name_with_nul;
            if(!lookup.actual_record || name.empty() || name.back()!=0 || name.size()>actual_row.size()-0x13 ||
               std::find(name.begin(),name.end()-1,0)!=name.end()-1)return std::nullopt;
            std::copy(name.begin(),name.end(),result.projected_row.begin()+0x13);
        }
        //Native selector>count leaves existing row text, but still refreshes
        //control3. Actual owner must qualify its retained NUL/string boundary.
        return result;
    }
private:
    explicit CnSelectedSubjectTitle32(std::array<std::uint8_t,2> bytes):bytes_(bytes) {}
    std::array<std::uint8_t,2> bytes_;
};
}
