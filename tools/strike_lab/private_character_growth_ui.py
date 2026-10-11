"""Read current native role stats after own-server settlement on a hidden desktop."""
import argparse
from contextlib import closing
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import psutil
import sqlite3
import struct
import time
from private_inventory_memory import kernel,read,Region
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,game_window,type_ascii,user
from private_owned_supply_20260927 import find_ui
from private_owned_companions_ui import control_point

def saved_role_owner(handle,logical,diagnostics):
    """Exact native22 stores plus the original UI ownership pointer relation."""
    stats=struct.unpack_from('<4H',logical,5);needle=struct.pack('<4I',*stats)
    address=0x10000;scanned=0;matches=set()
    while address<0x80000000 and scanned<800*1024*1024:
        region=Region()
        if not kernel.VirtualQueryEx(handle,address,c.byref(region),c.sizeof(region)):break
        base=region.BaseAddress or address;end=min(base+region.RegionSize,0x80000000)
        if region.State==0x1000 and not region.Protect&0x101:
            offset=base;tail=b''
            while offset<end:
                size=min(1024*1024,end-offset);raw=read(handle,offset,size)
                if raw:
                    scanned+=len(raw);combined=tail+raw;at=combined.find(needle)
                    while at>=0:
                        role=offset-len(tail)+at-0x78;ui=role-0x90-0x1539683c+0xa7f2f6c
                        state=read(handle,role,0x100)
                        if ui>0x10000 and state and len(state)==0x100 and state[0x26]==logical[1] and state[0x90:0x92]==logical[3:5] and state[0x60:0x64]==logical[17:21] and state[0x68:0x6c]==logical[21:25] and read(handle,ui+0x86888,4)==struct.pack('<I',role):
                            matches.add(ui);position=read(handle,role-0x90,0x28)
                            diagnostics.setdefault('owners',[]).append({'ui':hex(ui),'role':hex(role),
                                'position_prefix_hex':position.hex() if position else None})
                        at=combined.find(needle,at+1)
                    tail=combined[-15:]
                offset+=size
        address=end if end>address else address+0x1000
    diagnostics['matching_owners']=len(matches);require(len(matches)==1,'SAVED_ROLE_OWNER_NOT_UNIQUE');return matches.pop()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('db',type=Path)
    ap.add_argument('server_log',type=Path);ap.add_argument('--client-exe',type=Path,required=True)
    ap.add_argument('--profession',type=int,choices=range(1,5),default=1)
    ap.add_argument('--restore',action='store_true')
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--allocate',action='store_true')
    mode.add_argument('--allocated-restore',action='store_true')
    ap.add_argument('--rapid',action='store_true');ap.add_argument('--repeated-pattern',action='store_true');a=ap.parse_args()
    require(not (a.allocate or a.allocated_restore) or a.restore,'ALLOCATION_REQUIRES_SAVED_ENTRY')
    result={'accepted':False,'scope':'Owner-confirmed growth; CUSTOM-0013 seed/XP only in isolated server'}
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
        if not a.restore:
            wait_until(lambda:'DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36' in a.server_log.read_text('utf-8',errors='replace'),30,'BATTLE_NOT_INITIALIZED')
            time.sleep(.5);click(hwnd,515,157)
        def settled():
            with closing(sqlite3.connect(a.db.resolve().as_uri()+'?mode=ro',uri=True)) as db:
                row=db.execute('select r.logical,r.revision,x.total from character_role_snapshots r join character_experience x on x.character_id=r.character_id where r.character_id=4').fetchone()
            return row if row and row[0][1]==2 and row[2]==250 else None
        stored=wait_until(settled,25,'GROWTH_NOT_SETTLED');logical=stored[0]
        result['saved_role']={'logical_hex':logical.hex(),'revision':stored[1],'experience':stored[2]}
        handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READONLY_OPEN_FAILED')
        result['owner_locator']={}
        if a.restore:
            def restored_owner():
                result['owner_locator']={}
                try:return saved_role_owner(handle,logical,result['owner_locator'])
                except RuntimeError as error:
                    if str(error)!='SAVED_ROLE_OWNER_NOT_UNIQUE':raise
                    return None
            ui=wait_until(restored_owner,15,'SAVED_ROLE_OWNER_NOT_READY')
        else:ui=find_ui(handle,kind=2,scene=15,diagnostics=result['owner_locator'])
        # Pinned 4E6B40 uses this pointer directly; the world-position locator's
        # preceding 0x90 bytes are not the role-stat consumer's base.
        pointer=read(handle,ui+0x86888,4);require(pointer and len(pointer)==4,'ROLE_POINTER_MISSING');role=int.from_bytes(pointer,'little')
        position=read(handle,role-0x90,0x1a);require(position and len(position)==0x1a,'ROLE_POSITION_MISSING')
        result['native_position']={'kind':int.from_bytes(position[0x10:0x14],'little'),
            'scene':int.from_bytes(position[0x14:0x18],'little'),'area':int.from_bytes(position[0x18:0x1a],'little'),
            'x':int.from_bytes(position[8:12],'little'),'y':int.from_bytes(position[12:16],'little')}
        require(result['native_position']=={'kind':2,'scene':15,'area':2,'x':18,'y':12},'SAVED_POSITION_NOT_APPLIED')
        expected={'level':logical[1],'points':int.from_bytes(logical[3:5],'little'),
                  'stats':list(struct.unpack_from('<4H',logical,5))}
        # Owner-confirmed award, independently checked against the explicit
        # CUSTOM-0013 [10,10,10,10] baseline; not merely DB/client agreement.
        awards={1:[2,3,0,1],2:[1,0,3,2],3:[2,0,2,2],4:[1,1,1,3]}
        additions=[2,0,1,1] if a.repeated_pattern else [1,1,1,1]
        require(expected['stats']==[10+x+(additions[i] if a.allocated_restore else 0)
            for i,x in enumerate(awards[a.profession])],'WRONG_PROFESSION_AWARD')
        def observed():
            raw=read(handle,role,0x100)
            if not raw or len(raw)!=0x100:return None
            value={'level':raw[0x26],'points':struct.unpack_from('<H',raw,0x90)[0],
                   'stats':list(struct.unpack_from('<4I',raw,0x78))}
            result['last_native_role']=value
            return value if value==expected else None
        result['native_role']=wait_until(observed,15,'NATIVE_GROWTH_SNAPSHOT_NOT_APPLIED')
        require(expected['points']==(0 if a.allocated_restore else 4) and expected['level']==2,'WRONG_GROWTH_BUDGET')
        if a.allocate:
            # Original role-sheet controls 14h..17h, not injected packet calls.
            def panel():
                raw=read(handle,ui+0x232dda,2)
                require(raw is not None and len(raw)==2,'ROLE_PANEL_INDEX_UNAVAILABLE')
                index=int.from_bytes(raw,'little',signed=True)
                require(0<=index<128,'ROLE_PANEL_INDEX_INVALID')
                flags=read(handle,ui+0xe2988+index*0x2a08,2)
                require(flags is not None and len(flags)==2,'ROLE_PANEL_FLAGS_UNAVAILABLE')
                value={'index':index,'flags':int.from_bytes(flags,'little')}
                result['last_role_panel']=value
                return value if value['flags']&0x20 else None
            # Current primary toolbar 4B0D20 stores index +232DB6.
            # 4B1660 table at4B18B8 case5 -> 4B17C7 -> 4E79A0.
            if not panel():
                toolbar=int.from_bytes(read(handle,ui+0x232db6,2),'little',signed=True)
                result['role_open_control']={'toolbar':toolbar,'control':5,
                    'point':control_point(handle,ui,toolbar,5)}
                click(hwnd,*result['role_open_control']['point'])
            opened=wait_until(panel,8,'ROLE_PANEL_NOT_OPEN')
            result['allocation_stages']=[]
            original_logical=logical;original_revision=stored[1]
            if a.rapid:
                result['rapid_clicks']=[]
                for control,selector,index in ((20,2,0),(20,2,0),(22,1,2),(23,4,3)):
                    point=control_point(handle,ui,opened['index'],control)
                    result['rapid_clicks'].append({'control':control,'selector':selector,'point':point})
                    # The native mouse pump samples held buttons per frame;
                    # 5ms transitions were not four actual game clicks. Keep
                    # each button transition across a native frame.
                    click(hwnd,*point,interval=.04)
                    expected['stats'][index]+=1;expected['points']-=1
                def rapid_saved():
                    current=settled()
                    if not current or not original_revision<current[1]<=original_revision+4:return None
                    target=bytearray(original_logical);struct.pack_into('<H',target,3,0)
                    struct.pack_into('<4H',target,5,*expected['stats'])
                    return current if current[0]==bytes(target) else None
                current=wait_until(rapid_saved,8,'RAPID_ALLOCATION_NOT_PERSISTED')
                result['allocated_role']={'revision':current[1],'logical_hex':current[0].hex(),
                    'native':wait_until(observed,8,'RAPID_NATIVE_ALLOCATION_NOT_PROJECTED')}
            for step,(control,selector,index) in enumerate(() if a.rapid else ((20,2,0),(21,3,1),(22,1,2),(23,4,3)),1):
                current_panel=panel();require(current_panel is not None,'ROLE_PANEL_CLOSED')
                point=control_point(handle,ui,current_panel['index'],control)
                button=ui+0xe2988+current_panel['index']*0x2a08+0xa0+control*100
                result['pending_allocation_control']={'control':control,'selector':selector,'point':point,
                    'native_button_hex':read(handle,button,100).hex()}
                click(hwnd,*point)
                observed()
                expected['stats'][index]+=1;expected['points']-=1
                def allocation_saved():
                    current=settled()
                    if not current or current[1]!=original_revision+step:return None
                    target=bytearray(original_logical)
                    struct.pack_into('<H',target,3,expected['points'])
                    struct.pack_into('<4H',target,5,*expected['stats'])
                    require(current[0]==bytes(target),'ALLOCATION_CHANGED_UNRELATED_ROLE_FIELDS')
                    return current
                current=wait_until(allocation_saved,8,'ALLOCATION_NOT_PERSISTED')
                native=wait_until(observed,8,'NATIVE_ALLOCATION_NOT_PROJECTED')
                result['allocation_stages'].append({'control':control,'selector':selector,'point':point,
                    'revision':current[1],'logical_hex':current[0].hex(),'native':native})
            if not a.rapid:result['allocated_role']=result['allocation_stages'][-1]
            # Original button must stop submitting when its budget is empty.
            final_saved=settled()
            click(hwnd,*control_point(handle,ui,opened['index'],20));time.sleep(1)
            require(settled()==final_saved,'EMPTY_BUDGET_MUTATED_SAVE')
            require(observed() is not None,'EMPTY_BUDGET_MUTATED_NATIVE_ROLE')
            result['empty_budget_unchanged']=True
            require(a.server_log.read_text('utf-8',errors='replace').count('OWNED_ATTRIBUTE_ALLOCATION_HANDLED')==4,
                'FOUR_NATIVE_REQUESTS_NOT_HANDLED')
        if not a.restore:
            wait_until(lambda:'DIAGNOSTIC_POST_BATTLE_CONTEXT_ACCEPTED' in a.server_log.read_text('utf-8',errors='replace'),12,'POST_BATTLE_CONTEXT_REJECTED')
        require('Recovered world policy or response rejected' not in a.server_log.read_text('utf-8',errors='replace'),'WORLD_CONNECTION_REJECTED')
        require(process.is_running(),'CLIENT_EXITED');result['desktop_after']=desktop_names()
        require(result['desktop_after']==desktop,'INPUT_DESKTOP_CHANGED');result['accepted']=True
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
