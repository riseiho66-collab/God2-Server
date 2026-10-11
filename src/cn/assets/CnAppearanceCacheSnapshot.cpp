#include "cn/assets/CnAppearanceCacheSnapshot.h"
#include <utility>

namespace god2cn {
namespace {
std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) {
    return static_cast<std::uint16_t>(bytes[at]|(std::uint16_t(bytes[at+1])<<8));
}
std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t at) {
    return std::uint32_t(word(bytes,at))|(std::uint32_t(word(bytes,at+2))<<16);
}
}
CnAppearanceCacheSnapshot::CnAppearanceCacheSnapshot(std::array<CnAppearanceCacheContext,2> contexts,
    std::int32_t active,std::uint64_t revision,Current current)
    :contexts_(contexts),active_(active),revision_(revision),current_(std::move(current)) {}
std::optional<CnAppearanceCacheSnapshot> CnAppearanceCacheSnapshot::read_native_owner(
    std::span<const std::uint8_t> bytes,std::uint64_t revision,Current current) {
    if(bytes.size()<0x172bc4 || !revision || !current || !current())return std::nullopt;
    const auto active_word=dword(bytes,0x172bc0);
    if(active_word>1 && active_word!=0xffffffff)return std::nullopt; // Other source states unqualified.
    std::array<CnAppearanceCacheContext,2> contexts{};
    for(std::size_t index=0;index<contexts.size();++index) {
        const auto at=0x124f0+index*0xb0368;
        contexts[index]={dword(bytes,at),word(bytes,at+4),word(bytes,at+6),word(bytes,at+8),word(bytes,at+10)};
    }
    if(!current())return std::nullopt;
    return CnAppearanceCacheSnapshot(contexts,active_word==0xffffffff?-1:static_cast<std::int32_t>(active_word),
        revision,std::move(current));
}
std::optional<CnAppearanceCacheSwitchSource> CnAppearanceCacheSnapshot::switch_source(
    std::uint16_t family,std::uint16_t map) const {
    if(!current_ || !current_())return std::nullopt;
    std::size_t selected=static_cast<std::size_t>((active_+1)&1);bool hit=false;
    if(active_>=0)for(std::size_t index=0;index<contexts_.size();++index) {
        if(contexts_[index].family_word==family && contexts_[index].map_word==map) {selected=index;hit=true;break;}
    }
    const auto& context=contexts_[selected];
    if(!context.native_bank_word || !current_())return std::nullopt;
    return CnAppearanceCacheSwitchSource{revision_,static_cast<std::uint8_t>(selected),context.native_bank_word,
        hit?context.current_cursor:context.base_cursor,family,map,hit,!hit};
}
bool CnAppearanceCacheSnapshot::selected_bank_current(std::uint8_t context,std::uint32_t bank,std::uint64_t revision) const {
    return revision==revision_ && bank && context<contexts_.size() && active_==context &&
        contexts_[context].native_bank_word==bank && current_ && current_();
}
}
