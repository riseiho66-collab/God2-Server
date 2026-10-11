"""Bounded RTB/MDL source-to-native evidence; stdout only, no monster promotion."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz
from .current_battle_entry import NativeRun, BASE, SP, RETURN
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
RTBS = (CLIENT / 'Data2/Fight/Spg/spg9001.rtb', CLIENT / 'Data3/fight/spg/spg9184.rtb')
MDL = CLIENT / 'Data2/map/island01/Island01.mdlZ'
MDL_SHA = '88349e73e0baa95ca773dc54641a23d1baa19dbef25b3313866980ccbde6fce2'
PINS = {
    IMAGE: (3174400, IMAGE_SHA),
    RTBS[0]: (1558, 'f5846a76370cd14ce1f260153bf377db5e1c24fa1fd4311318037721c309fd15'),
    RTBS[1]: (2330, '860681bce02d0c57aaf634ace5332f3a4f28861113d98a95cd69896b6d111af2'),
    MDL: (106825, 'cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d'),
}
MAX_BYTES = 4 << 20
FIELDS = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
          'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
          'metal', 'wood', 'water', 'fire', 'earth', 'base_experience', 'capturable')
SPANS = {
    'rtb_writer_static_only': (0x2f1f0, 0x2f323, '5852f3e607e2e7ef7946b9384e7f82572e1a1805af7d628a1b64c40f9abb475c'),
    'rtb_text_converter_static_only': (0x2ed93, 0x2eec3, '934d0ca65b9a3af0d76f177fc460e1ec3b81be2460186407ef4a9a041b401d06'),
    'rtb_path': (0x2e211, 0x2e27b, 'd28b2cd7a77f2abb5f6e43dc986232aaea1449d9f6ac287f8c3978e9829bcc65'),
    'rtb_reader': (0x2f330, 0x2f50d, '16df7c00666ca1cbac7e7247067af3eb771ffd244c9df1282e03eaaaefff77c7'),
    'rtb_allocator': (0x2d930, 0x2d954, 'e2fc08f32c9f2f6cd46d9bf250d5e4c117eb141b331df00fa923e0aa40ffd74e'),
    'pool_allocator': (0x28740, 0x28877, 'ac69740d1c4709309b810417a72c5478067bf6b7b949d557f1bd80be087fae4d'),
    'rtb_resource': (0x2f7ea, 0x2f83c, 'b0e79e890ceda18e139c49078aa46cbf3b64c04f8a58b9b9fcf3a45ba3ee8d3c'),
    'rtb_frame_index': (0x30839, 0x30864, '2710e3b777fe88b8093b6c42bb5203d03a78f8555fbda64c1114b81b43fe1960'),
    'rtb_frame_render': (0x30864, 0x30a30, '1bf8a8cbabca536904c1f72853ce28cee4e26cc1faa22ed85ec0f7a7b7941510'),
    'render_move': (0x1dbc0, 0x1dce2, '0e50bd4e7389fb9049d5058025092fe41a422b6fc4c6128ab40742cca787d60a'),
    'render_scalar': (0x1df60, 0x1dfae, '3cc387cadca5280d8872e210f0a7c4ec1ec8bc735ab56e3bb61a2859d5b689b1'),
    'renderer_scalar_store': (0x26fe0, 0x2701d, '6a50a9e2095bf25c450cae3baf5f68505b2c6e708ab46ed889d2f6ff76eff30e'),
    'mdl_path': (0x3cef1, 0x3cf33, '0590a4fc982b04b106457dbc141a2d335780ba79c92bfd40a6020b48a424799d'),
    'mdl_dispatch': (0x3d420, 0x3d656, '49749e2f2c3aaacc8d0dc39a984f87d57cfb6b0d811ce475a29ee82c5940df34'),
    'model_catalog_reader': (0x4d750, 0x4d97b, '300fc9c58d802277592e537da12b6156df3e3ca4962fc66e2c8d47cb632ae69e'),
    'tile_reader': (0x4c420, 0x4c6c4, 'ba72a006550581e43c11cefbb98f1d87e31051dcc191e812d25916a14800e3a9'),
    'model_reader': (0x4c980, 0x4ce6b, '13a93ee79dbc667cc8517ff66ba369a420c23f6368ebb45b85ab00bb834458e1'),
    'model_lookup': (0x4c6f0, 0x4c735, 'b50cb2284a540a53d2bca54c2bb4706ec8624bc3e0475fa5d016ca0193b86e79'),
    'placement_reader': (0x3ee20, 0x3f1b4, 'a2008cc79a211947f6bbb137ee34447036f23e130c3064f6d0e8f9b83d3c551f'),
    'placement_setter': (0x41fc0, 0x41fe6, 'cad694e87fe3fe9862fffc07dbf7df9b4e3ff9ea7e5eec08a7a8667d8a87e7c7'),
    'attachment_setter_static_only': (0x37540, 0x3758c, 'e6136c59405b6da2fe3358c0ddfd95c1eb3002af97436a5e43a95f09f26b9815'),
    'placement_render_static_only': (0x42213, 0x422d0, 'af5feeabbdb304f58f79b952e93a76d874d2df45f17b0b9cffaa2c6ed7ee249b'),
    'model_action_static_only': (0x41ec0, 0x41f90, '42b33aa13d6cf5497401acb02c29d65cd974c3e7ab9c1acb4d19c27e241bd45c'),
}
CALLS = ((0x2e259, 0x2f330), (0x2f37d, 0x14785c), (0x2f422, 0x14785c),
         (0x2f48b, 0x14785c), (0x2f3ef, 0x2d930), (0x2f455, 0x2d930),
         (0x2d93e, 0x28740), (0x2f81d, 0x1ae20), (0x2fce9, 0x1afe0),
         (0x309d8, 0x1dbc0), (0x309ec, 0x1df60), (0x1dfa6, 0x26fe0),
         (0x3cf2e, 0x3d420), (0x3d587, 0x4d750), (0x3d5c6, 0x3ee20),
         (0x4d7da, 0x4d520), (0x4d8e5, 0x4c420), (0x4d95e, 0x4c980),
         (0x4ca1f, 0x4c050), (0x4cd1d, 0x41730), (0x3ef35, 0x4c6f0),
         (0x3ef6a, 0x38920), (0x38986, 0x41fc0), (0x3f041, 0x37540),
         (0x42246, 0x41ec0), (0x41f08, 0x4a0f0),
         (0x2f2b3, 0x1474e7), (0x2f2c4, 0x1474e7), (0x2f2e5, 0x1474e7))
LITERALS = ((0x187120, b'rtbv1.0', 0x2f386), (0x182350, b'rb', 0x2f34d),
            (0x187d24, b'.mdl', 0x3cef2), (0x187de4, b'MDL', 0x3d4d2),
            (0x188bbc, b'ROMFILE', 0x4d7aa), (0x188b9c, b'TileModel', 0x4d884),
            (0x188b90, b'ModelDat', 0x4d908),
            (0x188a6c, b'nModelDatIdx < m_nTotalModelDat || m_nTotalModelDat==0', 0x4c70e),
            (0x1877cc, b'%d %d %d %d %d %d', 0x3eeac),
            (0x186f98, b'Transparency:', 0x2ed94),
            (0x186f80, b'visible_anim:', 0x2ee46),
            (0x188344, b'pTile->GetTileType()==TileType_Action', 0x41ed5))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pinned(path):
    path = Path(path)
    if path not in PINS:
        raise ValueError('Only the fixed image, two RTBs and one MDLZ may be opened')
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse source rejected')
    size, digest = PINS[path]
    if path.stat().st_size != size or size > MAX_BYTES:
        raise ValueError('Pinned size changed')
    with path.open('rb') as stream:
        raw = stream.read(size + 1)
    if len(raw) != size or sha(raw) != digest:
        raise ValueError('Pinned hash changed')
    return raw


def native_evidence(image):
    if sha(image) != IMAGE_SHA:
        raise ValueError('Pinned image changed')
    for name, (start, end, digest) in SPANS.items():
        if sha(image[start:end]) != digest:
            raise ValueError('Native span changed: ' + name)
    for call, target in CALLS:
        if image[call] != 0xe8 or call + 5 + struct.unpack_from('<i', image, call + 1)[0] != target:
            raise ValueError('Native call changed')
    for address, value, operand in LITERALS:
        if (image[address:address + len(value) + 1] != value + b'\0'
                or struct.unpack_from('<I', image, operand)[0] != BASE + address):
            raise ValueError('Native literal changed')
    return {'base': BASE, 'rva_equals_file_offset': True, 'sha256': IMAGE_SHA,
            'spans': {name: {'start': a, 'end_exclusive': z, 'sha256': h}
                      for name, (a, z, h) in SPANS.items()},
            'calls': [{'rva': a, 'target_rva': z} for a, z in CALLS],
            'literals': [{'rva': a, 'value': s.decode(), 'operand_rva': p} for a, s, p in LITERALS]}


def parse_rtb(raw):
    if type(raw) is not bytes or not 14 <= len(raw) <= MAX_BYTES or raw[:8] != b'rtbv1.0\0':
        raise ValueError('Expected bounded rtbv1.0 source')
    objects, frames, flag0, flag1 = struct.unpack_from('<hhBB', raw, 8)
    if not 1 <= objects <= 256 or not 1 <= frames <= 4096:
        raise ValueError('RTB counts outside analysis bounds')
    table_end = 14 + objects * 52
    if len(raw) != table_end + objects * frames * 12:
        raise ValueError('RTB truncated or has unaccounted bytes')
    records = []
    for index in range(objects):
        offset = 14 + index * 52
        frame_start = table_end + index * frames * 12
        record = raw[offset:offset + 52]
        records.append({'index': index, 'offset': offset, 'end_exclusive': offset + 52,
                        'sha256': sha(record), 'raw_hex': record.hex(),
                        'resource_word_0': struct.unpack_from('<h', record)[0],
                        'serialized_pointer_48': struct.unpack_from('<I', record, 48)[0],
                        'frames_start': frame_start, 'frames_end': frame_start + frames * 12,
                        'frames_sha256': sha(raw[frame_start:frame_start + frames * 12])})
    return {'objects': objects, 'frames_per_object': frames, 'header_flags_raw': [flag0, flag1],
            'table_start': 14, 'table_end': table_end, 'records': records,
            'end_exclusive': len(raw), 'unaccounted_bytes': 0}


def parse_mdl(raw, *, allow_parent_rom=False):
    """Strict observed v1.6 grammar; raw line offsets include original CRLF."""
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_BYTES or b'\0' in raw:
        raise ValueError('Invalid MDL source')
    lines = raw.splitlines(keepends=True)
    if len(lines) > 50000 or any(not row.endswith(b'\r\n') or len(row) > 4096 for row in lines):
        raise ValueError('MDL line bounds or CRLF changed')
    offsets, cursor = [], 0
    for row in lines:
        offsets.append(cursor)
        cursor += len(row)
    at, regions = 0, []

    def line():
        nonlocal at
        if at >= len(lines):
            raise ValueError('Truncated MDL')
        value = lines[at][:-2]
        at += 1
        return value

    def nums(value, count=None):
        tokens = value.split()
        if (count is not None and len(tokens) != count) or not tokens:
            raise ValueError('MDL numeric width changed')
        if any(not re.fullmatch(rb'-?[0-9]{1,10}', token) for token in tokens):
            raise ValueError('MDL decimal token invalid')
        values = [int(token) for token in tokens]
        if any(not -0x80000000 <= v <= 0x7fffffff for v in values):
            raise ValueError('MDL integer out of bounds')
        return values

    def section(name, maximum):
        parts = line().split()
        if len(parts) != 2 or parts[0] != name:
            raise ValueError('Expected MDL ' + name.decode())
        count = nums(parts[1], 1)[0]
        if not 1 <= count <= maximum:
            raise ValueError('MDL section count bound')
        return count

    def region(name, first):
        start, end = offsets[first], offsets[at] if at < len(lines) else len(raw)
        regions.append({'name': name, 'start': start, 'end_exclusive': end,
                        'sha256': sha(raw[start:end])})

    if line() != b'MDL v1.6':
        raise ValueError('Only observed MDL v1.6 is qualified')
    region('header', 0)
    first = at
    roms = [line() for _ in range(section(b'ROMFILE', 128))]
    # Explicit analysis-only option: current44D520 reads%s and the native
    #55AF26 concatenation preserves these bounded source path tokens verbatim.
    #References are never opened; default simple-basename grammar is unchanged.
    # North001's literal FM'.ROM is also preserved as data, never shell text.
    rom_pattern = (rb"(?:\.\.\\){0,2}(?:[A-Za-z0-9_-]+\\){0,4}[A-Za-z0-9_'-]+\.[Rr][Oo][Mm]" if allow_parent_rom
                   else rb'[A-Za-z0-9_]+\.[Rr][Oo][Mm]')
    if any(len(value) >= 260 or not re.fullmatch(rom_pattern, value) for value in roms):
        raise ValueError('Unexpected ROM reference; references are never opened')
    region('ROMFILE', first)
    first = at
    tiles = []
    for _ in range(section(b'TileModel', 512)):
        row_offset = offsets[at]
        parts = line().split()
        if len(parts) != 6:
            raise ValueError('MDL tile width')
        values = nums(b' '.join(parts[1:]), 5)
        if not 0 <= values[3] < len(roms):
            raise ValueError('MDL ROM index')
        tiles.append({'offset': row_offset, 'name_hex': parts[0].hex(), 'fields': values})
    region('TileModel', first)
    first = at
    models = []
    cells_total = 0
    for _ in range(section(b'ModelDat', 512)):
        row_offset = offsets[at]
        layers = [nums(line(), 3) for _ in range(3)]
        if any(not -1 <= layer[0] < len(tiles) for layer in layers):
            raise ValueError('MDL layer reference')
        frames = nums(line())
        if not 1 <= frames[0] <= 10 or len(frames) != 1 + frames[0] * 2:
            raise ValueError('MDL frame offsets')
        extras = nums(line(), 8)
        if line() != b'Pass':
            raise ValueError('MDL Pass marker')
        grids = []
        for _ in range(frames[0]):
            width, height = nums(line(), 2)
            # Current44C980 ->441880 accepts zero dimensions and calls441730
            # only inside both positive loops. CityI2 has literal0x2 followed
            # by two empty rows; retain and validate those source rows.
            if not 0 <= width <= 512 or not 0 <= height <= 512:
                raise ValueError('MDL Pass dimensions')
            cells_total += width * height
            if cells_total > 1_000_000:
                raise ValueError('MDL aggregate cell bound')
            grid_start = offsets[at]
            for _ in range(height):
                row = line()
                if width == 0:
                    if row.split():
                        raise ValueError('Nonempty zero-width MDL Pass row')
                    continue
                if any(not 0 <= v <= 255 for v in nums(row, width)):
                    raise ValueError('MDL Pass byte range')
            grids.append({'width': width, 'height': height, 'start': grid_start,
                          'end_exclusive': offsets[at] if at < len(lines) else len(raw)})
        models.append({'offset': row_offset, 'layers': layers, 'frame_offsets': frames[1:],
                       'extra_8_ints': extras, 'grids': grids})
    region('ModelDat', first)
    first = at
    if line() != b'Model':
        raise ValueError('MDL Model marker')
    groups, placements = [], []
    while at < len(lines):
        group_offset = offsets[at]
        x, y, count = nums(line(), 3)
        if not 0 <= x < 128 or not 0 <= y < 128 or not 1 <= count <= 4096:
            raise ValueError('MDL block bound')
        groups.append({'offset': group_offset, 'x': x, 'y': y, 'count': count})
        for _ in range(count):
            if len(placements) >= 20000:
                raise ValueError('MDL placement bound')
            row_offset = offsets[at]
            row = line()
            parts = row.split()
            if len(parts) not in (10, 11):
                raise ValueError('MDL placement width')
            prefix = nums(b' '.join(parts[:9]), 9)
            attached = None
            if prefix[8] == 1:
                if len(parts) != 11 or not re.fullmatch(rb'[A-Za-z0-9_\\./-]{1,255}', parts[9]):
                    raise ValueError('MDL attached reference shape')
                attached = parts[9].decode('ascii')
            elif prefix[8] != 0 or len(parts) != 10:
                raise ValueError('MDL attachment flag')
            values = prefix + nums(parts[-1], 1)
            if not 0 <= values[0] < len(models):
                raise ValueError('MDL ModelDat index')
            if not 0 <= values[5] < len(models[values[0]]['grids']):
                raise ValueError('MDL frame index')
            placements.append({'offset': row_offset, 'end_exclusive': row_offset + len(row) + 2,
                               'sha256': sha(row + b'\r\n'), 'block': [x, y], 'fields': values,
                               'attached_reference': attached})
    region('Model', first)
    return {'format': 'MDL v1.6', 'regions': regions, 'rom_references': [r.decode() for r in roms],
            'tiles': tiles, 'models': models, 'groups': groups, 'placements': placements,
            'pass_cells': cells_total, 'unaccounted_bytes': len(raw) - regions[-1]['end_exclusive']}


def crt_return(n, value):
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    ret = n.get32(sp)
    n.registers(eax=value & 0xffffffff, esp=sp + 4)
    return ret - BASE


def native_rtb(image, raw):
    """Full 2F330 reader and original pool allocation, virtual CRT input only."""
    if sha(raw) not in {PINS[p][1] for p in RTBS}:
        raise ValueError('Execution requires pinned RTB bytes')
    layout = parse_rtb(raw)
    n = NativeRun(image)
    owner, allocator, slab, path = 0x3400000, 0x3600000, 0x3a00000, 0x3b00000
    record = owner + 0xa1040
    handle = 0x80010000
    n.map(owner, 0xa7000)
    n.map(allocator + 0x2a2800, 0x1000)
    n.put32(owner + 0xa6550, allocator)
    pool = allocator + 0x2a2800
    allocation_size = len(raw) - 14
    n.put32(pool + 4, slab)
    n.put32(pool + 8, 0)
    n.put32(pool + 12, allocation_size)
    n.put32(pool + 0x304, 0)
    n.put(slab - 16, b'\xa5' * 16 + b'\xcc' * allocation_size + b'\xa5' * 16)
    virtual_path = b'fixed-source.rtb\0'
    n.put(path, virtual_path)
    n.put(SP, struct.pack('<III', RETURN, 0, path))
    n.registers(ecx=owner, esp=SP)
    ranges = [(0x2f330, 0x2f50d), (0x2d930, 0x2d954), (0x28740, 0x28877)]
    stops = {0x14716f, 0x14785c, 0x147182}
    pc, position, opened, closed, io = 0x2f330, 0, False, False, []
    expected_reads = [(14, 1), (52, layout['objects'])] + [(12, layout['frames_per_object'])] * layout['objects']
    for _ in range(len(expected_reads) + 3):
        n.run(pc, ranges, stops, budget=20000)
        if n.stop == RETURN:
            break
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        if n.stop == 0x14716f:
            if opened or n.get32(sp + 4) != path or n.get32(sp + 8) != BASE + 0x182350:
                raise AssertionError('Unexpected fopen')
            opened = True
            pc = crt_return(n, handle)
        elif n.stop == 0x14785c:
            dest, size, count, file_handle = (n.get32(sp + i) for i in (4, 8, 12, 16))
            if (not opened or closed or file_handle != handle
                    or len(io) >= len(expected_reads) or (size, count) != expected_reads[len(io)]):
                raise AssertionError('Unexpected fread shape')
            length = size * count
            if position + length > len(raw):
                raise AssertionError('Read beyond source')
            if len(io) and not slab <= dest <= slab + allocation_size - length:
                raise AssertionError('Read beyond native slab')
            n.put(dest, raw[position:position + length])
            io.append({'source_offset': position, 'size': size, 'count': count,
                       'destination': dest, 'sha256': sha(raw[position:position + length])})
            position += length
            pc = crt_return(n, count)
        elif n.stop == 0x147182:
            if not opened or closed or position != len(raw) or n.get32(sp + 4) != handle:
                raise AssertionError('Unexpected fclose')
            closed = True
            pc = crt_return(n, 0)
    if (n.stop != RETURN or n.vm.reg_read(UC_X86_REG_EAX) & 0xffff
            or n.vm.reg_read(UC_X86_REG_ESP) != SP + 12 or not closed
            or len(io) != len(expected_reads) or n.get32(record + 8) != slab
            or bytes(n.vm.mem_read(record + 2, 4)) != raw[8:12]
            or bytes(n.vm.mem_read(record + 12, 2)) != raw[12:14]):
        raise AssertionError('RTB reader output or stack mismatch')
    for rec in layout['records']:
        address = slab + rec['index'] * 52
        frame_ptr = slab + layout['objects'] * 52 + rec['index'] * layout['frames_per_object'] * 12
        if (bytes(n.vm.mem_read(address, 48)) != raw[rec['offset']:rec['offset'] + 48]
                or n.get32(address + 48) != frame_ptr
                or bytes(n.vm.mem_read(frame_ptr, layout['frames_per_object'] * 12))
                != raw[rec['frames_start']:rec['frames_end']]):
            raise AssertionError('RTB records differ from native output')
    if (n.get32(pool + 8) != allocation_size
            or bytes(n.vm.mem_read(slab - 16, 16)) != b'\xa5' * 16
            or bytes(n.vm.mem_read(slab + allocation_size, 16)) != b'\xa5' * 16):
        raise AssertionError('RTB allocation/guard mismatch')
    return n, layout, {'return_slot': 0, 'instruction_count': len(n.visits),
                       'io': io, 'all_source_bytes_read': position, 'handle_closed': closed,
                       'original_allocators_executed': [0x2d930, 0x28740],
                       'serialized_pointers_replaced': layout['objects']}


def rtb_frame_consumers(n, raw, layout):
    """Reuse native-loaded records; stage playback context, stop before movement call."""
    owner, record, output = 0x3400000, 0x34a1040, []
    active, instance, resource_manager, renderer = 0x3b01000, 0x3b02000, 0x3c00000, 0x3d00000
    n.map(instance, 0x1000)
    n.map(resource_manager, 0x1000)
    n.map(renderer, 0x2000)
    n.put32(owner + 0xa654c, resource_manager)
    n.put32(resource_manager + 4, renderer)
    n.put(resource_manager + 0x1e, struct.pack('<H', 0))
    for rec in layout['records']:
        for frame in (0, 1, layout['frames_per_object'] - 1, layout['frames_per_object'] + 1):
            n.put(active, struct.pack('<h', frame))
            n.put32(SP + 0x18, rec['index'] * 52)
            n.put(instance + 2, b'\0\0')
            n.registers(esp=SP, edx=record, ebx=active, esi=instance, ebp=owner)
            n.run(0x30839, [(0x30839, 0x30864)], {0x30864}, budget=100)
            frame_ptr = n.vm.reg_read(UC_X86_REG_EBX)
            source_offset = rec['frames_start'] + frame % layout['frames_per_object'] * 12
            frame_bytes = raw[source_offset:source_offset + 12]
            if bytes(n.vm.mem_read(frame_ptr, 12)) != frame_bytes:
                raise AssertionError('Native modulo frame selection mismatch')
            n.run(0x30993, [(0x30993, 0x309dd)], {0x1dbc0}, budget=100)
            call_sp = n.vm.reg_read(UC_X86_REG_ESP)
            args = [n.get32(call_sp + off) for off in (4, 8, 12)]
            x, y = struct.unpack_from('<hh', frame_bytes)
            if args != [resource_manager + 0x10, x & 0xffffffff, y & 0xffffffff]:
                raise AssertionError('Frame movement arguments mismatch')
            # Independent scalar island, not a simulated return from movement.
            n.put32(SP, RETURN)
            n.registers(esp=SP, ebx=frame_ptr, esi=instance, ebp=owner)
            n.run(0x309dd, [(0x309dd, 0x309f1), (0x1df60, 0x1dfae),
                           (0x26fe0, 0x2701d)], {0x309f1}, budget=100)
            scalar = bytes(n.vm.mem_read(renderer + 0x12e8, 4))
            if scalar != frame_bytes[4:8] or n.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Frame renderer scalar mismatch')
            output.append({'object': rec['index'], 'playback_frame_fixture': frame,
                           'source_offset': source_offset, 'frame_hex': frame_bytes.hex(),
                           'movement_arguments': [x, y], 'renderer_scalar_hex': scalar.hex()})
    return output


def native_mdl_placement(image, placement, model_count):
    """Original row argument flow plus model lookup; no model/ROM load claimed."""
    values = placement['fields']
    if (type(model_count) is not int or not 1 <= model_count <= 512
            or len(values) != 10 or any(type(v) is not int or not -0x80000000 <= v <= 0x7fffffff for v in values)
            or not 0 <= values[0] < model_count or len(placement['block']) != 2
            or any(type(v) is not int or not 0 <= v < 128 for v in placement['block'])):
        raise ValueError('Bounded source placement required')
    n = NativeRun(image)
    owner, table, models, version = 0x3400000, 0x3500000, 0x3600000, 0x3700000
    handle = 0x80010000
    n.map(owner, 0x2000)
    n.put32(owner + 0x1220 + 0x14, model_count)
    n.put32(owner + 0x1220 + 0x10, table)
    n.put(table, b''.join(struct.pack('<I', models + i * 0x200) for i in range(model_count)))
    n.put(version, b'v1.6\0')
    n.put32(SP + 0x274, version)
    n.put32(SP + 0x14, placement['block'][0])
    n.put32(SP + 0x10, placement['block'][1])
    n.registers(esp=SP, ebp=owner, ebx=handle)
    n.run(0x3ee8d, [(0x3ee8d, 0x3ef6f)], {0x1490ad}, budget=100)
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    if n.get32(sp + 4) != handle or n.get32(sp + 8) != BASE + 0x1877cc:
        raise AssertionError('Unexpected placement fscanf')
    destinations = [n.get32(sp + 12 + i * 4) for i in range(6)]
    for dest, value in zip(destinations, values[:6]):
        if not SP <= dest <= SP + 0x50:
            raise AssertionError('Unexpected scanf destination')
        n.put32(dest, value & 0xffffffff)
    pc = crt_return(n, 6)
    # The two older-version coordinate-conversion checks precede this lookup.
    compared = []
    for _ in range(3):
        n.run(pc, [(0x3ee8d, 0x3ef6f), (0x4c6f0, 0x4c735)], {0x149a00, 0x38920}, budget=300)
        if n.stop == 0x38920:
            break
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        first, second = n.get32(sp + 4), n.get32(sp + 8)
        if first != version or second not in (BASE + 0x1877c4, BASE + 0x187cc8):
            raise AssertionError('Unexpected version comparison')
        token = image[second - BASE:second - BASE + 4]
        if token not in (b'v1.2', b'v1.1'):
            raise AssertionError('Unqualified version token')
        compared.append(token.decode())
        pc = crt_return(n, 1)
    if n.stop != 0x38920:
        raise AssertionError('Placement constructor call not reached')
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    args = [n.get32(sp + 4 + i * 4) for i in range(7)]
    expected = [*placement['block'], *values[1:5], models + values[0] * 0x200]
    if args != expected:
        raise AssertionError(('Placement argument mismatch', args, expected))
    count = len(n.visits)
    # Independent original initializer. Model pointers are explicit lookup fixtures.
    instance = 0x3800000
    n.put(instance - 16, b'\xa5' * 16 + b'\xcc' * 0x50 + b'\xa5' * 16)
    n.put(SP, struct.pack('<6I', RETURN, *args[2:]))
    n.registers(ecx=instance, esp=SP)
    n.run(0x41fc0, [(0x41fc0, 0x41fe6)], set(), budget=50)
    actual = [n.get32(instance + off) for off in (0xc, 0x10, 0x14, 0x18, 0x2c)]
    if (actual != args[2:] or n.vm.reg_read(UC_X86_REG_ESP) != SP + 24
            or bytes(n.vm.mem_read(instance - 16, 16)) != b'\xa5' * 16
            or bytes(n.vm.mem_read(instance + 0x50, 16)) != b'\xa5' * 16):
        raise AssertionError('Placement initializer mismatch')
    initializer_count = len(n.visits) - count
    # Separate store islands with source-derived post-fscanf locals, not constructor continuation.
    n.put32(SP + 0x40, values[5])
    n.registers(esp=SP, eax=instance)
    n.run(0x3ef6f, [(0x3ef6f, 0x3ef7d)], {0x3ef7d}, budget=20)
    for offset, value in ((0x60, values[6]), (0x5c, values[7]), (0x48, values[8])):
        n.put32(SP + offset, value & 0xffffffff)
    n.registers(esp=SP, esi=instance, edi=1)
    n.run(0x3efe9, [(0x3efe9, 0x3f000)], {0x3f000}, budget=20)
    n.put32(SP + 0x34, values[9])
    n.registers(esp=SP, esi=instance)
    n.run(0x3f07b, [(0x3f07b, 0x3f085)], {0x3f085}, budget=20)
    extras = [n.get32(instance + off) for off in (0x30, 0x1c, 0x20, 0x38)]
    if extras != [v & 0xffffffff for v in (values[5], values[6], values[7], values[9])]:
        raise AssertionError('MDL additional source-field stores mismatch')
    return {'source_offset': placement['offset'], 'fields': values,
            'version_comparisons': compared, 'constructor_arguments': args,
            'instance_offsets': [0xc, 0x10, 0x14, 0x18, 0x2c],
            'instance_values': actual, 'row_instructions': count,
            'initializer_instructions': initializer_count,
            'extra_store_instructions': len(n.visits) - count - initializer_count,
            'extra_store_offsets': [0x30, 0x1c, 0x20, 0x38], 'extra_store_values': extras,
            'model_pointer_is_fixture': True, 'monster_identity': None}


def build_report():
    image = read_pinned(IMAGE)
    evidence = native_evidence(image)
    rtb_results = []
    for path in RTBS:
        raw = read_pinned(path)
        n, layout, execution = native_rtb(image, raw)
        frames = rtb_frame_consumers(n, raw, layout)
        rtb_results.append({'path': path.relative_to(CLIENT).as_posix(), 'sha256': sha(raw),
                            'bytes': len(raw), 'structure': layout,
                            'reader_execution': execution, 'frame_execution': frames})
    packed = read_pinned(MDL)
    decoded = decode_csvz(packed, limit=MAX_BYTES)
    if len(decoded) != 389290 or sha(decoded) != MDL_SHA:
        raise ValueError('Decoded MDL changed')
    mdl = parse_mdl(decoded)
    samples = [mdl['placements'][i] for i in (0, len(mdl['placements']) // 2, len(mdl['placements']) - 1)]
    return {'scope': 'Two RTB representatives and one MDLZ, loader-first; no further family scan.',
            'native': evidence, 'rtb': rtb_results,
            'mdl': {'path': MDL.relative_to(CLIENT).as_posix(), 'bytes': len(packed),
                    'sha256': sha(packed), 'decoded_bytes': len(decoded), 'decoded_sha256': sha(decoded),
                    'structure': mdl, 'placement_execution': [native_mdl_placement(image, p, len(mdl['models'])) for p in samples]},
            'limits': [
                'RTB full binary reader executes with virtual CRT and a prepared native allocator slab.',
                'RTB playback contexts/handles are fixtures; movement stops before 1DBC0, scalar setter executes independently.',
                'MDL whole-file structure parsed independently; full native MDL/ROM/resource loader does not execute.',
                'Three MDL placement rows use a CRT fscanf adapter and original ModelDat lookup over fixture pointers.',
                '41FC0 is an independent initializer island; 38920 constructor/container insertion is not executed.',
                'Additional MDL stores are independent instruction islands with source-derived post-fscanf locals.',
                'Resource IDs/model indices are not monster IDs. No catalog/name/source_label join is performed.',
                'Structural byte coverage is not proof of every field meaning or absence in every consumer/file.'],
            'unresolved': {
                'rtb': 'Unqualified object fields, frame bytes 9..11, header flag meanings, and upstream gameplay ownership.',
                'mdl': 'Extra model integers and placement fields 6..9 lack full semantics; field9 flows into TileType_Action creation, not a qualified monster field.',
                'identity': 'Requires an actual native monster identity or composite key plus source version and consumer.'},
            'monster_field_authority': dict.fromkeys(FIELDS),
            'verified_wild_monster_records': 0, 'verified_boss_records': 0,
            'runtime_eligible': False, 'all_monster_numeric_data_complete': False,
            'next_family': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.summary:
        for result in report['rtb']:
            result['frame_execution_count'] = len(result.pop('frame_execution'))
        structure = report['mdl']['structure']
        for key in ('tiles', 'models', 'groups', 'placements'):
            structure[key + '_count'] = len(structure.pop(key))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
