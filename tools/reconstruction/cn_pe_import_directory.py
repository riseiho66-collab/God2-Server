"""Bounded file-only PE32 imports, preserving RVA/VA and declared/loaded distinction.

Some pinned CN descriptors alias short thunk arrays. A general parser can stop
on its error/oversized-array heuristic before later valid descriptors. Its
partial result cannot establish that a named IAT slot has no declaration.
This reader follows primary descriptor/ILT records with file-backed bounds.
It does not load DLLs, execute the image or observe resolved IAT addresses.
"""
import struct


class FileView:
    def __init__(self, pe, raw):
        if pe.OPTIONAL_HEADER.Magic != 0x10b:
            raise ValueError('Qualified reader is PE32 only')
        self.pe, self.raw = pe, raw

    def window(self, rva):
        if rva < 0:
            raise ValueError('Negative RVA')
        if rva < self.pe.OPTIONAL_HEADER.SizeOfHeaders:
            return rva, min(self.pe.OPTIONAL_HEADER.SizeOfHeaders, len(self.raw))-rva
        candidates = []
        for section in self.pe.sections:
            delta = rva-section.VirtualAddress
            if 0 <= delta < section.SizeOfRawData:
                offset = section.PointerToRawData+delta
                available = min(section.SizeOfRawData-delta, len(self.raw)-offset)
                if available > 0:
                    candidates.append((offset, available))
        if len(candidates) != 1:
            raise ValueError(f'RVA{rva:08x} lacks unique file-backed section')
        return candidates[0]

    def read(self, rva, size):
        offset, available = self.window(rva)
        if size < 0 or size > available:
            raise ValueError(f'RVA{rva:08x} crosses backing bounds')
        return self.raw[offset:offset+size]

    def string(self, rva):
        offset, available = self.window(rva)
        # Resource budget for metadata names, not a native gameplay string rule.
        data = self.raw[offset:offset+min(available, 4096)]
        nul = data.find(b'\0')
        if nul < 0:
            raise ValueError(f'Unterminated metadata string atRVA{rva:08x}')
        return data[:nul].decode('ascii')


def import_directory(pe, raw):
    view = FileView(pe, raw)
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
    if not directory.VirtualAddress or directory.Size < 20:
        raise ValueError('Missing bounded import directory')
    descriptor_limit = directory.Size//20
    if descriptor_limit > 100000:
        raise ValueError('Static descriptor resource budget exceeded')
    descriptors, bindings = [], []
    terminated = False
    base = pe.OPTIONAL_HEADER.ImageBase
    for index in range(descriptor_limit):
        rva = directory.VirtualAddress+20*index
        descriptor_bytes = view.read(rva, 20)
        oft, stamp, chain, name, ft = struct.unpack('<5I', descriptor_bytes)
        if not any((oft, stamp, chain, name, ft)):
            terminated = True
            break
        if not name or not ft:
            raise ValueError(f'Incomplete descriptor{index}')
        dll = view.string(name)
        lookup = oft or ft
        descriptor = {'index': index, 'descriptor_rva': f'{rva:08x}',
                      'descriptor_va': f'{base+rva:08x}',
                      'descriptor_bytes': descriptor_bytes.hex(),
                      'original_first_thunk_rva': f'{oft:08x}',
                      'first_thunk_rva': f'{ft:08x}', 'dll_name_rva': f'{name:08x}',
                      'dll': dll, 'timestamp': stamp, 'forwarder_chain': chain}
        descriptors.append(descriptor)
        # Traverse the actual ILT to itsNUL. Bounds are per file-backed section.
        _, available = view.window(lookup)
        for ordinal_index in range(min(available//4, 100000)):
            cell_rva = lookup+4*ordinal_index
            value = struct.unpack('<I', view.read(cell_rva, 4))[0]
            if not value:
                break
            iat_rva = ft+4*ordinal_index
            iat_bytes = view.read(iat_rva, 4)
            binding = {'descriptor_index': index, 'dll': dll,
                       'lookup_rva': f'{cell_rva:08x}', 'iat_rva': f'{iat_rva:08x}',
                       'iat_va': f'{base+iat_rva:08x}',
                       'file_lookup_u32': f'{value:08x}', 'file_iat_bytes': iat_bytes.hex(),
                       'file_iat_u32': f'{struct.unpack("<I", iat_bytes)[0]:08x}',
                       'loaded_binding_observed': False}
            if value & 0x80000000:
                binding.update({'ordinal': value & 0xffff, 'name': None, 'hint': None})
            else:
                binding.update({'ordinal': None, 'hint_name_rva': f'{value:08x}',
                                'hint': struct.unpack('<H', view.read(value, 2))[0],
                                'name': view.string(value+2)})
            bindings.append(binding)
            if len(bindings) > 100000:
                raise ValueError('Static binding resource budget exceeded')
        else:
            raise ValueError(f'Unterminated thunk array for descriptor{index}')
    if not terminated:
        raise ValueError('No descriptor terminator within declared directory')
    return {'descriptor_count': len(descriptors), 'binding_count': len(bindings),
            'directory_rva': f'{directory.VirtualAddress:08x}', 'directory_size': directory.Size,
            'descriptors': descriptors, 'bindings': bindings,
            'method': 'FILE_BACKED_PE32_DESCRIPTOR_ILT_READING',
            'loaded_binding_observed': False, 'native_execution': False}
