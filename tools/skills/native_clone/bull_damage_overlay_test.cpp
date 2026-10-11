// Exercise the actual render_hook, with a sprite raster sink replacing 426B30.
#define main existing_preload_main
#include "clone_preload_test.cpp"
#undef main
#include <vector>
#include <stdexcept>
#include <crtdbg.h>
#include <cstdlib>
template<class T>void put(void* p,unsigned o,T v){std::memcpy(static_cast<Byte*>(p)+o,&v,sizeof(v));}
std::vector<Byte> display(0x100000),actions(0x290*4096+16),source(0x1000);
std::array<unsigned,14> pixels{},glyph_draws{},star_draws{};
std::vector<unsigned> seen;
Byte* sprite(unsigned h){return display.data()+0x1258+h*200;}
Byte* action(unsigned h){return actions.data()+16+h*0x290;}
void __fastcall raster(void* d,void*,unsigned viewport,int px,int py,void* entry){
    assert(d==display.data()&&viewport==0&&py==42);
    const unsigned kind=static_cast<Byte*>(entry)[1];
    assert(px>=0&&px<14);seen.push_back(kind);
    if(kind==1){pixels[px]=90;++star_draws[px];}
    if(kind==2){pixels[px]=(pixels[px]+250)/2;++glyph_draws[px];}
}
void __fastcall traversal(void* d,void*,unsigned viewport){
    assert(render_stage==1);render_stage=2;
    for(Byte* p=bull_damage::read<Byte*>(d,0xf555c);p;p=bull_damage::read<Byte*>(p,0xc4))
        if(p[0]==2&&p[3]==viewport)raster(d,nullptr,viewport,bull_damage::read<short>(p,4),bull_damage::read<short>(p,6),p);
}
void foreground(){assert(render_stage==2);render_stage=3;pixels.fill(15);}
void initialize_action(unsigned h,unsigned image){
    auto* a=action(h);std::memset(a,0,0x290);a[0]=2;
    std::memset(a+0xac,0xff,106*2);std::memset(a+0x256,0xff,17*2);
    std::memset(a+0x27a,0xff,6*2);put<std::uint16_t>(a,0xe,static_cast<std::uint16_t>(image));
}
int main(){
    _set_error_mode(_OUT_TO_STDERR);_set_abort_behavior(0,_WRITE_ABORT_MSG|_CALL_REPORTFAULT);
    static_assert(sizeof(void*)==4);
    render_original=reinterpret_cast<Render>(&traversal);
    damage_draw=reinterpret_cast<DrawSprite>(&raster);
    overlay_foreground=&foreground;
    unsigned cases=0;
    for(unsigned side=0;side<2;++side)for(unsigned targets=1;targets<=14;++targets)for(unsigned hit=0;hit<4;++hit){
        std::fill(display.begin(),display.end(),Byte(0));std::fill(source.begin(),source.end(),Byte(0));
        put<void*>(actions.data(),4,display.data());source[0x239]=Byte(targets);source[0x234]=Byte(side*128);
        unsigned next=0;
        for(unsigned i=0;i<targets;++i){
            auto* text=source.data()+0x310+i*16;put<void*>(text,4,actions.data());put<std::uint16_t>(text,10,std::uint16_t(i*4));
            initialize_action(i*4,0xffff);initialize_action(i*4+1,next);initialize_action(i*4+2,next+1);initialize_action(i*4+3,next+2);
            // The child order deliberately differs from native sprite-list order.
            put<std::uint16_t>(action(i*4),0x256,std::uint16_t(i*4+2));
            put<std::uint16_t>(action(i*4),0x258,std::uint16_t(i*4+1));
            put<std::uint16_t>(action(i*4),0x25a,std::uint16_t(i*4+3));
            // Cycle/duplicate references must not duplicate rendering.
            put<std::uint16_t>(action(i*4+2),0x256,std::uint16_t(i*4));
            put<short>(action(i*4+2),0x254,1);put<std::uint16_t>(action(i*4+2),0xac,std::uint16_t(next+1));
            for(unsigned j=0;j<3;++j){auto* p=sprite(next+j);p[0]=j==2?3:2;p[1]=Byte(j+1);put<short>(p,4,short(i));put<short>(p,6,42);}
            next+=3;
        }
        // Unrelated visible actor and HUD remain in their original pass.
        auto* ordinary=sprite(next++);ordinary[0]=2;ordinary[1]=3;put<short>(ordinary,6,42);
        auto* hud=sprite(next++);hud[0]=2;hud[3]=1;
        for(unsigned h=0;h<next;++h)put<void*>(sprite(h),0xc4,h+1<next?sprite(h+1):nullptr);
        put<void*>(display.data(),0xf555c,sprite(0));
        const auto before=display;overlay_source=source.data();pixels.fill(0);glyph_draws.fill(0);star_draws.fill(0);seen.clear();render_stage=0;
        render_hook(display.data(),nullptr,0);
        assert(render_stage==3&&display==before&&seen.front()==3);
        for(unsigned i=0;i<targets;++i){assert(pixels[i]==170&&glyph_draws[i]==1&&star_draws[i]==1);}
        // Exceptions must restore visibility, too.
        try{bull_damage::Pass interrupted(display.data(),source.data());throw std::runtime_error("abort");}catch(const std::runtime_error&){}
        assert(display==before);++cases;
    }
    std::cout<<"PASS actual render hook: "<<cases<<" cases, both sides, 1..14 targets, four hits; stars then digits above foreground exactly once; unrelated sprites/HUD/hidden entries preserved; abort restores visibility\n";
}
