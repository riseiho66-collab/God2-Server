#include "cn/world/CnPrebornSubjectState.h"
#include <algorithm>
#include <limits>
#include <utility>

namespace god2cn {
namespace {
std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) {
    return static_cast<std::uint16_t>(bytes[at]+256u*bytes[at+1]);
}
std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t at) {
    return std::uint32_t(bytes[at])|(std::uint32_t(bytes[at+1])<<8)|
        (std::uint32_t(bytes[at+2])<<16)|(std::uint32_t(bytes[at+3])<<24);
}
}
CnPrebornSubjectState::Snapshot::Snapshot(Scope scope,Current current,std::uint16_t subject,std::uint16_t inline_role_word,
    std::array<std::uint32_t,4> counters,std::uint8_t count,std::int8_t index,std::uint32_t selected,std::uint32_t bank,std::optional<Selection> selection)
    :scope_(scope),current_(std::move(current)),subject_identifier_(subject),inline_role_word_(inline_role_word),inline_counters_(counters),count_(count),index_(index),
     selected_(selected),bank_(bank),selection_(std::move(selection)) {}
bool CnPrebornSubjectState::Snapshot::current() const {
    const auto observe=current_;const auto scope=scope_;
    return observe && observe(scope);
}
std::optional<CnSelectedSubjectUpdate::Projection> CnPrebornSubjectState::Snapshot::project_selected_update(
    const CnSelectedSubjectUpdate& update) const {
    if(!current() || !selection_)return std::nullopt;
    auto result=update.project_actual_selected_row(selection_->actual_native_row);
    if(!current())return std::nullopt;
    return result;
}
std::optional<CnPrebornSubjectState::Snapshot> CnPrebornSubjectState::read_actual_source(Scope scope,
    std::span<const std::uint8_t> members,std::span<const std::uint8_t> object,Current current) {
    constexpr std::size_t prefix=0x4508,list=0x168,stride=0x3ec,slots=16;
    if(!scope.actual_ui_owner_word || !scope.actual_object_word || !scope.actual_revision || !current ||
       members.size()!=8 || object.size()<prefix ||
       scope.actual_ui_owner_word>std::numeric_limits<std::uint32_t>::max()-0x430b0 ||
       scope.actual_object_word>std::numeric_limits<std::uint32_t>::max()-prefix || !current(scope))return std::nullopt;
    if(dword(members,0)!=scope.actual_object_word+0x90 || dword(members,4)!=scope.actual_object_word)return std::nullopt;
    const auto count=object[0x164],raw_index=object[0x15f];
    const auto index=static_cast<std::int8_t>(raw_index<128?int(raw_index):int(raw_index)-256);
    if(count>slots)return std::nullopt;
    const auto selected=dword(object,0x160),bank=dword(object,0x4504);
    const auto subject_identifier=word(object,0);
    const auto inline_role_word=word(object,0x90);
    const std::array<std::uint32_t,4> inline_counters={
        dword(object,0xec),dword(object,0xf4),dword(object,0xf0),dword(object,0xf8)};
    std::optional<Selection> selection;
    if(index>=0 && std::size_t(index)<count) {
        const auto offset=list+std::size_t(index)*stride;
        if(selected==scope.actual_object_word+offset) {
            const auto entry=object.subspan(offset,stride);
            const auto skill_count=entry[0x1f0];
            //100 pointer/flag slots end before native page bytes+3E8/+3E9.
            //Do not silently clip a larger count or manufacture missing refs.
            if(skill_count>(0x3e8-0x258)/4)return std::nullopt;
            Selection supplied{selected,word(entry,0),entry[0x5b],{}, {},std::nullopt,false};
            std::copy(entry.begin(),entry.end(),supplied.actual_native_row.begin());
            supplied.skills.reserve(skill_count);
            for(std::size_t n=0;n<skill_count;++n)
                supplied.skills.push_back({dword(entry,0x258+4*n),entry[0x1f1+n]});
            const auto auxiliary_count=entry[0x5c];
            // Read the ACTUAL prefix, never manufacture4D5830 output. The
            // geometric bound protects this supplied row; native leaf itself
            // has no such guard. Stale/nonmatching auxiliary words remain
            // owned data: WORLD30 may clear only the primary count. The match
            // flag describes these captured bytes, not a lifecycle invariant.
            if(auxiliary_count<=(0x1f0-0x60)/4) {
                std::vector<std::uint32_t> auxiliary;auxiliary.reserve(auxiliary_count);
                for(std::size_t n=0;n<auxiliary_count;++n)auxiliary.push_back(dword(entry,0x60+4*n));
                std::size_t at=0;bool matches=true;
                for(const auto& reference:supplied.skills)if(reference.actual_native_flags&2) {
                    if(at>=auxiliary.size() || auxiliary[at]!=reference.actual_native_pointer_word)matches=false;
                    ++at;
                }
                supplied.native_auxiliary_matches_flag_projection=matches && at==auxiliary.size();
                supplied.native_auxiliary_pointers=std::move(auxiliary);
            }
            selection=std::move(supplied);
        }
    }
    //A count0/unselected source is retained as such, never a default first slot.
    if(!current(scope))return std::nullopt;
    return Snapshot(scope,std::move(current),subject_identifier,inline_role_word,inline_counters,
        count,index,selected,bank,std::move(selection));
}
}
