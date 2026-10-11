"""Read qualified native battle menu/input state on the hidden own-server client.

No screenshot, foreground input, memory write or injected native calls.
"""
import struct
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import current_spell_bank_memory_20260927 as spell

lab=spell.lab


def widgets_at(handle,manager,include_closed=False):
    exact=lab.exact
    hit_pool=struct.unpack('<I',exact(handle,manager+4,4))[0]
    order=[];seen=set();node=struct.unpack('<I',exact(handle,manager+0x14,4))[0]
    while node:
        lab.require(node>0x10000 and node not in seen and len(order)<128,'WIDGET_ORDER_BOUND')
        seen.add(node);raw=exact(handle,node,16)
        widget=struct.unpack_from('<h',raw)[0]
        lab.require(0<=widget<128,'WIDGET_ID_BOUND')
        order.append(widget);node=struct.unpack_from('<I',raw,12)[0]
    widgets=[]
    for widget in order:
        base=manager+widget*0x2a08
        header=exact(handle,base+0x818,0x40)
        if not include_closed and not header[0]&0x20:continue
        controls=[]
        for index in range(84):
            raw=exact(handle,base+0x8b8+index*100,100)
            if not raw[0]:continue
            hit=struct.unpack_from('<h',raw,8)[0]
            if not 0<=hit<4096:continue
            hit_raw=exact(handle,hit_pool+hit*24,24)
            active,left,top,right,bottom,event=struct.unpack('<6i',hit_raw)
            if not include_closed and not active:continue
            controls.append({'control':index,'kind':raw[0],'hit':hit,
                'rect':[left,top,right,bottom],'active':active,'hit_event':event,'record_hex':raw.hex()})
        widgets.append({'widget':widget,'header_hex':header.hex(),'controls':controls})
    return {'manager':hex(manager),'widget_order':order,'widgets':widgets}


def capture(handle,ui,output):
    result=spell.capture(handle,ui,output)
    exact=lab.exact
    battle=int(result['battle'],16)
    result['input']={'battle_active':struct.unpack('<I',exact(handle,battle+0x44,4))[0],
        'battle_action_mode':struct.unpack('<I',exact(handle,battle+0x46c,4))[0],
        'command_flags':list(struct.unpack('<3I',exact(handle,battle+0xa9e9c34,12))),
        'selected_index':struct.unpack('<i',exact(handle,battle+0xa9df73c,4))[0],
        'ui_mode':struct.unpack('<I',exact(handle,ui+0xa3d08,4))[0],
        'ui_shortcuts_primary':exact(handle,ui+0xa3d18,60).hex(),
        'ui_shortcuts_alt':exact(handle,ui+0xa4114,60).hex(),
        'shared_ui':widgets_at(handle,ui+0xe2170),
        'battle_panels':widgets_at(handle,battle+0xa9ea59c,include_closed=True),
        'battle_panel_slots_hex':exact(handle,battle+0xab3b1d0,12).hex()}
    return result


if __name__=='__main__':
    spell.active.require_source()
    lab.fixture.SOURCE_DB=spell.active.SOURCE
    lab.configure_isolated_fixture=spell.configure
    lab.prepare_isolated_clone=spell.active.prepare
    lab.candidate_server=spell.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    lab.peer.find_ui=lambda h,a:spell.original_find_ui(h,a,expected_map=(2,15,2))
    lab.capture=capture
    lab.__file__=__file__
    raise SystemExit(lab.main())
