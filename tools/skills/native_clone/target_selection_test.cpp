#include "clone_hooks.cpp"
#include <cassert>
#include <iostream>
#include <vector>
namespace shunying_clone {
void initialize(std::uintptr_t){} void before_frame(void*){} void after_frame(void*){}
void before_render(void*){}
void on_action_initializing(void*,const void*,unsigned){}
void before_action_release(void*,const void*){}
void reset(void*){} void before_display_reset(void*){} bool has_tail(void*){return false;}
void on_result(void*,unsigned,unsigned,unsigned,unsigned,bool){}
}
std::array<Byte,112> definition{};
unsigned cancelled{},highlights{},setup_calls{},input_calls{},submit_calls{};
const Byte* __fastcall fake_definition(void*,void*,unsigned){return definition.data();}
void __fastcall fake_setup(void* p,void*,void*) {
    ++setup_calls;shunying_target::write<unsigned>(p,0x45c,3);
    shunying_target::clear_targets(p);
}
void __fastcall fake_cancel(void* p,void*) {
    ++cancelled;shunying_target::clear_targets(p);
    shunying_target::write<unsigned>(p,0x464,1);
    shunying_target::write<unsigned>(p,0xa9df73c,0xffffffff);
}
void __fastcall fake_highlight(void*,void*,void*,unsigned,unsigned){++highlights;}
void __fastcall fake_input(void*,void*,void*){++input_calls;}
unsigned __fastcall fake_submit(void* p,void*,unsigned,unsigned,unsigned,Byte*) {
    ++submit_calls;shunying_target::clear_targets(p);
    shunying_target::write<unsigned>(p,0xa9e9c38,0);
    shunying_target::write<unsigned>(p,0xa9e9c3c,0);return 1;
}
int main() {
    std::vector<Byte> memory(0xaa00000);void* ui=memory.data();
    using namespace shunying_target;
    selected_definition=reinterpret_cast<Definition>(fake_definition);
    selection_original=reinterpret_cast<Selection>(fake_setup);
    input_original=reinterpret_cast<Selection>(fake_input);
    cancel_selection=reinterpret_cast<Reset>(fake_cancel);
    refresh_highlights=reinterpret_cast<Highlight>(fake_highlight);
    submit_selection=reinterpret_cast<Submit>(fake_submit);
    definition[0]=126;definition[0x45]=16;
    write<unsigned>(ui,0x44,1);write<unsigned>(ui,0xa9e9c38,1);write<Byte>(ui,0x51,2);
    unsigned checks=0;
    for(unsigned mask=0;mask<0x4000;++mask) {
        write<unsigned>(ui,0x464,3);write<unsigned>(ui,0xa9df73c,0);
        write<unsigned>(ui,0x438,0x3fff);write<unsigned>(ui,0x144938+0x2f8,mask);
        selection_hook(ui,nullptr,nullptr);
        assert(read<unsigned>(ui,0x45c)==(maximum(mask)?maximum(mask):1));
        assert(read<unsigned>(ui,0x468)==0);assert(read<unsigned>(ui,0x460)==0);
        assert(read<unsigned>(ui,0x434)==0);++checks;
    }
    assert(cancelled==1 && setup_calls==0x4000);
    // Native blade3 and wrong-kind 126 do not enter custom clamping.
    for(unsigned kind=0;kind<2;++kind) {
        definition[0]=kind?126:8;definition[1]=Byte(kind);
        write<unsigned>(ui,0x464,3);write<unsigned>(ui,0xa9df73c,0);
        write<unsigned>(ui,0x438,1);write<unsigned>(ui,0x144938+0x2f8,1);
        selection_hook(ui,nullptr,nullptr);assert(read<unsigned>(ui,0x45c)==3);++checks;
    }
    definition[0]=126;definition[1]=0;
    write<unsigned>(ui,0x438,0x15);write<unsigned>(ui,0x144938+0x2f8,0x11);
    assert(enemies(ui)==0x11); // Dead slot2 excluded despite old selectable bit.
    write<unsigned>(ui,0x438,0x10);assert(enemies(ui)==0x10); // Nonselectable slot0 excluded.
    write<unsigned>(ui,0x438,0x3fff);write<unsigned>(ui,0x144938+0x2f8,0x3fff);
    write<Byte>(ui,0x44c,14);write<Byte>(ui,0x44d,27);write<Byte>(ui,0x44e,16);
    for(unsigned count=1;count<=3;++count)assert(valid_targets(ui,count,enemies(ui)));
    write<unsigned>(ui,0x460,1);assert(partial_confirm(ui,0,true));
    assert(!partial_confirm(ui,1,true));assert(!partial_confirm(ui,0,false));
    write<unsigned>(ui,0x460,2);assert(partial_confirm(ui,1,true));
    write<Byte>(ui,0x44d,14);assert(!valid_targets(ui,2,enemies(ui)));
    assert(!partial_confirm(ui,1,true)); // Duplicate is never a partial confirmation.
    write<Byte>(ui,0x44d,2);assert(!valid_targets(ui,2,enemies(ui))); // Friendly caster slot2.
    write<Byte>(ui,0x44d,28);assert(!valid_targets(ui,2,enemies(ui))); // Out of range.
    assert(!valid_targets(ui,0,enemies(ui)));assert(!valid_targets(ui,4,enemies(ui)));
    refresh(ui);assert(read<unsigned>(ui,0x460)==0); // Stale invalid selection cleared.
    assert(caster(ui)==2);write<unsigned>(ui,0xa9e9c38,0);write<unsigned>(ui,0xa9e9c3c,1);
    write<Byte>(ui,0x52,9);assert(caster(ui)==9);
    // Exercise the actual full-count submit guard, not just partial confirmation.
    for(unsigned count=1;count<=3;++count) {
        write<unsigned>(ui,0x464,3);write<unsigned>(ui,0xa9df73c,0);
        write<unsigned>(ui,0xa9e9c38,1);write<unsigned>(ui,0xa9e9c3c,0);
        for(unsigned i=0;i<count;++i)write<Byte>(ui,0x44c+i,Byte(14+i));
        assert(submit_hook(ui,nullptr,3,2,count,static_cast<Byte*>(ui)+0x44c)==1);
        assert(read<unsigned>(ui,0x460)==0 && read<unsigned>(ui,0xa9e9c38)==0);
    }
    assert(submit_calls==3);
    for(unsigned invalid=0;invalid<4;++invalid) {
        write<unsigned>(ui,0x464,3);write<unsigned>(ui,0xa9df73c,0);write<unsigned>(ui,0xa9e9c38,1);
        write<unsigned>(ui,0x438,0x3fff);write<unsigned>(ui,0x144938+0x2f8,invalid==1?3:0x3fff);
        write<Byte>(ui,0x44c,14);write<Byte>(ui,0x44d,15);write<Byte>(ui,0x44e,invalid==0?14:16);
        if(invalid==2)write<unsigned>(ui,0x438,3); // Hidden/nonselectable last target.
        assert(submit_hook(ui,nullptr,3,2,invalid==3?0:3,static_cast<Byte*>(ui)+0x44c)==0);
        assert(submit_calls==3 && read<unsigned>(ui,0x460)==0);
    }
    definition[0]=8;
    assert(submit_hook(ui,nullptr,3,2,0,nullptr)==1 && submit_calls==4); // Native8 unchanged.
    definition[0]=126;write<unsigned>(ui,0x464,3);write<unsigned>(ui,0xa9df73c,0);
    write<unsigned>(ui,0xa9e9c38,1);write<unsigned>(ui,0x438,3);write<unsigned>(ui,0x144938+0x2f8,3);
    selection_hook(ui,nullptr,nullptr);assert(read<unsigned>(ui,0x45c)==2); // Next F1 recalculates.
    write<unsigned>(ui,0x460,1);write<Byte>(ui,0x44c,14);write<unsigned>(ui,0x144938+0x2f8,2);
    refresh(ui);assert(read<unsigned>(ui,0x460)==0 && read<unsigned>(ui,0x45c)==1);
    write<unsigned>(ui,0x144938+0x2f8,0);const auto before_input=input_calls;
    input_hook(ui,nullptr,nullptr);assert(input_calls==before_input); // No click leakage after cancel.
    std::cout<<"target selection all 16384 living masks plus native8, zero/dead/nonselectable/duplicate/partial/central caster PASS; checks="<<checks<<"\n";
}
