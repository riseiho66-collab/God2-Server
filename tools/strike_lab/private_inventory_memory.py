"""Read-only bounded search for an original client's live slot-0 record."""
import ctypes as c
from ctypes import wintypes as w
import json
import struct
import sys

kernel = c.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.restype = w.HANDLE
kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
kernel.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
kernel.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t]
kernel.VirtualQueryEx.restype = c.c_size_t


class Region(c.Structure):
    _fields_ = [('BaseAddress', c.c_void_p), ('AllocationBase', c.c_void_p),
                ('AllocationProtect', w.DWORD), ('PartitionId', w.WORD),
                ('RegionSize', c.c_size_t), ('State', w.DWORD),
                ('Protect', w.DWORD), ('Type', w.DWORD)]


def read(handle, address, size):
    buffer = c.create_string_buffer(size)
    length = c.c_size_t()
    if not kernel.ReadProcessMemory(handle, address, buffer, size, c.byref(length)):
        return None
    return buffer.raw[:length.value]


def main():
    pid = int(sys.argv[1])
    item_id = int(sys.argv[2]) if len(sys.argv) > 2 else 3107
    if not 1 <= item_id <= 65535:
        raise ValueError('item id outside original client WORD range')
    handle = kernel.OpenProcess(0x1010, False, pid)
    if not handle:
        raise c.WinError(c.get_last_error())
    pattern_tail = item_id.to_bytes(2, 'little') + bytes(18)
    matches = []
    address = 0x10000
    scanned = 0
    while address < 0x80000000 and scanned < 800 * 1024 * 1024:
        region = Region()
        if not kernel.VirtualQueryEx(handle, address, c.byref(region), c.sizeof(region)):
            break
        base = region.BaseAddress or address
        end = min(base + region.RegionSize, 0x80000000)
        if region.State == 0x1000 and not region.Protect & 0x101:
            offset = base
            while offset < end:
                size = min(1024 * 1024, end - offset)
                raw = read(handle, offset, size)
                if raw:
                    scanned += len(raw)
                    at = -1
                    for count in (3, 2, 1):
                        at = raw.find(count.to_bytes(4, 'little') + pattern_tail)
                        if at >= 0:
                            break
                    if at >= 0:
                        slot = offset + at
                        ui = slot - 0x8560c
                        source_index_raw = read(handle, ui + 0x232dc8, 2)
                        source_index = int.from_bytes(source_index_raw, 'little', signed=True) if source_index_raw else None
                        source_mode = (read(handle, ui + 0xe2988 + 10760 * source_index, 1) or b'').hex() \
                            if source_index is not None and 0 <= source_index < 64 else None
                        widget_id_raw = read(handle, ui + 0x232e54, 2)
                        widget_id = int.from_bytes(widget_id_raw, 'little') if widget_id_raw else None
                        widget = ui + 0xe2170 + 0x818 + 0x2a08 * widget_id \
                            if widget_id is not None and widget_id < 128 else None
                        rect_raw = read(handle, widget + 0x18, 16) if widget else None
                        alt_rect_raw = read(handle, widget + 0x28, 16) if widget else None
                        children = []
                        if widget:
                            for child_index in range(106):
                                child = read(handle, widget + 0xa0 + child_index * 100, 0x30)
                                if child and child[0] != 0:
                                    children.append({'index': child_index,
                                        'flags': child[0],
                                        'rect': list(struct.unpack_from('<4i', child, 0x10))})
                        widgets = []
                        manager = ui + 0xe2170
                        for candidate_id in range(64):
                            candidate = read(handle, manager + 0x818 + 0x2a08 * candidate_id, 0x50)
                            if not candidate or len(candidate) < 0x50:
                                continue
                            kind = struct.unpack_from('<H', candidate)[0]
                            bounds = struct.unpack_from('<4i', candidate, 0x18)
                            if 0 < kind <= 0x100 and all(-1000 <= value <= 2000 for value in bounds):
                                row = {'id': candidate_id, 'kind': kind,
                                       'rect': list(bounds), 'header': candidate[:0x50].hex()}
                                if kind == 19 and bounds[1] >= 150 and bounds[2] - bounds[0] >= 100:
                                    row['children'] = []
                                    for child_index in range(106):
                                        child = read(handle, manager + 0x818 + 0x2a08 * candidate_id +
                                                     0xa0 + child_index * 100, 0x30)
                                        if child and child[0] != 0:
                                            row['children'].append({'index': child_index,
                                                'flags': child[0],
                                                'rect': list(struct.unpack_from('<4i', child, 0x10))})
                                widgets.append(row)
                        matches.append({'slot': hex(slot), 'ui': hex(ui),
                                        'pending': (read(handle, ui + 0x85608, 4) or b'').hex(),
                                        'target_pointer': (read(handle, ui + 0x8688c, 4) or b'').hex(),
                                        'action_mode': (read(handle, ui + 0xa3d08, 4) or b'').hex(),
                                        'action_records': (read(handle, ui + 0xa3d18, 60) or b'').hex(),
                                        'selected_action': (read(handle, ui + 0xa4158, 2) or b'').hex(),
                                        'selected_inventory_slot': (read(handle, ui + 0x855f0, 2) or b'').hex(),
                                        'inventory_source_index': source_index,
                                        'inventory_source_mode': source_mode,
                                        'selected_action_source': (read(handle, ui + 0xa3d02, 2) or b'').hex(),
                                        'selected_action_kind': (read(handle, ui + 0xa3d00, 2) or b'').hex(),
                                        'action_widget_id': widget_id,
                                        'action_widget_type': (read(handle, widget, 2) or b'').hex() if widget else None,
                                        'action_widget_rect': list(struct.unpack('<4i', rect_raw)) if rect_raw else None,
                                        'action_widget_alt_rect': list(struct.unpack('<4i', alt_rect_raw)) if alt_rect_raw else None,
                                        'action_widget_children': children,
                                        'ui_widgets': widgets})
                offset += size
        address = end if end > address else address + 0x1000
    print(json.dumps({'pid': pid, 'scanned': scanned, 'matches': matches}, indent=2))


if __name__ == '__main__':
    main()
