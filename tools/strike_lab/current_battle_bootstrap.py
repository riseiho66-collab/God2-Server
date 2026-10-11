"""Normal battle initializer on the same VM as original resource preload.

Input/display/context snapshots remain explicit test inputs. Native resources,
name checkpoint, renderer and control calls are real, not transplanted handles.
"""
from collections import Counter
import hashlib
import struct

from .current_battle_resources import NativeBattleResources, RENDERER, BASE, ROOT
from .current_battle_initializer import DISPLAY_STATE_SIZE, SOURCE_STATE_SIZE, ARENA_SIZE
from .current_indoor_resources import SP, RETURN, SCRATCH
from . import current_world_ui_resource as world_ui
from .current_world_ui_resource import NativeWorldUIResource
from .current_preview_role_resources import NativePreviewAnimationResources
from .current_item_metadata import NativeItemMetadata
from . import current_item_action_binding as item_binding
from . import current_battle_character_binding as character_binding
from . import current_skill_catalog_loader as skill_catalog
from .current_battle_learned_skills import NativeBattleLearnedSkills
from . import current_world_clock as world_clock
from . import current_owner_map_metadata as map_metadata
from .recover_combat_rules import CLIENT, read_pinned
from .recover_companion_growth import fields
from .omega_assets import decode_csvz
from .recover_companions import parse_sections
from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_MEM_WRITE)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                              UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_ESP,
                              UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EFLAGS)

ROOT_OBJECT, INPUT, BRIDGE = 0x7800000, 0x7900000, 0x7910000
BATTLE = 0x20000000
MANAGER = BATTLE + 0x144938
DISPLAY, SOURCE, MESSAGES = 0x7a00000, 0x8000000, 0x8200000
DESCRIPTOR, CONTEXT, QUEUE_STORAGE = 0x8300000, 0x8310000, 0x8320000
QUEUE, ARENA = BATTLE + 0xa9ea4b0, MANAGER + 0xa7fbdac
ATTACHMENTS = MANAGER + 0xa89738c
MOUSE, MOUSE_SIZE = 0x8400000, 0x12030
CONTROLS, CONTROLS_SIZE = BATTLE + 0xa9df74c, 0xa43c
PANELS, PANELS_SIZE = BATTLE + 0xa9ea59c, 0x150c34
LIST_CONTROL, LIST_SIZE = BATTLE + 0xab3b428, 0x244
SECOND_LIST = BATTLE + 0xab3b670
THIRD_LIST = BATTLE + 0xab3b1e0
CHARACTER_ROOT = 0x8520000
OWNER, OWNER_SIZE, OWNER_DESCRIPTOR = 0x30000000, 0x240000, 0x8720000
CHARACTER_UI, CHARACTER_STACK, CHARACTER_PACKET = OWNER, 0x8700000, 0x8710000
SELECTOR = BATTLE + 0xa9dc198
CONTROL_POSITIONS = BATTLE + 0xa940604
ENTRY, RESET_BOUNDARY, FIRST_WINDOW_END = 0x1112c0, 0x111654, 0x111659
OWNER_READ_BOUNDARY, BOUNDARY = 0x110228, 0x9b724
CATALOG_BOUNDARY = 0x1116a4
CHARACTER_BOUNDARY = 0x11bc2a
INSTANCE_DISPATCH, INSTANCE_INPUT = 0x8500000, 0x8510000
OWNER_STORE = OWNER + 0x85610
OWNER_PANELS = OWNER + 0xe2170
OWNER_BANK, OWNER_RENDERER = 0x31000000, 0x31400000
OWNER_UI_ASSETS = {
    2: (world_ui.ASSET.lower(), world_ui.ASSET_SHA, world_ui.ASSET_PLAIN_SHA),
    9: ('data3/flow/speceff2.romz',
        '6867c8639cafafb95077de1a583d737262f4f2f50b98e1ce26b4c49a1e3502b8',
        '6694fbe66c07e31553ae50a11757ce8a6660b1f3024846534711f3d223b33739'),
    15: ('data3/flow/martrom.romz',
         '0958bede7b2319983c07185b621ac7c791a44ab6e308e9b7774c4c6455fbdfbe',
         '991c45f68d7b938f4e6188770384bafb04736b48f5097aa88882da5e8c16bae3'),
    31: ('data3/flow/baseinterface.romz',
         '60718d5461b54a507cf13216985b0576f113a5bf8c9cda522077ec8b10958b77',
         'ad094bf9a4cad180ccf4bd7edc667cbb344e7f096b79db51a503288709e46e56'),
    32: ('data3/flow/channelswitch.romz',
         '27e3bf32fc6638635fb5d95eba017dc18baf16816495bee78e9301d80fdd97c7',
         '37192f309f3a7efcab63cd99d6522b78b9cc23ec83cdfc58d9b96fa1a1755b06'),
    33: ('data3/flow/cuse.romz',
         'a70489dbf53513f4f2b028020efbb246c64d10959de9088fcff61f687cf99358',
         'dacb8b796578a772b561e1a83659304edf2670cca1fc7f524571c08ed0d0a531'),
}
OWNER_MAP_ASSET = ('data3/flow/island01map.romz',
                   'b4806bf65a45b3b07a9f8cb3e2c30a8c86579948154531b0f02ebd6e830064d3',
                   'de22ae7038a1d03ad2ccd943e793ff46f7ba8312fb776033f8c4e680c52cc4b0')


