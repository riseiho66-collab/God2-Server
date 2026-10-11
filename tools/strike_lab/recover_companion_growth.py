"""Extract pinned CURRENT original-client growth evidence, never gameplay rules.

Run with --summary for a read-only digest, or --output for a separate JSON file.
--native-image optionally executes bounded original row consumers in Unicorn.
No historical source tree, server, live process, or network is used.
"""
import argparse
from pathlib import Path
import re
import struct
import sys

from .omega_assets import decode_csvz
from .recover_companions import digest, parse_sections, read_source, record, serialize


COMM = 'Data2/Patch/Comm/'
# Both compressed and decoded identities qualify this extraction profile.
SOURCE_HASHES = {
    'gamedata': (
        '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
        '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'),
    'message': (
        '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
        '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'),
    'NewCombatPet_Category': (
        '80c2b7d366d2ef0264df78f20de1b20fa21e14f6592f56676b090f83ddc064c6',
        'f8d1a1c22e8fc9195dd625ffc244e2ebbcee07492116976feece0bd9d26b813b'),
    'NewCombatPet_QualityStar': (
        '52b414716947b4982d74c7da4166f35f4dd1b8e2cba27265aa3f854a2ba8756e',
        'fde6e5b716e710d39b1b706efabd1cfc9d58ef9fc353033d709b38b4bc1a5fbf'),
    'NewCombatPet_AllInnate': (
        '1a33373f44cb768acbfdb23d635aaf9ff408cfa47e2c62924e324519e8c3dee1',
        '7efa5886018370222120df3dfac3dbf100116393a3990afd8be2e3b54e3b4fd7'),
    'NewCombatPet_Innate': (
        '3a47e93cb43113fcd1bf679210caa8959e9db5b0e7778f3395dab70a4eae12df',
        '939a258d3b9448744adfa15b54ae25977b9e1b0eaf4b0da25b3c410a523f99ba'),
    'PetDesignDesc': (
        '1fbf0c5bba7408b92a72f7386924bf0dde9d1baf45bfaf2ed835565bc429eef6',
        'ce38da4853eabf4da3c51c4ead0f5e0300a9c620514b6f9c05a1bce64dcec291'),
}
GAME_SECTIONS = ('ItemType', 'GOD', 'PET', 'COM', 'NCP', 'GodLevel',
                 'FightPetSkill', 'NewFightPet2Skill', 'CategoryNum')
AUX_LAYOUTS = {
    # Preamble length, declaration tag, literal declaration, actual data rows.
    'NewCombatPet_Category': (5, b'CategoryDetailNum', 469, 464),
    'NewCombatPet_AllInnate': (5, b'AllInnateNum', 144, 144),
    'NewCombatPet_Innate': (4, b'InnateCount', 41, 41),
    'PetDesignDesc': (5, b'PetDesignNum', 381, 381),
}
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
NATIVE_RANGES = {
    'tokenizer': (0x51be0, 0x51cd2),
    'accessors': (0x51ae0, 0x51bdc),
    'GodLevel_dispatch': (0x5668c, 0x566d7),
    'GodLevel_row': (0x5a8a4, 0x5a8dd),
    'category_dispatch': (0x56ac0, 0x56b0b),
    'category_row': (0x5c6a6, 0x5c9b5),
    'quality_dispatch': (0x56b0b, 0x56b51),
    'quality_row': (0x5ca92, 0x5caaf),
    'star_dispatch': (0x56b51, 0x56b97),
    'star_row': (0x5caf2, 0x5cb0f),
}


def source_path(name):
    return COMM + name + '.csvZ'


def load_current_sources(client_root):
    sources, decoded = {}, {}
    for name, (raw_sha, plain_sha) in SOURCE_HASHES.items():
        path = source_path(name)
        raw = read_source(client_root, path)
        if digest(raw) != raw_sha:
            raise ValueError('Unqualified current source: ' + path)
        plain = decode_csvz(raw)
        if digest(plain) != plain_sha:
            raise ValueError('Unqualified decoded source: ' + path)
        sources[path] = {'sha256': raw_sha, 'size': len(raw),
                         'decoded_sha256': plain_sha, 'decoded_size': len(plain)}
        decoded[name] = plain
    return sources, decoded


