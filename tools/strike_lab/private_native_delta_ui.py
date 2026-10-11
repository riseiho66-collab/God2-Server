"""Read native battle actors after real own-server83/0D, on hidden desktop only."""
import argparse
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

def blocks(handle):
    address=0x10000;scanned=0
    while address<0x100000000 and scanned<2048*1024*1024:
        region=Region()
        if not kernel.VirtualQueryEx(handle,address,c.byref(region),c.sizeof(region)):break
        base=region.BaseAddress or address;end=min(base+region.RegionSize,0x100000000)
        if region.State==0x1000 and not region.Protect&0x101:
            for offset in range(base,end,1024*1024):
                raw=read(handle,offset,min(1024*1024,end-offset))
                if raw:scanned+=len(raw);yield offset,raw
        address=max(end,address+4096)

def battle_actors(handle):
    candidates={0:set()}
    patterns={0:[struct.pack('<4I',52,mp,120,80) for mp in (16,26)]}
    for base,raw in blocks(handle):
        for slot,keys in patterns.items():
            for pattern in keys:
                at=raw.find(pattern)
                while at>=0:
                    actor=base+at-0xde8
                    if actor>0x10000 and read(handle,actor,2) is not None:candidates[slot].add(actor)
                    at=raw.find(pattern,at+1)
    managers={}
    for base,raw in blocks(handle):
        for actor in candidates[0]:
            at=raw.find(struct.pack('<I',actor))
            while at>=0:
                manager=base+at-0x38;table=read(handle,manager+0x38,28*24)
                target=struct.unpack_from('<I',table,14*24)[0] if table else 0
                target_vitals=read(handle,target+0xde8,16) if target>0x10000 else None
                # The native14 pointer qualifies this exact existing target.
                # Its MP is uninitialized because side1 bootstrap sends HP only.
                if target_vitals and struct.unpack_from('<I',target_vitals,8)[0]==150 and struct.unpack_from('<I',target_vitals)[0]<=150:
                    managers[manager]={str(i):{'pointer':hex(struct.unpack_from('<I',table,i*24)[0]),
                        'vitals':list(struct.unpack('<4I',read(handle,struct.unpack_from('<I',table,i*24)[0]+0xde8,16))),
                        'action_state':read(handle,struct.unpack_from('<I',table,i*24)[0]+0x239,1)[0],
                        'queue_header':read(handle,struct.unpack_from('<I',table,i*24)[0]+0x233,8).hex(),
                        'result_count':int.from_bytes(read(handle,struct.unpack_from('<I',table,i*24)[0]+0x2c4,2),'little'),
                        'accumulators':list(struct.unpack('<8i',read(handle,struct.unpack_from('<I',table,i*24)[0]+0xb60,32)))} for i in (0,14)}
                at=raw.find(struct.pack('<I',actor),at+1)
    require(len(managers)==1,f'EXPECTED_ONE_NATIVE_BATTLE_MANAGER found={len(managers)} candidates={[[hex(p) for p in sorted(v)] for v in candidates.values()]}')
    manager,actors=next(iter(managers.items()));return {'manager':hex(manager),'actors':actors}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('db',type=Path);ap.add_argument('server_log',type=Path);ap.add_argument('--client-exe',type=Path,required=True)
    a=ap.parse_args();result={'accepted':False};hwnd=process=handle=None
    try:
        desktop=desktop_names();result['desktop_before']=desktop
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        def find():
            hwnd,pid=game_window()
            if not hwnd:return None
            process=psutil.Process(pid);require(Path(process.exe()).resolve()==a.client_exe.resolve(),'WRONG_CLIENT')
            return hwnd,process
        hwnd,process=wait_until(find,35,'GAME_WINDOW_UNAVAILABLE');result['pid']=process.pid
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370)
        wait_until(lambda:'DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36' in a.server_log.read_text('utf-8',errors='replace'),30,'NATIVE_VITALS_NOT_SENT')
        time.sleep(.5);click(hwnd,515,157)
        wait_until(lambda:'ISOLATED_NATIVE_DELTA_SENT' in a.server_log.read_text('utf-8',errors='replace'),12,'NATIVE_DELTA_NOT_SENT')
        time.sleep(8);handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READONLY_OPEN_FAILED')
        result['native']=battle_actors(handle)
        with sqlite3.connect(a.db.resolve().as_uri()+'?mode=ro',uri=True) as db:
            result['saved_resources']=list(db.execute('select hp,max_hp,mp,max_mp,revision from character_resources where character_id=4').fetchone())
        require(result['native']['actors']['0']['vitals']==[52,16,120,80],'NATIVE_PLAYER_MP_DELTA_NOT_APPLIED')
        require(result['native']['actors']['14']['vitals'][::2]==[120,150],'NATIVE_ENEMY_HP_DELTA_NOT_APPLIED')
        require(result['saved_resources'][:4]==[52,120,16,80],'SERVER_RESOURCE_COMMIT_MISMATCH')
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
                    except psutil.TimeoutExpired:process.terminate()
            except psutil.NoSuchProcess:pass
        result['desktop_final']=desktop_names();a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
