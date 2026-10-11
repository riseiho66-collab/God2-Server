"""Explicit diagnostic battle session; native owners, synthetic event context."""
import struct

BASE = 0x400000


def call_page(address, battle, application, world, owner, catalog):
    for pointer in (address, battle, application, world, owner, catalog):
        if type(pointer) is not int or not 0x10000 <= pointer < 0x7fff0000:
            raise ValueError('Bounded native pointer required')
    if world + 0x1539683c >= 0x80000000:
        raise ValueError('Embedded world role exceeds32-bit user range')
    code = (b'\x68' + struct.pack('<I', address + 0x80) + b'\xb9'
            + struct.pack('<I', battle) + b'\xb8' + struct.pack('<I', BASE + 0x1112c0)
            + b'\xff\xd0\xcc\x0f\x0b')
    descriptor = struct.pack('<7I', application, address + 0x100,
        world + 0xa7f2f6c, owner, world + 0x1539683c, catalog, world + 0x15383410)
    # Explicit zero diagnostic event, not an observed server message.
    return (code.ljust(0x80, b'\0') + descriptor).ljust(0x100, b'\0') + bytes(0x3ec), len(code) - 3


class LiveBattleInitProbe:
    def __init__(self, run, probe_vitals=False, run_loop=False, with_actors=False, with_grant=False):
        self.run = run
        self.vitals = None
        if probe_vitals:
            from current_offline_vitals_live import LiveVitalsProbe
            self.vitals = LiveVitalsProbe(self, 'battle_init_probe', run_loop, with_actors, with_grant)

    def snapshot(self, driver, label, pointer, length):
        from current_offline_monster_live import LiveMonsterProbe
        return LiveMonsterProbe.snapshot(self, driver, label, pointer, length)

    @staticmethod
    def handles(index):
        return type(index) is int and 376 <= index <= 393

    def arm(self, driver, result, world):
        from pagefile_capacity_compat import memory, number
        from current_offline_client_run import install_owned_page
        self.world = world
        self.battle, application, owner, catalog = [number(driver, f'poi({world + offset:x})')
            for offset in (0xa7e05ec, 0xa7e05c4, 0xaa3647c, 0xaa36480)]
        if memory(driver, self.battle + 0x14, 4) != bytes(4):
            raise ValueError('Fresh unbound battle owner required')
        self.manager = self.battle + 0x144938
        self.sp = number(driver, '@esp')
        page = install_owned_page(driver, lambda address:
            call_page(address, self.battle, application, world, owner, catalog))
        self.descriptor = page['address'] + 0x80
        result['battle_init_probe'] = {'scope': 'NATIVE_INITIALIZER_WITH_ZERO_DIAGNOSTIC_EVENT_NOT_NETWORK',
            'world': world, 'battle': self.battle, 'entry_sp': self.sp, 'page': page,
            'stages': [], 'expected_role': world + 0x1539683c}
        for index, pc in ((380, BASE + 0x1112c0), (381, BASE + 0x11132f),
                          (382, BASE + 0x11151b), (383, page['return_trap'])):
            driver.command(f'bp{index} {pc:x}')
        driver.command(f'r @eip = {page["address"]:x}')

    def handle(self, index, event, driver, result):
        from pagefile_capacity_compat import memory, number
        if self.vitals and self.vitals.handles(index):
            return self.vitals.handle(index, event, driver, result)
        state = result['battle_init_probe']
        if index != 380 + len(state['stages']):
            raise ValueError('Native initialization stage order differs')
        event['stage'] = {380: 'BATTLE_INIT_ENTRY', 381: 'BATTLE_OWNERS_BOUND',
                          382: 'BATTLE_TEXT_INITIALIZED', 383: 'BATTLE_INIT_RETURN'}[index]
        state['stages'].append(event['stage'])
        driver.command(f'bc {index}')
        if index == 380 and (number(driver, '@ecx') != self.battle or
                number(driver, 'poi(@esp+4)') != self.descriptor or event['sp'] != self.sp - 8):
            raise ValueError('Native initializer ABI differs')
        if index in (381, 383):
            role = number(driver, f'poi({self.battle + 0x14:x})')
            if role != state['expected_role']:
                raise ValueError('Native role binding differs')
            state['observed_role'] = role
        if index == 383:
            if event['sp'] != self.sp or event['eax'] != 1:
                raise ValueError('Native initializer return differs')
            state.update(return_eax=event['eax'],
                battle_prefix_hex=memory(driver, self.battle, 0x80).hex(),
                control_hex=memory(driver, self.battle + 0xa9e9c28, 0x60).hex())
            if memory(driver, state['page']['address'], len(bytes.fromhex(state['page']['hex']))) != bytes.fromhex(state['page']['hex']):
                raise ValueError('Immutable diagnostic descriptor changed')
            if self.vitals:
                pointers = struct.unpack('<168I', memory(driver, self.manager + 0x38, 168 * 4))
                if any(not 0x10000 <= p < 0x7fff0000 for p in pointers):
                    raise ValueError('Native initialized actor table invalid')
                state['actor_pointers'] = list(pointers)
                return self.vitals.arm(driver, result)
            return 'NATIVE_BATTLE_INITIALIZER_RETURNED'
        return None
