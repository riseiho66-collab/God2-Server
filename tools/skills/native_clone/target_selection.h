// CUSTOM0058: native UI adaptation for custom skill 126 only.
#pragma once
#include <cstdint>
#include <cstring>
namespace shunying_target {
using Byte=unsigned char;
template<class T> inline T read(const void* p,unsigned at) {
    T value{};std::memcpy(&value,static_cast<const Byte*>(p)+at,sizeof(value));return value;
}
template<class T> inline void write(void* p,unsigned at,T value) {
    std::memcpy(static_cast<Byte*>(p)+at,&value,sizeof(value));
}
inline bool custom(const Byte* definition) {
    return definition && definition[0]==126 && definition[1]==0 && definition[0x45]==16;
}
inline unsigned enemies(const void* ui) {
    // 0051EE90 / 0051EDA0 use client-relative sides: 0 local, 1 opponents.
    // 00529870 death and 00520000 removal clear war+2F8; revive sets it.
    return read<unsigned>(ui,0x438)&read<unsigned>(ui,0x144938+0x2f8)&0x3fff;
}
inline unsigned maximum(unsigned mask) {
    unsigned count=0;for(;mask;mask&=mask-1)++count;return count<3?count:3;
}
inline bool valid_list(const Byte* targets,unsigned count,unsigned mask) {
    if(count==0 || count>3)return false;
    if(!targets)return false;
    unsigned seen=0;
    for(unsigned i=0;i<count;++i) {
        const auto target=targets[i];
        if(target<14 || target>=28)return false;
        const unsigned bit=1u<<(target-14);
        if(!(mask&bit) || (seen&bit))return false;
        seen|=bit;
    }
    return true;
}
inline bool valid_targets(const void* ui,unsigned count,unsigned mask) {
    return valid_list(static_cast<const Byte*>(ui)+0x44c,count,mask);
}
inline void clear_targets(void* ui) {
    write<unsigned>(ui,0x460,0);write<unsigned>(ui,0x43c,0);write<unsigned>(ui,0x440,0);
    std::memset(static_cast<Byte*>(ui)+0x44c,0,14);
}
inline bool active(const void* ui,const Byte* definition) {
    return custom(definition) && read<unsigned>(ui,0x464)==3 &&
        read<unsigned>(ui,0x44)!=0 &&
        (read<unsigned>(ui,0xa9e9c38)!=0 || read<unsigned>(ui,0xa9e9c3c)!=0);
}
// Returns false when there are no selectable living opponents. Caller then
// invokes native 00512620, which cancels skill selection without sending a turn.
inline bool refresh(void* ui) {
    const auto mask=enemies(ui),cap=maximum(mask);
    write<unsigned>(ui,0x434,0); // This custom skill is opponent-only.
    write<unsigned>(ui,0x438,mask);
    write<unsigned>(ui,0x45c,cap?cap:1); // Never arm a zero-target completion.
    const auto selected=read<unsigned>(ui,0x460);
    if(!cap || (selected && !valid_targets(ui,selected,mask)))clear_targets(ui);
    return cap!=0;
}
inline unsigned caster(const void* ui) {
    return read<Byte>(ui,read<unsigned>(ui,0xa9e9c38)==0 &&
        read<unsigned>(ui,0xa9e9c3c)!=0?0x52:0x51);
}
inline bool partial_confirm(const void* ui,unsigned previous_count,bool shift) {
    const auto count=read<unsigned>(ui,0x460);
    return shift && count>0 && count<3 && count==previous_count+1 &&
        valid_targets(ui,count,enemies(ui));
}
}
