"""Read the native visible chat list in an explicitly named isolated client."""
import ctypes as c
from pathlib import Path
import struct
import psutil
from private_npc_memory import kernel, MemoryBasicInformation


def read_chat(pid, expected_exe, codepage=950):
    if Path(psutil.Process(pid).exe()).resolve() != Path(expected_exe).resolve():
        raise ValueError('Unexpected client path')
    handle=kernel.OpenProcess(0x410, False, pid)
    if not handle:raise OSError(c.get_last_error(), 'OpenProcess')
    def read(address,size):
        block=c.create_string_buffer(size);n=c.c_size_t()
        return block.raw if kernel.ReadProcessMemory(handle,address,block,size,c.byref(n)) and n.value==size else None
    def integer(address):
        b=read(address,4)
        return struct.unpack('<I',b)[0] if b else 0
    try:
        address=0x10000;bases=set()
        while address<0x70000000:
            region=MemoryBasicInformation()
            if not kernel.VirtualQueryEx(handle,address,c.byref(region),c.sizeof(region)):break
            if region.state==0x1000 and region.region_size>0x15000000:
                bases.add(region.allocation_base)
            address=(region.base or address)+region.region_size
        for base in bases:
            for offset in range(0,0x10000,4):
                ui=base+offset+0xa7f2f6c
                options=integer(ui+0x86888);visible=integer(ui+0x39de8)
                if not 0x10000<options<0x70000000 or not 0x10000<visible<0x70000000:continue
                flags=read(options+0x449c,2);lines=integer(visible+0x67e8)
                if not flags or lines>=1000:continue
                history=read(visible,0x6800)
                if history is None:continue
                return {'world_address':base+offset,'common_enabled':bool(int.from_bytes(flags,'little')&16),
                        'visible_line_count':lines,'ascii_in_visible_list':b'probe123' in history,
                        'chinese_in_visible_list':'中'.encode(f'cp{codepage}') in history,
                        'display_mask':integer(ui+0x39e04)}
        raise RuntimeError('Native chat state not located')
    finally:kernel.CloseHandle(handle)
