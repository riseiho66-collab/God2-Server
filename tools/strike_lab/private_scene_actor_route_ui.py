"""Real hidden-desktop door movement, scene71/72/78 restoration and return.

Read-only client memory and window-local messages; no screenshots, injection,
memory writes, official connections or input-desktop switching.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import psutil
import sqlite3
import struct
import time
from private_inventory_memory import kernel,read
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,game_window,type_ascii,user
from private_owned_supply_20260927 import find_ui
from private_owned_companions_ui import native_world_records


def exact(handle,address,size):
    value=read(handle,address,size);require(value is not None and len(value)==size,'READONLY_STATE_UNAVAILABLE');return value


def world_state(handle,ui):
    role=int.from_bytes(exact(handle,ui+0x86888,4),'little')-0x90;world=role-0x1539683c
    require(world>0x10000,'WORLD_OWNER_INVALID')
    return {'world':world,'area':int.from_bytes(exact(handle,world+0x15396854,2),'little'),
        'scene':int.from_bytes(exact(handle,world+0x15396850,4),'little'),
        'kind':exact(handle,world+0x1539684c,1)[0],
        'x':int.from_bytes(exact(handle,world+0x224,4),'little'),
        'y':int.from_bytes(exact(handle,world+0x228,4),'little'),
        'camera':list(struct.unpack('<2i',exact(handle,world+0x21c,8)))}


def ground_point(handle,state,x,y):
    # Current native449330 ->449B30: same grid-to-pixel arithmetic used by
    # the renderer. Derive a click only; never execute/write game code.
    bridge=int.from_bytes(exact(handle,state['world']+0xa7e05dc,4),'little')
    manager=int.from_bytes(exact(handle,bridge+0xbc,4),'little')
    kind=int.from_bytes(exact(handle,manager+0x30,4),'little')
    if kind==0:
        origin=struct.unpack('<2i',exact(handle,manager+0x103c,8));lx,ly=x-origin[0],y-origin[1]
        px=(lx+ly)*40;py=(ly-lx)*20+400
    elif kind==2:
        indoor=int.from_bytes(exact(handle,manager+0x1030,4),'little')
        width,height=struct.unpack('<II',exact(handle,indoor+0x90,8))
        # These are the reconstructed pass-grid extents, not base-map width.
        # Current Kunlun god01 HMD produces a valid 75x75 grid.
        require(1<=width<=1025 and 1<=height<=1025,'INDOOR_WIDTH_INVALID')
        require(0<=x<width and 0<=y<height,'INDOOR_TARGET_OUT_OF_BOUNDS')
        px=(x+y)*40;py=(((width+1)//2)*2-2-x+y)*20
    else:raise AssertionError('UNQUALIFIED_MAP_GEOMETRY')
    point=(px+40-state['camera'][0],py+20-state['camera'][1])
    require(160<=point[0]<630 and 120<=point[1]<440,'GROUND_CLICK_OUTSIDE_QUALIFIED_PLAY_AREA')
    return point


def actor_snapshot(handle,ui,scene):
    state=world_state(handle,ui)
    if (state['area'],state['scene'])!=(2,scene):return None
    value=native_world_records(handle,ui)
    if set(value)!={'npc','monster'}:return None
    positions={'npc':(87,71),'monster':(87,72)} if scene==4 else {'npc':(17,19),'monster':(18,19)}
    for name,position in positions.items():
        # Scene identity changes before its receive queue/pools are restored.
        # Wait within the caller's deadline for the exact destination records.
        row=value[name]
        if (row['x'],row['y'])!=position:return None
        require(row['facing']==(5 if name=='npc' else 6),'NATIVE_ACTOR_DIRECTION_MISMATCH')
        require(row['renderer_active'],'NATIVE_ACTOR_RENDER_COMMAND_INACTIVE')
    if value['monster']['level_cache']!=27:return None
    return {'state':state,'actors':value}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('db',type=Path)
    ap.add_argument('server_log',type=Path);ap.add_argument('--client-exe',type=Path,required=True);a=ap.parse_args()
    result={'accepted':False,'scope':'Real current Taiwan client; synthetic isolated placement/level operands'}
    handle=process=hwnd=None
    try:
        desktop=desktop_names();result['desktop_before']=desktop
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        def window():
            hwnd,pid=game_window()
            if not hwnd:return None
            process=psutil.Process(pid);require(Path(process.exe()).resolve()==a.client_exe.resolve(),'WRONG_CLIENT');return hwnd,process
        hwnd,process=wait_until(window,35,'GAME_WINDOW_MISSING');result['pid']=process.pid
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370)
        wait_until(lambda:'NATIVE_WORLD_DISPLAY_RESTORED' in a.server_log.read_text('utf-8',errors='replace'),20,'WORLD_ACTORS_NOT_SENT')
        handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READONLY_CLIENT_OPEN_FAILED')
        ui=find_ui(handle);result['ui']=hex(ui)
        initial=wait_until(lambda:actor_snapshot(handle,ui,4),10,'INITIAL_ACTORS_NOT_ACCEPTED')
        result['initial']=initial;require((initial['state']['x'],initial['state']['y'])==(86,71),'INITIAL_PLAYER_POSITION_MISMATCH')
        point=ground_point(handle,initial['state'],86,70);result['entry_click']=point
        clicked=time.monotonic();click(hwnd,*point,interval=.03)
        indoor=wait_until(lambda:actor_snapshot(handle,ui,15),12,'INDOOR_ACTORS_NOT_ACCEPTED')
        result['indoor']={**indoor,'elapsed_seconds':time.monotonic()-clicked}
        # Return at once; neither an injected command nor a five-second idle
        # tick is needed to make the destination actor/level records arrive.
        point=ground_point(handle,indoor['state'],16,20);result['return_click']=point
        clicked=time.monotonic();click(hwnd,*point,interval=.03)
        outdoor=wait_until(lambda:actor_snapshot(handle,ui,4),12,'RETURN_ACTORS_NOT_ACCEPTED')
        result['returned']={**outdoor,'elapsed_seconds':time.monotonic()-clicked}
        for scene in (15,4):
            text=a.server_log.read_text('utf-8',errors='replace')
            # Session IDs include the one listener probe. Inspect the full
            # ordered marker rather than assigning any client identity here.
            require(f'area=2 scene={scene} batches=1' in text,'ARRIVAL_ROUTE_NOT_PROJECTED')
        # Click clear ground, outside the supplied NPC/monster sprite hitboxes.
        time.sleep(.6)  # Native scene fade/input gate outlives actor-pool restoration.
        point=ground_point(handle,world_state(handle,ui),83,73);result['continued_move_click']=point;click(hwnd,*point,interval=.03)
        def saved():
            with sqlite3.connect(a.db.resolve().as_uri()+'?mode=ro',uri=True) as db:
                row=db.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone()
            return list(row) if row and row[:4]==(2,4,83,73) else None
        result['saved_position']=wait_until(saved,12,'RETURN_MOVEMENT_NOT_SAVED')
        result['after_movement']=actor_snapshot(handle,ui,4);require(result['after_movement'],'ACTORS_LOST_AFTER_MOVEMENT')
        require(process.is_running(),'CLIENT_EXITED');result['desktop_after']=desktop_names()
        require(result['desktop_after']==desktop,'INPUT_DESKTOP_CHANGED')
        text=a.server_log.read_text('utf-8',errors='replace')
        require('policy or response rejected' not in text and 'WORLD_FRAME_REJECTED' not in text,'SERVER_REJECTED_NATIVE_CLIENT')
        result['accepted']=True
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        if handle:kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle(handle)
        if process:
            try:
                if process.is_running():
                    user.PostMessageW(hwnd,0x10,0,0)
                    try:process.wait(timeout=4)
                    except psutil.TimeoutExpired:process.terminate();process.wait(timeout=3)
            except psutil.NoSuchProcess:pass
        result['desktop_final']=desktop_names();a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0 if result['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