def raw_lines(decoded):
    """Preserve LF boundaries and CR bytes, including the source's CR CR LF."""
    if not isinstance(decoded, bytes) or not decoded or b'\0' in decoded:
        raise ValueError('Expected nonempty NUL-free decoded bytes')
    parts = decoded.split(b'\n')
    rows, offset = [], 0
    for index, line in enumerate(parts):
        if index == len(parts) - 1 and not line:
            break
        raw = line + (b'\n' if index < len(parts) - 1 else b'')
        if not line.rstrip(b'\r'):
            raise ValueError('Unexpected empty physical record')
        rows.append(record(raw, index + 1, offset))
        offset += len(raw)
    return rows


def fields(row):
    return [bytes.fromhex(value) for value in row['fields_hex']]


def decimal(token):
    # Blank/missing is never converted to zero.
    if not re.fullmatch(rb'[0-9]+', token):
        raise ValueError('Expected explicit unsigned decimal token')
    return int(token)


def parse_auxiliary(name, decoded):
    rows = raw_lines(decoded)
    if name == 'NewCombatPet_QualityStar':
        if (len(rows) != 7 or fields(rows[1]) != [b'RowDesc', b'1'] or
                fields(rows[2]) != [f'Lv{i}'.encode() for i in range(16)] or
                fields(rows[3]) != [b'QualityValue'] or fields(rows[5]) != [b'StarValue']):
            raise ValueError('Unexpected quality/star structure')
        for index in (4, 6):
            values = fields(rows[index])
            if len(values) != 16 or any(decimal(v) > 65535 for v in values):
                raise ValueError('Expected sixteen explicit WORD values')
        return {'source_file': source_path(name), 'preamble': rows[:3],
                'labels': [rows[3], rows[5]], 'records': [rows[4], rows[6]],
                'actual_record_count': 2, 'scalar_token_count': 32}
    prefix, tag, declaration, actual = AUX_LAYOUTS[name]
    if (len(rows) != prefix + actual or
            fields(rows[prefix - 1]) != [tag, str(declaration).encode()]):
        raise ValueError('Unexpected auxiliary declaration or row count: ' + name)
    data = rows[prefix:]
    if name == 'NewCombatPet_Category':
        keys = []
        for row in data:
            values = fields(row)
            if (len(values) != 12 or any(v not in (b'Y', b'N') for v in values[3:9]) or
                    values[11] not in (b'Y', b'N') or not values[10]):
                raise ValueError('Unexpected category record')
            keys.append((decimal(values[0]), decimal(values[1])))
            decimal(values[9])
        if keys != [(group, index) for group in range(1, 30) for index in range(16)]:
            raise ValueError('Unexpected category keys/order')
    return {'source_file': source_path(name), 'preamble': rows[:prefix - 1],
            'declaration': rows[prefix - 1], 'declared_count_literal': declaration,
            'actual_record_count': actual, 'declaration_matches_data_count': declaration == actual,
            'count_policy': 'Preserve both counts; no invented rows or repaired declaration',
            'records': data}


def select_rows(section, ids):
    result = []
    for key in ids:
        matches = [row for row in section['records'] if fields(row)[0] == str(key).encode()]
        if len(matches) != 1:
            raise ValueError('Missing or duplicate selected source key: ' + str(key))
        result.append(matches[0])
    return result


def unknown_contracts():
    dependencies = {
        'growth_rate': 'Original coefficient/curve definition, units and selected-curve consumer',
        'base_value': 'Original initial stat values and their template/instance binding',
        'upgrade_formula': 'Original level transition arithmetic, allocation, rounding and caps',
        'experience_thresholds': 'Original level-to-required-experience table or verified arithmetic',
    }
    return {family: {concept: {'status': 'unknown', 'value': None,
                              'missing_evidence': missing, 'runtime_eligible': False}
                     for concept, missing in dependencies.items()}
            for family in ('battle_pet', 'deity')}


