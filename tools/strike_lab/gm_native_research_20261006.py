"""GM static research and bounded read-only memory observation; no packet sends.

The memory mode creates its own client on a private desktop and closes only
that process. It neither switches desktops nor logs in or changes game memory.
"""
from pathlib import Path
import argparse
import collections
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.omega_assets import decode_csvz
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

CLIENT = ROOT.parent / 'God2'
OUT = ROOT / 'reverse/findings/gm-20261006'
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def source_messages():
    sources = []
    for filename, codec in [('message.csvZ', 'cp950'), ('message-gb.csvZ', 'cp936')]:
        path = CLIENT / 'Data2/Patch/Comm' / filename
        packed = path.read_bytes()
        plain = decode_csvz(packed)
        lines = plain.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith(b'SystemMessage,'))
        count = int(lines[index].split(b',')[1])
        rows = []
        for line_index, raw in enumerate(lines[index + 1:index + 1 + count], index + 2):
            fields = raw.split(b',')
            rows.append(dict(id=int(fields[0]), category=int(fields[1]), source_line=line_index,
                             text_variants=[f.decode(codec, errors='replace') for f in fields[2:]],
                             variant_bytes_hex=[f.hex() for f in fields[2:]], record_sha256=sha(raw)))
        keywords = ('gm', '管理員', '管理员', '禁言', '踢出', '停止使用', '停權', '封号', '權限', '权限')
        matches = [r for r in rows if any(k in ' '.join(r['text_variants']).lower() for k in keywords)]
        sources.append(dict(path=str(path), encoding=codec, compressed_sha256=sha(packed),
                            decoded_sha256=sha(plain), declared_records=count,
                            category_counts=dict(collections.Counter(r['category'] for r in rows)),
                            gm_and_account_candidates=matches, records=rows))
    save('system-message-catalog.json', sources)
    return sources

def static():
    p = pefile.PE(str(CLIENT / 'God2.exe'))
    code = p.get_data(0x1000, 0x16f000)
    strings = [(0x590168, '$gmsoft01 %s'), (0x58cde4, 'GM Tools FS2'),
               (0x592e80, 'gm_newarena'), (0x592e8c, 'gm_draw_system'),
               (0x592e9c, 'gm_deliver'), (0x592efc, 'gm_sysmsg'), (0x592f08, 'gm_mart')]
    refs = []
    for va, name in strings:
        positions = []
        at = 0
        while (at := code.find(struct.pack('<I', va), at)) >= 0:
            positions.append(hex(0x401000 + at))
            at += 4
        refs.append(dict(string=name, va=hex(va), actual_bytes_hex=p.get_data(va - 0x400000, len(name)+1).hex(),
                         immediate_reference_candidates=positions))
    ranges = [(0x4968e0,0x496990,'gmsoft-chat-producer'), (0x496990,0x496cc0,'chat-channel-producers'),
              (0x484ae0,0x484ecf,'system-message-consumer'), (0x483a80,0x483c80,'gm-notice-ui'),
              (0x46925c,0x4692b0,'world-notice-cases'), (0x4bff30,0x4c1f00,'mail-special-senders'),
              (0x46b9d0,0x46babf,'gm-tools-window-ipc'), (0x476570,0x476c60,'notice-text-transform'),
              (0x50f580,0x50f850,'text-container-binding'), (0x52f500,0x52f550,'language-conversion'),
              (0x5193ac,0x519450,'login-notice-cases')]
    evidence = []
    OUT.mkdir(parents=True, exist_ok=True)
    for start,end,name in ranges:
        raw = p.get_data(start - 0x400000, end-start)
        instructions = list(MD.disasm(raw,start))
        text = '\n'.join(f'{i.address:08X}  {i.bytes.hex():24} {i.mnemonic} {i.op_str}' for i in instructions)
        (OUT / (name+'.asm.txt')).write_text(text+'\n',encoding='utf-8')
        evidence.append(dict(name=name,start_va=hex(start),end_va_exclusive=hex(end),sha256=sha(raw),
                             direct_calls=[dict(va=hex(i.address),target=i.op_str) for i in instructions if i.mnemonic=='call']))
    calls = []
    for n in range(len(code)-4):
        if code[n] == 0xe8:
            target = 0x401000+n+5+struct.unpack_from('<i',code,n+1)[0]
            if target in (0x4968e0,0x46b9d0,0x4bff20):
                calls.append(dict(call_va=hex(0x401000+n),target_va=hex(target)))
    save('static-evidence.json',dict(client_path=str(CLIENT/'God2.exe'),
         client_sha256=sha((CLIENT/'God2.exe').read_bytes()),references=refs,ranges=evidence,
         selected_direct_call_candidates=calls,method='Current PE bytes and disassembly only; no injected calls, tests or packet sends.'))
    sources=source_messages()
    print(json.dumps(dict(output=str(OUT),gm_message_rows=sources[0]['gm_and_account_candidates'],references=refs),ensure_ascii=False))

