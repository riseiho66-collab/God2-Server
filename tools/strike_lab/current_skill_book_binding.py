"""Execute the original skill identity to book lookup, not damage arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_item_metadata import NativeItemMetadata
from .current_skill_identity import SOURCE, SOURCE_SHA256, decode_definitions
from .recover_combat_rules import CLIENT, IMAGE_SHA256, SKILLS, SOURCE_HASHES, read_pinned


class NativeSkillBookBinding(NativeItemMetadata):
    ITEM_SECTIONS = NativeItemMetadata.ITEM_SECTIONS + ('PFD',)
    POOL = 0x3800000
    CODE = NativeItemMetadata.CODE + ((0xa8e10, 0xa8f9f), (0x147000, 0x16f000))

    def __init__(self):
        super().__init__()
        self.definitions = decode_definitions(read_pinned(CLIENT / SOURCE, SOURCE_SHA256))
        self.vm.mem_map(self.POOL, 0x40000, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        self.records = {}
        self.sources = {}
        rows = [(section, index, row) for section in ('SKB', 'PFD')
                for index, row in enumerate(self.sections[section]['records'])
                if 6501 <= int(bytes.fromhex(row['fields_hex'][0])) <= 7199]
        for section, index, row in rows:
            result = self.item_row(section, index)
            key = result['key']
            if key in self.records:
                raise AssertionError('Duplicate native item index in lookup interval')
            address = self.POOL + len(self.records) * 0x200 + 16
            self.vm.mem_write(address - 16, b'\xa5' * 0x200)
            self.vm.mem_write(address, result['record'])
            self.records[key] = (address, result['record'])
            self.sources[key] = row
        # Publish retained parsed records through the original index-store edge.
        for key, (address, _) in self.records.items():
            self.reg('ESI', self.TABLE)
            self.reg('EAX', key)
            self.reg('EDX', address)
            at = self.TABLE + 0xb2d40 + key * 4
            self.allowed = ((at, at + 4),)
            try:
                self.run(0x59a20, 0x59a27)
            finally:
                self.allowed = None
        self.vm.mem_protect(self.POOL, 0x40000, self.uc.UC_PROT_READ)
        # This Unicorn build corrupts lazy CMP flags during REP MOVSD with a
        # global write hook. Protect inputs and observe only the output page;
        # do not patch flags or skip any original instruction.
        self.vm.hook_del(self.write_hook)
        self.write_hook = self.vm.hook_add(self.uc.UC_HOOK_MEM_WRITE, self._write,
                                           begin=self.OUTPUT, end=self.OUTPUT + 0x3fff)
        for address, size in ((self.TABLE, 0x100000), (self.OWNER, 0x100000),
                              (self.INPUT, 4096), (self.RECORD, 4096), (self.MAPS, 0x2000)):
            self.vm.mem_protect(address, size, self.uc.UC_PROT_READ)
        self.lookup_active = False
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self._observe_lookup)

    def _observe_lookup(self, vm, address, size, context):
        if not self.lookup_active:
            return
        if address == self.BASE + 0x59a60:
            sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
            self.visited.append(struct.unpack('<I', vm.mem_read(sp + 4, 4))[0] & 0xffff)
        if address == self.BASE + 0x148810:
            sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
            left, right, width = struct.unpack('<3I', vm.mem_read(sp + 4, 12))
            self.comparisons.append((self.visited[-1], width,
                                     bytes(vm.mem_read(left, width)), bytes(vm.mem_read(right, width))))
        if address in (self.BASE + 0xa8f09, self.BASE + 0xa8f0d):
            self.branch_trace.append((address - self.BASE,
                                      vm.reg_read(self.x86.UC_X86_REG_EAX) & 255,
                                      vm.reg_read(self.x86.UC_X86_REG_EFLAGS)))

    def run(self, start, stop):
        if start != 0xa8e10:
            return super().run(start, stop)
        self.active_code = True
        self.stop_address = self.BASE + stop
        try:
            self.vm.emu_start(self.BASE + start, self.stop_address,
                              count=500000, timeout=3000000)
        finally:
            self.active_code = False
        if self.vm.reg_read(self.x86.UC_X86_REG_EIP) != self.stop_address:
            raise AssertionError('Native skill book lookup did not return')

    def lookup(self, kind, skill_id):
        if type(kind) is not int or not 0 <= kind <= 3:
            raise ValueError('Only the four original skill banks are supported')
        if type(skill_id) is not int or not 0 <= skill_id <= 255:
            raise ValueError('Skill ID must be an explicit byte')
        self.vm.mem_write(self.OUTPUT, b'\xa5' * 16)
        self.vm.mem_write(self.OUTPUT + 4, bytes(2))
        self.visited = []
        self.comparisons = []
        self.branch_trace = []
        self.lookup_active = True
        try:
            pointer = self.call(0xa8e10, kind, skill_id, self.OUTPUT + 4,
                                this=self.OWNER, allowed=((self.OUTPUT + 4, self.OUTPUT + 6),))
        finally:
            self.lookup_active = False
        output = bytes(self.vm.mem_read(self.OUTPUT, 16))
        key = struct.unpack_from('<H', output, 4)[0]
        if output[:4] != b'\xa5' * 4 or output[6:] != b'\xa5' * 10:
            raise AssertionError('Book lookup escaped its WORD output')
        if pointer != (self.records[key][0] if key in self.records else 0):
            raise AssertionError('Book identity and returned parsed record disagree')
        if key == 0:
            return None
        row = self.sources[key]
        return dict(kind=kind, skill_id=skill_id, item_id=key,
                    source_line=row['source_line'], decoded_offset=row['decoded_offset'],
                    source_record_sha256=hashlib.sha256(bytes.fromhex(row['raw_record_hex']).rstrip(b'\r\n')).hexdigest(),
                    code=self.records[key][1][0x11c:0x12c].split(b'\0', 1)[0].decode('ascii'),
                    native_lookup_verified=True, damage_formula_verified=False)

    def catalog(self):
        entries, missing = [], []
        for kind, skill_id in sorted(self.definitions):
            match = self.lookup(kind, skill_id)
            if match is None:
                missing.append(dict(kind=kind, skill_id=skill_id))
            else:
                entries.append(match)
        from .current_skill_description_rules import build_ledger
        links = []
        for description in build_ledger()['entries']:
            for entry in entries:
                if entry['item_id'] != description['item_id']:
                    continue
                if entry['source_record_sha256'] != description['source_record_sha256']:
                    raise AssertionError('Description source differs from native parsed row')
                links.append(dict(kind=entry['kind'], skill_id=entry['skill_id'],
                                  item_id=entry['item_id'], source_column=description['source_column'],
                                  source_text=description['source_text'], claims=description['claims'],
                                  authority='description_only', executable=False))
        return dict(image_sha256=IMAGE_SHA256, book_source=SKILLS,
                    book_sha256=SOURCE_HASHES[SKILLS], skill_source=SOURCE,
                    skill_sha256=SOURCE_SHA256,
                    lookup_rva='0xA8E10', definition_count=len(self.definitions),
                    parsed_item_count=len(self.records),
                    entries=entries, unmatched=missing, description_links=links,
                    authority='native_metadata_lookup_only', production_enabled=False,
                    boundary='Synthetic owner/table populated by original row parser. '
                             'Original formatter, comparison, lookup and return execute. '
                             'Row-loader CRT decimal conversion remains adapted. '
                             'No full client session or combat formula is verified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = NativeSkillBookBinding().catalog()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(matched=len(result['entries']), unmatched=len(result['unmatched']))))


if __name__ == '__main__':
    main()