def build_growth(client_root, native_image=None):
    sources, decoded = load_current_sources(client_root)
    sections = parse_sections(decoded['gamedata'], GAME_SECTIONS)
    for section in sections.values():
        section['source_file'] = source_path('gamedata')
    auxiliary = {name: parse_auxiliary(name, decoded[name])
                 for name in (*AUX_LAYOUTS, 'NewCombatPet_QualityStar')}
    messages = parse_sections(decoded['message'], ('SystemMessage', 'ProgramMsg'))
    items = parse_sections(decoded['gamedata'], ('SPI', 'MIS02'))
    text_only = []
    for file, section_name, section, ids in (
            ('message', 'SystemMessage', messages['SystemMessage'], (845, 860, 861, *range(1309, 1317))),
            ('message', 'ProgramMsg', messages['ProgramMsg'], (911, 1051)),
            ('gamedata', 'SPI', items['SPI'], (6254,)),
            ('gamedata', 'MIS02', items['MIS02'], (16542, 16762, 16763))):
        text_only.append({'source_file': source_path(file), 'section': section_name,
                          'section_header': section['header'], 'records': select_rows(section, ids),
                          'evidence_class': 'source_text_only', 'runtime_verified': False,
                          'runtime_eligible': False})
    classification = []
    for tag in ('GOD', 'PET', 'COM', 'NCP'):
        matches = [row for row in sections['ItemType']['records'] if fields(row)[2] == tag.encode()]
        if len(matches) != 1:
            raise ValueError('Expected unique current ItemType tag: ' + tag)
        classification.append({'tag': tag, 'source_file': source_path('gamedata'),
                               'source': matches[0], 'runtime_subtype': None,
                               'evidence_class': 'source_label_only'})
    result = {
        'schema': 'god2-current-companion-growth-evidence-v1',
        'authority': 'Pinned current original-client bytes only',
        'runtime_eligible': False,
        'sources': sources, 'sections': sections, 'auxiliary_tables': auxiliary,
        'source_category_labels': classification, 'text_only_records': text_only,
        'unknown_contracts': unknown_contracts(),
        'field_policy': 'Zero-based raw fields; CP950 is display only. Unknown is null, never zero. '
                        'No subtype from names, stat from a price, skill unlock from a tail integer, '
                        'EXP threshold from GodLevel, or formula from Base100_Index37.',
        'native_verification': {'status': 'not_run', 'growth_formula_verified': False},
    }
    if native_image is not None:
        result['native_verification'] = verify_native_rows(native_image, decoded)
    return result