class Startup(c.Structure):
    _fields_=[('cb',w.DWORD),('lpReserved',w.LPWSTR),('lpDesktop',w.LPWSTR),('lpTitle',w.LPWSTR),
              ('dwX',w.DWORD),('dwY',w.DWORD),('dwXSize',w.DWORD),('dwYSize',w.DWORD),
              ('dwXCountChars',w.DWORD),('dwYCountChars',w.DWORD),('dwFillAttribute',w.DWORD),
              ('dwFlags',w.DWORD),('wShowWindow',w.WORD),('cbReserved2',w.WORD),
              ('lpReserved2',c.POINTER(c.c_byte)),('hStdInput',w.HANDLE),('hStdOutput',w.HANDLE),('hStdError',w.HANDLE)]

class ProcessInfo(c.Structure):
    _fields_=[('hProcess',w.HANDLE),('hThread',w.HANDLE),('dwProcessId',w.DWORD),('dwThreadId',w.DWORD)]

class Region(c.Structure):
    _fields_=[('BaseAddress',c.c_void_p),('AllocationBase',c.c_void_p),('AllocationProtect',w.DWORD),
              ('PartitionId',w.WORD),('RegionSize',c.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]

def memory():
    k=c.WinDLL('kernel32',use_last_error=True)
    u=c.WinDLL('user32',use_last_error=True)
    u.CreateDesktopW.argtypes=[w.LPCWSTR,w.LPCWSTR,c.c_void_p,w.DWORD,w.DWORD,c.c_void_p]
    u.CreateDesktopW.restype=w.HANDLE
    u.CloseDesktop.argtypes=[w.HANDLE]
    k.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(Startup),c.POINTER(ProcessInfo)]
    k.CreateProcessW.restype=w.BOOL
    k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t]
    k.VirtualQueryEx.restype=c.c_size_t
    k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
    k.TerminateProcess.argtypes=[w.HANDLE,w.UINT]
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
    k.CloseHandle.argtypes=[w.HANDLE]
    exe=CLIENT/'God2.exe'
    identity=sha(exe.read_bytes())
    result=dict(method='ReadProcessMemory on own isolated pre-login client; no memory writes, UI input, desktop switch, packet injection or login.',
                executable=str(exe),client_sha256=identity,snapshots=[])
    desktop=None
    pi=ProcessInfo()
    def read(a,n):
        if n<=0 or n>2**20 or a<0x10000 or a+n>=0x80000000:return None
        buf=c.create_string_buffer(n);got=c.c_size_t()
        if not k.ReadProcessMemory(pi.hProcess,a,buf,n,c.byref(got)):return None
        return buf.raw[:got.value] if got.value==n else None
    def cstring(a,n=380):
        for size in (n,128,64,32,16):
            raw=read(a,size)
            if raw and b'\0' in raw:return raw.split(b'\0',1)[0]
        return None
    try:
        name='God2GMResearch-'+str(k.GetCurrentProcessId())
        desktop=u.CreateDesktopW(name,None,None,0,0x100000|0x01ff,None)
        if not desktop:raise c.WinError(c.get_last_error())
        si=Startup();si.cb=c.sizeof(si);si.lpDesktop='WinSta0\\'+name
        si.dwFlags=1;si.wShowWindow=0
        cmd=c.create_unicode_buffer(f'"{exe}" 127.0.0.1 127.0.0.1 6001 1')
        if not k.CreateProcessW(str(exe),cmd,None,None,False,0x08000000,None,str(CLIENT),c.byref(si),c.byref(pi)):
            raise c.WinError(c.get_last_error())
        result.update(pid=pi.dwProcessId,private_desktop=name)
        print('Owned hidden client PID',pi.dwProcessId,flush=True)
        p=pefile.PE(str(exe))
        for delay in (3,6,9):
            time.sleep(delay)
            exitcode=w.DWORD();k.GetExitCodeProcess(pi.hProcess,c.byref(exitcode))
            snap=dict(seconds=sum((3,6,9)[:len(result['snapshots'])+1]),exit_code=exitcode.value)
            result['snapshots'].append(snap)
            if exitcode.value!=259:break
            samples=[]
            for va,size in ((0x4968e0,0xa9),(0x590168,12),(0x46925c,0x50),(0x484ae0,0x31d),(0x4c00a6,0xf5)):
                actual=read(va,size);expected=p.get_data(va-0x400000,size)
                samples.append(dict(va=hex(va),bytes=size,readable=actual is not None,
                                    sha256=sha(actual) if actual else None,matches_current_pe=actual==expected))
            snap['code_samples']=samples
            # Existing independently derived current-client static catalog owner.
            owner=0x5e053c
            raw=read(owner+0xb2c60,8)
            snap['catalog_header_candidate']=dict(owner=hex(owner),header_hex=raw.hex() if raw else None)
            if raw:
                ptr,count=struct.unpack_from('<Ih',raw)
                if 1<=count<=32767 and 0x10000<ptr<0x80000000:
                    catalog=read(ptr,count*16)
                    if catalog:
                        picked=[]
                        for key in (1,44,45,188,380,807,862,1011,1012,1081,1082,1230,1231,1307):
                            if key>count:continue
                            row=catalog[(key-1)*16:key*16]
                            variants=[]
                            for pointer in struct.unpack_from('<3I',row,4):
                                text=cstring(pointer)
                                variants.append(dict(pointer=hex(pointer),text_hex=text.hex() if text is not None else None,
                                                     text=text.decode('cp950',errors='replace') if text else ''))
                            picked.append(dict(id=key,entry_va=hex(ptr+(key-1)*16),category=row[0],record_hex=row.hex(),variants=variants))
                        snap['catalog_candidates']=dict(pointer=hex(ptr),count=count,entries=picked)
            # Scan only readable committed allocations for the source-qualified
            # GM text-container vtable. Retain only candidates with 6/41 layout.
            hits=[];address=0x10000;scanned=0;regions=0
            while address<0x80000000 and scanned<400*1024**2:
                r=Region()
                if not k.VirtualQueryEx(pi.hProcess,address,c.byref(r),c.sizeof(r)):break
                start=int(r.BaseAddress or address);end=min(start+r.RegionSize,0x80000000)
                if end<=address:break
                if r.State==0x1000 and not r.Protect&0x101 and r.Protect&255 in (2,4,8,0x20,0x40,0x80):
                    regions+=1
                    for a in range(start,end,1024**2):
                        raw=read(a,min(1024**2,end-a))
                        if not raw:continue
                        scanned+=len(raw);pos=0
                        while (pos:=raw.find(struct.pack('<I',0x571330),pos))>=0:
                            candidate=a+pos;header=read(candidate,0x160)
                            if header and struct.unpack_from('<II',header,0x148)==(6,41):
                                flag=read(candidate+0xa640,1)
                                hits.append(dict(text_container_va=hex(candidate),ui_owner_candidate=hex(candidate-0x232f6c),
                                                 vtable='0x571330',active_rows=6,row_capacity=41,flag_hex=flag.hex() if flag else None,
                                                 header_sha256=sha(header)))
                            pos+=4
                        if scanned>=400*1024**2:break
                address=end
            snap['gm_text_containers']=hits;snap['scan_bytes']=scanned;snap['readable_regions']=regions
            print('Snapshot',snap['seconds'],'seconds:',scanned,'bytes read;',len(hits),'GM text containers',flush=True)
    except Exception as error:
        result['error']=repr(error)
        print('Observation limitation:',repr(error),flush=True)
    finally:
        if pi.hProcess:
            status=w.DWORD();k.GetExitCodeProcess(pi.hProcess,c.byref(status))
            if status.value==259:k.TerminateProcess(pi.hProcess,0);k.WaitForSingleObject(pi.hProcess,10000)
            k.GetExitCodeProcess(pi.hProcess,c.byref(status))
            result['owned_client_closed']=status.value!=259
            k.CloseHandle(pi.hProcess)
        if pi.hThread:k.CloseHandle(pi.hThread)
        if desktop:u.CloseDesktop(desktop)
        result['client_file_unchanged']=sha(exe.read_bytes())==identity
        save('memory-observation.json',result)
        print('Memory evidence saved; owned client closed:',result.get('owned_client_closed'),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory',action='store_true')
    args=parser.parse_args()
    if args.memory:memory()
    else:static()
