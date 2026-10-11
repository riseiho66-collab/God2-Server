#pragma once
#include <array>
#include <cstdint>
#include <cstring>

// CUSTOM-0059: defer only this cast's native floating-text ACT trees. The
// native 426AB0 linked-list order is preserved, including stars behind digits.
// Never move the ACTs, recreate damage, or change their animation/depth/viewport.
namespace bull_damage {
using Byte=unsigned char;
template<class T>T read(const void* p,unsigned offset){T v{};std::memcpy(&v,static_cast<const Byte*>(p)+offset,sizeof(v));return v;}
class Pass {
    void* display_{};
    std::array<Byte*,5000> entries_{};
    unsigned count_{};
public:
    Pass(void* display,const void* source):display_(display){
        if(!display||!source)return;
        const unsigned targets=read<Byte>(source,0x239);
        if(targets>14)return;
        std::array<bool,5000> selected{};
        std::array<bool,4096> visited{};
        std::array<unsigned,4096> pending{};
        unsigned queued=0;
        const auto enqueue=[&](unsigned h){if(h<4096&&!visited[h]){visited[h]=true;pending[queued++]=h;}};
        const void* manager=nullptr;
        for(unsigned i=0;i<targets;++i){
            const auto* text=static_cast<const Byte*>(source)+0x310+i*16;
            const void* owner=read<void*>(text,4);
            if(!owner||read<void*>(owner,4)!=display)continue;
            if(manager&&manager!=owner)continue;
            manager=owner;enqueue(read<std::uint16_t>(text,10));
        }
        for(unsigned n=0;n<queued;++n){
            const auto* action=static_cast<const Byte*>(manager)+0x10+pending[n]*0x290;
            if(action[0]!=2)continue;
            const auto select=[&](unsigned h){if(h<5000)selected[h]=true;};
            select(read<std::uint16_t>(action,0xe));
            const int followers=read<std::int16_t>(action,0x254);
            if(followers>=0&&followers<=106)
                for(int j=0;j<followers;++j)select(read<std::uint16_t>(action,0xac+j*2));
            // 51DE40 -> 41F040 creates digits and impact star as child ACTs.
            for(unsigned j=0;j<17;++j)enqueue(read<std::uint16_t>(action,0x256+j*2));
            if(action[9]||action[10])for(unsigned j=0;j<6;++j)enqueue(read<std::uint16_t>(action,0x27a+j*2));
        }
        const auto pool=reinterpret_cast<std::uintptr_t>(display)+0x1258;
        auto* entry=read<Byte*>(display,0xf555c);
        for(unsigned n=0;entry&&n<5000;++n){
            const auto address=reinterpret_cast<std::uintptr_t>(entry);
            if(address<pool||address-pool>=5000*200||(address-pool)%200)break;
            const unsigned h=static_cast<unsigned>((address-pool)/200);
            if(selected[h]&&entry[0]==2&&entry[3]==0){entries_[count_++]=entry;entry[0]=3;}
            entry=read<Byte*>(entry,0xc4);
        }
    }
    Pass(const Pass&)=delete;
    Pass& operator=(const Pass&)=delete;
    ~Pass(){restore();}
    void restore(){for(unsigned i=0;i<count_;++i)entries_[i][0]=2;}
    template<class Draw>void draw(Draw native){
        restore();
        for(unsigned i=0;i<count_;++i){auto* entry=entries_[i];
            native(display_,0,int(read<std::int16_t>(entry,4)),int(read<std::int16_t>(entry,6)),entry);
        }
        count_=0;
    }
};
}
