// Exercises the actual scoped preload/result hook code with native callees mocked.
#include "clone_hooks.cpp"
#include <cassert>
#include <iostream>
unsigned seen_id{}, seen_preload{}, custom_calls{}, ordinary_calls{}, result_calls{};
std::array<unsigned,4> seen_actors{};
unsigned render_stage{};
unsigned present_stage{};
void* present_screen{};
void* render_display{};
void* emission_parent{};
unsigned emitted_handle{},released_actions{},create_calls{};
const void* overlay_source{};
void (*overlay_foreground)(){};
namespace bull_native_tick {
void initialize(std::uintptr_t){}
void reset(void*){}
unsigned step(void* w,void* a,Original original){return original(w,a);}
}
namespace bull_effect {
void initialize(std::uintptr_t){}
void preload(void*){}
void on_result(void*,unsigned,unsigned){}
bool begin_actor(void*,unsigned,unsigned){return true;}
void finish_actor(void*,unsigned,unsigned){}
void before_frame(void*){}
bool has_tail(void*){return false;}
void reset(void*){}
void reset_display(void*){}
void begin_battle_draw(void*){}
void end_battle_draw(){}
void draw_ground(void*,unsigned){}
void draw_foreground(void*,unsigned){if(overlay_foreground)overlay_foreground();}
const void* damage_source(void*,unsigned viewport){return viewport==0?overlay_source:nullptr;}
void before_present(void*){}
void before_screen_present(void* s){assert(present_stage==0);present_screen=s;present_stage=1;}
void before_renderer_present(void* r){assert(present_stage==0);present_screen=r;present_stage=1;}
void after_present(){assert(present_stage==2);present_stage=3;}
}
namespace battle_background {
void captured(void*){}
void before_battle_draw(void*){}
void screen_rebuilt(void*){}
}
namespace shunying_clone {
void initialize(std::uintptr_t){}
void before_frame(void*){}
void after_frame(void*){}
void before_render(void* display){assert(render_stage==0);render_display=display;render_stage=1;}
void on_action_initializing(void*,const void* parent,unsigned handle){emission_parent=const_cast<void*>(parent);emitted_handle=handle;}
void before_action_release(void*,const void*){++released_actions;}
void reset(void*){}
void before_display_reset(void*){}
bool has_tail(void*){return false;}
void on_result(void*,unsigned,unsigned,unsigned,unsigned,bool custom){if(custom)++custom_calls;else ++ordinary_calls;}
}
void __fastcall fake_result(void*,void*,Byte* packet,unsigned side,unsigned slot,unsigned target_side,unsigned target_slot){
    ++result_calls;seen_id=packet[10];
    seen_actors={side,slot,target_side,target_slot};
}
void __fastcall fake_render(void* display,void*,unsigned viewport){
    assert(render_stage==1 && display==render_display && viewport==3);render_stage=2;
}
void __fastcall fake_create(void* manager,void*,unsigned handle,unsigned x,unsigned y,unsigned bank,unsigned action,
                            unsigned facing,unsigned depth,unsigned mode,unsigned delay,void* clip){
    assert(handle==17 && x==18 && y==19 && bank==20 && action==21 && facing==22 && depth==23 && mode==24 && delay==25 && clip==reinterpret_cast<void*>(26));
    assert(emitted_handle==17);++create_calls;
    action_step_hook(manager,nullptr,reinterpret_cast<void*>(2));
    assert(current_action==reinterpret_cast<void*>(1));
}
void __fastcall fake_step(void* manager,void*,void* action){
    assert(current_action==action && current_action_manager==manager);
    if(action==reinterpret_cast<void*>(1)){
        action_create_hook(manager,nullptr,17,18,19,20,21,22,23,24,25,reinterpret_cast<void*>(26));
        assert(emission_parent==action);
    }
}
void __fastcall fake_release(void*,void*,void*){assert(released_actions==1);}
unsigned __fastcall fake_preload(void* engine,void*,Byte* packet){
    seen_preload=packet[0xb];
    result_hook(engine,nullptr,packet+1,packet[2]/14,packet[2]%14,1-packet[2]/14,2);
    assert(packet[0xb]==seen_preload); // Inner result must restore the preload value.
    return 0xabcdef01;
}
void __fastcall fake_present(void* screen,void*,int flip,int stretch,int fps){assert(present_stage==1&&screen==present_screen&&flip==0&&stretch==1&&fps==0);present_stage=2;}
void __fastcall fake_renderer_present(void* renderer,void*){assert(present_stage==1&&renderer==present_screen);present_stage=2;}
int main(){
    static_assert(sizeof(void*)==4);
    result_original=reinterpret_cast<Result>(&fake_result);
    preload_original=reinterpret_cast<Preload>(&fake_preload);
    unsigned checks=0;
    present_original=reinterpret_cast<Present>(&fake_present);
    present_hook(reinterpret_cast<void*>(0x1234),nullptr,0,1,0);
    assert(present_stage==3);++checks;
    present_stage=0;renderer_present_original=reinterpret_cast<Reset>(&fake_renderer_present);
    renderer_present_hook(reinterpret_cast<void*>(0x5678),nullptr);
    assert(present_stage==3);++checks;
    render_original=reinterpret_cast<Render>(&fake_render);
    render_hook(reinterpret_cast<void*>(0x1234),nullptr,3);
    assert(render_stage==2);++checks;
    action_step_original=reinterpret_cast<ActionStep>(&fake_step);
    action_create_original=reinterpret_cast<ActionCreate>(&fake_create);
    action_release_original=reinterpret_cast<ActionStep>(&fake_release);
    action_step_hook(reinterpret_cast<void*>(0x1000),nullptr,reinterpret_cast<void*>(1));
    assert(create_calls==1 && !current_action && !current_action_manager);++checks;
    action_release_hook(reinterpret_cast<void*>(0x1000),nullptr,reinterpret_cast<void*>(2));++checks;
    for(unsigned side=0;side<2;++side)for(Byte command:{Byte(3),Byte(0x17)}){
        std::array<Byte,32> packet{};packet[1]=command;packet[2]=Byte(side*14+13);packet[0xb]=126;
        const auto original_packet=packet;
        const auto before=custom_calls;
        assert(preload_hook(reinterpret_cast<void*>(1),nullptr,packet.data())==0xabcdef01);++checks;
        assert(seen_preload==8 && seen_id==8);++checks;
        assert(custom_calls==before+1 && packet[0xb]==126);++checks;
        assert(custom_preload_packet==nullptr);++checks;
        const std::array<unsigned,4> expected_actors{side,13,1-side,2};
        assert(seen_actors==expected_actors && packet==original_packet);++checks;
    }
    // Native blade3 and unrelated skill IDs remain untouched and are not clones.
    for(Byte id:{Byte(8),Byte(25),Byte(125)}){
        std::array<Byte,32> packet{};packet[1]=3;packet[0xb]=id;
        const auto before=ordinary_calls;preload_hook(nullptr,nullptr,packet.data());
        assert(seen_preload==id && seen_id==id && packet[0xb]==id);++checks;
        assert(ordinary_calls==before+1 && custom_calls==4);++checks;
    }
    // Wrong skill kind is not the custom skill even when its numeric ID is 126.
    std::array<Byte,32> other{};other[1]=3;other[0xb]=126;other[0xc]=1;
    preload_hook(nullptr,nullptr,other.data());assert(seen_preload==126 && custom_calls==4);++checks;
    // A direct result consumer still supports 126 without an outer preloader.
    std::array<Byte,32> direct{};direct[0]=3;direct[10]=126;
    result_hook(nullptr,nullptr,direct.data(),0,0,1,0);
    assert(seen_id==8 && direct[10]==126 && custom_calls==5);++checks;
    std::cout<<"preload/result hook checks="<<checks<<" passed\n";
    return 0;
}
