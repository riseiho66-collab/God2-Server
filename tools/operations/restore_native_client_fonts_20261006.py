"""Owner-authorized font-only rollback; preserves every unrelated client byte."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import struct
import pefile
import psutil

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT.parent/'God2/God2.exe'
NATIVE=ROOT.parent/'God2/God2.unpacked.exe'
OUT=ROOT/'artifacts/releases/native-font-restore-20261006'
BEFORE='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
NATIVE_SHA='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
SITES=[(0x532918,'e8e2281e0090','ff150c015700'),(0x538dc6,'e8c3c31d0090','ff1514015700')]

def sha(b):return hashlib.sha256(b).hexdigest()
def require(condition,message):
    if not condition:raise RuntimeError(message)

def main():
    require(not OUT.exists(),'Existing release retained; do not overwrite')
    require(not any(p.info['exe'] and Path(p.info['exe'])==CLIENT for p in psutil.process_iter(['exe'])),'Client running; close game before font replacement')
    native=NATIVE.read_bytes();require(sha(native)==NATIVE_SHA,'Native reference changed')
    original=CLIENT.read_bytes();require(sha(original)==BEFORE,'Current client changed')
    pe=pefile.PE(data=original);ref=pefile.PE(data=native)
    patched=bytearray(original);changes=[];allowed=set()
    for va,old,new in SITES:
        off=pe.get_offset_from_rva(va-pe.OPTIONAL_HEADER.ImageBase)
        ref_off=ref.get_offset_from_rva(va-ref.OPTIONAL_HEADER.ImageBase)
        require(original[off:off+6]==bytes.fromhex(old),'Font callsite changed')
        require(native[ref_off:ref_off+6]==bytes.fromhex(new),'Native reference callsite differs')
        target=va+5+struct.unpack_from('<i',original,off+1)[0]
        require(any(s.Name.rstrip(b'\0')==b'.fontcfg' and s.VirtualAddress+pe.OPTIONAL_HEADER.ImageBase<=target<s.VirtualAddress+pe.OPTIONAL_HEADER.ImageBase+s.Misc_VirtualSize for s in pe.sections),'Old call is not font wrapper')
        patched[off:off+6]=bytes.fromhex(new);allowed.update(range(off,off+6))
        changes.append({'va':hex(va),'file_offset':off,'before':old,'after':new})
    diff=[i for i,(a,b) in enumerate(zip(original,patched)) if a!=b]
    require(len(original)==len(patched) and set(diff)<=allowed,'Unexpected changed bytes')
    OUT.mkdir(parents=True)
    (OUT/'God2.before.exe').write_bytes(original)
    (OUT/'God2.native-fonts.exe').write_bytes(patched)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];k.CreateFileW.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.CreateFileW(str(CLIENT),0xC0000000,0,None,3,0x80,None)
    require(handle!=ctypes.c_void_p(-1).value,f'Cannot exclusively open client: {ctypes.get_last_error()}')
    import msvcrt
    try:fd=msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY)
    except BaseException:k.CloseHandle(handle);raise
    with os.fdopen(fd,'r+b',buffering=0) as f:
        require(f.read()==original,'Client changed before exclusive write')
        try:
            for c in changes:
                f.seek(c['file_offset']);require(f.write(bytes.fromhex(c['after']))==6,'Short write')
            os.fsync(f.fileno());f.seek(0);require(f.read()==patched,'Installed bytes differ')
        except BaseException:
            f.seek(0);f.write(original);os.fsync(f.fileno());raise
    receipt={'font_calls_restored':True,'client':str(CLIENT),'before_sha256':BEFORE,
             'after_sha256':sha(bytes(patched)),'native_reference_sha256':NATIVE_SHA,
             'changes':changes,'changed_byte_count':len(diff),'other_client_bytes_unchanged':True,
             'fontcfg_payload_retained_unreachable_from_restored_calls':True,
             'build_run':False,'game_run':False,'runtime_tests_run':False,'visual_acceptance':False,
             'server_database_modified':False,'text_conversion_modified':False,
             'activation':'next normal launch uses restored native font calls'}
    (OUT/'restoration.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
