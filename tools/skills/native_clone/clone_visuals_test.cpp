// CUSTOM-0058 synthetic ownership/count/frame regressions, not native UI proof.
#include "clone_visuals.h"
#include "clone_particles.h"
#include <cmath>
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using Byte = unsigned char;
std::vector<Byte> war(0x400), action(0x290020), display(0xf6000),rtg(0xa6560);
std::array<int,4> slash_clip{0,0,800,600},slash_clip2{5,5,795,595};
std::array<std::array<std::array<Byte, 0xecc>, 6>, 28> actors{};
unsigned allocations{}, releases{}, checks{}, clock_ms{};
std::array<std::array<Byte,32>,3> bitmaps{};
std::array<std::array<Byte,64>,3> pixels{};
std::array<std::array<unsigned short,16>,3> spans{};
std::array<std::array<unsigned short,256>,3> palettes{};
template<class T> void set(void* p,unsigned off,T x){std::memcpy(static_cast<Byte*>(p)+off,&x,sizeof(x));}
template<class T> T get(void* p,unsigned off){T v;std::memcpy(&v,static_cast<Byte*>(p)+off,sizeof(v));return v;}
Byte* entry(unsigned h){return display.data()+0x1258+h*200;}
unsigned __fastcall alloc(void*,void*) {
    for(unsigned h=0;h<5000;++h)if(entry(h)[0]==0){entry(h)[0]=1;++allocations;return h;}
    return 0xffff;
}
void __fastcall init(void*,void*,unsigned h,int x,int y,void* image,unsigned flags,int z,void* palette,void* clip){
    auto p=entry(h);p[0]=2;set<short>(p,4,short(x));set<short>(p,6,short(y));set<short>(p,8,short(z));
    set<void*>(p,0x8c,image);set<void*>(p,0x94,palette);p[1]=Byte(flags);set<float>(p,0x90,1.0f);
    if(clip){std::memcpy(p+0x98,clip,16);set<void*>(p,0xb8,p+0x98);}else set<void*>(p,0xb8,nullptr);
}
void __fastcall free_image(void*,void*,unsigned h){assert(entry(h)[0]!=0);entry(h)[0]=0;++releases;}
void __fastcall position(void*,void*,unsigned h,int x,int y){set<short>(entry(h),4,short(x));set<short>(entry(h),6,short(y));}
void __fastcall depth(void*,void*,unsigned h,int z){
    if(get<short>(entry(h),8)!=short(z))entry(h)[2]=0; // native 00426CF0 -> 00425DC0
    set<short>(entry(h),8,short(z));
}
void expect(bool ok){if(!ok)std::cerr<<"failed check "<<checks+1<<" allocations="<<allocations<<" releases="<<releases<<"\n";assert(ok);++checks;}
void prepare(unsigned side){
    std::fill(war.begin(),war.end(),Byte{});std::fill(action.begin(),action.end(),Byte{});std::fill(display.begin(),display.end(),Byte{});
    clock_ms=1000;
    for(unsigned i=0;i<4096;++i){auto row=action.data()+0x10+i*0x290;set<unsigned short>(row,0xe,0xffff);for(unsigned c=0;c<17;++c)set<unsigned short>(row,0x256+c*2,0xffff);for(unsigned c=0;c<6;++c)set<unsigned short>(row,0x27a+c*2,0xffff);}
    set<unsigned short>(display.data(),0x1210,0xf800);set<unsigned short>(display.data(),0x1212,0x7e0);set<unsigned short>(display.data(),0x1214,0x1f);
    for(unsigned i=0;i<3;++i){
        set<unsigned short>(bitmaps[i].data(),0,8);set<unsigned short>(bitmaps[i].data(),2,8);bitmaps[i][6]=0;
        set<void*>(bitmaps[i].data(),8,palettes[i].data());set<void*>(bitmaps[i].data(),0x10,spans[i].data());set<void*>(bitmaps[i].data(),0x14,pixels[i].data());
        for(unsigned j=0;j<256;++j)palettes[i][j]=static_cast<unsigned short>(j?0xf800:0);
        for(unsigned y=0;y<8;++y){spans[i][2*y]=static_cast<unsigned short>(y/2);spans[i][2*y+1]=static_cast<unsigned short>(8-y/2);}
        pixels[i].fill(1);spans[i][0]=spans[i][1]=0;
    }
    set<void*>(war.data(),0xc,action.data());set<void*>(action.data(),4,display.data());
    for(unsigned i=0;i<28;++i)for(unsigned layer=0;layer<6;++layer){
        auto a=actors[i][layer].data();std::memset(a,0,0xecc);
        set<void*>(war.data(),0x38+(i*6+layer)*4,a);set<unsigned short>(a,0x1a,0xffff);
        set<short>(a,0x1d4,short(i<14?500-int(i)*10:200+int(i-14)*20));
        set<short>(a,0x1d6,short(i<14?350-int(i)*10:200+int(i-14)*30));
    }
    for(unsigned layer=0;layer<2;++layer){
        auto a=actors[side*14][layer].data();set<unsigned short>(a,0x1a,static_cast<unsigned short>(layer));
        auto act=action.data()+0x10+layer*0x290;act[0]=2;set<unsigned short>(act,0xe,static_cast<unsigned short>(100+layer));
        set<short>(act,0x12,get<short>(a,0x1d4));set<short>(act,0x14,get<short>(a,0x1d6));
        auto p=entry(100+layer);p[0]=2;p[1]=Byte(side+1);set<short>(p,4,short(get<short>(a,0x1d4)-16));set<short>(p,6,short(get<short>(a,0x1d6)-32));set<short>(p,8,get<short>(a,0x1d6));
        set<void*>(p,0x8c,bitmaps[layer].data());set<void*>(p,0x94,palettes[layer].data());set<float>(p,0x90,1.0f);
    }
    actors[side*14][0][0x1ea]=0x13;actors[side*14][0][0x233]=3;allocations=releases=0;
    actors[side*14][0][0x1e9]=3;actors[side*14][0][0x23a]=Byte((1-side)<<7);
}
}
std::uintptr_t clone_test_native(unsigned rva){
    switch(rva){
    case 0x25b60:return reinterpret_cast<std::uintptr_t>(&alloc);
    case 0x25dc0:return reinterpret_cast<std::uintptr_t>(&init);
    case 0x26a30:return reinterpret_cast<std::uintptr_t>(&free_image);
    case 0x26e80:return reinterpret_cast<std::uintptr_t>(&position);
    case 0x26cf0:return reinterpret_cast<std::uintptr_t>(&depth);
    default:assert(false);return 0;
    }
}

