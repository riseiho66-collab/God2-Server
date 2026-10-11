"""Bounded native experiments in the debugger-owned offline client.

The 45-byte input is an explicit diagnostic logical record, never a capture or
original numerical authority. Optional phase/vitals diagnostics are separately
opted in and labeled; there is no listener or UI input.
"""
import struct

BASE = 0x400000
ACTOR_SIZE = 0xecc
STAGES = {
    360: (0x115c90, 'MONSTER_CONSTRUCTOR_ENTRY'),
    361: (0x115e0c, 'ENEMY_SOURCE_LOOKUP_RETURN'),
    362: (0x115f8c, 'FIGHT_RESOURCE_ROW_SELECTED'),
    363: (0x120650, 'MONSTER_RESOURCE_LOOKUP_ENTRY'),
    364: (0x115fc7, 'MONSTER_RESOURCE_LOOKUP_RETURN'),
    365: (0x11602a, 'MONSTER_ACTOR_CREATION_RETURN'),
    366: (0x12ccd0, 'MONSTER_DISPLAY_INITIALIZER_ENTRY'),
    367: (0x11661c, 'MONSTER_DISPLAY_INITIALIZER_RETURN'),
}


def identity_record(side):
    if type(side) is not int or side not in (0, 1):
        raise ValueError('Explicit side0 or1 required')
    record = bytearray(45)
    record[0], record[1], record[9] = 0x1c, side * 14, 1
    struct.pack_into('<HH', record, 5, 0x400, 1)
    return bytes(record)


def call_page(address, battle, side):
    for pointer in (address, battle):
        if type(pointer) is not int or not 0x10000 <= pointer < 0x7fff0000:
            raise ValueError('Bounded32-bit user pointer required')
    code = (b'\x68' + struct.pack('<I', address + 0x100) + b'\xb9'
            + struct.pack('<I', battle) + b'\xb8' + struct.pack('<I', BASE + 0x115c90)
            + b'\xff\xd0\xcc\x0f\x0b')
    return code.ljust(0x100, b'\0') + identity_record(side), len(code) - 3


def text_init_page(manager, display, owner, handle):
    if any(type(p) is not int or not 0x10000 <= p < 0x7fff0000 for p in (manager, display, owner)):
        raise ValueError('Bounded native owner pointers required')
    if type(handle) is not int or not 0 <= handle < 256:
        raise ValueError('Loaded name-registry handle required')
    code = b''.join(b'\x68' + struct.pack('<I', value) for value in (handle, owner, display))
    code += b'\xb9' + struct.pack('<I', manager) + b'\xb8' + struct.pack('<I', BASE + 0x11f920)
    code += b'\xff\xd0\xcc\x0f\x0b'
    return code, len(code) - 3


def live_string(driver, pointer, limit=256):
    from pagefile_capacity_compat import memory
    if not 0x10000 <= pointer < pointer + limit < 0x80000000:
        raise ValueError('Readable bounded native string pointer required')
    raw = bytearray()
    for offset in range(0, limit, 16):
        raw += memory(driver, pointer + offset, min(16, limit - offset))
        if 0 in raw:
            return bytes(raw[:raw.index(0)])
    raise ValueError('Native string exceeds bound')


def phase_call_page(manager):
    if type(manager) is not int or not 0x10000 <= manager < 0x7fff0000:
        raise ValueError('Bounded native manager pointer required')
    code = (b'\x6a\x00\xb9' + struct.pack('<I', manager) + b'\xb8'
            + struct.pack('<I', BASE + 0x12ac20) + b'\xff\xd0\xcc\x0f\x0b')
    return code, len(code) - 3


