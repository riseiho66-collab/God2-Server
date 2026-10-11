"""Current native music selection and explicit absent-device playback fixture.

Compose NativeWorldMusicMixin before NativeWorldScene/NativeColdWorldActor and
call install_music(absent_device_fixture=True) after their constructor. Game
functions execute unchanged; the only added service is the catalog's CRT calloc.
No DirectSound device, successful playback, or WAV decoding is simulated.
"""
import hashlib
import struct
from contextlib import contextmanager

from .current_cold_world_actor import NativeColdWorldActor
from .current_world_actor import ROOT, BASE, WORLD, ACTOR, MESSAGES
from .current_indoor_resources import SP, STACK
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EDI, UC_X86_REG_ESI,
                              UC_X86_REG_ESP, UC_X86_REG_EIP)

SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
SLOTS, PATHS = WORLD+0x15aac444, WORLD+0x15aac480
COUNT, PLAYING = WORLD+0x15aad380, WORLD+0x15aad384
OVERRIDE, SOUND_OWNER = WORLD+0xa87d9c4, WORLD+0xa7e05e8
CURRENT = BASE+0x19a628
SECTION = b'Map_City_Coordniate'


def music_source():
    """Validate before exposing the original unchecked reader to source bytes."""
    path = ROOT.parent/'God2'/SOURCE
    if path.stat().st_size > 1024*1024:
        raise ValueError('Music catalog source bound')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Pinned music catalog changed')
    plain = decode_csvz(raw, limit=4*1024*1024)
    if hashlib.sha256(plain).hexdigest() != PLAIN_SHA:
        raise ValueError('Pinned music catalog decode changed')
    rows = parse_catalog(plain)
    if len(rows) != 144:
        raise ValueError('Unexpected music catalog count')
    lines = plain.splitlines(keepends=True)
    first, last = rows[0]['source_line']-1, rows[-1]['source_line']
    span = (sum(map(len, lines[:first])), sum(map(len, lines[:last])))
    return raw, plain, rows, span