unsigned clone_test_milliseconds(){return clock_ms;}
namespace shunying_clone::particles {
void initialize(std::uintptr_t){}
void begin_frame(void*,unsigned,unsigned){}
void burst(unsigned,float,float,float,float){}
void return_stream(unsigned,float,float,float,float,float,float){}
void silhouette(unsigned,const void*,float,float,unsigned,float){}
void end_frame(unsigned){}
void release_cast(unsigned){}
void reset_display(void*){}
}
void step(unsigned elapsed){clock_ms+=elapsed;shunying_clone::before_frame(war.data());shunying_clone::after_frame(war.data());shunying_clone::before_render(display.data());}
void selected(unsigned side,unsigned count){
    auto a=actors[side*14][0].data();
    for(unsigned i=0;i<count;++i){shunying_clone::on_result(war.data(),side,0,1-side,i,true);++a[0x239];}
}
void near(float a,float b){expect(std::abs(a-b)<.005f);}
int main(){
    static_assert(sizeof(void*)==4);shunying_clone::initialize(0x400000);
    for(unsigned side=0;side<2;++side)for(unsigned count=1;count<=3;++count){
        prepare(side);selected(side,count);auto a=actors[side*14][0].data();
        step(0);expect(allocations==0);step(199);expect(allocations==0);
        step(101);expect(allocations==2*(count-1));
        if(count>1){
            near(get<float>(entry(0),0x90),.14f);
            expect(get<void*>(entry(0),0x8c)==bitmaps[0].data());
            expect(entry(0)[1]==entry(100)[1]); // real caster facing survives cloning
            expect(get<void*>(entry(0),0x94)!=palettes[0].data());
            expect(palettes[0][1]==0xf800);
            const auto ownpalette=get<unsigned short*>(entry(0),0x94);
            expect(ownpalette[1]!=0xf800 && (ownpalette[1]&0x7e0)!=0);
            step(200);near(get<float>(entry(0),0x90),.42f);
            const auto originx=get<short>(a,0x1d4);
            expect(get<short>(entry(0),4)==std::lround(originx-72.0f/1.28f-16));
            shunying_clone::on_result(war.data(),side,0,1-side,0,true);step(0);
            expect(allocations==2*(count-1));
            // Warp does not follow native walking. It freezes the last cast pose
            // for four 30Hz ticks, then follows current caster layers.
            a[0x233]=5;step(1);const unsigned target=(1-side)*14+1;
            const float sign=side==0?1.0f:-1.0f;
            expect(get<short>(entry(0),4)==std::lround(get<short>(actors[target][0].data(),0x1d4)+sign*78/1.28f-16));
            expect(get<short>(entry(100),4)==std::lround(get<short>(actors[(1-side)*14][0].data(),0x1d4)+sign*78/1.28f-16));
            const short warp_x=get<short>(entry(100),4);
            set<void*>(entry(100),0x8c,bitmaps[2].data());step(100);
            expect(get<short>(entry(100),4)==warp_x);
            expect(get<void*>(entry(0),0x8c)==bitmaps[0].data());
            step(34);expect(get<void*>(entry(0),0x8c)==bitmaps[2].data());
            a[0x239]=0;step(1);expect(shunying_clone::has_tail(war.data()));
            expect(get<short>(entry(100),4)==originx-16);
            step(333);near(get<float>(entry(0),0x90),.21021f);
            auto scaled=get<Byte*>(entry(0),0x8c);expect(scaled!=bitmaps[2].data());
            expect(get<unsigned short>(scaled,0)==6);
            auto outputspans=get<unsigned short*>(scaled,0x10);
            expect(outputspans[0]==0 && outputspans[1]==0);
            expect(outputspans[10]==3 && outputspans[11]==4);
            expect(get<void*>(scaled,0x14)!=pixels[2].data());
            step(334);expect(releases==allocations);expect(shunying_clone::has_tail(war.data()));
            step(333);expect(!shunying_clone::has_tail(war.data()));
        }else{a[0x239]=0;step(1);expect(!shunying_clone::has_tail(war.data()));}
        shunying_clone::reset(war.data());expect(releases==allocations);
        expect(entry(100)[0]==2 && entry(101)[0]==2);
    }
    prepare(0);selected(0,3);step(0);step(500);expect(allocations==4);
    shunying_clone::on_result(war.data(),0,0,1,0,false);expect(releases==4);
    step(100);expect(allocations==4);
    actors[0][0][0x239]=0;selected(0,2);step(0);step(500);expect(allocations==6);
    shunying_clone::before_display_reset(action.data());expect(releases==4);
    shunying_clone::before_display_reset(display.data());expect(releases==6);
    step(100);expect(allocations==6);
    // Native first target (+23A), not latest result (+235), is the real actor.
    prepare(0);selected(0,3);auto a=actors[0][0].data();
    a[0x23a]=0x82;a[0x235]=0x80;a[0x233]=4;step(0);expect(allocations==4);
    expect(get<short>(entry(0),4)==245 && get<short>(entry(0),6)==227);
    expect(get<short>(entry(2),4)==265 && get<short>(entry(2),6)==257);
    shunying_clone::reset(war.data());expect(releases==4);
    // Pending results remain until native activation; cancellation still frees.
    prepare(1);selected(1,2);a=actors[14][0].data();a[0x1ea]=0;
    step(500);expect(allocations==0);a[0x1ea]=0x13;step(0);expect(allocations==0);
    step(500);expect(allocations==2);a[0x1ea]=0;step(0);expect(releases==2);
    expect(!shunying_clone::has_tail(war.data()));
    // Native RTG track visuals are full-color copies, never shadow-filtered.
    for(unsigned side=0;side<2;++side)for(unsigned count=2;count<=3;++count){
        shunying_clone::reset(war.data());prepare(side);selected(side,count);
        std::fill(rtg.begin(),rtg.end(),Byte{});
        set<void*>(war.data(),0x20,rtg.data());set<void*>(rtg.data(),0xa654c,action.data());
        set<unsigned>(rtg.data(),0xa6540,1);set<unsigned>(rtg.data(),0,2);
        set<short>(rtg.data(),0x28,0);set<short>(rtg.data(),0xa1042,3);
        set<unsigned short>(actors[side*14][5].data(),0x1a,0);
        const auto primary=actors[(1-side)*14][0].data();
        for(unsigned i=0;i<3;++i){
            set<unsigned>(rtg.data(),0x34+i*0x20,2);
            set<unsigned short>(rtg.data(),0x40+i*0x20,static_cast<unsigned short>(2+i));
            auto action_entry=action.data()+0x10+(2+i)*0x290;action_entry[0]=2;
            set<unsigned short>(action_entry,0xe,static_cast<unsigned short>(110+i));
            // Distinct native directional frame and horizontal-flip flag per
            // side: never pass by checking two identical friendly fixtures.
            auto source=entry(110+i);source[0]=2;source[1]=Byte(side?6:7);source[2]=3;source[3]=1;
            set<short>(source,4,short(get<short>(primary,0x1d4)+10+int(i)));
            set<short>(source,6,short(get<short>(primary,0x1d6)+20));set<short>(source,8,500);
            set<void*>(source,0x8c,bitmaps[2-side].data());set<void*>(source,0x94,palettes[2-side].data());
            set<float>(source,0x90,.73f);set<void*>(source,0xb8,slash_clip.data());set<void*>(source,0xbc,slash_clip2.data());
        }
        actors[side*14][0][0x233]=4;step(0);expect(allocations==5*(count-1));
        const unsigned first=2*(count-1);
        for(unsigned clone=0;clone<count-1;++clone){
            const auto target=actors[(1-side)*14+1+clone][0].data();
            auto output=entry(first+clone*3);
            expect(get<short>(output,4)==get<short>(target,0x1d4)+10);
            expect(get<short>(output,6)==get<short>(target,0x1d6)+20);
            expect(get<void*>(output,0x8c)==bitmaps[2-side].data());
            expect(get<void*>(output,0x94)==palettes[2-side].data());near(get<float>(output,0x90),.73f);
            expect(output[1]==Byte(side?6:7) && output[2]==3 && output[3]==1);
            expect(get<void*>(output,0xb8)!=slash_clip.data());expect(get<void*>(output,0xbc)!=slash_clip2.data());
            expect(std::memcmp(get<void*>(output,0xb8),slash_clip.data(),16)==0);
            expect(std::memcmp(get<void*>(output,0xbc),slash_clip2.data(),16)==0);
        }
        // A track can change its frame/palette and disappear before the RTG ends.
        set<void*>(entry(110),0x8c,bitmaps[1].data());set<void*>(entry(110),0x94,palettes[1].data());
        slash_clip[0]=2;step(33);
        expect(get<void*>(entry(first),0x8c)==bitmaps[1].data());
        expect(get<void*>(entry(first),0x94)==palettes[1].data());
        expect(get<int>(get<void*>(entry(first),0xb8),0)==2);
        action[0x10+3*0x290]=1;step(33);expect(releases==count-1);
        set<unsigned>(rtg.data(),0x34+2*0x20,0);step(33);expect(releases==2*(count-1));
        // Pausing the RTG releases the last visible slash immediately.
        set<unsigned>(rtg.data(),0,1);step(33);expect(releases==3*(count-1));
        set<unsigned>(rtg.data(),0,2);step(33);expect(allocations==6*(count-1));
        actors[side*14][0][0x239]=0;step(33);expect(releases==4*(count-1));
        shunying_clone::reset(war.data());expect(releases==allocations);
        expect(entry(110)[0]==2 && entry(111)[0]==2 && entry(112)[0]==2);
        slash_clip[0]=0;
    }
    // Composite slash: root + follow + attached grandchild + spawned ACT,
    // including duplicate handles and a cycle. Only five unique images render.
    prepare(0);selected(0,2);actors[0][0][0x233]=4;
    std::fill(rtg.begin(),rtg.end(),Byte{});set<void*>(war.data(),0x20,rtg.data());
    set<void*>(rtg.data(),0xa654c,action.data());set<unsigned>(rtg.data(),0xa6540,1);
    set<unsigned>(rtg.data(),0,2);set<short>(rtg.data(),0x28,0);set<short>(rtg.data(),0xa1042,2);
    set<unsigned short>(actors[0][5].data(),0x1a,0);
    for(unsigned i=0;i<2;++i){set<unsigned>(rtg.data(),0x34+i*0x20,2);set<unsigned short>(rtg.data(),0x40+i*0x20,static_cast<unsigned short>(2+i));}
    for(unsigned i=2;i<6;++i){auto row=action.data()+0x10+i*0x290;row[0]=2;set<unsigned short>(row,0xe,static_cast<unsigned short>(i==2?110:118+i));}
    auto root_action=action.data()+0x10+2*0x290;
    set<short>(root_action,0x254,2);set<unsigned short>(root_action,0xac,120);set<unsigned short>(root_action,0xae,120);
    set<unsigned short>(root_action,0x256,3);root_action[10]=1;set<unsigned short>(root_action,0x27a,5);
    set<unsigned short>(action.data()+0x10+3*0x290,0x256,4);
    set<unsigned short>(action.data()+0x10+4*0x290,0x256,2); // Cycle back to root.
    const unsigned order[]{123,110,121,120,122};
    for(unsigned i=0;i<5;++i){auto row=entry(order[i]);row[0]=2;row[1]=Byte(i+1);row[3]=1;
        set<short>(row,4,short(200+int(i)));set<short>(row,6,200);set<short>(row,8,500);
        set<void*>(row,0x8c,bitmaps[i%3].data());set<void*>(row,0x94,palettes[i%3].data());set<float>(row,0x90,1);
        set<void*>(row,0xc4,i<4?entry(order[i+1]):nullptr);
    }
    set<void*>(display.data(),0xf555c,entry(order[0]));
    // Native can advance its special ACT after the battle frame hook.
    shunying_clone::before_frame(war.data());shunying_clone::after_frame(war.data());
    expect(allocations==2);
    set<void*>(entry(120),0x8c,bitmaps[2].data());set<void*>(entry(120),0x94,palettes[2].data());
    shunying_clone::before_render(display.data());expect(allocations==7);
    for(unsigned i=0;i<5;++i){
        expect(entry(2+i)[1]==entry(order[i])[1]);
        expect(get<void*>(entry(2+i),0x8c)==get<void*>(entry(order[i]),0x8c));
        expect(get<void*>(entry(2+i),0x94)==get<void*>(entry(order[i]),0x94));
        near(get<float>(entry(2+i),0x90),1.0f);
        expect(get<short>(entry(2+i),4)==get<short>(entry(order[i]),4)+20);
    }
    // Re-render without advancing ACT/timers preserves the same source frame.
    shunying_clone::before_render(display.data());expect(allocations==7);
    action[0x10+5*0x290]=0;shunying_clone::before_render(display.data());expect(releases==1);
    set<unsigned short>(root_action,0x256,0xffff);set<unsigned>(rtg.data(),0x34+0x20,0);
    shunying_clone::before_render(display.data());expect(releases==3);
    actors[0][0][0x239]=0;step(33);expect(releases==5);
    shunying_clone::reset(war.data());expect(releases==allocations);
    for(unsigned source:order)expect(entry(source)[0]==2);

    // Native9006 detached emissions: fifth group creates two independent ACTs
    // (blue blade + red cross) without +27A ownership. Creation hooks must
    // preserve BOTH, even though parent+A6 only names the latest child.
    for(unsigned side=0;side<2;++side)for(unsigned count=2;count<=3;++count){
        prepare(side);selected(side,count);actors[side*14][0][0x233]=4;
        std::fill(rtg.begin(),rtg.end(),Byte{});set<void*>(war.data(),0x20,rtg.data());
        set<void*>(rtg.data(),0xa654c,action.data());set<unsigned>(rtg.data(),0xa6540,1);
        set<unsigned>(rtg.data(),0,2);set<short>(rtg.data(),0x28,0);set<short>(rtg.data(),0xa1042,1);
        set<unsigned short>(actors[side*14][5].data(),0x1a,0);
        set<unsigned>(rtg.data(),0x34,2);set<unsigned short>(rtg.data(),0x40,2);
        auto root=action.data()+0x10+2*0x290;root[0]=2;set<unsigned short>(root,0xe,110);
        for(unsigned i=0;i<5;++i){auto d=entry(110+i);d[0]=2;d[1]=Byte(i+1);
            set<void*>(d,0x8c,bitmaps[i%3].data());set<void*>(d,0x94,palettes[i%3].data());
            set<float>(d,0x90,1);set<short>(d,4,200);set<short>(d,6,200);set<short>(d,8,400);
        }
        const auto create=[&](const void* parent,unsigned h,unsigned dh){
            shunying_clone::on_action_initializing(action.data(),parent,h);
            auto row=action.data()+0x10+h*0x290;row[0]=2;set<unsigned short>(row,0xe,static_cast<unsigned short>(dh));
        };
        create(root,3,111);create(root,4,112);set<unsigned short>(root,0xa6,4);
        // An unrelated body/UI ACT cannot attribute a generated image to this cast.
        create(action.data()+0x10,6,114);
        step(0);expect(allocations==5*(count-1));
        for(unsigned clone=0;clone<count-1;++clone){
            const unsigned first=2*(count-1)+3*clone;
            for(unsigned i=0;i<3;++i){expect(entry(first+i)[1]==Byte(i+1));
                expect(get<void*>(entry(first+i),0x8c)==bitmaps[i%3].data());
                expect(get<void*>(entry(first+i),0x94)==palettes[i%3].data());near(get<float>(entry(first+i),0x90),1);}
        }
        // Pending child ownership is available to nested initialization immediately.
        create(action.data()+0x10+3*0x290,5,113);shunying_clone::before_render(display.data());
        expect(allocations==6*(count-1));
        // Release prevents stale display even before native clears its active byte.
        shunying_clone::before_action_release(action.data(),action.data()+0x10+3*0x290);
        shunying_clone::before_render(display.data());expect(releases==count-1);
        // Reinitialization for a foreign actor cancels old attribution even if the
        // same ACT and Display addresses and bitmap are immediately reused.
        create(nullptr,4,112);shunying_clone::before_render(display.data());expect(releases==2*(count-1));
        // Invalid manager / pointers / handles cannot acquire visual ownership.
        shunying_clone::on_action_initializing(nullptr,root,3);
        shunying_clone::on_action_initializing(action.data(),root,4096);
        shunying_clone::on_action_initializing(action.data(),root+1,7);
        shunying_clone::before_render(display.data());expect(allocations==6*(count-1));
        actors[side*14][0][0x239]=0;step(33);expect(releases==4*(count-1));
        shunying_clone::reset(war.data());expect(releases==allocations);
        for(unsigned i=0;i<5;++i)expect(entry(110+i)[0]==2);
    }
    // Owner gate: real-body ground attachments follow both sides, retain their
    // relative depth/render mode, restore on return/cancel/reset, never clone.
    // This exercises native composite ownership; it is not a rendered UI claim.
    for(unsigned side=0;side<2;++side)for(unsigned count=2;count<=3;++count)
    for(unsigned ending=0;ending<3;++ending){
        prepare(side);selected(side,count);
        auto body=actors[side*14][0].data();auto root=action.data()+0x10;
        const short hx=get<short>(body,0x1d4),hy=get<short>(body,0x1d6);
        const auto attach=[&](unsigned h,int dx,int dy,int dz){
            auto p=entry(h);p[0]=2;p[1]=1;p[2]=3;
            set<short>(p,4,short(hx+dx));set<short>(p,6,short(hy+dy));set<short>(p,8,short(hy+dz));
            set<void*>(p,0x8c,bitmaps[0].data());set<void*>(p,0x94,palettes[0].data());set<float>(p,0x90,.5f);
        };
        attach(200,-20,-4,-1);attach(201,-15,-6,-2);attach(202,-10,-8,-3);attach(203,10,10,5);
        // Shared follow handle must translate once; a child cycle is bounded.
        set<short>(root,0x254,2);set<unsigned short>(root,0xac,200);set<unsigned short>(root,0xae,200);
        set<unsigned short>(root,0x256,2);
        auto child=action.data()+0x10+2*0x290;child[0]=2;set<unsigned short>(child,0xe,201);
        set<unsigned short>(child,0x256,0);child[9]=1;set<unsigned short>(child,0x27a,3);
        auto moving=action.data()+0x10+3*0x290;moving[0]=2;set<unsigned short>(moving,0xe,202);
        // Generation flag +10 alone denotes an emission that native movement
        // does not drag with its caster. Leave this visual at the native point.
        root[10]=1;set<unsigned short>(root,0x27a,4);
        auto detached=action.data()+0x10+4*0x290;detached[0]=2;set<unsigned short>(detached,0xe,203);
        step(500);expect(get<short>(entry(200),4)==hx-20);
        body[0x233]=5;step(1);
        const auto target=actors[(1-side)*14][0].data();const float sign=side==0?1.f:-1.f;
        const int dx=int(std::lround(get<short>(target,0x1d4)+sign*78/1.28f))-hx;
        const int dy=int(std::lround(get<short>(target,0x1d6)+sign*76/1.28f))-hy;
        for(unsigned repeat=0;repeat<3;++repeat){
            for(unsigned i=0;i<3;++i){auto p=entry(200+i);
                expect(get<short>(p,4)==hx-20+int(i)*5+dx);
                expect(get<short>(p,6)==hy-4-int(i)*2+dy);
                expect(get<short>(p,8)==hy-1-int(i)+dy);
                expect(p[2]==3);near(get<float>(p,0x90),.5f);
            }
            expect(get<short>(entry(203),4)==hx+10 && get<short>(entry(203),8)==hy+5);
            expect(allocations==2*(count-1));step(33);
        }
        if(ending==0){body[0x239]=0;step(1);}
        else if(ending==1)shunying_clone::reset(war.data());
        else shunying_clone::before_display_reset(display.data());
        for(unsigned i=0;i<3;++i){auto p=entry(200+i);
            expect(get<short>(p,4)==hx-20+int(i)*5 && get<short>(p,6)==hy-4-int(i)*2);
            expect(get<short>(p,8)==hy-1-int(i) && p[2]==3 && p[0]==2);
        }
        shunying_clone::reset(war.data());expect(releases==allocations);
    }
    std::cout<<"clone_visuals mock checks="<<checks<<" passed\n";
}
