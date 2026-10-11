"""Window-local skill inputs on the owned hidden-desktop client.

VM_READ observers only; no injected functions or memory writes. Synthetic
ownership, cost and damage remain CUSTOM-0012, not recovered formulas.
"""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import struct
import sqlite3
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import current_battle_input_memory_20260927 as inputs
from tools.strike_lab import private_potion_ui as window
spell=inputs.spell
lab=spell.lab


def capture(handle,ui,output):
    result=inputs.capture(handle,ui,output)
    battle=int(result['battle'],16);selector=int(result['selector'],16)
    exact=lab.exact
    def state(label):
        data={'action_mode':struct.unpack('<I',exact(handle,battle+0x46c,4))[0],
              'flags':list(struct.unpack('<3I',exact(handle,battle+0xa9e9c34,12))),
              'selected_index':struct.unpack('<i',exact(handle,battle+0xa9df73c,4))[0],
              'active':struct.unpack('<I',exact(handle,battle+0x44,4))[0],
              'panels':inputs.widgets_at(handle,battle+0xa9ea59c,True)}
        lab.save(output/(label+'.json'),data)
        return data
    lab.kernel.GetProcessId.argtypes=[w.HANDLE]
    lab.kernel.GetProcessId.restype=w.DWORD
    hwnd,pid=window.game_window()
    lab.require(hwnd and pid==lab.kernel.GetProcessId(handle),'OWNED_WINDOW_REQUIRED')
    deadline=time.monotonic()+4
    while list(struct.unpack('<3I',exact(handle,battle+0xa9e9c34,12)))!=[0,1,0]:
        lab.require(time.monotonic()<deadline,'PLAYER_COMMAND_GRANT_NOT_RECEIVED')
        time.sleep(.05)
    initial=state('cast-before')
    lab.require(initial['flags']==[0,1,0],'PLAYER_COMMAND_NOT_GRANTED')
    # Existing private_skill_ui route uses role command control12. Resolve
    # its current enabled hit rectangle rather than replaying old coordinates.
    role_index=struct.unpack('<H',exact(handle,battle+0xab3b1d0,2))[0]
    deadline=time.monotonic()+3
    while not exact(handle,battle+0xa9ea59c+role_index*0x2a08+0x818,1)[0]&0x20:
        lab.require(time.monotonic()<deadline,'ROLE_PANEL_NOT_ENABLED')
        time.sleep(.05)
    initial=state('cast-before')
    role_panel=next(p for p in initial['panels']['widgets'] if p['widget']==role_index)
    lab.require(int(role_panel['header_hex'][:2],16)&0x20,'ROLE_PANEL_CLOSED')
    button=next(p for p in role_panel['controls'] if p['control']==12)
    left,top,right,bottom=button['rect']
    lab.require(button['active'] and 0<=left<right<=800 and 0<=top<bottom<=600,'ROLE_SKILL_HIT_INVALID')
    window.click(hwnd,(left+right)//2,(top+bottom)//2)
    time.sleep(.4)
    opened=state('cast-skill-menu')
    result['cast_input']=opened
    # This first observation qualifies the pane before subsequent selection.
    result['skill_menu_opened']=opened['action_mode']==3
    lab.require(result['skill_menu_opened'],'SKILL_MENU_NOT_OPENED')
    manager=struct.unpack('<I',exact(handle,selector+0x2e24,4))[0]
    index_ptr=struct.unpack('<I',exact(handle,selector+0x2e30,4))[0]
    index=struct.unpack('<H',exact(handle,index_ptr,2))[0]
    lab.require(manager==battle+0xa9ea59c,'SKILL_PANEL_OWNER')
    result['primary_skill_widget']=index
    lab.save(output/'cast-pane-qualified.json',result)
    panel=next(p for p in opened['panels']['widgets'] if p['widget']==index)
    lab.require(int(panel['header_hex'][:2],16)&0x20,'PRIMARY_SKILL_PANEL_CLOSED')
    icon=next(p for p in panel['controls'] if p['control']==0)
    left,top,right,bottom=icon['rect']
    lab.require(icon['active'] and 0<=left<right<=800 and 0<=top<bottom<=600,'SKILL_ICON_HIT_INVALID')
    window.click(hwnd,(left+right)//2,(top+bottom)//2)
    time.sleep(.35)
    selected=state('cast-skill-selected')
    lab.require(selected['selected_index']==0,'SKILL_NOT_SELECTED')
    # Original projection5134EB uses these coordinates for actor14. Require
    # the existing participant pointer and source-derived projected bounds.
    actor=struct.unpack('<I',exact(handle,battle+0x144938+0x38+14*24,4))[0]
    role=int(result['role'],16)
    before_mp=struct.unpack('<I',exact(handle,role+0x64,4))[0]
    before_hp=struct.unpack('<I',exact(handle,actor+0xde8,4))[0]
    x,y=struct.unpack('<2i',exact(handle,battle+0xa940604+14*8,8))
    lab.save(output/'cast-target-qualified.json',{'actor':hex(actor),'slot':14,'projected_xy':[x,y]})
    lab.require(actor>0x10000 and 0<=x<800 and 0<=y<600,'TARGET_PROJECTION_INVALID')
    lab.require((before_mp,before_hp)==(50,150),'EXPECTED_SYNTHETIC_CAST_RESOURCES')
    window.click(hwnd,x,y)
    time.sleep(.4)
    result['after_target']=state('cast-target-selected')
    deadline=time.monotonic()+20
    while 'DIAGNOSTIC_PLAYER_SKILL actor=0 kind=1 id=1' not in (output/'server.log').read_text('utf-8',errors='replace'):
        lab.require(time.monotonic()<deadline,'NATIVE_KIND1_COMMAND_NOT_SENT')
        time.sleep(.1)
    result['physical_cast_accepted']=True
    lab.save(output/'cast-command-accepted.json',result)
    deadline=time.monotonic()+18
    while 'DIAGNOSTIC_POST_BATTLE_CONTEXT_ACCEPTED' not in (output/'server.log').read_text('utf-8',errors='replace'):
        lab.require(time.monotonic()<deadline,'POST_BATTLE_RECEIPT_NOT_ACCEPTED')
        time.sleep(.1)
    after_mp=struct.unpack('<I',exact(handle,role+0x64,4))[0]
    active=struct.unpack('<I',exact(handle,battle+0x44,4))[0]
    with sqlite3.connect((output/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
        resources=db.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources WHERE character_id=4').fetchone()
        settlements=db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0]
    result['terminal_acceptance']={'native_mp_before':before_mp,'native_mp_after':after_mp,
        'native_enemy_hp_before':before_hp,'battle_active_after':active,
        'saved_resources':resources,'settlements':settlements,
        'formula_origin':'CUSTOM-0012 test fee8/lethal power1000%, not original balance'}
    lab.require(after_mp==42 and active==0 and resources[:4]==(100,120,42,80) and settlements==1,'CAST_TERMINAL_STATE_MISMATCH')
    lab.save(output/'cast-terminal-accepted.json',result)
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
