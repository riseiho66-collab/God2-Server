#define BULL_TICK_TEST
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>
#include "bull_native_tick.cpp"
namespace {
using Byte=unsigned char;
std::array<std::array<Byte,4096>,28> actors;
std::array<Byte,110> definition;
std::array<Byte,64> manager;
unsigned now{},original_calls{},float_count{},cast_poses{},phase_number{};
bool owner_available=true;
unsigned finishes{};
std::vector<int> deltas;
template<class T>void write(void* p,unsigned o,T v){std::memcpy(static_cast<Byte*>(p)+o,&v,sizeof(v));}
template<class T>T read(void* p,unsigned o){T v{};std::memcpy(&v,static_cast<Byte*>(p)+o,sizeof(v));return v;}
void* __fastcall lookup(void*,void*,unsigned side,unsigned slot,unsigned layer){assert(side<2&&slot<14&&layer==0);return actors[side*14+slot].data();}
void __fastcall pose_mock(void*,void*,void* who,unsigned state,unsigned once){assert(once==1);if(who==actors[0].data()&&state==19)++cast_poses;}
void __fastcall text_mock(void*,void*,unsigned side,unsigned slot,unsigned ts,unsigned ti,int delta,unsigned zero,unsigned status,unsigned end){
    assert(side<2&&slot<14&&ts==1-side&&ti<14&&zero==0&&status==0&&end==28);
    auto* a=actors[side*14+slot].data();const auto idx=read<Byte>(a,0x239);assert(idx<14);
    write<std::int16_t>(a,0x28a+idx*2,static_cast<std::int16_t>(delta));++phase_number;
}
void __fastcall hp_mock(void*,void*,void* target,int delta){deltas.push_back(delta);write<int>(target,0xde8,std::max(0,read<int>(target,0xde8)+delta));}
void __fastcall bar_mock(void*,void*,void*){}
void __fastcall float_mock(void*,void*){++float_count;}
unsigned __fastcall original_mock(void*,void*,void* source){++original_calls;if(read<const Byte*>(source,0xec4)[0]==150){assert(read<Byte>(source,0x233)==7);write<Byte>(source,0x239,0);}return 1;}
void setup(unsigned count,int damage){
    actors={};definition={};definition[0]=150;now=0;original_calls=0;float_count=0;cast_poses=0;phase_number=0;deltas.clear();owner_available=true;finishes=0;
    auto* a=actors[0].data();write<const Byte*>(a,0xec4,definition.data());write<Byte>(a,0x239,static_cast<Byte>(count));
    for(unsigned i=0;i<count;++i){write<Byte>(a,0x23a+i,static_cast<Byte>(128+i));write<std::int16_t>(a,0x28a+i*2,static_cast<std::int16_t>(-damage));write<int>(actors[14+i].data(),0xde8,damage);write<Byte>(actors[14+i].data(),0x232,9);}
    bull_native_tick::initialize(0);
}
}
namespace bull_effect{
unsigned test_recording_hit{};
unsigned recording_damage(){return test_recording_hit;}
unsigned elapsed_ms(void*){return now;}
bool begin_actor(void*,unsigned,unsigned){return owner_available;}
void finish_actor(void*,unsigned,unsigned){++finishes;}
}
std::uintptr_t bull_tick_test_native(unsigned rva){
    switch(rva){case 0x11e6e0:return reinterpret_cast<std::uintptr_t>(&lookup);case 0x129870:return reinterpret_cast<std::uintptr_t>(&pose_mock);
    case 0x12b060:return reinterpret_cast<std::uintptr_t>(&text_mock);case 0x128a70:return reinterpret_cast<std::uintptr_t>(&hp_mock);
    case 0x12d9f0:return reinterpret_cast<std::uintptr_t>(&bar_mock);case 0x11dcc0:return reinterpret_cast<std::uintptr_t>(&float_mock);default:assert(false);return 0;}
}
int main(){
    const auto original=reinterpret_cast<bull_native_tick::Original>(&original_mock);
    for(unsigned count:{1u,2u,14u})for(int loss:{0,1,3,101,32767}){
        setup(count,loss);void* source=actors[0].data();
        assert(bull_native_tick::step(manager.data(),source,original)==0&&cast_poses==1);
        for(unsigned ms:{2333u,3666u,4999u,6333u}){now=ms;bull_native_tick::step(manager.data(),source,original);}
        assert(float_count==3*count); // fourth starts at6334ms, not one ms early.
        now=6334;assert(bull_native_tick::step(manager.data(),source,original)==0);assert(float_count==4*count&&phase_number==4*count);
        for(unsigned i=0;i<count;++i){assert(read<int>(actors[14+i].data(),0xde8)==0);assert(read<Byte>(actors[14+i].data(),0x232)==9);assert(read<std::int16_t>(source,0x28a+i*2)==-loss);}
        now=7999;assert(bull_native_tick::step(manager.data(),source,original)==0&&original_calls==0);
        now=8000;assert(bull_native_tick::step(manager.data(),source,original)==1&&original_calls==1);
        assert(read<Byte>(source,0x239)==0&&finishes==1);for(unsigned i=0;i<count;++i)assert(read<Byte>(actors[14+i].data(),0x232)==9);
    }
    setup(1,100);definition[0]=126;assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==1&&cast_poses==0&&float_count==0);
    setup(14,100);now=8000;assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==1&&float_count==56); // skipped-frame catchup.
    setup(1,101);write<Byte>(actors[0].data(),0x224,9);write<Byte>(actors[14].data(),0x277,1);
    bull_native_tick::step(manager.data(),actors[0].data(),original);now=5000;bull_native_tick::step(manager.data(),actors[0].data(),original);
    assert(read<Byte>(actors[14].data(),0x277)==1&&read<Byte>(actors[14].data(),0x232)==0);
    now=6334;bull_native_tick::step(manager.data(),actors[0].data(),original);
    assert(read<Byte>(actors[14].data(),0x277)==0&&read<Byte>(actors[14].data(),0x232)==9&&read<Byte>(actors[14].data(),0x1ea)==9);
    setup(2,100);write<Byte>(actors[0].data(),0x23b,0x8f);write<Byte>(actors[0].data(),0x233,7);
    assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==1&&read<Byte>(actors[14].data(),0x232)==9&&float_count==0);
    // Opposing caster uses the same timeline and native packed side/slot ABI.
    setup(14,101);
    actors[27]=actors[0];
    auto* enemy=actors[27].data();write<Byte>(enemy,0x234,0x8d);
    for(unsigned i=0;i<14;++i){actors[i]={};write<Byte>(enemy,0x23a+i,static_cast<Byte>(i));write<int>(actors[i].data(),0xde8,101);}
    bull_native_tick::step(manager.data(),enemy,original);now=8000;
    assert(bull_native_tick::step(manager.data(),enemy,original)==1&&float_count==56);
    for(unsigned i=0;i<14;++i)assert(read<int>(actors[i].data(),0xde8)==0);
    setup(1,101);owner_available=false;now=8000;
    assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==0);
    assert(cast_poses==0&&float_count==0&&read<Byte>(actors[14].data(),0x232)==9&&finishes==0);
    owner_available=true;now=0;
    assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==0&&cast_poses==1);
    now=8000;assert(bull_native_tick::step(manager.data(),actors[0].data(),original)==1&&finishes==1&&float_count==4);
    bull_native_tick::reset(nullptr);
    // Two same-side casters share every target; native ingestion sets the
    // batch death state before either acts. Each action drains once, only
    // at its fourth visual phase, regardless of native execution order.
    unsigned shared_cases=0;
    for(unsigned side:{0u,1u})for(unsigned count:{1u,2u,14u})for(bool reverse:{false,true}){
        setup(0,0);
        const unsigned first_slot=side*14,last_slot=side*14+13,target_base=(1-side)*14;
        auto* a=actors[first_slot].data();auto* b=actors[last_slot].data();
        for(auto slot:{first_slot,last_slot}){
            auto* source=actors[slot].data();write<const Byte*>(source,0xec4,definition.data());
            write<Byte>(source,0x234,static_cast<Byte>(side*128+slot%14));write<Byte>(source,0x239,static_cast<Byte>(count));
            for(unsigned i=0;i<count;++i){write<Byte>(source,0x23a+i,static_cast<Byte>((1-side)*128+i));
                write<std::int16_t>(source,0x28a+i*2,-100);write<Byte>(source,0x224+i,slot==last_slot?9:0);}
        }
        for(unsigned i=0;i<count;++i){auto* target=actors[target_base+i].data();write<int>(target,0xde8,200);
            write<Byte>(target,0x232,9);write<Byte>(target,0x277,2);}
        std::array<void*,2> order=reverse?std::array<void*,2>{b,a}:std::array<void*,2>{a,b};
        for(unsigned turn=0;turn<2;++turn){
            now=0;assert(bull_native_tick::step(manager.data(),order[turn],original)==0);
            now=5000;assert(bull_native_tick::step(manager.data(),order[turn],original)==0);
            for(unsigned i=0;i<count;++i)assert(read<Byte>(actors[target_base+i].data(),0x277)==2-turn);
            now=6334;assert(bull_native_tick::step(manager.data(),order[turn],original)==0);
            for(unsigned i=0;i<count;++i){auto* target=actors[target_base+i].data();
                assert(read<Byte>(target,0x277)==1-turn);assert(read<int>(target,0xde8)==100*(1-int(turn)));
                assert(read<Byte>(target,0x1ea)==(turn?9:15));}
            now=8000;assert(bull_native_tick::step(manager.data(),order[turn],original)==1);
        }
        assert(float_count==8*count&&finishes==2);++shared_cases;
    }
    assert(shared_cases==12);
    unsigned fixed_cases=0;
    for(unsigned side:{0u,1u})for(unsigned count:{1u,3u,14u})for(int initial:{99999,20007,1}){
        setup(count,9999);bull_effect::test_recording_hit=9999;
        const auto caster=side*14,target_base=(1-side)*14;
        if(side)actors[caster]=actors[0];
        auto* source=actors[caster].data();write<Byte>(source,0x234,Byte(side*128));
        for(unsigned i=0;i<count;++i){
            write<Byte>(source,0x23a+i,Byte((1-side)*128+i));
            auto* target=actors[target_base+i].data();write<int>(target,0xde8,initial);
            write<Byte>(target,0x232,initial<=39996?9:0);write<Byte>(target,0x277,1);
        }
        bull_native_tick::step(manager.data(),source,original);
        for(unsigned ms:{2334u,3667u,5000u,6334u}){now=ms;bull_native_tick::step(manager.data(),source,original);}
        assert(deltas.size()==count*4);for(int delta:deltas)assert(delta==-9999);
        for(unsigned i=0;i<count;++i)assert(read<int>(actors[target_base+i].data(),0xde8)==std::max(0,initial-39996));
        now=8000;assert(bull_native_tick::step(manager.data(),source,original)==1);++fixed_cases;
    }
    bull_effect::test_recording_hit=0;
    std::cout<<"Recording fixed damage: "<<fixed_cases<<" cases, both sides,9999 each hit,99999HP and overkill PASS\n";
    std::cout<<"bull native timeline: 1/2/14 targets, zero/rounding/max loss, four hits, death delay, 8s cleanup, native126 passthrough PASS\n";
    std::cout<<"shared-target death: both caster sides, 1/2/14 targets, forward/reverse execution: 12 cases PASS\n";
}