class LiveMonsterProbe:
    def __init__(self, run, side, probe_phase=False, probe_vitals=False):
        identity_record(side)
        self.run, self.side = run, side
        self.actor = None
        self.probe_phase = probe_phase
        self.vitals = None
        if probe_vitals:
            from current_offline_vitals_live import LiveVitalsProbe
            self.vitals = LiveVitalsProbe(self)

    @staticmethod
    def handles(index):
        return index in STAGES or (type(index) is int and 368 <= index <= 379)

    def arm_phase(self, driver, result):
        from pagefile_capacity_compat import number
        from current_offline_client_run import install_owned_page
        page = install_owned_page(driver, lambda address: phase_call_page(self.manager))
        self.phase_sp = number(driver, '@esp')
        result['phase_probe'] = {'scope': 'Explicit phase0 call after diagnostic constructor, not packet receipt',
            'manager': self.manager, 'entry_sp': self.phase_sp, 'page': page,
            'stages': [], 'before': self.snapshot(driver, 'phase-before', self.manager + 0xa7fbc58, 0x70)}
        for index, pc in ((371, BASE + 0x12ac20), (372, BASE + 0x12ae2f),
                          (373, BASE + 0x12ae35), (374, page['return_trap'])):
            driver.command(f'bp{index} {pc:x}')
        driver.command(f'r @eip = {page["address"]:x}')

    def handle_phase(self, index, event, driver, result):
        from pagefile_capacity_compat import memory, number
        state = result['phase_probe']
        expected = (371, 372, 375, 373, 374)[len(state['stages'])]
        if index != expected:
            raise ValueError('Native phase stages out of order')
        event['stage'] = {371: 'PHASE_ENTRY', 372: 'PHASE_CLOCK_CALL',
                          375: 'PHASE_OS_CLOCK_ENTRY',
                          373: 'PHASE_CLOCK_RETURN', 374: 'PHASE_RETURN'}[index]
        state['stages'].append(event['stage'])
        driver.command(f'bc {index}')
        if index == 371:
            if (number(driver, '@ecx') != self.manager or
                    number(driver, 'poi(@esp+4)') != 0 or event['sp'] != self.phase_sp - 8):
                raise ValueError('Native phase entry arguments differ')
        if index == 372:
            state['clock_target'] = number(driver, 'poi(5707bc)')
            bridge = memory(driver, state['clock_target'], 8)
            if bridge[:4] != bytes.fromhex('83ec00e9'):
                raise ValueError('Verified timer tail bridge differs')
            target = state['clock_target'] + 8 + struct.unpack_from('<i', bridge, 4)[0]
            state['bridge_hex'], state['os_clock_target'] = bridge.hex(), target
            driver.command(f'bp375 {target:x}')
        if index == 375:
            if event['pc'] != state['os_clock_target'] or event['ret'] != BASE + 0x12ae35:
                raise ValueError('OS clock target or native return address differs')
        if index == 373:
            state['clock_eax'] = event['eax']
        if index == 374:
            if event['sp'] != self.phase_sp:
                raise ValueError('Native phase RET4 stack differs')
            timestamp = struct.unpack('<I', memory(driver, self.manager + 0xa7fbcc0, 4))[0]
            count = struct.unpack('<i', memory(driver, self.manager + 0xa7fbc64, 4))[0]
            if timestamp != state['clock_eax'] or event['eax'] != int(count > 0):
                raise ValueError('Native phase timestamp or return predicate differs')
            state.update(return_eax=event['eax'], count=count, stored_timestamp=timestamp,
                         after=self.snapshot(driver, 'phase-after', self.manager + 0xa7fbc58, 0x70))
            if self.vitals:
                return self.vitals.arm(driver, result)
            return 'NATIVE_PHASE_CLOCK_RETURNED'
        return None

    def snapshot(self, driver, label, pointer, length):
        from lab import sha
        if not 0x10000 <= pointer < pointer + length < 0x80000000 or not 1 <= length <= 0x10000:
            raise ValueError('Bounded live snapshot required')
        path = self.run / (label + '.bin')
        if path.exists():
            raise ValueError('Live evidence must not be overwritten')
        output = driver.command(f'.writemem "{path.as_posix()}" {pointer:x} L{length:x}')
        if not path.is_file() or path.stat().st_size != length:
            raise ValueError('Live snapshot incomplete')
        return {'path': str(path), 'address': pointer, 'length': length,
                'sha256': sha(path), 'debugger_output': output}

    def arm(self, driver, result, world):
        from pagefile_capacity_compat import memory, number
        from current_offline_client_run import install_owned_page
        self.battle = number(driver, f'poi({world + 0xa7e05ec:x})')
        self.manager = self.battle + 0x144938
        state = result['monster_probe'] = {
            'mode': 'DIAGNOSTIC_IDENTITY_ONLY_NOT_OFFICIAL_PACKET',
            'side': self.side, 'slot': 0, 'world': world, 'battle': self.battle,
            'manager': self.manager, 'record_hex': identity_record(self.side).hex(),
            'source_selector': {'area_generation': 1, 'area': 1, 'scene': 0, 'ordinal': 1},
            'stat_update_records_supplied': 0, 'original_numeric_values_recovered': 0,
            'memory_files': []}
        if not 0x10000 <= self.battle < self.battle + 0xab3b8c4 < 0x80000000:
            return 'NATIVE_BATTLE_OWNER_UNAVAILABLE'
        state['memory_files'] += [self.snapshot(driver, 'battle-prefix', self.battle, 0x80),
                                  self.snapshot(driver, 'battle-manager-before', self.manager, 0x400)]
        state['bindings'] = {name: number(driver, f'poi({pointer:x})') for name, pointer in (
            ('game_data', self.battle + 0x28), ('display_owner', self.battle + 0x83458),
            ('rom_bank', self.manager + 8), ('renderer', self.manager + 0xc),
            ('name_registry', self.manager + 0x14))}
        pointers = struct.unpack('<168I', memory(driver, self.manager + 0x38, 168 * 4))
        state['actor_pointers'] = list(pointers)
        if (any(not 0x10000 <= p < 0x7fff0000 for p in state['bindings'].values()) or
                any(not 0x10000 <= p < 0x7fff0000 for p in pointers)):
            return 'NATIVE_MONSTER_PREREQUISITES_NOT_READY'
        self.actor = pointers[self.side * 14 * 6]
        state['actor'] = self.actor
        state['memory_files'].append(self.snapshot(driver, 'monster-before', self.actor, ACTOR_SIZE))
        application = number(driver, f'poi({world + 0xa7e05c4:x})')
        bindings = state['bindings']
        catalog, renderer, bank = (bindings[k] for k in ('game_data', 'renderer', 'rom_bank'))
        display = number(driver, f'poi({application + 0x42c:x})')
        owner = number(driver, f'poi({application + 0x428:x})')
        h0 = number(driver, f'poi({bindings["display_owner"]:x})')
        count = number(driver, f'poi({bindings["name_registry"] + 0x404:x})')
        if (catalog != application + 0x444 or catalog != number(driver, f'poi({world + 0xaa36480:x})') or
                catalog != number(driver, f'poi({self.manager + 4:x})') or
                bank != number(driver, f'poi({renderer + 0xc:x})') or
                display != number(driver, f'poi({world + 0xa7e05dc:x})') or
                owner != number(driver, f'poi({world + 0xa7e05c8:x})') or
                not 0 <= h0 < count <= 256 or memory(driver, self.manager + 0x310, 16) != bytes(16)):
            raise ValueError('Fresh original text initialization sources differ')
        name_pointer = number(driver, f'poi({bindings["name_registry"] + 4 + 4 * h0:x})')
        resource_name = live_string(driver, name_pointer)
        if not resource_name.replace(b'\\', b'/').lower().endswith(b'data3/fight/gui/fightgui2.rom'):
            raise ValueError('Original FightComm3[0] GUI binding differs')
        if memory(driver, bank + h0 * 0x1514, 4) == b'\xff' * 4:
            raise ValueError('Original FightComm3 GUI descriptor is not loaded')
        if struct.unpack('<h', memory(driver, catalog + 0xb2c6c, 2))[0] < 0x2ee:
            raise ValueError('Original message catalog bound too small')
        table = number(driver, f'poi({catalog + 0xb2c68:x})')
        strings = {}
        for ordinal in (0x2e2, 0x2e6, 0x2e7, 0x2ee):
            pointer = number(driver, f'poi({table + (ordinal - 1) * 4:x})')
            strings[str(ordinal)] = live_string(driver, pointer).hex()
        self.text_expected = (display, renderer, owner, catalog, h0)
        state['text_init'] = {'display': display, 'owner': owner, 'gui_handle': h0,
                              'gui_name_hex': resource_name.hex(), 'catalog_strings': strings,
                              'scope': 'Explicit original11F920 call, not complete battle-session initialization'}
        page = install_owned_page(driver, lambda address: text_init_page(self.manager, display, owner, h0))
        state['text_init']['page'] = page
        self.sp = number(driver, '@esp')
        driver.command(f'bp369 {BASE + 0x11f920:x}')
        driver.command(f'bp370 {page["return_trap"]:x}')
        driver.command(f'r @eip = {page["address"]:x}')
        return None

    def arm_constructor(self, driver, state):
        from pagefile_capacity_compat import number
        from current_offline_client_run import install_owned_page
        page = install_owned_page(driver, lambda address: call_page(address, self.battle, self.side))
        self.packet = page['address'] + 0x100
        self.sp = number(driver, '@esp')
        state['call_page'], state['entry_sp'] = page, self.sp
        for index, (rva, _) in STAGES.items():
            driver.command(f'bp{index} {BASE + rva:x}')
        driver.command(f'bp368 {page["return_trap"]:x}')
        driver.command(f'r @eip = {page["address"]:x}')
        return None

    def handle(self, index, event, driver, result):
        from pagefile_capacity_compat import memory, number
        if self.vitals and self.vitals.handles(index):
            return self.vitals.handle(index, event, driver, result)
        if index in (371, 372, 373, 374, 375):
            return self.handle_phase(index, event, driver, result)
        state = result['monster_probe']
        if index in (369, 370):
            event['stage'] = 'MONSTER_TEXT_BIND_ENTRY' if index == 369 else 'MONSTER_TEXT_BIND_RETURN'
            event['ecx'] = number(driver, '@ecx')
            driver.command(f'bc {index}')
            if index == 369:
                arguments = struct.unpack('<3I', memory(driver, event['sp'] + 4, 12))
                if event['ecx'] != self.manager or arguments != (self.text_expected[0], self.text_expected[2], self.text_expected[4]):
                    raise ValueError('Original text-wrapper arguments differ')
                event['arguments'] = arguments
            else:
                fields = struct.unpack('<5I', memory(driver, self.manager + 0x310, 20))
                if fields != self.text_expected or event['sp'] != self.sp:
                    raise ValueError('Original text-wrapper bindings/RET0C differ')
                state['text_init']['observed_bindings'] = fields
                event['memory_files'] = [self.snapshot(driver, 'battle-text-bound', self.manager + 0x310, 0x40)]
                self.arm_constructor(driver, state)
            return None
        event.update(stage=STAGES[index][1] if index in STAGES else 'MONSTER_CALL_RETURN',
                     ecx=number(driver, '@ecx'), stack=driver.command('dd @esp L10'))
        driver.command(f'bc {index}')
        if index == 360:
            if (event['ecx'] != self.battle or number(driver, 'poi(@esp+4)') != self.packet or
                    memory(driver, self.packet, 45) != identity_record(self.side)):
                raise ValueError('Actual monster call arguments differ')
        if index == 361:
            event['memory_files'] = [self.snapshot(driver, 'monster-source-row', event['eax'], 26)]
        if index == 362:
            pointer = number(driver, '@esi')
            event['memory_files'] = [self.snapshot(driver, 'monster-fight-row', pointer, 92)]
        if index in (365, 367, 368):
            event['memory_files'] = [self.snapshot(driver, f'monster-stage-{index}', self.actor, ACTOR_SIZE)]
        if index == 368:
            if event['sp'] != self.sp or memory(driver, self.packet, 45) != identity_record(self.side):
                raise ValueError('Native RET4 stack or immutable diagnostic record differs')
            state['return_eax'] = event['eax']
            if event['eax'] != 1:
                return 'NATIVE_MONSTER_CONSTRUCTOR_REJECTED'
            if self.probe_phase:
                self.arm_phase(driver, result)
                return None
            return 'NATIVE_MONSTER_CONSTRUCTOR_RETURNED'
        return None