class NativeWorldMusicMixin:
    @contextmanager
    def music_preserve_caller(self):
        """Native probes use the host's scratch stack without consuming its frame."""
        context = self.vm.context_save()
        stack = bytes(self.vm.mem_read(STACK, 0x80000))
        try:
            yield
        finally:
            self.vm.mem_write(STACK, stack)
            self.vm.context_restore(context)

    def install_music(self, *, absent_device_fixture):
        """Install once; preserve an existing scene catalog and parser state."""
        with self.music_preserve_caller():
            self._install_music(absent_device_fixture=absent_device_fixture)

    def _install_music(self, *, absent_device_fixture):
        if absent_device_fixture is not True:
            raise ValueError('Only an explicit absent-device fixture is qualified')
        if hasattr(self, 'music_visits'):
            raise ValueError('Music already installed')
        raw, plain, rows, span = music_source()
        if self.u32(SOUND_OWNER) != 0:
            raise ValueError('Refusing to replace an existing sound owner')
        self.music_rows, self.music_source_span = rows, span
        self.music_visits, self.music_selections = [], []
        self.music_resolver_calls, self.music_playback_calls = [], []
        self.music_results, self.music_callocs = [], []
        for rva in (0x565ec, 0x59a80, 0x51a90, 0x51be0, 0xf7380, 0x4d9f0,
                    0xf76e0, 0x59d80, 0x59e00, 0xf7400, 0xf7520, 0x4dd90,
                    0x4e660, 0x4e680, 0xf7625, 0x4ec90, 0x4e080, 0x4e9e0):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._music_observe,
                                               begin=BASE+rva, end=BASE+rva))
        # Check the complete CSVZ against the real decompressor before providing
        # its text-mode row stream to the complete native catalog reader.
        context, output = self.allocate(0xd440), self.allocate(len(plain)+3)
        handle = 0x83000000
        if handle in self.handles:
            raise AssertionError('Music source handle collision')
        self.handles[handle] = [raw, 0]
        try:
            self.call(0x1760, this=context)
            self.music_loading_source = True
            self.call(0x1ec0, handle, output, this=context)
            if bytes(self.vm.mem_read(output, len(plain))) != plain:
                raise AssertionError('Original music CSV decompression mismatch')
            self.call(0x17b0, this=context)
        finally:
            self.music_loading_source = False
            self.handles.pop(handle, None)
        self.music_native_decoded_sha = hashlib.sha256(
            bytes(self.vm.mem_read(output, len(plain)))).hexdigest()
        self.music_catalog_reused = self.u32(MESSAGES+0xd2abc) != 0
        if not self.music_catalog_reused:
            previous = bytes(self.vm.mem_read(MESSAGES+4, 6))
            self.handles[handle] = [plain[span[0]:span[1]].replace(b'\r\n', b'\n'), 0]
            try:
                self.vm.mem_write(MESSAGES+4, struct.pack('<I', handle))
                self.call(0x51920, 24, this=MESSAGES)
                # Original section dispatch, including its call at 565EC.
                self.vm.reg_write(UC_X86_REG_ESP, SP)
                self.vm.reg_write(UC_X86_REG_EDI, MESSAGES)
                self.vm.mem_write(SP+0xc, struct.pack('<I', len(rows)))
                self.vm.mem_write(SP+0x18, SECTION+b'\0')
                self._slice(0x565ab, 0x565f1)
                if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                    raise AssertionError('Music catalog caller stack imbalance')
                data, position = self.handles[handle]
                if position != len(data):
                    raise AssertionError('Music reader did not consume every row')
            finally:
                self.handles.pop(handle, None)
                self.vm.mem_write(MESSAGES+4, previous)
        self.music_records = self.u32(MESSAGES+0xd2abc)
        self._verify_music_catalog()
        self._map_rw(SLOTS, PLAYING+4-SLOTS)
        self._map_rw(OVERRIDE, 4)
        self.vm.mem_protect(CURRENT & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
        # Explicit no-event input; F7520 otherwise substitutes its image table.
        self.vm.mem_write(OVERRIDE, struct.pack('<I', 0))
        self.call(0xf7380, this=WORLD)
        # DB2C allocates exactly 15360; 4D9F0 constructs a null device owner.
        self.music_sound = self.allocate(0x15360)
        self.call(0x4d9f0, this=self.music_sound)
        if self.u32(self.music_sound) != 0:
            raise AssertionError('Sound constructor did not leave an absent device')
        self.vm.mem_write(SOUND_OWNER, struct.pack('<I', self.music_sound))
        if self.music_state()['current'] != -1:
            raise AssertionError('Expected pinned cold current-music sentinel')
        self.music_installed = True

    def run(self, start, *args, **kwargs):
        if start == 0x1ec0 and getattr(self, 'music_loading_source', False):
            kwargs.setdefault('instruction_limit', 300000000)
            kwargs.setdefault('timeout_us', 90000000)
        return super().run(start, *args, **kwargs)

    def _verify_music_catalog(self):
        count = struct.unpack('<h', self.vm.mem_read(MESSAGES+0xd2aba, 2))[0]
        if count != len(self.music_rows) or not self.music_records:
            raise AssertionError('Music catalog count/pointer mismatch')
        for index, row in enumerate(self.music_rows):
            pointer = self.music_records+index*0x1a4
            selector = struct.unpack('<H', self.vm.mem_read(pointer+0xf0, 2))[0]
            if (selector != row['packed_selector'] or
                    self.u32(pointer+0xf4) & 3 != row['kind']):
                raise AssertionError('Music catalog selector mismatch')
            for column, offset in ((8, 0x30), (9, 0x70)):
                expected = bytes.fromhex(row['raw_fields_hex'][column])
                if self.string(pointer+offset, 64) != expected:
                    raise AssertionError('Music catalog path mismatch')

    def _service(self, vm, address, size, context):
        if address == BASE+0x147e23:
            sp = vm.reg_read(UC_X86_REG_ESP)
            if self.u32(sp) == BASE+0x59aad:
                count, width = self.u32(sp+4), self.u32(sp+8)
                if (count, width) != (144, 0x1a4):
                    raise AssertionError('Unqualified music catalog calloc')
                pointer = self.allocate(count*width)
                self.music_callocs.append((count, width))
                vm.reg_write(UC_X86_REG_EAX, pointer)
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        return super()._service(vm, address, size, context)

    def _music_observe(self, vm, address, size, context):
        rva = address-BASE
        self.music_visits.append(rva)
        sp = vm.reg_read(UC_X86_REG_ESP)
        if rva == 0xf76e0:
            self.music_resolver_calls.append(tuple(
                self.u32(sp+4+i*4) & 0xffff for i in range(4)))
        elif rva == 0xf7400:
            self.music_selections.append((self.u32(sp)-BASE, self.string(self.u32(sp+4))))
        elif rva == 0xf7520:
            self.music_playback_calls.append(self.u32(sp+4) & 0xffff)
        elif rva == 0x4e680:
            if self.u32(self.music_sound) != 0:
                raise AssertionError('Live-device path is outside the music fixture')
        elif rva == 0xf7625:
            self.music_results.append(vm.reg_read(UC_X86_REG_EAX))
        elif rva in (0x4ec90, 0x4e080):
            raise AssertionError('Unexpected successful/device-backed music path')

    def _require_music(self):
        if not getattr(self, 'music_installed', False):
            raise ValueError('Install music sources and the explicit device fixture first')

    def resolve_music(self, area, kind, scene, *, combat=False):
        self._require_music()
        if (any(type(value) is not int or not 0 <= value <= 65535
                for value in (area, kind, scene)) or kind > 3 or type(combat) is not bool):
            raise ValueError('Music selectors require WORDs, kind 0..3, and a boolean mode')
        with self.music_preserve_caller():
            result = self.call(0xf76e0, area, kind, scene, int(combat), this=WORLD)
        return struct.unpack('<h', struct.pack('<H', result & 0xffff))[0]

    def play_music_without_device(self, slot, *, event=0):
        """Return native state, never interpret F7520's residual EAX as success."""
        self._require_music()
        if type(slot) is not int or not -32768 <= slot <= 32767:
            raise ValueError('Music slot must be a signed WORD')
        if type(event) is not int or event not in (0, 1, 2):
            raise ValueError('Only the three original event-table entries are bounded')
        previous = bytes(self.vm.mem_read(OVERRIDE, 4))
        with self.music_preserve_caller():
            self.vm.mem_write(OVERRIDE, struct.pack('<I', event))
            try:
                self.call(0xf7520, slot & 0xffff, this=WORLD)
            finally:
                self.vm.mem_write(OVERRIDE, previous)
        return self.music_state()

    def continue_music(self):
        """Execute only 10078F..1007B0 using the actor already in native memory."""
        self._require_music()
        with self.music_preserve_caller():
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_ESI, WORLD)
            self.vm.reg_write(UC_X86_REG_EDI, self.actor_address)
            self._slice(0x10078f, 0x1007b0)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Music continuation stack imbalance')
        return self.music_state()

    def music_state(self):
        count = struct.unpack('<h', self.vm.mem_read(COUNT, 2))[0]
        if not 0 <= count <= 30:
            raise AssertionError('Native music registry capacity exceeded')
        return {
            'current': struct.unpack('<h', self.vm.mem_read(CURRENT, 2))[0],
            'playing': self.u32(PLAYING),
            'device': self.u32(self.music_sound),
            'paths': tuple(self.string(PATHS+i*128, 128) for i in range(count)),
            'slots': struct.unpack('<30h', self.vm.mem_read(SLOTS, 60)),
        }


class NativeWorldMusic(NativeWorldMusicMixin, NativeColdWorldActor):
    """Standalone cold-actor host; scene users can compose the mixin directly."""
    def __init__(self, *, absent_device_fixture):
        super().__init__()
        self.install_music(absent_device_fixture=absent_device_fixture)