class BootstrapResources(NativeBattleResources):
    # The embedded UI spans 0xA7E0000 bytes. Keep it outside the ROM heap.
    battle_address = BATTLE

    def load_item_asset(self, metadata, *, bank=item_binding.BANK):
        path = self.string(metadata.MAPS + item_binding.GROUP * 0x84 + 4)
        if path.decode('ascii').replace('\\', '/').lower() + 'z' != item_binding.ASSET:
            raise ValueError('Original RomMaps selected unexpected item resource')
        raw = read_pinned(CLIENT / item_binding.ASSET, item_binding.ASSET_SHA)
        plain = decode_csvz(raw, limit=1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != item_binding.PLAIN_SHA:
            raise ValueError('Pinned item resource decode changed')
        self.files[item_binding.ASSET] = raw
        self.decoded[item_binding.ASSET] = plain
        self.owner_item_asset = item_binding.ASSET
        self.vm.mem_write(SCRATCH, path + b'\0')
        self.active_name = item_binding.ASSET
        result = self.call(0x29820, SCRATCH, item_binding.SLOT, this=bank)
        if result == 0xffffffff:
            raise AssertionError('Original item ROM loader failed')
        return result

    def load_owner_graphics(self):
        self._prepare_graphics_services()
        sources, rows = world_ui.pinned_sources()
        raw_csv, plain_csv = sources[0]
        self.owner_ui_assets = {asset for asset, _, _ in OWNER_UI_ASSETS.values()}
        for index, (asset, raw_sha, plain_sha) in OWNER_UI_ASSETS.items():
            if rows[index][1].replace('\\', '/').lower().lstrip('/') + 'z' != asset:
                raise ValueError('Original FieldComm3 asset binding differs')
            if (CLIENT / asset).stat().st_size > 4 * 1024 * 1024:
                raise ValueError('Owner UI asset exceeds input bound')
            raw = read_pinned(CLIENT / asset, raw_sha)
            plain = decode_csvz(raw, limit=8 * 1024 * 1024)
            if hashlib.sha256(plain).hexdigest() != plain_sha:
                raise ValueError('Pinned owner UI asset decode changed')
            self.files[asset], self.decoded[asset] = raw, plain
        for address, size in ((OWNER_BANK, 0x2a3000), (OWNER_RENDERER, 0x291000)):
            if any(lo < address + size and address <= hi for lo, hi, _ in self.vm.mem_regions()):
                raise ValueError('Owner graphics mapping overlaps existing memory')
            self.vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        self.call(0x29700, this=OWNER_BANK)
        self.call(0x297e0, 4 * 1024 * 1024, this=OWNER_BANK)
        self.call(0x2b180, 0x6400000, this=OWNER_BANK)
        self.owner_csv_bytes = plain_csv
        NativeWorldUIResource._check_decompression(self, raw_csv, plain_csv)
        self.call(0x546e0, this=OWNER + 0xcff74)
        self.owner_csv_active = True
        try:
            self.call(0x815c0, this=OWNER)
        finally:
            self.owner_csv_active = False
        records = self.u32(OWNER + 0xe2164)
        if self.string(records + 2 * 0x108 + 4) != world_ui.LITERAL_PATH:
            raise AssertionError('Original world UI reader selected a different asset')
        # Original preload-loop iterations retain the selected source slots.
        # Unselected FieldComm3 resources are not claimed loaded.
        for index in OWNER_UI_ASSETS:
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, OWNER)
            self.vm.reg_write(UC_X86_REG_EDI, index)
            self.vm.reg_write(UC_X86_REG_EBX, index * 0x108)
            self.vm.mem_write(SP + 0x118, struct.pack('<I', OWNER_BANK))
            self.run(0x81620, 0x8167b, instruction_limit=50000000)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP or self.u32(records + index * 0x108) != index:
                raise AssertionError('Original owner resource preload did not retain source slot')
        self.call(0x1aa10, 0x6400000, 0, OWNER_BANK, this=OWNER_RENDERER)
        self.owner_ui_records = records
        self.owner_ui_rows = rows
        self.owner_ui_resource = OWNER_BANK + 2 * item_binding.STRIDE
        self.owner_ui_resource_bytes = bytes(self.vm.mem_read(self.owner_ui_resource, item_binding.STRIDE))
        return self.owner_ui_resource

    def load_owner_map(self, character):
        """Execute the original dynamic area-2 load on a private scratch stack."""
        if (not getattr(self, 'owner_ui_records', None) or
                getattr(self, 'owner_map_load_attempted', False) or
                self.u32(OWNER_RENDERER + 0xc) != OWNER_BANK or
                struct.unpack('<H', self.vm.mem_read(character + 0x18, 2))[0] != 2):
            raise ValueError('Fresh owner graphics and explicit area-2 character required')
        asset, raw_sha, plain_sha = OWNER_MAP_ASSET
        path = self.string(self.u32(BASE + 0x170e48 + 2 * 12))
        group = struct.unpack('<H', self.vm.mem_read(BASE + 0x170e48 + 2 * 12 + 4, 2))[0]
        if path.replace(b'\\', b'/').lower().lstrip(b'/').decode() + 'z' != asset or group != 47:
            raise ValueError('Original dynamic map path/group differs')
        if (CLIENT / asset).stat().st_size > 4 * 1024 * 1024:
            raise ValueError('Map asset input bound')
        raw = read_pinned(CLIENT / asset, raw_sha)
        plain = decode_csvz(raw, limit=8 * 1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != plain_sha:
            raise ValueError('Pinned map resource decode changed')
        self.owner_map_load_attempted = True
        self.files[asset], self.decoded[asset] = raw, plain
        self.owner_ui_assets.add(asset)
        self.owner_map_load_calls, self.owner_map_load_writes = Counter(), []
        self.owner_map_load_args = []
        # Native 29820 reserves D554 bytes via _chkstk, before nested calls.
        # A midpoint ESP in a 64-KiB allocation overwrites the preceding catalog.
        private_stack = self.allocate(0x20000)
        private_sp = private_stack + 0x1f000
        saved = self.vm.context_save()
        stack = bytes(self.vm.mem_read(SP - 0x2000, 0x2400))
        hooks = []

        def code(vm, address, size, _):
            pc = address - BASE
            self.owner_map_load_calls[pc] += 1
            if pc in (0x68001, 0x680bb):
                sp = vm.reg_read(UC_X86_REG_ESP)
                self.owner_map_load_args.append((pc, self.string(self.u32(sp)), self.u32(sp + 4),
                                                 vm.reg_read(UC_X86_REG_ECX)))
            if pc in (0x68016, 0x680d0):
                raise AssertionError('Original map loader reached failure report')

        def write(vm, access, address, size, value, _):
            if not OWNER + 0x232f4c <= address < address + size <= OWNER + 0x232f58:
                raise AssertionError('Dynamic map loader changed unrelated owner fields')
            self.owner_map_load_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        try:
            self.vm.reg_write(UC_X86_REG_ESP, private_sp)
            self.vm.reg_write(UC_X86_REG_EBP, OWNER)
            self.vm.mem_write(private_sp + 0x118, struct.pack('<II', OWNER_BANK, character))
            hooks.append(self.vm.hook_add(UC_HOOK_CODE, code,
                                         begin=BASE + 0x67f20, end=BASE + 0x68115))
            hooks.append(self.vm.hook_add(UC_HOOK_MEM_WRITE, write,
                                         begin=OWNER, end=OWNER + OWNER_SIZE - 1))
            self.run(0x816b0, 0x816dc, instruction_limit=500000000, timeout_us=240000000)
            if self.vm.reg_read(UC_X86_REG_ESP) != private_sp:
                raise AssertionError('Original map load did not return with its real stack')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
            self.vm.context_restore(saved)
        if bytes(self.vm.mem_read(SP - 0x2000, 0x2400)) != stack:
            raise AssertionError('Map load changed pending main stack')
        if (self.u32(OWNER + 0x232f4c) != OWNER_BANK or
                self.u32(OWNER + 0x232f50) != 1 or self.u32(OWNER + 0x232f54) != 2 or
                self.u32(OWNER_BANK + 47 * item_binding.STRIDE) == 0xffffffff or
                (asset, 47, len(plain)) not in self.parser_inputs):
            raise AssertionError('Original dynamic map load/binding incomplete')
        self.owner_map_loaded = True
        return {'asset': asset, 'raw_sha256': raw_sha, 'plain_sha256': plain_sha,
                'group': group, 'area': 2, 'bank': OWNER_BANK}

    def _service(self, vm, address, size, context):
        if getattr(self, 'owner_csv_active', False) and address in (BASE + 0x2530, BASE + 0x147e23):
            sp = vm.reg_read(UC_X86_REG_ESP)
            if address == BASE + 0x2530:
                path = self.string(self.u32(sp + 4))
                if path != world_ui.CWD + b'\\Data2\\Patch\\\\FieldComm3.csv':
                    raise AssertionError('Unqualified owner CSV path')
                self.opens.append(path)
                result, cleanup = 0x82000000, 4
                self.handles[result] = [self.owner_csv_bytes.replace(b'\r\n', b'\n'), 0]
            else:
                if (self.u32(sp + 4), self.u32(sp + 8)) != (0x108, 65):
                    raise AssertionError('Unqualified owner CSV allocation')
                result, cleanup = self.allocate(0x108 * 65), 0
            vm.reg_write(UC_X86_REG_EAX, result)
            vm.reg_write(UC_X86_REG_ESP, sp + 4 + cleanup)
            vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
            return
        if address == BASE + 0x14716f and getattr(self, 'owner_ui_assets', None):
            sp = vm.reg_read(UC_X86_REG_ESP)
            path = self.string(self.u32(sp + 4)).decode('ascii').replace('\\', '/').lower()
            prefix = world_ui.CWD.decode().replace('\\', '/').lower() + '/'
            path = path[len(prefix):] if path.startswith(prefix) else path
            if path in self.owner_ui_assets or path + 'z' in self.owner_ui_assets:
                if self.string(self.u32(sp + 8)) != b'rb':
                    raise AssertionError('Owner ROM is read-only')
                self.attempts.append(path)
                result = 0
                if path in self.files:
                    self.opens.append(path)
                    result = 0x80000000 + 4 * len(self.opens)
                    self.handles[result] = [self.files[path], 0]
                    self.active_name = path
                vm.reg_write(UC_X86_REG_EAX, result)
                vm.reg_write(UC_X86_REG_ESP, sp + 4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        if skill_catalog.handles_service(self, address):
            return skill_catalog.file_service(self, vm, address, size, context)
        if address == BASE + 0x14716f and getattr(self, 'owner_item_asset', None):
            sp = vm.reg_read(UC_X86_REG_ESP)
            path = self.string(self.u32(sp + 4)).decode('ascii').replace('\\', '/').lower()
            if path in (item_binding.ASSET, item_binding.ASSET[:-1]):
                return item_binding.NativeItemActionBinding._service(self, vm, address, size, context)
        return super()._service(vm, address, size, context)

    def prepare_rectangles(self):
        self.rect_apis = {self.u32(0x5706c4): 'copy', self.u32(0x5706c8): 'offset'}
        self.rect_calls = Counter()
        for address in self.rect_apis:
            page = address & ~4095
            if not any(lo <= page <= hi for lo, hi, _ in self.vm.mem_regions()):
                self.vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_EXEC)
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._rectangle,
                                              begin=address, end=address))

    def _rectangle(self, vm, address, size, context):
        if address not in self.rect_apis:
            raise AssertionError('Unqualified rectangle adapter')
        self.rect_calls[self.rect_apis[address]] += 1
        # Reuse only the existing OS adapter, never its game-resource handlers.
        NativePreviewAnimationResources._service(self, vm, address, size, context)


