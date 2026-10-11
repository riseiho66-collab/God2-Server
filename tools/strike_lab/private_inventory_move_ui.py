"""Private-desktop native bag drag 0->5->0; read-only DB/client verification.

Run only as the private_desktop_runner sidecar beside an explicitly named
disposable client copy. This script never launches a game, switches desktop,
takes screenshots, injects code, writes process memory, or writes the database.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import psutil
from private_potion_ui import click, drag, game_window, type_ascii, user
from private_inventory_memory import kernel, read


def require(value,message):
    if not value:
        raise RuntimeError(message)


def desktop_names():
    kernel.GetCurrentThreadId.restype=w.DWORD
    user.GetThreadDesktop.argtypes=[w.DWORD]
    user.GetThreadDesktop.restype=w.HANDLE
    user.OpenInputDesktop.argtypes=[w.DWORD,w.BOOL,w.DWORD]
    user.OpenInputDesktop.restype=w.HANDLE
    user.GetUserObjectInformationW.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)]
    user.CloseDesktop.argtypes=[w.HANDLE]
    def name(handle):
        buffer=c.create_unicode_buffer(256)
        needed=w.DWORD()
        require(bool(handle) and user.GetUserObjectInformationW(handle,2,buffer,c.sizeof(buffer),c.byref(needed)),
                'DESKTOP_NAME_UNAVAILABLE')
        return buffer.value
    current=name(user.GetThreadDesktop(kernel.GetCurrentThreadId()))
    input_handle=user.OpenInputDesktop(0,False,1)
    try:
        active=name(input_handle)
    finally:
        if input_handle:user.CloseDesktop(input_handle)
    return {'current':current,'input':active}


def state(db,character):
    with sqlite3.connect(f'file:{db.as_posix()}?mode=ro',uri=True) as conn:
        rows=conn.execute('SELECT slot,item_id,count,revision FROM diagnostic_inventory_slots '
                          'WHERE character_id=? ORDER BY slot',(character,)).fetchall()
        position=conn.execute('SELECT area,scene,x,y,revision FROM recovered_positions '
                              'WHERE character_id=?',(character,)).fetchone()
    return {'slots':rows,'position':position}


def pair(snapshot):
    slots={row[0]:row[1:] for row in snapshot['slots']}
    require(0 in slots and 5 in slots,'BOTH_SLOTS_MUST_BE_EXPLICITLY_SAVED')
    return slots[0],slots[5]


def inventory(handle,ui):
    raw=read(handle,ui+0x8560c,50*24)
    require(raw is not None and len(raw)==50*24,'NATIVE_INVENTORY_READ_FAILED')
    return {'0':raw[:24].hex(),'5':raw[5*24:6*24].hex(),'all_slots_hex':raw.hex()}


def wait_until(predicate,seconds,message):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        result=predicate()
        if result:return result
        time.sleep(.15)
    raise RuntimeError(message)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    ap.add_argument('db',type=Path)
    ap.add_argument('server_log',type=Path)
    ap.add_argument('--client-exe',type=Path,required=True)
    ap.add_argument('--character-id',type=int,default=4)
    ap.add_argument('--server-marker',required=True)
    args=ap.parse_args()
    result={'accepted':False,'stages':[]}
    hwnd=None;process=None;handle=None
    try:
        desktops=desktop_names();result['desktops_before']=desktops
        require(desktops['current'].startswith('God2Lab-') and desktops['current']!=desktops['input'],
                'REFUSING_INPUT_DESKTOP_AUTOMATION')
        require(args.client_exe.name.lower()!='god2.exe','DISPOSABLE_CLIENT_COPY_REQUIRED')
        before=state(args.db,args.character_id);result['before']=before
        source,destination=pair(before)
        require(source[:2]==(5569,1) and destination[:2]==(0,0),'ISOLATED_MOVE_FIXTURE_UNEXPECTED')
        require(before['position'] is not None and before['position'][:2]==(2,4),'TOWN_FIXTURE_REQUIRED')
        initial_log=args.server_log.read_text(encoding='utf-8',errors='replace')
        initial_markers=initial_log.count(args.server_marker)
        def find_game():
            found,pid=game_window()
            if not found:return None
            candidate=psutil.Process(pid)
            require(Path(candidate.exe()).resolve()==args.client_exe.resolve(),'WRONG_PRIVATE_CLIENT_PROCESS')
            return found,candidate
        hwnd,process=wait_until(find_game,35,'GAME_WINDOW_NOT_FOUND')
        created=process.create_time();result.update(pid=process.pid,client_exe=str(args.client_exe),created=created)
        time.sleep(2)
        click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow')
        click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4)
        click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4)
        click(hwnd,452,370)
        wait_until(lambda:'WORLD_INITIALIZER_TAIL_ACCEPTED' in args.server_log.read_text(
            encoding='utf-8',errors='replace'),20,'WORLD_INITIALIZER_NOT_ACCEPTED')
        time.sleep(3);click(hwnd,708,584);time.sleep(2)
        result['stages'].append('inventory_opened')
        # Locate slot zero once. The old helper assumes its match is slot zero;
        # never use it to rederive UI after the item has moved to slot five.
        helper=Path(__file__).with_name('private_inventory_memory.py')
        scan=subprocess.run([sys.executable,'-B',str(helper),str(process.pid),'5569'],
                            capture_output=True,check=True,timeout=20)
        result['initial_inventory_scan']=json.loads(scan.stdout)
        matches=[candidate for candidate in result['initial_inventory_scan']['matches']
                 if isinstance(candidate.get('inventory_source_index'),int)
                 and 0<=candidate['inventory_source_index']<64
                 and candidate.get('inventory_source_mode')
                 and int(candidate['inventory_source_mode'],16)&0x20
                 and candidate.get('selected_inventory_slot')=='ffff']
        result['qualified_ui_candidates']=[candidate['ui'] for candidate in matches]
        require(len(matches)==1,'EXPECTED_ONE_INITIAL_SLOT_ZERO')
        ui=int(matches[0]['ui'],16);result['ui_base']=hex(ui)
        handle=kernel.OpenProcess(0x1010,False,process.pid)
        require(bool(handle),'READONLY_PROCESS_OPEN_FAILED')
        occupied=(bytes([1,0,0,0])+bytes.fromhex('c115')+bytes(18)).hex()
        empty=bytes(24).hex()
        memory=inventory(handle,ui);result['native_before']=memory
        require(memory['0']==occupied and memory['5']==empty,'INITIAL_NATIVE_MINIMAL_SLOTS_MISMATCH')
        for index,(start,end,expected0,expected5) in enumerate((
                ((580,302),(580,347),(0,0),(5569,1)),
                ((580,347),(580,302),(5569,1),(0,0))),1):
            prior=state(args.db,args.character_id)
            points=drag(hwnd,start,end)
            def observed():
                current=state(args.db,args.character_id)
                zero,five=pair(current)
                native=inventory(handle,ui)
                if zero[:2]!=expected0 or five[:2]!=expected5:return None
                if native['0']!=(occupied if expected0[0] else empty):return None
                if native['5']!=(occupied if expected5[0] else empty):return None
                log=args.server_log.read_text(encoding='utf-8',errors='replace')
                if log.count(args.server_marker)<initial_markers+index:return None
                return current,native
            current,native=wait_until(observed,12,f'MOVE_{index}_NOT_ACCEPTED')
            old0,old5=pair(prior);new0,new5=pair(current)
            require(new0[2]>old0[2] and new5[2]>old5[2],'SLOT_REVISIONS_DID_NOT_ADVANCE')
            require(current['position']==before['position'],'MOVE_CHANGED_SAVED_POSITION')
            require([r for r in current['slots'] if r[0] not in (0,5)]==
                    [r for r in before['slots'] if r[0] not in (0,5)],'UNRELATED_SLOT_CHANGED')
            result['stages'].append({'move':index,'points':points,'db':current,'native':native})
        result['after']=state(args.db,args.character_id)
        result['server_marker_lines']=[line for line in args.server_log.read_text(
            encoding='utf-8',errors='replace').splitlines() if args.server_marker in line]
        result['client_alive']=process.is_running() and process.create_time()==created and game_window()[0]==hwnd
        require(result['client_alive'],'CLIENT_NOT_ALIVE_AFTER_ROUNDTRIP')
        result['desktops_after']=desktop_names()
        require(result['desktops_after']==desktops,'DESKTOP_IDENTITY_CHANGED')
        result['accepted']=True
    except Exception as error:
        result['error']=f'{type(error).__name__}: {error}'
    finally:
        result['desktops_final']=desktop_names()
        if handle:
            kernel.CloseHandle.argtypes=[w.HANDLE]
            kernel.CloseHandle(handle)
        if hwnd and process:
            try:
                if process.is_running() and Path(process.exe()).resolve()==args.client_exe.resolve():
                    user.PostMessageW(hwnd,0x10,0,0)
                    try:process.wait(timeout=4)
                    except psutil.TimeoutExpired:process.terminate()
            except psutil.NoSuchProcess:pass
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if result['accepted'] else 1


if __name__=='__main__':raise SystemExit(main())
