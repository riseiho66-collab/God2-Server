"""Current skill aliases and native consumers; no wild-monster assignments.

Only pinned current gamedata, cbspec2 and the mapped image are source inputs.
JSON goes to stdout. No catalog sweep, gameplay, file writes or child processes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz
from .recover_companions import parse_sections
from .recover_companion_growth import _NativeRows
from .current_battle_entry import IMAGE, IMAGE_SHA256, pinned_image
from .current_skill_identity import SOURCE as SKILL_SOURCE, SOURCE_SHA256, decode_definitions

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
GAME = 'Data2/Patch/Comm/gamedata.csvZ'
GAME_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
# count, row start/stop, pointer/count fields, row counter, lookup entry/call
TABLES = {
    'FightPetSkill': (254, 0x5896a, 0x58a80, 0xd2cc0, 0xd2cbc, 0x18, 0xa2880, 0xa28fd),
    'NewFightPet2Skill': (255, 0x58b31, 0x58c47, 0xd2d78, 0xd2d74, 0x1c, 0xa4f60, 0xa4fe3),
}
SPANS = {
    'fight_row': (0x5896a, 0x58a80, '867d89a3060c7cc9c17f24b4efe9b0f9d1e1a9bcd7c8d3426752cdff9545edac'),
    'new_row': (0x58b31, 0x58c47, 'bab431400d8d4216ac82ac8effd6262b18d580302f76254b79309f494f67df8a'),
    'substring': (0x5ac80, 0x5acbc, 'fc53dcbc01b62b7d1355489add14ddaa590e3a7518104a3d349c1e22fbe100f3'),
    'fields': (0x51ae0, 0x51cd2, '90fb810f004e440ab7799b402a3371665d3b004d26c28048be3470a99f9fbeb0'),
    'memcpy': (0x147b80, 0x147c30, 'ed34e00645fdbee50fade979929ca4c115d59601b74336f7206cabd2eca7ae7c'),
    'sscanf_entry': (0x1480b4, 0x1480b5, 'a25513c7e0f6eaa80a3337ee18081b9e2ed09e00af8531c8f7bb2542764027e7'),
    'atoi': (0x14828c, 0x148322, '213cbf2462f39a9d677bb0c1220b5b2c4c47c2d98487fc42065639a6ca14485b'),
    'strchr': (0x148990, 0x148a5c, 'a4d43aa01f5b3db8839024433e2579f873e3cd2a234dbd89ac151292935a770c'),
    'compare': (0x155980, 0x1559f1, '15f10791ed4f20992bedc3eb3e925f6321848494c350d6895b488652dc08525c'),
    'compare_return': (0x155a7a, 0x155a81, '557fa1de40d7d7821a3cafee26b1834d48c96f270fe4bba978fb6aafdb10f60c'),
    'fight_lookup': (0xa2880, 0xa2906, '446730385314f69b6d39b661177b0c25447f9ce7c90dc66622fbc8aa86665852'),
    'new_lookup': (0xa4f60, 0xa4fec, '35baa5f470ea988a59e99c8c0716bb328ac9835ea99b87eb6e531fcb5aaa8ee3'),
    'template_lookup': (0x59a60, 0x59a7e, 'b944430a3785216d0a76d3f5ebd52d959cbd05ce85e5148ae90833a855e39ced'),
    'template_candidate': (0xad9b0, 0xadae8, '27de6d0b41ac23b936b4e6f761519d7c8b9bc9068c8440c84a299c1071b450bb'),
    'category_tail': (0x5c9b5, 0x5c9da, '6d58a767068112a481bff0e3751650dfd0f459e45ccffb686310a4f31bd2ad73'),
    'dispatch': (0x567d2, 0x56863, '158daa1d16118abc438bcb6d21736483b268312952d649cd4ca10463785fca1f'),
    'bank_literals': (0x18a15c, 0x18a16c, '69173130eed3dc2e54dd9a3501d03bd76327014020d68d729284af816ea3d7d2'),
}
EXECUTED = tuple(SPANS)[:12]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_pin(raw, expected):
    if sha(raw) != expected:
        raise ValueError('Pinned current source changed')
    return raw


def read_pinned(path, expected, limit):
    path = Path(path)
    if any(p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400
           for p in (path, *path.parents)):
        raise ValueError('Reparse source rejected')
    if path.stat().st_size > limit:
        raise ValueError('Source size bound')
    with path.open('rb') as stream:
        return check_pin(stream.read(limit + 1), expected)


def sources():
    plain = decode_csvz(read_pinned(CLIENT / GAME, GAME_SHA, 1 << 20), limit=4 << 20)
    check_pin(plain, PLAIN_SHA)
    sections = parse_sections(plain, tuple(TABLES))
    for name, section in sections.items():
        if section['declared_count'] != TABLES[name][0]:
            raise ValueError('Pinned alias section changed')
        for index, row in enumerate(section['records'], 1):
            fields = [bytes.fromhex(f) for f in row['fields_hex']]
            if (len(fields) not in (3, 4, 6) or fields[0] != str(index).encode()
                    or re.fullmatch(rb'Spc[A-D][0-9]{2,3}', fields[1]) is None):
                raise ValueError('Unsupported pinned alias row')
    skill = read_pinned(CLIENT / SKILL_SOURCE, SOURCE_SHA256, 128 << 10)
    return sections, decode_definitions(skill)


class NativeAliases(_NativeRows):
    """Original row -> original lookup in one VM, with explicit loader state.

    Full file loading, allocation and row-count publication are not executed.
    The two lookup functions stop BEFORE A9710; no return value is invented.
    """

    def __init__(self):
        self.image = read_pinned(IMAGE, IMAGE_SHA256, 4 << 20)
        for lo, hi, digest in SPANS.values():
            check_pin(self.image[lo:hi], digest)
        super().__init__(self.image)
        self.array = {name: self.OUTPUT + i * 0x1000 for i, name in enumerate(TABLES)}
        self.wrapper, self.results = self.OUTPUT + 0x3000, self.OUTPUT + 0x3100
        self.vm.mem_write(self.TABLE + 0xcff70, struct.pack('<I', self.TABLE))
        self.vm.mem_write(self.wrapper + 0xdc, struct.pack('<I', self.TABLE))
        for name, config in TABLES.items():
            count, _, _, pointer, count_field, *_ = config
            self.vm.mem_write(self.TABLE + pointer, struct.pack('<I', self.array[name]))
            self.vm.mem_write(self.TABLE + count_field, struct.pack('<H', count))
            self.vm.mem_write(self.array[name], b'\xa5' * 0x400)
        self.stops, self.visits, self.reads = set(), [], []
        self.traced_writes = []
        self.active = False
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self._instruction)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_READ, self._read)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_WRITE, self._trace_write)

    def _instruction(self, vm, address, size, _):
        if not self.active:
            return
        rva = address - self.BASE
        if rva in self.stops:
            vm.emu_stop()
            return
        if not any(SPANS[k][0] <= rva and rva + size <= SPANS[k][1] for k in EXECUTED):
            raise AssertionError(f'Unqualified instruction {rva:X}')
        self.visits.append(rva)

    def _read(self, vm, access, address, size, value, _):
        if not self.active:
            return
        spans = [(self.BASE, self.BASE + len(self.image)),
                 (self.STACK, self.STACK + 0x10000), (self.INPUT, self.INPUT + 4096),
                 (self.TABLE, self.TABLE + 0x78 + 6 * 380),
                 (self.TABLE + 0xcff70, self.TABLE + 0xcff74),
                 (self.TABLE + 0xd2cbc, self.TABLE + 0xd2cc4),
                 (self.TABLE + 0xd2d74, self.TABLE + 0xd2d7c),
                 (self.OUTPUT, self.OUTPUT + 0x4000)]
        if not any(lo <= address and address + size <= hi for lo, hi in spans):
            raise AssertionError(f'Unqualified read {address:X}')
        if not self.STACK <= address < self.STACK + 0x10000:
            self.reads.append((vm.reg_read(self.x86.UC_X86_REG_EIP) - self.BASE, address, size))

    def _trace_write(self, vm, access, address, size, value, _):
        if self.active and not self.STACK <= address < self.STACK + 0x10000:
            if self.allowed is None and not (
                    self.TABLE + 0xc <= address and address + size <= self.TABLE + 0x10
                    or self.TABLE + 0x78 <= address and address + size <= self.TABLE + 0x78 + 6 * 380):
                raise AssertionError(f'Unqualified tokenizer write {address:X}')
            self.traced_writes.append((vm.reg_read(self.x86.UC_X86_REG_EIP) - self.BASE,
                                       address, size, value))

    def execute(self, start, stops):
        for key in EXECUTED:
            lo, hi, digest = SPANS[key]
            check_pin(bytes(self.vm.mem_read(self.BASE + lo, hi - lo)), digest)
        self.stops, self.visits, self.reads = set(stops), [], []
        self.traced_writes = []
        self.active = True
        try:
            self.vm.emu_start(self.BASE + start, self.RETURN, count=50000, timeout=1000000)
        finally:
            self.active = False
        stop = self.vm.reg_read(self.x86.UC_X86_REG_EIP) - self.BASE
        if stop not in self.stops:
            raise AssertionError('Native replay did not reach qualified stop')
        return {'start_rva': start, 'stop_rva': stop, 'reads': list(self.reads),
                'writes': list(self.traced_writes), 'executed_rvas': sorted(set(self.visits))}

    def run(self, start, stop):
        return self.execute(start, {stop})

    def load_row(self, name, row, ordinal, *, bank_live_in=0xa5):
        count, start, stop, _, _, counter, *_ = TABLES[name]
        if not 1 <= ordinal <= count or not 0 <= bank_live_in <= 255:
            raise ValueError('Row diagnostic bounds')
        width = len(bytes.fromhex(row['raw_record_hex']).rstrip(b'\r\n').split(b','))
        if width not in (3, 4, 6):
            raise ValueError('Unsupported diagnostic row width')
        self.tokenize(row, width)
        self.vm.mem_write(self.SP, bytes(0x900))
        self.vm.mem_write(self.SP + counter, struct.pack('<I', ordinal - 1))
        for reg, value in (('ESP', self.SP), ('ESI', self.TABLE), ('EBP', count), ('EBX', bank_live_in)):
            self.reg(reg, value)
        address = self.array[name] + 2 * (ordinal - 1)
        self.allowed = [(address, address + 2)]
        try:
            trace = self.run(start, stop)
        finally:
            self.allowed = None
        if (self.vm.reg_read(self.x86.UC_X86_REG_ESP) != self.SP
                or self.columns != [0, 1, 1]):
            raise AssertionError('Row stack/column contract changed')
        trace['columns'] = list(self.columns)
        return list(self.vm.mem_read(address, 2)), trace

    def lookup(self, name, alias):
        if type(alias) is not int or not 0 <= alias <= 0xffffffff:
            raise ValueError('Expected explicit DWORD alias input')
        _, _, _, _, _, _, entry, call = TABLES[name]
        self.vm.mem_write(self.results, b'\xa5' * 8)
        self.vm.mem_write(self.SP, struct.pack('<4I', self.RETURN, alias, self.results, self.results + 4))
        self.reg('ESP', self.SP)
        self.reg('ECX', self.TABLE if name == 'FightPetSkill' else self.wrapper)
        self.allowed = [(self.results, self.results + 8)]
        try:
            trace = self.execute(entry, {call, self.RETURN - self.BASE})
        finally:
            self.allowed = None
        trace['alias_input'] = alias
        if trace['stop_rva'] == call:
            sp = self.vm.reg_read(self.x86.UC_X86_REG_ESP)
            bank, skill_id, first, second = struct.unpack('<4I', self.vm.mem_read(sp, 16))
            if sp != self.SP - 20 or (first, second) != (self.results, self.results + 4):
                raise AssertionError('Original lookup call arguments changed')
            trace.update(pair=[bank, skill_id], status='stopped_before_A9710')
        else:
            if self.vm.reg_read(self.x86.UC_X86_REG_ESP) != self.SP + 16:
                raise AssertionError('Lookup return stack imbalance')
            trace.update(pair=None, status='native_alias_rejection',
                         outputs=list(struct.unpack('<2I', self.vm.mem_read(self.results, 8))))
        return trace


def build_report():
    sections, definitions = sources()
    vm = NativeAliases()
    tables = {}
    for name, section in sections.items():
        rows = []
        for ordinal, source in enumerate(section['records'], 1):
            pair, writer = vm.load_row(name, source, ordinal)
            consumer = vm.lookup(name, ordinal)
            if consumer['pair'] != pair:
                raise AssertionError('Same-VM alias producer/consumer mismatch')
            token = bytes.fromhex(source['fields_hex'][1])
            expected = [{'A': 0, 'B': 3, 'C': 2, 'D': 1}[chr(token[3])], int(token[4:])]
            if pair != expected:
                raise AssertionError('Source token disagrees with native reader')
            definition = definitions.get(tuple(pair))
            rows.append({'source': source, 'alias_index': ordinal, 'native_pair': pair,
                         'writer': writer, 'consumer': consumer,
                         'definition_identity_cross_check_only': None if definition is None else {
                             'source_offset': definition.source_offset, 'sha256': sha(definition.raw)},
                         'definition_status': 'populated_identity_match' if definition else 'no_populated_definition',
                         'monster_identity_join': None, 'monster_skill_assignment': None,
                         'runtime_eligible': False})
        tables[name] = {'header': section['header'], 'rows': rows,
                        'row_count': len(rows), 'distinct_pairs': len({tuple(r['native_pair']) for r in rows}),
                        'without_populated_definition': sum(r['definition_status'] == 'no_populated_definition' for r in rows)}
    return {'schema': 'current-monster-skill-element-experience-v1',
            'source_pins': {GAME: GAME_SHA, 'decoded_gamedata': PLAIN_SHA,
                            SKILL_SOURCE: SOURCE_SHA256, str(IMAGE.relative_to(ROOT)): IMAGE_SHA256},
            'base_va': 0x400000, 'rva_equals_file_offset': True,
            'spans': {k: {'start_rva': lo, 'end_rva_exclusive': hi, 'sha256': h,
                           'authority': 'executed_bounded_slices' if k in EXECUTED else 'static_only'}
                      for k, (lo, hi, h) in SPANS.items()},
            'tables': tables,
            'wild_monster_proof': {'skill_assignments': None, 'elements': None, 'base_experience': None,
                                   'verified_identity_bound_values': 0, 'all_monsters_including_bosses_complete': False},
            'identity_policy': 'No name/label join. Require native identity or versioned composite key plus actual consumer.',
            'catalog': {'recomputed': False, 'source': 'main-agent handoff', 'visible_unique_composite_keys': 7791},
            'limits': ['Row/lookup invocations are separate; full startup loader and allocation are unexecuted.',
                       'Alias count fields and object pointers are explicit synthetic prerequisites.',
                       'A9710 is not executed; populated cbspec2 identity matching is a source cross-check only.',
                       'Template +11C/+11D frontier is static item/companion evidence, not wild ownership.',
                       'Category tail only is inspected; other readers of columns 9..11 are not excluded.',
                       'No new element or base-EXP source proof; no claim of global absence.'],
            'runtime_eligible': False}


def summary(report):
    return {'schema': report['schema'], 'tables': {
        name: {k: table[k] for k in ('row_count', 'distinct_pairs', 'without_populated_definition')}
        for name, table in report['tables'].items()},
        'wild_monster_proof': report['wild_monster_proof'], 'catalog': report['catalog'],
        'runtime_eligible': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(summary(report) if args.summary else report, ensure_ascii=True, sort_keys=True))


if __name__ == '__main__':
    main()
