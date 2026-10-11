"""Read-only bounded scan for the original client's two known town guide actors."""
import ctypes as c
from ctypes import wintypes as w
import math
from pathlib import Path
import struct

import psutil


class MemoryBasicInformation(c.Structure):
    _fields_ = [('base', c.c_void_p), ('allocation_base', c.c_void_p),
                ('allocation_protect', w.DWORD), ('partition_id', w.WORD),
                ('padding', w.WORD), ('region_size', c.c_size_t),
                ('state', w.DWORD), ('protect', w.DWORD), ('kind', w.DWORD),
                ('tail_padding', w.DWORD)]


kernel = c.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
kernel.OpenProcess.restype = w.HANDLE
kernel.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p,
                                   c.POINTER(MemoryBasicInformation), c.c_size_t]
kernel.VirtualQueryEx.restype = c.c_size_t
kernel.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p,
                                     c.c_size_t, c.POINTER(c.c_size_t)]
kernel.ReadProcessMemory.restype = w.BOOL
kernel.CloseHandle.argtypes = [w.HANDLE]


def read_guides(pid, expected_exe):
    actual = Path(psutil.Process(pid).exe()).resolve()
    if actual != Path(expected_exe).resolve():
        raise ValueError(f'unexpected game executable: {actual}')
    handle = kernel.OpenProcess(0x0410, False, pid)  # QUERY_INFORMATION | VM_READ
    if not handle:
        raise OSError(c.get_last_error(), 'OpenProcess failed')
    try:
        # Earlier current-client world allocations placed guide pool 0x1d..0x36
        # billion-byte-address range. Bound this scan to below 0x40000000.
        address, ceiling = 0x1d000000, 0x40000000
        marker = struct.pack('<I', 1606)
        stride = 0x1d8
        overlap = stride + 0x40
        readable = 0
        searched = 0
        while address < ceiling:
            info = MemoryBasicInformation()
            if not kernel.VirtualQueryEx(handle, address, c.byref(info), c.sizeof(info)):
                address += 0x1000
                continue
            start = int(info.base or address)
            end = min(start + info.region_size, ceiling)
            if end <= address:
                address += 0x1000
                continue
            if (info.state == 0x1000 and not (info.protect & 0x101)
                    and info.protect & 0xff in (2, 4, 8, 0x20, 0x40, 0x80)):
                readable += end - max(start, address)
                cursor = max(start, address)
                while cursor < end:
                    size = min(1 << 20, end-cursor)
                    length = min(size+overlap, end-cursor)
                    buffer = c.create_string_buffer(length)
                    transferred = c.c_size_t()
                    if kernel.ReadProcessMemory(handle, cursor, buffer, length,
                                                c.byref(transferred)) and transferred.value == length:
                        block = buffer.raw
                        searched += size
                        offset = block.find(marker)
                        while offset >= 0:
                            if offset + stride + 0x20 <= len(block):
                                x, y = struct.unpack_from('<ii', block, offset+0x10)
                                second = struct.unpack_from('<I', block, offset+stride)[0]
                                x2, y2 = struct.unpack_from('<ii', block, offset+stride+0x10)
                                if (x, y, second, x2, y2) == (110, 69, 1607, 112, 70):
                                    p1 = struct.unpack_from('<ff', block, offset+0x18)
                                    p2 = struct.unpack_from('<ff', block, offset+stride+0x18)
                                    if all(math.isfinite(v) for v in (*p1, *p2)):
                                        return {'actor_address': cursor+offset,
                                                'actor_offsets': [0, stride],
                                                'world_coordinates': [[x, y], [x2, y2]],
                                                'projected': [list(p1), list(p2)],
                                                'readable_bytes': readable,
                                                'searched_bytes': searched}
                            offset = block.find(marker, offset+1)
                    cursor += size
            address = end
        return {'found': False, 'readable_bytes': readable,
                'searched_bytes': searched}
    finally:
        kernel.CloseHandle(handle)