class _NativeRows:
    """Synthetic memory around original tokenizer/row code; only CRT %d adapted."""

    BASE, TABLE, STACK, INPUT, OUTPUT = 0x400000, 0x3000000, 0x3200000, 0x3300000, 0x3400000
    SP, RETURN = STACK + 0x8000, STACK + 0xff00

    def __init__(self, image, *, vm=None):
        # Reuse the installed research runtime and its existing decimal adapter.
        # Do not initialize NPC/resource loaders or their unrelated asset inputs.
        packages = Path(__file__).resolve().parents[2] / 'artifacts/tooling/crypto-oracle-python'
        if str(packages) not in sys.path:
            sys.path.insert(0, str(packages))
        import unicorn as uc
        from unicorn import x86_const as x86
        from .current_npc_resources import NativeNpcResources
        self.uc, self.x86 = uc, x86
        self.vm = vm if vm is not None else uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        if vm is None:
            self.vm.mem_map(self.BASE, (len(image) + 4095) & ~4095, uc.UC_PROT_READ | uc.UC_PROT_EXEC)
            self.vm.mem_write(self.BASE, image)
        for address, size in ((self.TABLE, 0x100000), (self.STACK, 0x10000),
                              (self.INPUT, 4096), (self.OUTPUT, 0x4000)):
            self.vm.mem_map(address, size, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.adapter = NativeNpcResources.__new__(NativeNpcResources)
        self.adapter.vm, self.adapter.find_first = self.vm, None
        # A resource VM already owns its qualified CRT adapter. Never install
        # a second handler that would consume the same call twice.
        if vm is None:
            self.vm.hook_add(uc.UC_HOOK_CODE, self._decimal,
                             begin=self.BASE + 0x1480b4, end=self.BASE + 0x1480b4)
        self.columns = []
        self.vm.hook_add(uc.UC_HOOK_CODE, self._column,
                         begin=self.BASE + 0x51b60, end=self.BASE + 0x51b60)
        self.allowed = None
        self.writes = []
        self.write_hook = self.vm.hook_add(uc.UC_HOOK_MEM_WRITE, self._write)

    def reg(self, name, value):
        self.vm.reg_write(getattr(self.x86, 'UC_X86_REG_' + name), value)

    def _decimal(self, vm, address, size, context):
        sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
        if struct.unpack('<I', vm.mem_read(sp, 4))[0] != self.BASE + 0x51bc9:
            raise AssertionError('Unexpected decimal adapter caller')
        self.adapter._crt(vm, address, size, context)

    def _column(self, vm, address, size, context):
        sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
        self.columns.append(struct.unpack('<I', vm.mem_read(sp + 4, 4))[0])

    def _write(self, vm, access, address, size, value, context):
        if self.allowed is None or self.STACK <= address < address + size <= self.STACK + 0x10000:
            return
        if not any(start <= address < address + size <= end for start, end in self.allowed):
            raise AssertionError(f'Unexpected native row write: {address:x}+{size}')
        self.writes.append((address, size))

    def run(self, start, stop):
        target = self.BASE + stop
        hook = self.vm.hook_add(self.uc.UC_HOOK_CODE, lambda vm, a, s, c: vm.emu_stop(),
                                begin=target, end=target)
        try:
            self.vm.emu_start(self.BASE + start, target, count=50000, timeout=1000000)
        finally:
            self.vm.hook_del(hook)
        if self.vm.reg_read(self.x86.UC_X86_REG_EIP) != target:
            raise AssertionError('Native row did not reach exact stop')

    def tokenize(self, row, width):
        raw = bytes.fromhex(row['raw_record_hex']).replace(b'\r\n', b'\n')
        if not raw.endswith(b'\n') or len(raw) >= 2048 or any(len(f) >= 380 for f in fields(row)):
            raise ValueError('Source outside native tokenizer bounds')
        self.allowed = None
        self.vm.mem_write(self.INPUT, raw + b'\0')
        self.vm.mem_protect(self.INPUT, 4096, self.uc.UC_PROT_READ)
        self.vm.mem_write(self.TABLE + 8, struct.pack('<H', width))
        self.vm.mem_write(self.SP, struct.pack('<II', self.RETURN, self.INPUT))
        self.reg('ESP', self.SP)
        self.reg('ECX', self.TABLE)
        self.run(0x51be0, self.RETURN - self.BASE)
        if self.vm.reg_read(self.x86.UC_X86_REG_ESP) != self.SP + 8:
            raise AssertionError('Tokenizer stack imbalance')
        self.vm.mem_protect(self.INPUT, 4096, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        self.reg('ESP', self.SP)
        self.columns.clear()
        self.writes.clear()

    def row(self, start, stop, columns, allowed):
        self.allowed = allowed
        try:
            self.run(start, stop)
        finally:
            self.allowed = None
        if self.vm.reg_read(self.x86.UC_X86_REG_ESP) != self.SP:
            raise AssertionError('Row slice stack imbalance')
        if set(self.columns) != set(columns) or not self.writes:
            raise AssertionError('Native row field access/write mismatch')


def verify_native_rows(image_path, decoded):
    """Recheck original decoded bytes; derived caller records are not authority.

    Dispatch references are statically bound; only tokenizer/accessor/row slices
    execute. Allocation, file I/O, full dispatch, upgrades and UI do not execute.
    """
    for name in ('gamedata', 'NewCombatPet_Category', 'NewCombatPet_QualityStar'):
        if digest(decoded[name]) != SOURCE_HASHES[name][1]:
            raise ValueError('Unqualified native row source: ' + name)
    sections = parse_sections(decoded['gamedata'], ('GodLevel',))
    auxiliary = {name: parse_auxiliary(name, decoded[name])
                 for name in ('NewCombatPet_Category', 'NewCombatPet_QualityStar')}
    image_path = Path(image_path)
    image = read_source(image_path.parent, image_path.name)
    if digest(image) != IMAGE_SHA:
        raise ValueError('Unqualified current native image')
    bindings = (
        ('GodLevel', 0x5668d, 0x18a064, 0x566cd, 0x5a880),
        ('CategoryDetailNum', 0x56ac1, 0x189fa0, 0x56b01, 0x5c640),
        ('QualityValue', 0x56b0c, 0x189f90, 0x56b47, 0x5ca70),
        ('StarValue', 0x56b52, 0x189f84, 0x56b8d, 0x5cad0),
    )
    for tag, operand, string_rva, call, target in bindings:
        if (struct.unpack_from('<I', image, operand)[0] != 0x400000 + string_rva or
                image[string_rva:string_rva + len(tag) + 1] != tag.encode() + b'\0' or
                image[call] != 0xe8 or
                call + 5 + struct.unpack_from('<i', image, call + 1)[0] != target):
            raise AssertionError('Native dispatch reference changed: ' + tag)
    probe = _NativeRows(image)
    vm, table, output = probe.vm, probe.TABLE, probe.OUTPUT
    titles = sections['GodLevel']['records']
    expected = bytearray(b'\xa5' * (4 * 94))
    vm.mem_write(table + 0xd2aca, bytes(expected))
    for row in titles:
        label, code = fields(row)
        index = decimal(code) - 1
        if not 0 <= index < 4 or len(label) >= 94:
            raise ValueError('GodLevel row outside qualified native bounds')
        probe.tokenize(row, 2)
        probe.reg('ESI', table)
        start = table + 0xd2aca + index * 94
        probe.row(0x5a8a4, 0x5a8dd, (0, 1), [(start, start + len(label) + 1)])
        expected[index * 94:index * 94 + len(label) + 1] = label + b'\0'
        if bytes(vm.mem_read(table + 0xd2aca, len(expected))) != expected:
            raise AssertionError('GodLevel native bytes differ')
    title_sha = digest(bytes(expected))

    category = auxiliary['NewCombatPet_Category']['records']
    expected = bytearray(b'\xa5' * 0x4000)
    vm.mem_write(output, bytes(expected))
    vm.mem_write(table + 0xfc2c4, struct.pack('<I', output))
    vm.mem_write(table + 0xfc2c8, b'\0\0')  # Explicit synthetic row counter.
    for count, row in enumerate(category, 1):
        values = fields(row)
        index = (decimal(values[0]) - 1) * 16 + decimal(values[1])
        label = values[2]
        if len(label) >= 16:
            raise ValueError('Category name exceeds native row name field')
        probe.tokenize(row, 12)
        probe.reg('EBP', table)
        probe.reg('EBX', 0)
        vm.mem_write(probe.SP, bytes(0x80))  # Original function's local scratch.
        start = output + index * 22
        allowed = [(start, start + len(label) + 1), (table + 0xfc2c8, table + 0xfc2ca)]
        for column, token in enumerate(values[3:9]):
            if token == b'Y':
                allowed.append((start + 16 + column, start + 17 + column))
                expected[index * 22 + 16 + column] = 1
        probe.row(0x5c6a6, 0x5c9b5, range(9), allowed)
        expected[index * 22:index * 22 + len(label) + 1] = label + b'\0'
        if (bytes(vm.mem_read(output, len(expected))) != expected or
                struct.unpack('<H', vm.mem_read(table + 0xfc2c8, 2))[0] != count):
            raise AssertionError('Category native bytes/counter differ')
    category_sha = digest(bytes(expected))

    quality_result = {}
    for row, label, pointer, start, stop in zip(
            auxiliary['NewCombatPet_QualityStar']['records'], ('QualityValue', 'StarValue'),
            (0xfc2cc, 0xfc2d0), (0x5ca92, 0x5caf2), (0x5caaf, 0x5cb0f)):
        expected = struct.pack('<16H', *(decimal(v) for v in fields(row))) + b'\xa5\xa5'
        vm.mem_write(output, b'\xa5' * 34)
        vm.mem_write(table + pointer, struct.pack('<I', output))
        probe.tokenize(row, 16)
        probe.reg('EDI', table)
        probe.row(start, stop, range(16), [(output, output + 32)])
        if bytes(vm.mem_read(output, 34)) != expected:
            raise AssertionError('Quality/star native bytes or canary differ')
        quality_result[label] = {'word_count': 16, 'stored_bytes_sha256': digest(expected[:32])}
    adapter = Path(__file__).with_name('current_npc_resources.py')
    return {
        'status': 'verified_bounded_original_row_execution', 'image_sha256': IMAGE_SHA,
        'growth_formula_verified': False, 'gameplay_runtime_verified': False,
        'GodLevel': {'rows': len(titles), 'stride': 94, 'poisoned_state_sha256': title_sha,
                     'contract': 'Column 1 minus one selects title slot for current codes 1..4; column 0 copied'},
        'CategoryDetailNum': {
            'rows': len(category), 'stride': 22, 'poisoned_state_sha256': category_sha,
            'consumed_columns': list(range(9)), 'unconsumed_columns': [9, 10, 11],
            'contract': 'Name at +0; Y in columns 3..8 sets +16..21 to 1; N preserves supplied bytes'},
        'quality_star': quality_result,
        'static_dispatch_bindings': {tag: {'string_rva': string_rva, 'call_rva': call,
                                           'loader_rva': target, 'dispatch_executed': False}
                                    for tag, _, string_rva, call, target in bindings},
        'code_ranges': {name: {'start_rva': start, 'stop_rva_exclusive': stop,
                              'sha256': digest(image[start:stop])}
                        for name, (start, stop) in NATIVE_RANGES.items()},
        'adapter': {'path': 'tools/strike_lab/current_npc_resources.py',
                    'sha256': digest(adapter.read_bytes()), 'service': 'CRT %d sscanf at RVA 1480B4 only'},
        'execution_boundary': 'Original tokenizer, accessors and row slices; dispatch references are static. '
                              'Synthetic pointers, scratch and A5 poison. No allocator, file loader, UI, '
                              'packet consumer, stat upgrade, EXP calculation or live process executed.',
        'per_call_limits': {'instructions': 50000, 'timeout_microseconds': 1000000},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--native-image', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--summary', action='store_true', help='Print compact JSON, no file required')
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error('--check requires --output')
    if args.output is not None:
        target = args.output.resolve()
        if target.is_relative_to(args.client_root.resolve()) or (
                args.native_image is not None and target == args.native_image.resolve()):
            parser.error('Output must not overwrite current-client evidence')
    result = build_growth(args.client_root, args.native_image)
    encoded = serialize(result)
    if args.output is not None:
        if args.check:
            if args.output.read_bytes() != encoded:
                raise SystemExit('Artifact differs')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(encoded)
    if args.summary or args.output is not None:
        print(serialize({'sha256': digest(encoded), 'checked': args.check,
                         'sources': len(result['sources']),
                         'section_counts': {n: s['declared_count'] for n, s in result['sections'].items()},
                         'auxiliary_counts': {n: s['actual_record_count']
                                              for n, s in result['auxiliary_tables'].items()},
                         'native_verification': result['native_verification'],
                         'unknown_contracts': result['unknown_contracts']}).decode('ascii'), end='')
    else:
        print(encoded.decode('ascii'), end='')


if __name__ == '__main__':
    main()
