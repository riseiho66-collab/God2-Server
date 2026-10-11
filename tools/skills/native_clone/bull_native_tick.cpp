// CUSTOM-0059: four presentation hits conserve the single authoritative result.
// Only definition 0/150 enters this timeline; all other skills use native code.
#include "bull_native_tick.h"
#include "bull_effect.h"
#include <array>
#include <cstring>

#if defined(BULL_TICK_TEST)
extern std::uintptr_t bull_tick_test_native(unsigned rva);
#endif
namespace bull_native_tick {
namespace {
using Byte=unsigned char;
std::uintptr_t base{};
template<class T>T get(const void* p,unsigned o){T v{};std::memcpy(&v,static_cast<const Byte*>(p)+o,sizeof(v));return v;}
template<class T>void put(void* p,unsigned o,T v){std::memcpy(static_cast<Byte*>(p)+o,&v,sizeof(v));}
template<class T>T api(unsigned rva){
#if defined(BULL_TICK_TEST)
    return reinterpret_cast<T>(bull_tick_test_native(rva));
#else
    return reinterpret_cast<T>(base+rva);
#endif
}
struct Cast {
    void* war{};void* source{};unsigned count{},phase{},recording_hit{};bool idle{};
    std::array<Byte,14> targets{},final_states{};
    std::array<unsigned,14> losses{};
};
std::array<Cast,28> casts;
void* actor(void* war,unsigned packed){
    if((packed&15)>=14)return nullptr;
    return api<void*(__thiscall*)(void*,unsigned,unsigned,unsigned)>(0x11e6e0)(war,(packed>>7)&1,packed&15,0);
}
void pose(void* war,void* who,unsigned state){
    if(get<std::uint16_t>(who,0x1a)<0x1000)
        api<void(__thiscall*)(void*,void*,unsigned,unsigned)>(0x129870)(war,who,state,1);
}
bool custom(void* source){
    if(!source)return false;
    auto definition=get<const Byte*>(source,0xec4);
    return definition && definition[0]==150 && definition[1]==0;
}
unsigned index(void* source){const auto p=get<Byte>(source,0x234);return (p>>7)*14+(p&15);}
void impact(Cast& cast,unsigned phase){
    constexpr unsigned cumulative[]{0,20,45,75,100};
    const auto owner=get<Byte>(cast.source,0x234);
    for(unsigned i=0;i<cast.count;++i){
        void* target=actor(cast.war,cast.targets[i]);
        if(!target)continue;
        const auto loss=cast.recording_hit?cast.recording_hit:
            cast.losses[i]*cumulative[phase+1]/100-cast.losses[i]*cumulative[phase]/100;
        // The received total is signed16; partitioning cannot exceed its range.
        const int delta=-static_cast<int>(loss);
        // 52B060 allocates/prepares hidden native floating text at +310+i*16.
        // Its index is source+239 during result ingestion. Restore both fields
        // immediately so the native target list and accepted total stay intact.
        const auto count=get<Byte>(cast.source,0x239);
        const auto total=get<std::int16_t>(cast.source,0x28a+i*2);
        put<Byte>(cast.source,0x239,static_cast<Byte>(i));
        api<void(__thiscall*)(void*,unsigned,unsigned,unsigned,unsigned,int,unsigned,unsigned,unsigned)>(0x12b060)(
            cast.war,owner>>7,owner&15,cast.targets[i]>>7,cast.targets[i]&15,delta,0,0,28);
        put<Byte>(cast.source,0x239,count);
        put<std::int16_t>(cast.source,0x28a+i*2,total);
        api<void(__thiscall*)(void*,void*,int)>(0x128a70)(cast.war,target,delta);
        api<void(__thiscall*)(void*,void*)>(0x12d9f0)(cast.war,target);
        if(get<Byte>(target,0x1ea)!=9){
            unsigned reaction=15;
            // Native524820 drains one pending action when the target's batch
            // final state OR this action says death. final_states preserves
            // the batch state while +232 is temporarily hidden for our four
            // visual phases. Checking only this action leaks the earlier
            // nonlethal hits when a later caster kills the shared target.
            if(phase==3&&(cast.final_states[i]==9||get<Byte>(cast.source,0x224+i)==9)){
                const auto pending=get<Byte>(target,0x277);
                reaction=pending<=1?9:15;
                if(pending>1)put<Byte>(cast.source,0x224+i,15);
                if(pending)put<Byte>(target,0x277,static_cast<Byte>(pending-1));
                put<Byte>(target,0x232,cast.final_states[i]);
            }
            pose(cast.war,target,reaction);
            put<Byte>(target,0x1ea,static_cast<Byte>(reaction));
        }
        api<void(__thiscall*)(void*)>(0x11dcc0)(static_cast<Byte*>(cast.source)+0x310+i*16);
    }
}
}
void initialize(std::uintptr_t image_base){base=image_base;casts={};}
void reset(void* war){for(auto& c:casts)if(!war||c.war==war)c={};}
unsigned step(void* war,void* source,Original original){
    if(!custom(source))return original(war,source);
    const auto owner=get<Byte>(source,0x234);
    const auto slot=index(source);
    if((owner&15)>=14||slot>=casts.size())return original(war,source);
    auto& c=casts[slot];
    if(c.war!=war||c.source!=source){
        c={};c.war=war;c.source=source;c.count=get<Byte>(source,0x239);
        if(!c.count||c.count>14){c={};return original(war,source);}
        for(unsigned i=0;i<c.count;++i){
            c.targets[i]=get<Byte>(source,0x23a+i);
            const int received=get<std::int16_t>(source,0x28a+i*2);
            if(received>0||(c.targets[i]&15)>=14||((c.targets[i]^get<Byte>(source,0x234))&128)==0){
                c={};return original(war,source);
            }
            c.losses[i]=static_cast<unsigned>(-received);
            if(void* target=actor(war,c.targets[i]))c.final_states[i]=get<Byte>(target,0x232);
        }
        // Result records may queue more than one caster before native playback.
        // The9999 token avoids signed16 overflow for four39996-total test hits.
        // Require every result to match the explicit local recording setting.
        if(bull_effect::recording_damage()==9999){
            bool matched=true;for(unsigned i=0;i<c.count;++i)matched=matched&&c.losses[i]==9999;
            if(matched)c.recording_hit=9999;
        }
        // A waiting owner must not alter a target or share another cast's clock.
        if(!bull_effect::begin_actor(war,owner>>7,owner&15)){c={};return 0;}
        // Validate all entries before changing any native actor state.
        for(unsigned i=0;i<c.count;++i){
            if(void* target=actor(war,c.targets[i])){
                // Death follows all four hits. The authoritative final state
                // remains saved and is restored for original end-of-cast cleanup.
                if(c.final_states[i]==9)put<Byte>(target,0x232,0);
            }
        }
        pose(war,source,19); // stationary native casting gesture during whistle.
        put<Byte>(source,0x233,4);
    }
    else if(!bull_effect::begin_actor(war,owner>>7,owner&15))return 0;
    const auto elapsed=bull_effect::elapsed_ms(war);
    if(elapsed>=837&&!c.idle){pose(war,source,0);c.idle=true;}
    constexpr unsigned ticks[]{70,110,150,190};
    while(c.phase<4&&std::uint64_t(elapsed)*30>=std::uint64_t(ticks[c.phase])*1000){impact(c,c.phase);++c.phase;}
    if(elapsed<8000)return 0;
    for(unsigned i=0;i<c.count;++i)if(void* target=actor(war,c.targets[i]))
        put<Byte>(target,0x232,c.final_states[i]);
    // Native phase7 restores idle/death poses, publishes +259, clears +239 and
    // returns completion once; native batch88/0B sequencing remains unchanged.
    put<Byte>(source,0x233,7);
    c={};
    const auto completed=original(war,source);
    if(completed)bull_effect::finish_actor(war,owner>>7,owner&15);
    return completed;
}
}
