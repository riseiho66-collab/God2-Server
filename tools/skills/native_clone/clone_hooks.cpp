// CUSTOM-0058: version-pinned, isolated client rendering bridge.
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include "clone_visuals.h"
#include "target_selection.h"
#include "battle_background.h"
#include "bull_effect.h"
#include "bull_native_tick.h"
#include "bull_damage_overlay.h"

#if !defined(_M_IX86)
#error Verified God2 bridge requires x86.
#endif

namespace {
using Byte=unsigned char;
using Preload=unsigned(__thiscall*)(void*,Byte*);
using Result=void(__thiscall*)(void*,Byte*,unsigned,unsigned,unsigned,unsigned);
using Frame=unsigned(__thiscall*)(void*,void*,void*);
using Reset=void(__thiscall*)(void*);
using Render=void(__thiscall*)(void*,unsigned);
using DrawSprite=void(__thiscall*)(void*,unsigned,int,int,void*);
DrawSprite damage_draw{};
using ActionStep=void(__thiscall*)(void*,void*);
using ActionCreate=void(__thiscall*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*);
using Selection=void(__thiscall*)(void*,void*);
using Definition=const Byte*(__thiscall*)(void*,unsigned);
using Submit=unsigned(__thiscall*)(void*,unsigned,unsigned,unsigned,Byte*);
using Highlight=void(__thiscall*)(void*,void*,unsigned,unsigned);
using ScreenRebuild=int(__thiscall*)(void*,int,int,int,unsigned);
Render background_capture_original{},battle_draw_original{};
using Present=void(__thiscall*)(void*,int,int,int);
Present present_original{};
Reset renderer_present_original{};
bull_native_tick::Original skill_tick_original{};
ScreenRebuild screen_rebuild_original{};
Selection selection_original{},input_original{};
Definition selected_definition{};
Submit submit_selection{};
Reset cancel_selection{};
Highlight refresh_highlights{};
Preload preload_original{};
Result result_original{};
Byte* custom_preload_packet{};
Frame frame_original{};
Reset reset_original{};
Reset display_reset_original{};
Render render_original{};
ActionStep action_step_original{},action_release_original{};
ActionCreate action_create_original{};
void* current_action_manager{};
void* current_action{};
void* completed_war{};

void note(const char* value) {
    HANDLE file=CreateFileA("shunying-clone.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,
        nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file!=INVALID_HANDLE_VALUE) {
        DWORD written{};WriteFile(file,value,static_cast<DWORD>(std::strlen(value)),&written,nullptr);
        CloseHandle(file);
    }
}

const Byte* current_definition(void* ui) {
    const auto index=shunying_target::read<unsigned>(ui,0xa9df73c);
    return index==0xffffffff?nullptr:selected_definition(ui,index);
}
bool refresh_custom_selection(void* ui) {
    if(!shunying_target::refresh(ui)) {cancel_selection(ui);return false;}
    refresh_highlights(ui,static_cast<Byte*>(ui)+0x43c,
        shunying_target::read<unsigned>(ui,0x460),3);
    return true;
}
void __fastcall selection_hook(void* ui,void*,void* context) {
    selection_original(ui,context);
    if(shunying_target::active(ui,current_definition(ui)))refresh_custom_selection(ui);
}
void __fastcall input_hook(void* ui,void*,void* context) {
    const bool custom=shunying_target::active(ui,current_definition(ui));
    const auto previous=shunying_target::read<unsigned>(ui,0x460);
    if(custom && !refresh_custom_selection(ui)) return;
    // Shift+click the final target confirms an optional 1/2-target selection.
    // This modifier is sampled only in the original battle input loop, and
    // only a NEW native mouse selection can confirm; keyboard/chat alone cannot.
    DWORD foreground_process{};
    GetWindowThreadProcessId(GetForegroundWindow(),&foreground_process);
    const bool shift=custom && foreground_process==GetCurrentProcessId() &&
        (GetKeyState(VK_SHIFT)&0x8000)!=0;
    input_original(ui,context);
    if(custom && shunying_target::active(ui,current_definition(ui)) &&
       shunying_target::partial_confirm(ui,previous,shift)) {
        submit_selection(ui,3,shunying_target::caster(ui),
            shunying_target::read<unsigned>(ui,0x460),static_cast<Byte*>(ui)+0x44c);
    }
}
unsigned __fastcall submit_hook(void* ui,void*,unsigned action,unsigned caster,unsigned count,Byte* targets) {
    if(action==3 && shunying_target::custom(current_definition(ui))) {
        if(!shunying_target::active(ui,current_definition(ui)) ||
           !shunying_target::valid_list(targets,count,shunying_target::enemies(ui))) {
            shunying_target::clear_targets(ui);
            cancel_selection(ui);
            return 0; // Native cancellation; no empty/duplicate/stale command.
        }
    }
    return submit_selection(ui,action,caster,count,targets);
}

unsigned __fastcall preload_hook(void* engine,void*,Byte* packet) {
    if(packet && (packet[1]==3 || packet[1]==0x17) && packet[0xb]==150 && packet[0xc]==0)bull_effect::preload(engine);
    const bool custom=packet && (packet[1]==3 || packet[1]==0x17) && packet[0xb]==126 && packet[0xc]==0;
    if(!custom)return preload_original(engine,packet);
    // 00516AE0 loads ROM/RTB and populates the actor's +34/+DF8 cache before
    // calling 0052C520(packet+1). Both stages must use the same native blade3
    // entry; remapping only the latter leaves rtgRomIdx/rtgDataIdx at -1.
    Byte* previous=custom_preload_packet;
    custom_preload_packet=packet+1;
    packet[0xb]=8;
    const auto result=preload_original(engine,packet);
    packet[0xb]=126;
    custom_preload_packet=previous;
    note("CUSTOM126 preloaded native8 ROM/RTB before result playback\r\n");
    return result;
}

void __fastcall result_hook(void* war,void*,Byte* packet,unsigned side,unsigned slot,unsigned target_side,unsigned target_slot) {
    const bool custom=packet && (packet[0]==3 || packet[0]==0x17) &&
        (packet[10]==126 || packet==custom_preload_packet) && packet[11]==0;
    const bool bull=packet && (packet[0]==3 || packet[0]==0x17) && packet[10]==150 && packet[11]==0;
    if(bull){bull_effect::on_result(war,side&0xff,slot&0xff);completed_war=nullptr;}
    shunying_clone::on_result(war,side&0xff,slot&0xff,target_side&0xff,target_slot&0xff,custom);
    if(custom) {
        completed_war=nullptr;
        // Keep the original learned blade3 actor action and its hit-event timing.
        // The server still owns one damage result per selected target.
        const Byte original_id=packet[10];
        packet[10]=8;
        result_original(war,packet,side,slot,target_side,target_slot);
        packet[10]=original_id;
        note("CUSTOM126 native8 action + current-caster visual target\r\n");
    } else result_original(war,packet,side,slot,target_side,target_slot);
}
unsigned __fastcall frame_hook(void* war,void*,void* out,void* context) {
    bull_effect::before_frame(war);
    shunying_clone::before_frame(war);
    const auto result=frame_original(war,out,context);
    shunying_clone::after_frame(war);
    if(result) completed_war=war;
    // Preserve the original completion until the display-only return particles
    // have finished. Native simulation/render update still runs every call.
    if(shunying_clone::has_tail(war) || bull_effect::has_tail(war)) return 0;
    if(completed_war==war) { completed_war=nullptr;bull_native_tick::reset(war);bull_effect::reset(war);return 1; }
    return result;
}
void __fastcall reset_hook(void* war,void*) {
    if(completed_war==war) completed_war=nullptr;
    bull_native_tick::reset(war);
    bull_effect::reset(war);
    shunying_clone::reset(war);
    reset_original(war);
}
void __fastcall display_reset_hook(void* display,void*) {
    completed_war=nullptr;
    bull_effect::reset_display(display);
    shunying_clone::before_display_reset(display);
    display_reset_original(display);
}
void __fastcall render_hook(void* display,void*,unsigned viewport) {
    // The UI advances another native ACT manager after the battle frame.
    // Mirror the final native visual tree immediately before display traversal.
    shunying_clone::before_render(display);
    bull_effect::draw_ground(display,viewport);
    if(const void* source=bull_effect::damage_source(display,viewport)){
        bull_damage::Pass damage(display,source);
        render_original(display,viewport);
        bull_effect::draw_foreground(display,viewport);
        damage.draw(damage_draw);
        return;
    }
    render_original(display,viewport);
    bull_effect::draw_foreground(display,viewport);
}
void __fastcall background_capture_hook(void* renderer,void*,unsigned viewport) {
    background_capture_original(renderer,viewport);
    battle_background::captured(renderer);
}
void __fastcall battle_draw_hook(void* renderer,void*,unsigned viewport) {
    battle_background::before_battle_draw(renderer);
    bull_effect::begin_battle_draw(renderer);
    battle_draw_original(renderer,viewport);
    bull_effect::end_battle_draw();
}
unsigned __fastcall skill_tick_hook(void* war,void*,void* actor) {
    return bull_native_tick::step(war,actor,skill_tick_original);
}
void __fastcall present_hook(void* screen,void*,int flip,int stretch,int fps) {
    bull_effect::before_screen_present(screen);
    present_original(screen,flip,stretch,fps);
    bull_effect::after_present();
}
void __fastcall renderer_present_hook(void* renderer,void*) {
    bull_effect::before_renderer_present(renderer);
    renderer_present_original(renderer);
    bull_effect::after_present();
}
int __fastcall screen_rebuild_hook(void* screen,void*,int width,int height,int bits,unsigned flags) {
    const auto result=screen_rebuild_original(screen,width,height,bits,flags);
    battle_background::screen_rebuilt(screen);
    return result;
}
void __fastcall action_step_hook(void* manager,void*,void* action) {
    void* previous_manager=current_action_manager;
    void* previous_action=current_action;
    current_action_manager=manager;
    current_action=action;
    action_step_original(manager,action);
    current_action_manager=previous_manager;
    current_action=previous_action;
}
void __fastcall action_create_hook(void* manager,void*,unsigned handle,unsigned x,unsigned y,
                                  unsigned bank,unsigned action,unsigned facing,unsigned depth,
                                  unsigned mode,unsigned delay,void* clip) {
    // ACT_STEP opcode10 can emit independent slash/flash animations that are
    // intentionally absent from the native parent's owned child list.
    shunying_clone::on_action_initializing(manager,
        current_action_manager==manager?current_action:nullptr,handle&0xffff);
    action_create_original(manager,handle,x,y,bank,action,facing,depth,mode,delay,clip);
}
void __fastcall action_release_hook(void* manager,void*,void* action) {
    shunying_clone::before_action_release(manager,action);
    action_release_original(manager,action);
}

struct Hook {
    Byte* entry{};void* replacement{};unsigned length{};std::array<Byte,8> expected{};
    Byte* trampoline{};
};
void relative(Byte* instruction,const void* target) {
    instruction[0]=0xe9;
    const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(target)-
        (reinterpret_cast<std::uintptr_t>(instruction)+5));
    std::memcpy(instruction+1,&delta,4);
}
bool install() {
    const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);
    const auto pe=reinterpret_cast<IMAGE_NT_HEADERS32*>(base+dos->e_lfanew);
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE || pe->Signature!=IMAGE_NT_SIGNATURE ||
       pe->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 || pe->OptionalHeader.SizeOfImage<0x190000) return false;
    std::array<Hook,18> hooks{{
        {reinterpret_cast<Byte*>(base+0x12c520),reinterpret_cast<void*>(result_hook),7,{0x8b,0x44,0x24,0x0c,0x83,0xec,0x08}},
        {reinterpret_cast<Byte*>(base+0x129020),reinterpret_cast<void*>(frame_hook),7,{0x83,0xec,0x0c,0x8b,0x44,0x24,0x14}},
        {reinterpret_cast<Byte*>(base+0x11fc40),reinterpret_cast<void*>(reset_hook),6,{0x83,0xec,0x10,0x53,0x8b,0xd9}},
        {reinterpret_cast<Byte*>(base+0x27400),reinterpret_cast<void*>(display_reset_hook),8,{0x51,0x53,0x56,0x57,0x89,0x4c,0x24,0x0c}},
        {reinterpret_cast<Byte*>(base+0x116ae0),reinterpret_cast<void*>(preload_hook),6,{0x81,0xec,0x34,0x01,0x00,0x00}},
        {reinterpret_cast<Byte*>(base+0x1154e0),reinterpret_cast<void*>(selection_hook),6,{0x51,0x53,0x55,0x56,0x8b,0xf1}},
        {reinterpret_cast<Byte*>(base+0x113080),reinterpret_cast<void*>(input_hook),7,{0x83,0xec,0x20,0x55,0x56,0x8b,0xf1}},
        {reinterpret_cast<Byte*>(base+0x118e50),reinterpret_cast<void*>(submit_hook),8,{0x83,0xec,0x10,0x53,0x8a,0x5c,0x24,0x18}},
        {reinterpret_cast<Byte*>(base+0x26ab0),reinterpret_cast<void*>(render_hook),5,{0x53,0x8b,0x5c,0x24,0x08}},
        {reinterpret_cast<Byte*>(base+0x1c360),reinterpret_cast<void*>(action_step_hook),5,{0x83,0xec,0x18,0x53,0x55}},
        {reinterpret_cast<Byte*>(base+0x1b9c0),reinterpret_cast<void*>(action_create_hook),8,{0x51,0x53,0x55,0x56,0x8b,0x74,0x24,0x14}},
        {reinterpret_cast<Byte*>(base+0x1b330),reinterpret_cast<void*>(action_release_hook),5,{0x53,0x8b,0xd9,0x55,0x56}},
        {reinterpret_cast<Byte*>(base+0x327a0),reinterpret_cast<void*>(background_capture_hook),5,{0x56,0x8b,0xf1,0x6a,0x00}},
        {reinterpret_cast<Byte*>(base+0x32810),reinterpret_cast<void*>(battle_draw_hook),5,{0x53,0x56,0x8b,0xf1,0x57}},
        {reinterpret_cast<Byte*>(base+0x13dd40),reinterpret_cast<void*>(screen_rebuild_hook),6,{0x81,0xec,0x04,0x01,0x00,0x00}},
        {reinterpret_cast<Byte*>(base+0x13ca50),reinterpret_cast<void*>(present_hook),5,{0x83,0xec,0x50,0x53,0x56}},
        {reinterpret_cast<Byte*>(base+0x124820),reinterpret_cast<void*>(skill_tick_hook),6,{0x83,0xec,0x14,0x53,0x55,0x56}},
        {reinterpret_cast<Byte*>(base+0x32a20),reinterpret_cast<void*>(renderer_present_hook),8,{0x56,0x8b,0xf1,0xe8,0xd8,0x0e,0xfd,0xff}}
    }};
    for(const auto& hook:hooks)
        if(std::memcmp(hook.entry,hook.expected.data(),hook.length)!=0) return false;
    for(auto& hook:hooks) {
        hook.trampoline=static_cast<Byte*>(VirtualAlloc(nullptr,32,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
        if(!hook.trampoline) {
            for(auto& prior:hooks) if(prior.trampoline) VirtualFree(prior.trampoline,0,MEM_RELEASE);
            return false;
        }
        std::memcpy(hook.trampoline,hook.entry,hook.length);
        // This pinned prologue contains a rel32 call at+3 to403900.
        // Rebase its displacement when copying it into the trampoline.
        if(hook.entry==reinterpret_cast<Byte*>(base+0x32a20)) {
            const auto delta=static_cast<std::uint32_t>(base+0x3900-
                reinterpret_cast<std::uintptr_t>(hook.trampoline+8));
            std::memcpy(hook.trampoline+4,&delta,4);
        }
        relative(hook.trampoline+hook.length,hook.entry+hook.length);
        DWORD old{};
        if(!VirtualProtect(hook.trampoline,32,PAGE_EXECUTE_READ,&old)) {
            for(auto& prior:hooks) if(prior.trampoline) VirtualFree(prior.trampoline,0,MEM_RELEASE);
            return false;
        }
        FlushInstructionCache(GetCurrentProcess(),hook.trampoline,32);
    }
    result_original=reinterpret_cast<Result>(hooks[0].trampoline);
    frame_original=reinterpret_cast<Frame>(hooks[1].trampoline);
    reset_original=reinterpret_cast<Reset>(hooks[2].trampoline);
    display_reset_original=reinterpret_cast<Reset>(hooks[3].trampoline);
    preload_original=reinterpret_cast<Preload>(hooks[4].trampoline);
    selection_original=reinterpret_cast<Selection>(hooks[5].trampoline);
    input_original=reinterpret_cast<Selection>(hooks[6].trampoline);
    selected_definition=reinterpret_cast<Definition>(base+0x1156a0);
    damage_draw=reinterpret_cast<DrawSprite>(base+0x26b30);
    submit_selection=reinterpret_cast<Submit>(hooks[7].trampoline);
    render_original=reinterpret_cast<Render>(hooks[8].trampoline);
    action_step_original=reinterpret_cast<ActionStep>(hooks[9].trampoline);
    action_create_original=reinterpret_cast<ActionCreate>(hooks[10].trampoline);
    action_release_original=reinterpret_cast<ActionStep>(hooks[11].trampoline);
    background_capture_original=reinterpret_cast<Render>(hooks[12].trampoline);
    battle_draw_original=reinterpret_cast<Render>(hooks[13].trampoline);
    screen_rebuild_original=reinterpret_cast<ScreenRebuild>(hooks[14].trampoline);
    present_original=reinterpret_cast<Present>(hooks[15].trampoline);
    bull_effect::initialize(base);
    skill_tick_original=reinterpret_cast<bull_native_tick::Original>(hooks[16].trampoline);
    renderer_present_original=reinterpret_cast<Reset>(hooks[17].trampoline);
    bull_native_tick::initialize(base);
    cancel_selection=reinterpret_cast<Reset>(base+0x112620);
    refresh_highlights=reinterpret_cast<Highlight>(base+0x111e10);
    shunying_clone::initialize(base);
    // Keep the original protection storage bound to the installed hook table.
    std::array<DWORD,std::tuple_size_v<decltype(hooks)>> protections{};
    for(unsigned i=0;i<hooks.size();++i) {
        if(!VirtualProtect(hooks[i].entry,hooks[i].length,PAGE_EXECUTE_READWRITE,&protections[i])) {
            for(unsigned j=0;j<i;++j) {
                DWORD ignored{};VirtualProtect(hooks[j].entry,hooks[j].length,protections[j],&ignored);
            }
            for(auto& hook:hooks) VirtualFree(hook.trampoline,0,MEM_RELEASE);
            return false; // No entry code has been changed.
        }
    }
    for(auto& hook:hooks) {
        relative(hook.entry,hook.replacement);
        for(unsigned i=5;i<hook.length;++i) hook.entry[i]=0x90;
        FlushInstructionCache(GetCurrentProcess(),hook.entry,hook.length);
    }
    for(unsigned i=0;i<hooks.size();++i) {
        DWORD ignored{};
        // Once installed, remain loaded even if restoring a page protection fails.
        VirtualProtect(hooks[i].entry,hooks[i].length,protections[i],&ignored);
    }
    return true;
}
}

BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(instance);
        if(!install()) { note("HOOK INSTALL REJECTED: version/signature/protection mismatch\r\n");return FALSE; }
        note("HOOKS INSTALLED: CUSTOM0058 id126 current-caster display-only clones\r\n");
    }
    // Process teardown owns the renderer; never call back into it from detach.
    return TRUE;
}