class NativeBattleBootstrap:
    def __init__(self, context, display_state, source_state, *, owner_record=None,
                 owner_catalog=False, character_row=None, learned_records=()):
        if type(context) is not bytes or len(context) != 0x3ec:
            raise ValueError('Explicit transition context required')
        if type(display_state) is not bytes or len(display_state) != DISPLAY_STATE_SIZE:
            raise ValueError('Explicit display-manager snapshot required')
        if type(source_state) is not bytes or len(source_state) != SOURCE_STATE_SIZE:
            raise ValueError('Explicit source snapshot required')
        if owner_record is not None and (type(owner_record) is not bytes or
                len(owner_record) != 25 or owner_record[0] != 0x3b or owner_record[2] != 44):
            raise ValueError('Explicit logical 3B slot44 record required')
        if type(owner_catalog) is not bool or (owner_catalog and
                (owner_record is None or owner_record[5:7] != b'\x34\x12')):
            raise ValueError('Catalog integration currently requires explicit MIS:4660 fixture')
        if character_row is not None and (not owner_catalog or type(character_row) is not bytes or
                len(character_row) != 19 or character_row[0] != 0x30 or
                not 100 <= abs(struct.unpack_from('<b', character_row, 1)[0]) <= 127 or
                b'\0' not in character_row[2:18] or character_row[18] == 1):
            raise ValueError('Explicit qualified S2C30 row and owner catalog required')
        if (type(learned_records) is not tuple or len(learned_records) > 100 or
                (learned_records and character_row is None) or any(
                    type(record) is not bytes or len(record) != 4 or record[0] != 0x34
                    for record in learned_records)):
            raise ValueError('Explicit tuple of qualified logical S2C34 records required')
        self.owner_record = owner_record
        self.owner_metadata = None
        self.character = None
        self.boundary = (CHARACTER_BOUNDARY if character_row is not None else
                         CATALOG_BOUNDARY if owner_catalog else
                         BOUNDARY if owner_record is not None and owner_record[5:7] != b'\0\0'
                         else OWNER_READ_BOUNDARY)
        self.native = n = BootstrapResources()
        self.handles = n.preload()
        n._prepare_renderer()
        n.prepare_rectangles()
        # This original constructor tail saves the populated name count. Its
        # pending queue-capacity argument is discarded only between stages.
        n.vm.reg_write(UC_X86_REG_ESP, SP)
        n.vm.reg_write(UC_X86_REG_ESI, BATTLE)
        n.vm.reg_write(UC_X86_REG_EDI, 0)
        n.run(0x110e72, 0x110e95)
        if n.vm.reg_read(UC_X86_REG_ESP) != SP - 4:
            raise AssertionError('Native preload checkpoint stack changed')
        self.checkpoint = n.u32(n.names + 0x40c)
        self._put(BATTLE, b'\xa5' * 0x500)
        self._put32(BATTLE + 0x28, MESSAGES)
        self._put(CONTEXT, context)
        self._put(DESCRIPTOR, struct.pack('<7I', ROOT_OBJECT, CONTEXT,
                  OWNER, 0x8340000, CHARACTER_ROOT, 0, 0x8350000))
        for offset, value in ((0x428, MOUSE), (0x424, INPUT),
                              (0x42c, BRIDGE), (0x438, 0x8370000)):
            self._put32(ROOT_OBJECT + offset, value)
        self._put(INPUT, b'\xa5' * 16)
        self._put(MOUSE - 16, b'\xa5' * (MOUSE_SIZE + 32))
        for offset, value in ((0xa0, SOURCE), (0xa8, DISPLAY), (0xac, 0x8380000)):
            self._put32(BRIDGE + offset, value)
        self._put(SOURCE - 16, b'\xa5' * 16 + source_state + b'\xa5' * 16)
        self._put(DISPLAY - 16, b'\xa5' * 16 + display_state + b'\xa5' * 16)
        if owner_catalog:
            # Original constructor tail consumes its explicit display argument.
            # Normal 1112C0 later resets this manager via 20580/27400.
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.reg_write(UC_X86_REG_ESI, BATTLE)
            n.vm.reg_write(UC_X86_REG_EBX, n.reader)
            n.vm.mem_write(SP + 0x340, struct.pack('<I', DISPLAY))
            n.run(0x110e95, 0x110eab)
            if n.u32(BATTLE + 0x30) != DISPLAY or n.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Original constructor display binding differs')
        self._load_messages()
        n.call(0x11f960, MESSAGES, this=MANAGER)
        self._put(QUEUE, struct.pack('<6I', 0, QUEUE_STORAGE, 0x120, 0x240, 0x1400, 0xa5a5a5a5))
        self._put(QUEUE_STORAGE, b'\xa5' * 0x1400)
        self._put(ARENA - 16, b'\xa5' * (ARENA_SIZE + 16))
        self._put(ATTACHMENTS, b'\xa5' * (28 * 0x2c + 16))
        for index in range(28):
            self._put32(ATTACHMENTS + index * 0x2c + 0x28, 0)
        self._put(MANAGER + 0xa7fbc58, b'\xa5' * 0x68)
        self._put(MANAGER + 0x310, b'\xa5' * 0xa7e0140)
        self._put(BATTLE + 0xa9df744, b'\xa5' * 16)
        self._put(CONTROLS, b'\xa5' * (CONTROLS_SIZE + 16))
        self._put(PANELS - 16, b'\xa5' * (PANELS_SIZE + 48))
        self._put(THIRD_LIST, b'\xa5' * LIST_SIZE)
        self._put(LIST_CONTROL - 16, b'\xa5' * (LIST_SIZE + 32))
        self._put(SECOND_LIST, b'\xa5' * 0x270)
        self._put32(BATTLE + 0xa9df6c8, RENDERER)
        self._put(BATTLE + 0xa924c88, b'\xa5' * 16)
        self._put(BATTLE + 0xa9e9c1c, b'\xa5' * 0x64)
        for offset in (0xa9ea4c8, 0xa9e9c74):
            self._put32(BATTLE + offset, 0xa5a5a5a5)
        self._prepare_control_positions()
        for page in (0x5b4000, 0x5b8000):
            n.vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.registry = [n.u32(0x5b4ed8 + i * 4) for i in range(20)]
        if owner_catalog:
            self.owner_metadata = NativeItemMetadata(vm=n.vm)
            rows = self.owner_metadata.sections['MIS']['records']
            matches = [i for i, row in enumerate(rows) if fields(row)[0] == b'4660']
            if len(matches) != 1:
                raise ValueError('Expected unique pinned MIS:4660 source row')
            self.owner_item = self.owner_metadata.item_row('MIS', matches[0], retain=True)
            self.owner_item_load_result = n.load_item_asset(self.owner_metadata)
            self._prepare_owner()
            self.registry = [n.u32(0x5b4ed8 + i * 4) for i in range(20)]
            self.owner_item_binding = item_binding.bind_existing(
                n, owner=OWNER, table=self.owner_metadata.TABLE, record=self.owner_metadata.RECORD + 16)
            self.owner_item_bytes = bytes(n.vm.mem_read(self.owner_metadata.RECORD, 0x1ac))
            self.owner_maps_bytes = bytes(n.vm.mem_read(self.owner_metadata.MAPS, 0x2000))
        if character_row is not None:
            self._put(MANAGER + skill_catalog.OFFSET, b'\xa5' * skill_catalog.BODY_SIZE)
            self.skill_catalog = skill_catalog.load_catalog(n, MANAGER)
            self._prepare_character(character_row, learned_records)
        self.counts = Counter()
        self.item_calls = Counter()
        for rva in (ENTRY, RESET_BOUNDARY, FIRST_WINDOW_END, 0x181b7, 0x11d377, 0x11fff3, 0x11fd6d,
                    0x205e0, 0x1ad2d, 0x1adcd, 0x1114aa, 0x11fbf0,
                    0x11db47, 0x1afe0, 0x1b560, 0x1081be, 0x1082f0,
                    0x11f95a, 0x1fe00, 0x34650, 0x34680, 0x188c0,
                    0x343b0, 0x35fa0, 0x104160, 0x1041a0, 0x107ca0,
                    0x1e3d0, 0x1e560, 0x10fb10, 0x10fdbe, 0x104ea0,
                    0x106550, 0x1057d0, 0x106c70, 0x10c350, 0x10c540,
                    0x10caa0, 0x10d1d0, 0x10d540, 0x10d310, 0x146cf7,
                    0x10ff00, 0x110210, 0x9b670, 0x9b720, 0x59a60, 0x1e710,
                    0x25b60, 0x25dc0, 0x111660, 0x110273, 0x27400, 0x271e0,
                    0x110480, 0x11062c, 0x111667, 0x11bb80, 0x1116a4):
            n.hooks.append(n.vm.hook_add(UC_HOOK_CODE, self._observe,
                                        begin=BASE+rva, end=BASE+rva))
        self.owner_reads = []
        if owner_record is not None:
            self._seed_owner_slot(owner_record)
            self._put32(OWNER + 0xcff70, self.owner_metadata.TABLE if owner_catalog else 0xa5a5a5a5)
            n.hooks.append(n.vm.hook_add(UC_HOOK_MEM_READ, self._owner_read,
                                        begin=OWNER_STORE, end=OWNER_STORE + 1200 - 1))
            n.hooks.append(n.vm.hook_add(UC_HOOK_MEM_READ, self._owner_read,
                                        begin=OWNER + 0xcff70, end=OWNER + 0xcff73))
        self.attempted = self.completed_prefix = False

    def _prepare_owner(self):
        """Explicit descriptor stages, not the full original world UI startup."""
        n = self.native
        if any(lo < OWNER + OWNER_SIZE and OWNER <= hi for lo, hi, _ in n.vm.mem_regions()):
            raise ValueError('New owner mapping overlaps existing VM memory')
        self._put(OWNER - 16, b'\xa5' * (OWNER_SIZE + 32))
        n.load_owner_graphics()
        self.owner_world_item_load_result = n.load_item_asset(self.owner_metadata, bank=OWNER_BANK)
        self.owner_initial = bytes(n.vm.mem_read(OWNER, OWNER_SIZE))
        descriptor = [0xa5a5a5a5] * 15
        for index, value in ((0, ROOT_OBJECT), (2, BRIDGE), (3, MESSAGES),
                             (4, INPUT), (5, MOUSE), (7, OWNER_RENDERER),
                             (8, self.owner_metadata.TABLE), (10, CHARACTER_ROOT)):
            descriptor[index] = value
        self._put(OWNER_DESCRIPTOR, struct.pack('<15I', *descriptor))
        self.owner_binding_writes = []
        self.owner_preparation_calls = Counter()

        def write(vm, access, address, size, value, data):
            if SP - 0x1000 <= address < address + size <= SP + 0x100:
                return
            if not any(lo <= address < address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (RENDERER, RENDERER + 0x291000),
                    (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (DISPLAY, DISPLAY + DISPLAY_STATE_SIZE),
                    (0x6400000, 0x6500000))):
                raise AssertionError('Owner preparation escaped new object')
            self.owner_binding_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        def code(vm, address, size, data):
            pc = address - BASE
            if pc in (0x81895, 0x81a08, 0x81c1d):
                vm.emu_stop()
            elif address not in n.os_apis and not any(lo <= pc and pc + size <= hi for lo, hi in (
                    (0x817ca, 0x81895), (0x819dd, 0x81a08), (0x104160, 0x10446d),
                    (0x81c12, 0x81c1d), (0x1044a0, 0x104500), (0x107dd0, 0x107e0b),
                    (0x205a0, 0x205e3),
                    (0x107ca0, 0x107cc7), (0x1ae20, 0x1e6f0), (0x25000, 0x274cb),
                    (0x27570, 0x275a1),
                    (0x1497ec, 0x149886), (0x147b80, 0x147c7e))):
                raise AssertionError(f'Unqualified owner preparation PC {pc:X}')
            if pc in (0x104160, 0x1041a0, 0x10419b, 0x1042c0):
                self.owner_preparation_calls[pc] += 1

        hooks = [n.vm.hook_add(UC_HOOK_MEM_WRITE, write), n.vm.hook_add(UC_HOOK_CODE, code)]
        try:
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.mem_write(SP + 0x18, struct.pack('<I', 0xa5a5a5a5))
            n.vm.reg_write(UC_X86_REG_ESI, OWNER)
            n.vm.reg_write(UC_X86_REG_EDI, OWNER_DESCRIPTOR)
            n.run(0x817ca, 0x81895, instruction_limit=1000)
            n.run(0x819dd, 0x81a08, instruction_limit=200000)
            n.vm.reg_write(UC_X86_REG_ESI, OWNER)
            n.run(0x81c12, 0x81c1d, instruction_limit=200000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP or
                self.owner_preparation_calls != Counter({0x104160: 1, 0x1041a0: 1, 0x10419b: 1, 0x1042c0: 1}) or
                bytes(n.vm.mem_read(OWNER_PANELS + 0x150c18, 2)) != b'\xff\xff'):
            raise AssertionError('Original owner panel preparation did not return')
        self.owner_prepared = bytes(n.vm.mem_read(OWNER, OWNER_SIZE))

    def prepare_character_appearance(self, body):
        """Run the world actor's exact appearance stores on this same actor.

        The explicit 36-byte body is diagnostic input, not recovered ownership
        or monster statistics. CPU context and the pending initializer survive.
        """
        if (self.character is None or type(body) is not bytes or len(body) != 36 or
                getattr(self, 'appearance_prepared', False) or
                getattr(self, 'owner_bridge_attempted', False)):
            raise ValueError('Fresh character and explicit world appearance body required')
        n, c = self.native, self.character
        saved_stack = bytes(n.vm.mem_read(c.sp + 0x28, 36))
        n.vm.mem_write(c.sp + 0x28, body)
        try:
            stage = c._run(0x68328, 0x6834b, ((0x68328, 0x6834b),),
                           registers={'EBP': CHARACTER_ROOT},
                           writable=((CHARACTER_ROOT + 0x28, CHARACTER_ROOT + 0x2c),
                                     (CHARACTER_ROOT + 0x4584, CHARACTER_ROOT + 0x458c)))
        finally:
            n.vm.mem_write(c.sp + 0x28, saved_stack)
        expected = bytearray(self.character_prepared)
        expected[0x4584:0x458c] = body[12:20]
        struct.pack_into('<I', expected, 0x28, body[13] >> 5)
        if bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected:
            raise AssertionError('Original appearance producer changed unrelated actor bytes')
        self.character_prepared = bytes(expected)
        for pc, address, size, value in stage['writes']:
            if CHARACTER_ROOT <= address < CHARACTER_ROOT + len(expected):
                self.character_written.update(range(address, address + size))
        self.appearance_stage, self.appearance_body = stage, body
        self.appearance_prepared = True

    def _prepare_control_positions(self):
        n = self.native
        self._put(CONTROL_POSITIONS, b'\xa5' * 224)
        self.control_positions = bytes(n.vm.mem_read(0x571aa8, 224))
        self.control_position_writes = []

        def write(vm, access, address, size, value, context):
            if not CONTROL_POSITIONS <= address < address + size <= CONTROL_POSITIONS + 224:
                raise AssertionError('Original coordinate copy wrote outside its table')
            self.control_position_writes.append((address - CONTROL_POSITIONS, size, value))

        hook = n.vm.hook_add(UC_HOOK_MEM_WRITE, write)
        # The next instruction was translated by the earlier resource stage.
        stop_hook = n.vm.hook_add(UC_HOOK_CODE, lambda vm, *_: vm.emu_stop(),
                                 begin=BASE + 0x11f4ef, end=BASE + 0x11f4ef)
        try:
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.reg_write(UC_X86_REG_ESI, MANAGER)
            n.run(0x11f4c5, 0x11f4ef, instruction_limit=1000, timeout_us=1000000)
        finally:
            n.vm.hook_del(hook)
            n.vm.hook_del(stop_hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP or
                bytes(n.vm.mem_read(CONTROL_POSITIONS, 224)) != self.control_positions or
                [(offset, size) for offset, size, _ in self.control_position_writes] !=
                [(offset, 4) for offset in range(0, 224, 4)]):
            raise AssertionError('Original coordinate table copy differs')

    def _prepare_character(self, row, learned_records):
        n = self.native
        self._put(CHARACTER_STACK, b'\xa5' * 0x4000)
        self._put(CHARACTER_PACKET, b'\xa5' * 4096)
        self._put(SELECTOR, b'\xa5' * 0x351c)
        if n.call(0x11b7b0, this=SELECTOR) != SELECTOR:
            raise AssertionError('Original selector constructor did not return this')
        self.selector_constructed = bytes(n.vm.mem_read(SELECTOR, 0x351c))
        expected_selector = bytearray(b'\xa5' * 0x351c)
        struct.pack_into('<I', expected_selector, 0, 0x5715e4)
        expected_selector[4:0x2d10] = bytes(0x2d0c)
        struct.pack_into('<I', expected_selector, 0x2e10, 0)
        struct.pack_into('<H', expected_selector, 0x2e1c, 0xffff)
        for offset in (0x2e38, 0x3080, 0x32c8):
            struct.pack_into('<I', expected_selector, offset, 0)
            expected_selector[offset + 0x210:offset + 0x224] = bytes(0x14)
            struct.pack_into('<I', expected_selector, offset + 0x23c, 0xffff)
        if self.selector_constructed != expected_selector:
            raise AssertionError('Original selector constructor footprint differs')
        self.character = c = character_binding.NativeBattleCharacterBinding(
            n.vm, root=CHARACTER_ROOT, ui=CHARACTER_UI, sp=CHARACTER_STACK + 0x2000,
            packet=CHARACTER_PACKET)
        self.character_initial = b'\xa5' * character_binding.ROOT_SIZE
        c.prepare_new_root(self.character_initial)
        self.character_stages = [c.reset_rows(), *c.bind_packet_source(), c.append_named_row(row)]
        self.learned = NativeBattleLearnedSkills(c, battle=BATTLE)
        self.character_stages.append(self.learned.publish_catalog_pointer())
        self.learned_stages = [self.learned.write_learned_skill(record) for record in learned_records]
        self.character_stages.extend(self.learned_stages)
        expected = bytearray(self.character_initial)
        self.character_written = set()
        for stage in self.character_stages:
            for _, address, size, value in stage['writes']:
                if CHARACTER_ROOT <= address < CHARACTER_ROOT + len(expected):
                    offset = address - CHARACTER_ROOT
                    expected[offset:offset + size] = (value & ((1 << (8 * size)) - 1)).to_bytes(size, 'little')
                    self.character_written.update(range(address, address + size))
        self.character_prepared = bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected)))
        if self.character_prepared != expected:
            raise AssertionError('Character changed outside original writer trace')
        self.character_reads = []
        n.hooks.append(n.vm.hook_add(UC_HOOK_MEM_READ, self._character_read,
                                    begin=CHARACTER_ROOT, end=CHARACTER_ROOT + len(expected) - 1))

    def _character_read(self, vm, access, address, size, value, context):
        if not all(byte in self.character_written for byte in range(address, address + size)):
            raise AssertionError('Unqualified character source byte read')
        self.character_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

    def continue_selector_windows(self):
        """Resume the retained native stack, stopping before 11BF40 population.

        This is a second execution segment, not a new initializer invocation.
        Neither completed selector population nor live UI is claimed here.
        """
        n = self.native
        if (not self.completed_prefix or self.boundary != CHARACTER_BOUNDARY or
                getattr(self, 'selector_windows_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + CHARACTER_BOUNDARY or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x54):
            raise ValueError('Completed untouched character prefix required')
        self.selector_windows_attempted = True
        self.selector_window_calls = Counter()
        tracked = (0x11a9d0, 0x11ac91, 0x11adb0, 0x11b09e,
                   0x11bc84, 0x11c4b0, 0x11c4ea)

        def observe(vm, address, size, data):
            self.selector_window_calls[address - BASE] += 1

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe, begin=BASE + rva, end=BASE + rva)
                 for rva in tracked]
        try:
            n.run(CHARACTER_BOUNDARY, 0x11bc95, instruction_limit=10000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x54 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body']):
            raise AssertionError('Selector windows changed retained stack/source/catalog')
        self.selector_windows_completed = True
        return dict(self.selector_window_calls)

    def continue_selector_population(self):
        """Resume through the original 11BB80 return, not full battle entry."""
        n = self.native
        if (not getattr(self, 'selector_windows_completed', False) or
                getattr(self, 'selector_population_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x11bc95 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x54):
            raise ValueError('Untouched completed selector windows required')
        self.selector_population_attempted = True
        self.selector_population_calls = Counter()
        self.selector_label_copies = []
        tracked = (0x11bf40, 0x11c045, 0x11c050, 0x11c1c9,
                   0x11bd70, 0x11bdc4, 0x11b290, 0x11b568,
                   0x11c4f0, 0x11c515, 0x11bd65, 0x11bf94, 0x11bf99)

        def observe(vm, address, size, data):
            pc = address - BASE
            if pc == 0x11bf80:
                stack = vm.reg_read(UC_X86_REG_ESP)
                destination, fmt, source = struct.unpack('<3I', vm.mem_read(stack, 12))
                # CRT adapters read via host memory, outside Unicorn's read hook.
                if (not all(at in self.character_written for at in range(source, source + 16)) or
                        n.string(fmt) != b'%s'):
                    raise AssertionError('Unqualified native character label source')
                raw = bytes(vm.mem_read(source, 16))
                if b'\0' not in raw:
                    raise AssertionError('Character label exceeds native name bounds')
                self.selector_label_copies.append({
                    'source': source, 'destination': destination, 'expected': raw.split(b'\0', 1)[0]})
            elif pc == 0x11bf85:
                copy = self.selector_label_copies[-1]
                copy['actual'] = bytes(vm.mem_read(copy['destination'], len(copy['expected']) + 1))
                if (copy['actual'] != copy['expected'] + b'\0' or
                        vm.reg_read(UC_X86_REG_EAX) != len(copy['expected'])):
                    raise AssertionError('Character label CRT copy differs')
            else:
                self.selector_population_calls[pc] += 1

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe, begin=BASE + rva, end=BASE + rva)
                 for rva in (*tracked, 0x11bf80, 0x11bf85)]
        try:
            n.run(0x11bc95, 0x1116a9, instruction_limit=10000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x1c or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body'] or
                any(bytes(n.vm.mem_read(at, len(before))) != before
                    for at, before in self.selector_neighbors.items())):
            raise AssertionError('Selector return changed retained stack/source/catalog/neighbors')
        if self.selector_population_calls != Counter({rva: 1 for rva in tracked}):
            raise AssertionError('Original selector population did not traverse every required return')
        self.selector_population_completed = True
        return dict(self.selector_population_calls)

    def continue_participant_controls(self):
        """Create the original 2x14 controls before the character UI bridge."""
        n = self.native
        if (not getattr(self, 'selector_population_completed', False) or
                getattr(self, 'participant_controls_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x1116a9 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x1c or
                bytes(n.vm.mem_read(CONTROL_POSITIONS, 224)) != self.control_positions):
            raise ValueError('Untouched selector return and native coordinates required')
        self.participant_controls_attempted = True
        self.participant_control_calls = Counter()
        self.participant_control_args = []
        self.participant_control_ids = []
        tracked = (0x1116eb, 0x1116f0, 0x111700, 0x111705, 0x11171d,
                   0x111722, 0x111736, 0x11173b, 0x111747, 0x11174c)

        def observe(vm, address, size, data):
            pc = address - BASE
            self.participant_control_calls[pc] += 1
            if pc == 0x1116eb:
                if vm.reg_read(UC_X86_REG_ECX) != CONTROLS:
                    raise AssertionError('Participant control manager differs')
                self.participant_control_args.append(struct.unpack(
                    '<6I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 24)))
            elif pc == 0x1116f0:
                self.participant_control_ids.append(vm.reg_read(UC_X86_REG_EAX))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe, begin=BASE + pc, end=BASE + pc)
                 for pc in tracked]
        try:
            n.run(0x1116a9, 0x11177d, instruction_limit=10000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x1c or
                self.participant_control_calls != Counter({pc: 28 for pc in tracked}) or
                self.participant_control_ids != list(range(28)) or
                bytes(n.vm.mem_read(CONTROL_POSITIONS, 224)) != self.control_positions or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body']):
            raise AssertionError('Original participant controls or retained state differ')
        self.participant_controls_completed = True
        return dict(self.participant_control_calls)

    def continue_owner_bridge_prefix(self):
        """Continue the actual 81C20 call to the C3080 resource/UI boundary."""
        n = self.native
        if (not getattr(self, 'participant_controls_completed', False) or
                not getattr(self, 'appearance_prepared', False) or
                getattr(self, 'owner_bridge_attempted', False) or
                self.character.ui != OWNER or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x11177d or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x1c or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise ValueError('Untouched controls, shared owner and produced appearance required')
        self.owner_bridge_attempted = True
        self.owner_bridge_calls = Counter()
        self.owner_bridge_writes = []

        def code(vm, address, size, data):
            pc = address - BASE
            if pc == 0xc3080:
                vm.emu_stop()
                return
            elif address not in n.os_apis and not any(lo <= pc and pc + size <= hi for lo, hi in (
                    (0x11177d, 0x111796), (0x81c20, 0x81c81), (0x81f08, 0x81f0d),
                    (0x1041a0, 0x1042b8), (0x104470, 0x104494),
                    (0x107ca0, 0x107cc7), (0x1ae20, 0x1e6f0), (0x25000, 0x274cb),
                    (0x1497ec, 0x149886), (0x147b80, 0x147c7e),
                    (0x83410, 0x83441), (0x1a920, 0x1a937))):
                raise AssertionError(f'Unqualified owner bridge PC {pc:X}')
            if pc in (0x81c20, 0x1041a0, 0x104470, 0x25c80,
                      0x83410, 0x1a920, 0x81f08):
                self.owner_bridge_calls[pc] += 1

        def write(vm, access, address, size, value, data):
            if SP - 0x1000 <= address < address + size <= SP:
                return
            allowed = ((OWNER, OWNER + OWNER_SIZE),
                       (RENDERER, RENDERER + 0x291000), (0x6400000, 0x6500000),
                       (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                       (BATTLE + 0xa9e9c84, BATTLE + 0xa9e9c85),
                       (CHARACTER_ROOT + 0x92, CHARACTER_ROOT + 0x94))
            if not any(lo <= address < address + size <= hi for lo, hi in allowed):
                raise AssertionError('Original owner bridge wrote outside qualified objects')
            self.owner_bridge_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, code), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0x11177d, 0xc3080, instruction_limit=200000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        expected = bytearray(self.character_prepared)
        expected[0x92:0x94] = expected[0x28:0x2a]
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x3c or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body']):
            raise AssertionError('Owner bridge changed retained stack/character/catalog')
        self.character_prepared = bytes(expected)
        self.character_written.update(range(CHARACTER_ROOT + 0x92, CHARACTER_ROOT + 0x94))
        self.owner_bridge_completed_prefix = True
        return dict(self.owner_bridge_calls)

    def continue_owner_map_panel(self):
        """Create the real world-map panel, stopping at its clock refresh call."""
        n = self.native
        if (not getattr(self, 'owner_bridge_completed_prefix', False) or
                getattr(self, 'owner_map_panel_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3080 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x3c or
                n.u32(OWNER + 0xcff60) != OWNER_RENDERER or
                n.u32(OWNER_RENDERER + 0xc) != OWNER_BANK):
            raise ValueError('Untouched owner bridge and correct world resource bank required')
        self.owner_map_panel_attempted = True
        self.owner_map_panel_calls = Counter()
        self.owner_map_panel_writes = []
        tracked = (0xc3080, 0x104ea0, 0x104f50, 0x1fe00, 0x1afe0,
                   0x107710, 0x146cf7, 0x1e3d0, 0xc3119)

        def observe(vm, address, size, data):
            self.owner_map_panel_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return  # The existing SEH hook checks the exact native instruction.
            if SP - 0x1000 <= address < address + size <= SP:
                return
            if not any(lo <= address < address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (MOUSE, MOUSE + MOUSE_SIZE))):
                raise AssertionError(f'Owner map panel write escaped qualified objects: {address:X}')
            self.owner_map_panel_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe, begin=BASE + pc, end=BASE + pc)
                 for pc in tracked]
        hooks.append(n.vm.hook_add(UC_HOOK_MEM_WRITE, write))
        hooks.append(n.vm.hook_add(UC_HOOK_CODE, lambda vm, *_: vm.emu_stop(),
                                  begin=BASE + 0xc3640, end=BASE + 0xc3640))
        try:
            n.run(0xc3080, 0xc3640, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf4 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body']):
            raise AssertionError('Owner map panel changed retained stack/character/catalog')
        self.owner_map_panel_completed_prefix = True
        return dict(self.owner_map_panel_calls)

    def prepare_character_clock(self, record, *, clock_ms):
        """Preserve the pending map-panel call while its native packet writer runs."""
        n = self.native
        if (not getattr(self, 'owner_map_panel_completed_prefix', False) or
                getattr(self, 'clock_prepared', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3640 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf4):
            raise ValueError('Untouched pending map clock call required')
        clock = world_clock.NativeWorldClock(n.vm, owner=OWNER, character=CHARACTER_ROOT,
            sp=CHARACTER_STACK + 0x2000, packet=CHARACTER_PACKET)
        stage = clock.write_clock(record, clock_ms=clock_ms)
        expected = bytearray(self.character_prepared)
        stores = [(pc, at, size, value) for pc, at, size, value in stage['writes']
                  if CHARACTER_ROOT <= at < CHARACTER_ROOT + len(expected)]
        if [(at, size) for _, at, size, _ in stores] != [
                (CHARACTER_ROOT + 0x453c, 4), (CHARACTER_ROOT + 0x4540, 4)]:
            raise AssertionError('Original clock writer footprint differs')
        for _, at, size, value in stores:
            expected[at - CHARACTER_ROOT:at - CHARACTER_ROOT + size] = value.to_bytes(size, 'little')
        if bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected:
            raise AssertionError('Clock writer changed unrelated character bytes')
        self.character_prepared = bytes(expected)
        self.character_written.update(range(CHARACTER_ROOT + 0x453c, CHARACTER_ROOT + 0x4544))
        self.clock, self.clock_stage = clock, stage
        self.clock_prepared = True
        return stage

    def continue_owner_map_clock(self, *, clock_ms):
        """Return through C3640 and build map controls before unowned map fields."""
        n = self.native
        world_clock._dword(clock_ms, 'external clock_ms')
        if (not getattr(self, 'clock_prepared', False) or
                getattr(self, 'owner_map_clock_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3640 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf4 or
                self.clock._state() != self.clock_stage['state']):
            raise ValueError('Untouched map clock call and original packet writer receipt required')
        self.clock._verify(world_clock.CONSUMER_RANGES, clock=True)
        self.owner_map_clock_attempted = True
        self.owner_map_clock_calls, self.owner_map_clock_writes = Counter(), []
        self.owner_clock_samples, self.owner_clock_labels = [], []
        self.owner_clock_text_records = []
        tracked = (0xc3640, 0xc3710, 0xc36de, 0xc311e, 0x149630, 0x1077c0,
                   0x1e500, 0x26700, 0x26140, 0x106550, 0x1057d0)

        def imported_clock(vm, address, size, data):
            sp = vm.reg_read(UC_X86_REG_ESP)
            ret = n.u32(sp)
            if self.owner_clock_samples or sp != SP - 0x110 or ret != BASE + 0xc365d:
                raise AssertionError('Unqualified external map clock call')
            self.owner_clock_samples.append({'iat': world_clock.CLOCK_IAT,
                'target': address, 'value': clock_ms, 'return': ret, 'stack': sp})
            vm.reg_write(UC_X86_REG_EAX, clock_ms)
            vm.reg_write(UC_X86_REG_ESP, sp + 4)
            vm.reg_write(UC_X86_REG_EIP, ret)

        def observe(vm, address, size, data):
            pc = address - BASE
            self.owner_map_clock_calls[pc] += 1
            if pc == 0x1e500:
                sp = vm.reg_read(UC_X86_REG_ESP)
                ret, handle, slot, text = struct.unpack('<4I', vm.mem_read(sp, 16))
                if ret != BASE + 0x107840 or slot & 0xffff != 2:
                    raise AssertionError('Unqualified world clock text setter')
                self.owner_clock_labels.append({'handle': handle & 0xffff, 'slot': slot & 0xffff,
                    'text': n.string(text), 'renderer': vm.reg_read(UC_X86_REG_ECX)})
            elif pc == 0x26140:
                sp = vm.reg_read(UC_X86_REG_ESP)
                ret, record, text = struct.unpack('<3I', vm.mem_read(sp, 12))
                if ret == BASE + 0x267c7:
                    self.owner_clock_text_records.append({'record': record, 'text': n.string(text)})

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return  # Existing hook verifies the exact SEH access.
            if SP - 0x2000 <= address < address + size <= SP:
                return
            if not any(lo <= address < address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (MOUSE, MOUSE + MOUSE_SIZE))):
                raise AssertionError(f'Map clock/control write escaped qualified storage: {address:X}')
            self.owner_map_clock_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        page = world_clock.CLOCK_TARGET & ~4095
        mapped = not any(lo <= page <= hi for lo, hi, _ in n.vm.mem_regions())
        if mapped:
            n.vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_EXEC)
        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe, begin=BASE + pc, end=BASE + pc)
                 for pc in tracked]
        hooks.append(n.vm.hook_add(UC_HOOK_CODE, imported_clock,
                                  begin=world_clock.CLOCK_TARGET, end=world_clock.CLOCK_TARGET))
        hooks.append(n.vm.hook_add(UC_HOOK_MEM_WRITE, write))
        hooks.append(n.vm.hook_add(UC_HOOK_CODE, lambda vm, *_: vm.emu_stop(),
                                  begin=BASE + 0xc328b, end=BASE + 0xc328b))
        try:
            n.run(0xc3640, 0xc328b, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
            if mapped:
                n.vm.mem_unmap(page, 4096)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0 or
                len(self.owner_clock_samples) != 1 or len(self.owner_clock_labels) != 1 or
                len(self.owner_clock_text_records) != 1 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared or
                bytes(n.vm.mem_read(self.skill_catalog['destination'], skill_catalog.BODY_SIZE)) != self.skill_catalog['body']):
            raise AssertionError('Map clock/control continuation changed retained source/stack/catalog')
        self.owner_map_clock_completed_prefix = True
        return dict(self.owner_map_clock_calls)

    def prepare_character_map_selector(self, packed_selector):
        """Original 6865C stores from an explicit world-body+24 DWORD input."""
        world_clock._dword(packed_selector, 'packed map selector')
        n, c = self.native, self.character
        if (not getattr(self, 'owner_map_clock_completed_prefix', False) or
                getattr(self, 'map_selector_prepared', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc328b or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0):
            raise ValueError('Untouched map-selector read boundary required')
        scratch = bytes(n.vm.mem_read(c.sp + 0x40, 4))
        n.vm.mem_write(c.sp + 0x40, struct.pack('<I', packed_selector))
        try:
            stage = c._run(0x6865c, 0x68675, ((0x6865c, 0x68675),),
                registers={'EBP': CHARACTER_ROOT},
                writable=((CHARACTER_ROOT + 0x14, CHARACTER_ROOT + 0x1a),))
        finally:
            n.vm.mem_write(c.sp + 0x40, scratch)
        expected = bytearray(self.character_prepared)
        struct.pack_into('<H', expected, 0x18, packed_selector & 0x3f)
        struct.pack_into('<I', expected, 0x14, (packed_selector & 0xffff) >> 6)
        if bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected:
            raise AssertionError('Original map selector stores changed unrelated character bytes')
        self.character_prepared = bytes(expected)
        self.character_written.update(range(CHARACTER_ROOT + 0x14, CHARACTER_ROOT + 0x1a))
        self.map_selector_stage, self.map_selector_input = stage, packed_selector
        self.map_selector_prepared = True
        return stage

    def prepare_character_map_coordinates(self, packed_position):
        """Execute original world-body+28 coordinate stores, not a full receive."""
        world_clock._dword(packed_position, 'packed position')
        n, c = self.native, self.character
        if (not getattr(self, 'owner_map_sprite_completed_prefix', False) or
                getattr(self, 'map_coordinates_prepared', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3331 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0):
            raise ValueError('Untouched coordinate read boundary required')
        scratch = bytes(n.vm.mem_read(c.sp + 0x44, 4))
        n.vm.mem_write(c.sp + 0x44, struct.pack('<I', packed_position))
        try:
            stage = c._run(0x68636, 0x68653, ((0x68636, 0x68653),),
                registers={'EBP': CHARACTER_ROOT},
                writable=((CHARACTER_ROOT + 8, CHARACTER_ROOT + 16),))
        finally:
            n.vm.mem_write(c.sp + 0x44, scratch)
        expected = bytearray(self.character_prepared)
        struct.pack_into('<II', expected, 8, (packed_position >> 2) & 0x7fff,
                         packed_position >> 17)
        if bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected:
            raise AssertionError('Coordinate writer changed unrelated character bytes')
        self.character_prepared = bytes(expected)
        self.character_written.update(range(CHARACTER_ROOT + 8, CHARACTER_ROOT + 16))
        self.map_coordinate_stage, self.map_coordinate_input = stage, packed_position
        self.map_coordinates_prepared = True
        return stage

    def continue_owner_map_label(self):
        """Resume coordinate reads and real C3B60 label update on the retained stack."""
        n = self.native
        if (not getattr(self, 'map_coordinates_prepared', False) or
                getattr(self, 'owner_map_label_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3331 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0):
            raise ValueError('Native coordinates and retained label boundary required')
        self.owner_map_label_attempted = True
        self.owner_map_label_calls, self.owner_map_label_writes = Counter(), []

        def observe(vm, address, size, data):
            self.owner_map_label_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (MOUSE, MOUSE + MOUSE_SIZE))):
                raise AssertionError(f'Map label write escaped objects: {address:X}')
            self.owner_map_label_writes.append(
                (vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0xc3331, 0xc3348, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise AssertionError('Map label changed retained stack or character')
        self.owner_map_label_completed_prefix = True
        return dict(self.owner_map_label_calls)

    def complete_owner_map_panel(self):
        """Run the remaining C3080 controls through its original caller return."""
        n = self.native
        if (not getattr(self, 'owner_map_label_completed_prefix', False) or
                getattr(self, 'owner_map_completion_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc3348 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0):
            raise ValueError('Retained map label return required')
        self.owner_map_completion_attempted = True
        self.owner_map_completion_calls, self.owner_map_completion_writes = Counter(), []

        def observe(vm, address, size, data):
            self.owner_map_completion_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (MOUSE, MOUSE + MOUSE_SIZE))):
                # 205A0 accepts indices0..30 and writes four DWORD rectangle fields.
                if not DISPLAY + 8 <= address < address + size <= DISPLAY + 0x1f8:
                    raise AssertionError(f'Map completion write escaped objects: {address:X}')
            self.owner_map_completion_writes.append(
                (vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0xc3348, 0x81f0d, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x34 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise AssertionError('Map completion changed caller stack or character')
        self.owner_map_completed = True
        return dict(self.owner_map_completion_calls)

    def prepare_owner_toolbar_messages(self):
        """Populate the owner catalog via native ProgramMsg rows and bind text globals."""
        n = self.native
        if (not getattr(self, 'owner_map_completed', False) or
                getattr(self, 'owner_toolbar_messages_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x81f0d or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x34):
            raise ValueError('Fresh retained owner toolbar boundary required')
        target = n.u32(OWNER + 0xcff70)
        if bytes(n.vm.mem_read(target + 0xb2c68, 6)) != bytes(6):
            raise ValueError('Owner message slot must be uninitialized')
        self.owner_toolbar_messages_attempted = True
        saved = n.vm.context_save()
        stack = bytes(n.vm.mem_read(SP - 0x2000, 0x2400))
        parser = bytes(n.vm.mem_read(target + 4, map_metadata.PARSER_SIZE - 4))
        try:
            self._put32(target + 0xb2c68, n.allocate(len(self.message_rows) * 4))
            self._put(target + 8, struct.pack('<H', 2))
            for row in self.message_rows:
                line = bytes.fromhex(row['raw_record_hex']).replace(b'\r\n', b'\n')
                n.vm.mem_write(SCRATCH, line + b'\0')
                n.call(0x51be0, SCRATCH, this=target)
                n.vm.reg_write(UC_X86_REG_ESP, SP)
                n.vm.reg_write(UC_X86_REG_EBX, target)
                n.vm.reg_write(UC_X86_REG_EBP, len(self.message_rows))
                n.run(0x58cd4, 0x58d67)
                if n.vm.reg_read(UC_X86_REG_ESP) != SP:
                    raise AssertionError('Owner message row stack changed')
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.reg_write(UC_X86_REG_ECX, OWNER)
            # Pinned PE .data contains this page; no instruction bytes reside here.
            n.vm.mem_protect(BASE + 0x1b7000, 4096, UC_PROT_READ | UC_PROT_WRITE)
            self.owner_toolbar_message_writes = []

            def binding_write(vm, access, address, size, value, data):
                if SP - 0x2000 <= address and address + size <= SP:
                    return
                if not any(lo <= address and address + size <= hi for lo, hi in (
                        (BASE + 0x1b7550, BASE + 0x1b7594),
                        (BASE + 0x1b7698, BASE + 0x1b7698 + 8 * 0x33))):
                    raise AssertionError(f'Text binding escaped globals: {address:X}')
                self.owner_toolbar_message_writes.append((address, size, value))

            hook = n.vm.hook_add(UC_HOOK_MEM_WRITE, binding_write)
            try:
                n.run(0xb0af0, 0xb0bee, instruction_limit=100000)
                n.call(0xb3a10, this=OWNER)
            finally:
                n.vm.hook_del(hook)
            self.owner_toolbar_text_bindings = []
            for source, destination, count in ((0x192568, 0x1b758c, 2),
                                               (0x19256c, 0x1b7564, 10),
                                               (0x192580, 0x1b7550, 5)):
                for index in range(count):
                    key = struct.unpack('<H', n.vm.mem_read(BASE + source + index * 2, 2))[0]
                    pointer = n.u32(BASE + destination + index * 4)
                    expected = n.u32(self.message_pointers + (key - 1) * 4)
                    if not pointer or n.string(pointer) != n.string(expected):
                        raise AssertionError('Owner text binding differs from original ProgramMsg')
                    self.owner_toolbar_text_bindings.append((key, pointer, n.string(pointer)))
            self.owner_toolbar_messages_prepared = True
        finally:
            n.vm.mem_write(target + 4, parser)
            n.vm.mem_write(SP - 0x2000, stack)
            n.vm.context_restore(saved)
        self.owner_map_metadata._verify_records(bound=True)

    def prepare_owner_toolbar_cache(self):
        """Construct the original owner control cache and execute its pointer store."""
        n = self.native
        if (getattr(self, 'owner_toolbar_cache_attempted', False) or
                not getattr(self, 'owner_toolbar_messages_prepared', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x81f0d or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x34 or
                n.u32(OWNER + 0x232ebc) != 0xa5a5a5a5):
            raise ValueError('Untouched owner control-cache slot required')
        self.owner_toolbar_cache_attempted = True
        pointer = n.allocate(0x3ae54)  # Original allocation request at80FDB.
        n.vm.mem_write(pointer, b'\xa5' * 0x3ae54)
        saved = n.vm.context_save()
        stack = bytes(n.vm.mem_read(SP - 0x2000, 0x2400))
        self.owner_toolbar_cache_writes = []

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not (pointer <= address and address + size <= pointer + 0x3ae54 or
                    address == OWNER + 0x232ebc and size == 4):
                raise AssertionError(f'Control constructor escaped object: {address:X}')
            self.owner_toolbar_cache_writes.append((address, size, value))

        hook = n.vm.hook_add(UC_HOOK_MEM_WRITE, write)
        try:
            n.call(0x85df0, OWNER, this=pointer)
            if n.vm.reg_read(UC_X86_REG_EAX) != pointer or n.u32(pointer + 0xdc) != OWNER:
                raise AssertionError('Original control constructor owner/return differs')
            n.vm.reg_write(UC_X86_REG_ESI, OWNER)
            n.run(0x81029, 0x8102f)
            if n.u32(OWNER + 0x232ebc) != pointer:
                raise AssertionError('Original control pointer store failed')
            self.owner_toolbar_cache = pointer
        finally:
            n.vm.hook_del(hook)
            n.vm.mem_write(SP - 0x2000, stack)
            n.vm.context_restore(saved)

    def prepare_owner_toolbar_channel(self):
        """Bind a native empty channel container through descriptor slot eleven."""
        n = self.native
        if (getattr(self, 'owner_toolbar_channel_attempted', False) or
                not getattr(self, 'owner_toolbar_cache', None) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x81f0d or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x34 or
                n.u32(OWNER + 0x39de8) != 0xa5a5a5a5 or
                n.u32(OWNER_DESCRIPTOR + 0x2c) != 0xa5a5a5a5):
            raise ValueError('Untouched owner channel binding required')
        self.owner_toolbar_channel_attempted = True
        # 6447E/64489 constructs this type; 652FF publishes it at descriptor +2C.
        pointer = n.allocate(0x67f4)
        n.vm.mem_write(pointer, b'\xa5' * 0x67f4)
        saved = n.vm.context_save()
        stack = bytes(n.vm.mem_read(SP - 0x2000, 0x2400))
        self.owner_toolbar_channel_writes = []

        def write(vm, access, address, size, value, data):
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not (pointer <= address and address + size <= pointer + 0x67f4 or
                    address == OWNER + 0x39de8 and size == 4):
                raise AssertionError(f'Channel constructor escaped object: {address:X}')
            self.owner_toolbar_channel_writes.append((address, size, value))

        hook = n.vm.hook_add(UC_HOOK_MEM_WRITE, write)
        try:
            n.call(0x5feb0, this=pointer)
            if n.vm.reg_read(UC_X86_REG_EAX) != pointer:
                raise AssertionError('Original channel constructor return differs')
            self._put32(OWNER_DESCRIPTOR + 0x2c, pointer)
            n.vm.reg_write(UC_X86_REG_ESI, OWNER)
            n.vm.reg_write(UC_X86_REG_EDI, OWNER_DESCRIPTOR)
            n.run(0x81811, 0x8181a)
            if n.u32(OWNER + 0x39de8) != pointer:
                raise AssertionError('Original channel pointer binding failed')
            self.owner_toolbar_channel = pointer
        finally:
            n.vm.hook_del(hook)
            n.vm.mem_write(SP - 0x2000, stack)
            n.vm.context_restore(saved)

    def continue_owner_toolbar(self):
        """Build original B0D20 controls, stopping before its character consumer."""
        n = self.native
        if (not getattr(self, 'owner_map_completed', False) or
                not getattr(self, 'owner_toolbar_messages_prepared', False) or
                not getattr(self, 'owner_toolbar_cache', None) or
                not getattr(self, 'owner_toolbar_channel', None) or
                getattr(self, 'owner_toolbar_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0x81f0d or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x34):
            raise ValueError('Retained map caller return required')
        self.owner_toolbar_attempted = True
        self.owner_toolbar_calls, self.owner_toolbar_writes = Counter(), []

        def observe(vm, address, size, data):
            self.owner_toolbar_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (MOUSE, MOUSE + MOUSE_SIZE),
                    (DISPLAY + 8, DISPLAY + 0x1f8), (BASE + 0x1b7598, BASE + 0x1b7698),
                    (self.owner_toolbar_cache, self.owner_toolbar_cache + 0x3ae54))):
                raise AssertionError(f'Toolbar write escaped objects: {address:X}')
            self.owner_toolbar_writes.append(
                (vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0x81f0d, 0xe72d0, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x8c or
                n.u32(SP - 0x8c) != BASE + 0xb129a or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise AssertionError('Toolbar changed character or pending consumer call')
        self.owner_toolbar_completed_prefix = True
        return dict(self.owner_toolbar_calls)

    def prepare_character_vitals(self, maxima_record, current_record):
        """Run explicit native packet writers without replacing pending UI state."""
        n = self.native
        if (not getattr(self, 'owner_toolbar_completed_prefix', False) or
                getattr(self, 'character_vitals_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xe72d0 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x8c):
            raise ValueError('Pending original character consumer required')
        for raw, opcode, length in ((maxima_record, 0x22, 25), (current_record, 0x2b, 21)):
            if type(raw) is not bytes or len(raw) != length or raw[0] != opcode:
                raise ValueError('Explicit role maxima/current records required')
        self.character_vitals_attempted = True
        stages = [self.character.write_role_scalars(maxima_record),
                  self.character.write_role_current_vitals(current_record)]
        expected = bytearray(self.character_prepared)
        for stage in stages:
            for _, at, size, value in stage['writes']:
                if CHARACTER_ROOT <= at < CHARACTER_ROOT + len(expected):
                    expected[at - CHARACTER_ROOT:at - CHARACTER_ROOT + size] = value.to_bytes(size, 'little')
                    self.character_written.update(range(at, at + size))
        if bytes(n.vm.mem_read(CHARACTER_ROOT, len(expected))) != expected:
            raise AssertionError('Vitals writers changed unrelated character bytes')
        self.character_prepared = bytes(expected)
        self.character_vitals_stages = stages
        self.character_vitals_prepared = True

    def continue_owner_vitals(self):
        """Execute the retained E72D0/AC070 call through its real caller return."""
        n = self.native
        if (not getattr(self, 'character_vitals_prepared', False) or
                getattr(self, 'owner_vitals_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xe72d0 or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x8c):
            raise ValueError('Fresh native vitals consumer boundary required')
        self.owner_vitals_attempted = True
        self.owner_vitals_calls, self.owner_vitals_writes = Counter(), []

        def code(vm, address, size, data):
            self.owner_vitals_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE), (MOUSE, MOUSE + MOUSE_SIZE),
                    (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (0x6400000, 0x6500000), (DISPLAY + 8, DISPLAY + 0x1f8),
                    (CHARACTER_ROOT + 0xec, CHARACTER_ROOT + 0xf0),
                    (CHARACTER_ROOT + 0xf4, CHARACTER_ROOT + 0xf8))):
                raise AssertionError(f'Vitals consumer escaped objects: {address:X}')
            self.owner_vitals_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, code), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0xe72d0, 0xb129a, instruction_limit=200000, timeout_us=10000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x7c:
            raise AssertionError('Vitals consumer did not return on the retained stack')
        self.owner_vitals_completed = True
        return dict(self.owner_vitals_calls)

    def prepare_owner_map_metadata(self):
        """Load original map rows into the existing owner table, preserving CPU."""
        n = self.native
        if (not getattr(self, 'owner_map_clock_completed_prefix', False) or
                getattr(self, 'owner_map_metadata_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc328b or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0 or
                self.owner_metadata is None or
                n.u32(OWNER + 0xcff70) != self.owner_metadata.TABLE):
            raise ValueError('Untouched map boundary and existing owner catalog required')
        self.owner_map_metadata_attempted = True
        before = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                  bytes(n.vm.mem_read(SP - 0x2000, 0x2000)))
        self.owner_map_metadata = maps = map_metadata.attach_and_load(n, owner=OWNER)
        after = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                 bytes(n.vm.mem_read(SP - 0x2000, 0x2000)))
        if before != after or maps.table != self.owner_metadata.TABLE:
            raise AssertionError('Map loader changed pending call or owner catalog binding')
        return maps.provenance

    def continue_owner_map_metadata(self):
        """Resume real C3080 lookups; stop before the unqualified map sprite call."""
        n, maps = self.native, getattr(self, 'owner_map_metadata', None)
        if (maps is None or not maps.loaded or
                not getattr(self, 'map_selector_prepared', False) or
                getattr(self, 'owner_map_lookup_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc328b or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0):
            raise ValueError('Retained map boundary, native selector and complete map catalog required')
        maps._binding()
        maps._verify_records(bound=True)
        scene = struct.unpack('<H', n.vm.mem_read(CHARACTER_ROOT + 0x14, 2))[0]
        area = struct.unpack('<H', n.vm.mem_read(CHARACTER_ROOT + 0x18, 2))[0]
        selected, base = maps.lookup(area, scene), maps.lookup(area, 0)
        if not selected['metadata'] or not base['metadata']:
            raise ValueError('This continuation requires both native map metadata bindings')
        self.owner_map_lookup_attempted = True
        self.owner_map_lookup_calls, self.owner_map_lookup_writes = Counter(), []
        self.owner_map_lookup_reads = []

        def code(vm, address, size, data):
            pc = address - BASE
            if pc == 0xc332c:
                vm.emu_stop()
                return
            if not any(lo <= pc and pc + size <= hi for lo, hi in
                       ((0xc328b, 0xc32e2), (0xc32fd, 0xc332c), *map_metadata.LOOKUP_CODE)):
                raise AssertionError(f'Unqualified map-lookup continuation instruction {pc:X}')
            self.owner_map_lookup_calls[pc] += 1

        def memory(vm, access, address, size, value, data):
            if access == UC_MEM_WRITE:
                if not (SP - 0x2000 <= address and address + size <= SP or
                        OWNER + 0x8aa4c <= address and address + size <= OWNER + 0x8aa50):
                    raise AssertionError(f'Unexpected map-lookup continuation write {address:X}')
                self.owner_map_lookup_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                                    address, size, value))
            elif not SP - 0x2000 <= address < SP:
                self.owner_map_lookup_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                    address, size, bytes(vm.mem_read(address, size))))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, code),
                 n.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)]
        try:
            n.run(0xc328b, 0xc332c, instruction_limit=10000, timeout_us=1000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x104 or
                n.u32(OWNER + 0x8aa4c) != selected['record'] or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise AssertionError('Map continuation changed source or pending call layout')
        self.owner_map_selected, self.owner_map_base = selected, base
        self.owner_map_lookup_completed_prefix = True
        return dict(self.owner_map_lookup_calls)

    def continue_owner_map_sprite(self):
        """Execute the pending map control call; retain the character-read boundary."""
        n = self.native
        if (not getattr(self, 'owner_map_lookup_completed_prefix', False) or
                not getattr(n, 'owner_map_loaded', False) or
                getattr(self, 'owner_map_sprite_attempted', False) or
                n.vm.reg_read(UC_X86_REG_EIP) != BASE + 0xc332c or
                n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x104 or
                n.u32(OWNER_RENDERER + 0xc) != OWNER_BANK):
            raise ValueError('Pending original map control and owner bank required')
        self.owner_map_sprite_attempted = True
        self.owner_map_sprite_calls, self.owner_map_sprite_writes = Counter(), []

        def observe(vm, address, size, data):
            self.owner_map_sprite_calls[address - BASE] += 1

        def write(vm, access, address, size, value, data):
            if address == 0 and size == 4:
                return  # Existing SEH adapter validates its instruction.
            if SP - 0x2000 <= address and address + size <= SP:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in (
                    (OWNER, OWNER + OWNER_SIZE),
                    (OWNER_RENDERER, OWNER_RENDERER + 0x291000),
                    (MOUSE, MOUSE + MOUSE_SIZE),
                    (0x6400000, 0x6500000))):
                raise AssertionError(f'Map control write escaped objects: {address:X}')
            self.owner_map_sprite_writes.append(
                (vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, observe),
                 n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(0xc332c, 0xc3331, instruction_limit=2000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        if (n.vm.reg_read(UC_X86_REG_ESP) != SP - 0xf0 or
                bytes(n.vm.mem_read(CHARACTER_ROOT, len(self.character_prepared))) != self.character_prepared):
            raise AssertionError('Map control changed pending stack or character source')
        self.owner_map_sprite_completed_prefix = True
        return dict(self.owner_map_sprite_calls)

    def _seed_owner_slot(self, record):
        n = self.native
        self._put(INSTANCE_DISPATCH, b'\xa5' * 0x24)
        self._put32(INSTANCE_DISPATCH + 0x20, OWNER)
        self._put(INSTANCE_INPUT, record + b'\xa5' * 16)
        self._put(OWNER_STORE - 16, b'\xa5' * 1232)
        self.owner_store_writes = []
        self.owner_store_code = []

        def code(vm, address, size, context):
            pc = address - BASE
            if pc == 0x98e2d:
                return
            if not any(lo <= pc < hi for lo, hi in (
                    (0x1193c2, 0x1193e7), (0x1194f2, 0x1194fe), (0x98dd0, 0x98e2d))):
                raise AssertionError('Unexpected owner packet instruction')
            self.owner_store_code.append(pc)

        def write(vm, access, address, size, value, context):
            if SP - 0x80 <= address < address + size <= SP + 0x40:
                return
            dest = OWNER_STORE + 44 * 24
            if not dest <= address < address + size <= dest + 20:
                raise AssertionError('Owner packet wrote outside slot44')
            self.owner_store_writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, code), n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.reg_write(UC_X86_REG_EFLAGS, 2)
            n.vm.reg_write(UC_X86_REG_EBP, INSTANCE_DISPATCH)
            n.vm.reg_write(UC_X86_REG_EAX, INSTANCE_INPUT)
            n.run(0x1193c2, 0x98e2d, instruction_limit=1000, timeout_us=1000000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        expected = bytearray(b'\xa5' * 1232)
        expected[16 + 44 * 24:36 + 44 * 24] = record[5:]
        if bytes(n.vm.mem_read(OWNER_STORE - 16, 1232)) != expected:
            raise AssertionError('Original owner slot bytes/canaries differ')
        if bytes(n.vm.mem_read(INSTANCE_INPUT, 41)) != record + b'\xa5' * 16:
            raise AssertionError('Original owner packet changed')

    def _owner_read(self, vm, access, address, size, value, context):
        if address <= OWNER + 0xcff73 and address + size > OWNER + 0xcff70:
            if self.owner_metadata is None or self.native.u32(OWNER + 0xcff70) != self.owner_metadata.TABLE:
                raise AssertionError('Unqualified owner catalog pointer read')
        self.owner_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

    def _load_messages(self):
        n = self.native
        path = ROOT.parent / 'God2/Data2/Patch/Comm/message.csvZ'
        if path.stat().st_size > 1024 * 1024:
            raise ValueError('Message source size bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598':
            raise ValueError('Pinned ProgramMsg changed')
        plain = decode_csvz(raw, limit=4 * 1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8':
            raise ValueError('Pinned ProgramMsg decode changed')
        NativeWorldUIResource._check_decompression(n, raw, plain)
        self.message_rows = parse_sections(plain, ('ProgramMsg',))['ProgramMsg']['records']
        if len(self.message_rows) != 1080:
            raise ValueError('ProgramMsg row count changed')
        self._put(MESSAGES, bytes(0xb3000))
        self.message_pointers = n.allocate(1080 * 4)
        self._put32(MESSAGES + 0xb2c68, self.message_pointers)
        self._put(MESSAGES + 8, struct.pack('<H', 2))
        for row in self.message_rows:
            line = bytes.fromhex(row['raw_record_hex']).replace(b'\r\n', b'\n')
            if len(line) >= 2048:
                raise ValueError('ProgramMsg line bound')
            n.vm.mem_write(SCRATCH, line + b'\0')
            n.call(0x51be0, SCRATCH, this=MESSAGES)
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n.vm.reg_write(UC_X86_REG_EBX, MESSAGES)
            n.vm.reg_write(UC_X86_REG_EBP, 1080)
            n.run(0x58cd4, 0x58d67)
            if n.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Original ProgramMsg row stack changed')

    def _put(self, address, raw):
        vm = self.native.vm
        cursor, limit = address & ~4095, (address + len(raw) + 4095) & ~4095
        for begin, end, _ in sorted(vm.mem_regions()):
            if end < cursor:
                continue
            if begin >= limit:
                break
            if begin > cursor:
                vm.mem_map(cursor, begin-cursor, UC_PROT_READ | UC_PROT_WRITE)
            cursor = max(cursor, end+1)
            if cursor >= limit:
                break
        if cursor < limit:
            vm.mem_map(cursor, limit-cursor, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(address, raw)

    def _put32(self, address, value):
        self._put(address, struct.pack('<I', value))

    def _observe(self, vm, address, size, context):
        self.counts[address - BASE] += 1
        returns = {0x1e710: 0x9b704, 0x25b60: 0x11027f, 0x25dc0: 0x1102b5, 0x271e0: 0x1102f3}
        pc = address - BASE
        item_call = pc in returns and self.native.u32(vm.reg_read(UC_X86_REG_ESP)) == BASE + returns[pc]
        if item_call:
            self.item_calls[pc] += 1
        if pc == 0x1e710 and item_call:
            self.item_image_args = struct.unpack('<5I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP) + 4, 20))
        if address == BASE + 0x110273:
            self.item_image_result = (vm.reg_read(UC_X86_REG_EAX),
                                      *struct.unpack('<3I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP) + 8, 12)))
            self.sprite_pool_before = bytes(vm.mem_read(DISPLAY + 0x1258, 5000 * 0xc8))
        if pc == 0x25dc0 and item_call:
            self.item_sprite_args = struct.unpack('<8I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP) + 4, 32))
        if address == BASE + RESET_BOUNDARY:
            self.reset_counts = self.counts.copy()
            self.reset_snapshots = {
                'mouse': bytes(vm.mem_read(MOUSE, MOUSE_SIZE)),
                'panels': bytes(vm.mem_read(PANELS, PANELS_SIZE)),
                'following': bytes(vm.mem_read(PANELS + PANELS_SIZE, 16)),
            }
        if address == BASE + FIRST_WINDOW_END:
            self.first_window_counts = self.counts.copy()
            self.first_window_rect_calls = self.native.rect_calls.copy()
        if address == BASE + 0x111660:
            self.second_window_counts = self.counts.copy()
            self.second_window_rect_calls = self.native.rect_calls.copy()
        if address == BASE + 0x111667:
            self.third_window_counts = self.counts.copy()
        if address == BASE + 0x1116a4:
            self.third_call_this = vm.reg_read(UC_X86_REG_ECX)
            self.third_call_args = struct.unpack('<9I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 36))
            self.selector_neighbors = {at: bytes(vm.mem_read(at, 16))
                                       for at in (SELECTOR - 16, SELECTOR + 0x351c)}

    def initialize(self):
        if self.attempted:
            raise ValueError('Fresh normal initialization only')
        self.attempted = True
        n = self.native
        n.vm.reg_write(UC_X86_REG_ESP, SP)
        n.vm.mem_write(SP, struct.pack('<II', RETURN, DESCRIPTOR))
        n.vm.reg_write(UC_X86_REG_ECX, BATTLE)
        n.run(ENTRY, self.boundary, instruction_limit=10000000, timeout_us=30000000)
        expected_stack = {CHARACTER_BOUNDARY: 0x54, CATALOG_BOUNDARY: 0x40,
                          BOUNDARY: 0x17c, OWNER_READ_BOUNDARY: 0x150}[self.boundary]
        if n.vm.reg_read(UC_X86_REG_ESP) != SP - expected_stack:
            raise AssertionError('Normal initializer call boundary stack changed')
        self.completed_prefix = True
        return self.counts
