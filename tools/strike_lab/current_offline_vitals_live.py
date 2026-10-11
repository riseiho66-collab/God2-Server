"""Opt-in diagnostic values for a native receiver, never species authority."""
import struct

BASE = 0x400000


def diagnostic_record(with_actors=False):
    raw = bytearray(121)
    raw[0] = 0x88
    for slot in range(14):
        if with_actors:
            struct.pack_into('<II', raw, 5 + slot * 8, 100 if slot == 0 else 0, 50 if slot == 0 else 0)
            continue
        struct.pack_into('<II', raw, 5 + slot * 8, 1000 + slot, 50 + slot)
    return bytes(raw)


def call_page(address, battle):
    for pointer in (address, battle):
        if type(pointer) is not int or not 0x10000 <= pointer < 0x7fff0000:
            raise ValueError('Bounded32-bit pointer required')
    code = (b'\x68' + struct.pack('<I', address + 0x100) + b'\xb9'
            + struct.pack('<I', battle) + b'\xb8' + struct.pack('<I', BASE + 0x118a90)
            + b'\xff\xd0\xcc\x0f\x0b')
    return code.ljust(0x100, b'\0') + diagnostic_record(), len(code) - 3


class LiveVitalsProbe:
    def __init__(self, owner, source_key='monster_probe', run_loop=False, with_actors=False, with_grant=False):
        self.owner = owner
        self.source_key = source_key
        self.run_loop = run_loop
        self.with_actors = with_actors
        if with_grant and not (run_loop and with_actors):
            raise ValueError('Grant probe requires initialized participant loop')
        self.with_grant = with_grant
        self.action_enabled = False

    @staticmethod
    def handles(index):
        return index in (376, 377, 378, 379, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393)

    def arm(self, driver, result):
        from current_offline_client_run import install_owned_page
        from pagefile_capacity_compat import memory, number
        o = self.owner
        role = number(driver, f'poi({o.battle + 0x14:x})')
        local_slot = memory(driver, o.battle + 0x51, 1)[0]
        source = result[self.source_key]['world'] + 0x1539683c
        result['vitals_preflight'] = {'role': role, 'local_slot': local_slot,
            'role_binding_producer_rva': '111326', 'descriptor_source_offset': 16,
            'expected_role_source': source,
            'role_source_prefix': o.snapshot(driver, 'vitals-role-source', source, 0x20)}
        if not 0x10000 <= role < 0x7fff0000:
            return 'NATIVE_VITALS_ROLE_BINDING_MISSING'
        pointers = struct.unpack('<168I', memory(driver, o.manager + 0x38, 168 * 4))
        if list(pointers) != result[self.source_key]['actor_pointers']:
            raise ValueError('Native actor ownership changed before receiver probe')
        self.actors = [pointers[slot * 6] for slot in range(28)]
        self.before = [memory(driver, address + 0xde8, 16) for address in self.actors]
        self.sp = number(driver, '@esp')
        self.payload = diagnostic_payload(self.with_actors, self.with_grant)
        self.record = diagnostic_record(self.with_actors)
        page = install_owned_page(driver, lambda address:
            loop_call_page(address, o.battle, self.with_actors, self.with_grant) if self.run_loop else call_page(address, o.battle))
        self.packet = page['address'] + 0x100
        result['vitals_probe'] = {'scope': 'DIAGNOSTIC_VALUES_NOT_NATIVE_STATS_NOT_NETWORK_CAPTURE',
            'record_hex': self.record.hex(), 'page': page, 'entry_sp': self.sp,
            'actors': self.actors, 'before_hex': [b.hex() for b in self.before], 'stages': [],
            'native_loop': self.run_loop,
            'with_grant': self.with_grant, 'grant_stages': [],
            'with_actors': self.with_actors, 'payload_hex': self.payload.hex(),
            'controls_before': o.snapshot(driver, 'vitals-controls-before', o.battle + 0xa9e9c28, 0x60)}
        result[self.source_key]['stat_update_records_supplied'] = 4 if self.with_actors else 1
        stops = [(376, BASE + 0x118a90), (377, BASE + 0x12d360), (378, BASE + 0x116ac0)]
        if self.with_grant:
            stops += [(388, BASE + 0x117590), (389, BASE + 0x1177b5), (390, BASE + 0x1121f0)]
        if self.run_loop:
            ring = struct.unpack('<5I', memory(driver, o.battle + 0xa9ea4b0, 20))
            if ring[2] != ring[3] or ring[4] <= len(self.payload) or not 0x10000 <= ring[1] < 0x7fff0000:
                raise ValueError('Empty native battle queue with sufficient capacity required')
            result['vitals_probe']['ring_before'] = ring
            stops += [(384, BASE + 0x11d4e0), (385, BASE + 0x115770),
                      (386, BASE + 0x1140c0), (387, BASE + 0x115a51)]
        else:
            stops += [(379, page['return_trap'])]
        for index, pc in stops:
            driver.command(f'bp{index} {pc:x}')
        driver.command(f'r @eip = {page["address"]:x}')
        return None

    def handle(self, index, event, driver, result):
        from pagefile_capacity_compat import memory, number
        o, state = self.owner, result['vitals_probe']
        if index in (391, 392, 393):
            return self.handle_action(index, event, driver, result)
        if index == 390:
            if not self.with_grant or state['grant_stages'] != ['GRANT_ENTRY']:
                raise ValueError('Rearm outside first grant')
            event['stage'] = 'GRANT_REARM_ENTRY'
            state['rearm_entry'] = {'counter': number(driver, f'poi({o.battle + 0xa9e9c64:x})'),
                                    'ecx': number(driver, '@ecx')}
            if state['rearm_entry']['ecx'] != o.battle or state['rearm_entry']['counter'] != 0:
                raise ValueError('Rearm context or counter differs')
            driver.command('bc 390')
            return None
        if index in (388, 389):
            if not self.with_grant or index != 388 + len(state['grant_stages']):
                raise ValueError('Unexpected grant stage')
            event['stage'] = 'GRANT_ENTRY' if index == 388 else 'GRANT_RETURN'
            state['grant_stages'].append(event['stage'])
            driver.command(f'bc {index}')
            if index == 388:
                if (number(driver, '@ecx') != o.battle or
                        memory(driver, number(driver, 'poi(@esp+4)'), 17) != grant_record()):
                    raise ValueError('Grant receiver ABI or record differs')
                state['grant_sp'] = event['sp']
            else:
                state['grant_controls'] = list(struct.unpack('<3I', memory(driver, o.battle + 0xa9e9c34, 12)))
                state['grant_actors'] = list(memory(driver, o.battle + 0x51, 2))
                state['grant_counter'] = number(driver, f'poi({o.battle + 0xa9e9c64:x})')
                if (event['sp'] != state['grant_sp'] or event['eax'] != 1 or
                        state['grant_controls'][1:] != [1, 0] or state['grant_actors'][0] != 0):
                    raise ValueError('Native first grant return differs')
            return None
        order = (384, 385, 386, 376, 377, 378, 387) if self.run_loop else (376, 377, 378, 379)
        expected_index = ((386, 387)[len(state['stages']) - len(order)]
                          if state.get('awaiting_grant_dispatch') else order[len(state['stages'])])
        if index != expected_index:
            raise ValueError('Native receiver stages out of order')
        event['stage'] = {376: 'VITALS_ENTRY', 377: 'VITALS_BATCH',
                          378: 'VITALS_CLEANUP', 379: 'VITALS_RETURN',
                          384: 'VITALS_NATIVE_QUEUE', 385: 'VITALS_LOOP_ENTRY',
                          386: 'VITALS_DISPATCH_ENTRY', 387: 'VITALS_DISPATCH_RETURN'}[index]
        state['stages'].append(event['stage'])
        driver.command(f'bc {index}')
        if index == 384:
            if (number(driver, '@ecx') != o.battle + 0xa9ea4b0 or
                    number(driver, 'poi(@esp+4)') != self.packet or number(driver, 'poi(@esp+8)') != len(self.payload)):
                raise ValueError('Original queue writer arguments differ')
        if index == 385:
            state['loop_entry_eax'] = event['eax']
            ring = struct.unpack('<5I', memory(driver, o.battle + 0xa9ea4b0, 20))
            if (ring[3] - ring[2]) % ring[4] != len(self.payload):
                raise ValueError('Native queue writer length differs')
            state['ring_queued'] = ring
        if index == 386:
            state['dispatch_sp'] = event['sp']
        receiver_packet = o.battle + 0xa9e9cb0 if self.run_loop else self.packet
        if index == 376:
            if (number(driver, '@ecx') != o.battle or number(driver, 'poi(@esp+4)') != receiver_packet
                    or (not self.run_loop and event['sp'] != self.sp - 8)
                    or memory(driver, receiver_packet, 121) != self.record):
                raise ValueError('Native receiver entry differs')
            if self.with_actors:
                self.before = [memory(driver, address + 0xde8, 16) for address in self.actors]
                state['before_88_hex'] = [b.hex() for b in self.before]
                state['created_actor_snapshots'] = [o.snapshot(driver, f'dispatch-actor-{i}',
                    self.actors[i], 0xecc) for i in (0, 14)]
                handles = [struct.unpack('<h', memory(driver, self.actors[i] + 0x1a, 2))[0] for i in (0, 14)]
                state['created_actor_handles'] = handles
                if any(not 0 <= handle < 4096 for handle in handles):
                    raise ValueError('Both diagnostic participants must have real native handles')
        if index == 377:
            if number(driver, '@ecx') != o.manager or number(driver, 'poi(@esp+4)') != receiver_packet + 1:
                raise ValueError('Native batch arguments differ')
        if index in (379, 387):
            if self.with_grant and not state['grant_stages'] and not state.get('awaiting_grant_dispatch'):
                ring = struct.unpack('<5I', memory(driver, o.battle + 0xa9ea4b0, 20))
                if (ring[3] - ring[2]) % ring[4] != 17:
                    raise ValueError('First bulk dispatch must leave exactly the grant record')
                state['ring_after_bulk'] = ring
                state['awaiting_grant_dispatch'] = True
                for bp, pc in ((386, BASE + 0x1140c0), (387, BASE + 0x115a51)):
                    driver.command(f'bp{bp} {pc:x}')
                return None
            if self.with_grant and (state['grant_stages'] != ['GRANT_ENTRY', 'GRANT_RETURN'] or 'rearm_entry' not in state):
                raise ValueError('Dispatch returned without completed first grant and rearm')
            after = [memory(driver, p + 0xde8, 16) for p in self.actors]
            state.update(after_hex=[b.hex() for b in after], return_eax=event['eax'],
                controls_after=o.snapshot(driver, 'vitals-controls-after', o.battle + 0xa9e9c28, 0x60))
            expected = [self.record[5 + i * 8:13 + i * 8] + self.before[i][8:]
                        if i < 14 else self.before[i] for i in range(28)]
            stack_ok = event['sp'] == (state['dispatch_sp'] + 12 if self.run_loop else self.sp)
            if (not stack_ok or (not self.run_loop and event['eax'] != 1) or after != expected or
                    memory(driver, self.packet, len(self.payload)) != self.payload):
                raise ValueError('Native receiver return, vitals, maxima or immutable input differ')
            if self.run_loop:
                ring = struct.unpack('<5I', memory(driver, o.battle + 0xa9ea4b0, 20))
                state['ring_after'] = ring
                if ring[2:4] != (0, 0):
                    raise ValueError('Dispatched native queue did not empty')
                if self.action_enabled:
                    return self.arm_action(driver, result)
                return 'NATIVE_BATTLE_DISPATCH_RETURNED'
            return 'NATIVE_VITALS_RECEIVER_RETURNED'
        return None

    def arm_action(self, driver, result):
        from current_offline_client_run import install_owned_page
        from pagefile_capacity_compat import memory, number
        battle = self.owner.battle
        network = number(driver, f'poi({battle + 0x10:x})')
        if memory(driver, network + 0x2cb8, 1) != b'\0':
            raise ValueError('Action diagnostic requires disconnected transport')
        page = install_owned_page(driver, lambda address: action_call_page(address, battle))
        result['action_probe'] = {'scope': 'EXPLICIT_NATIVE_CALL_NOT_UI_NOT_NETWORK_DELIVERY',
            'page': page, 'entry_sp': number(driver, '@esp'), 'network': network, 'stages': []}
        for bp, pc in ((391, BASE + 0x118e50), (392, page['return_trap']), (393, BASE + 0x1191ee)):
            driver.command(f'bp{bp} {pc:x}')
        driver.command(f'r @eip = {page["address"]:x}')
        return None

    def handle_action(self, index, event, driver, result):
        from pagefile_capacity_compat import memory, number
        state = result['action_probe']
        expected = (391, 393, 392)
        if index != expected[len(state['stages'])]:
            raise ValueError('Native action stage order differs')
        event['stage'] = {391: 'ACTION_ENTRY', 393: 'ACTION_POST_BUILD', 392: 'ACTION_RETURN'}[index]
        state['stages'].append(event['stage'])
        driver.command(f'bc {index}')
        if index == 391:
            args = struct.unpack('<4I', memory(driver, event['sp'] + 4, 16))
            if args != (1, 0, 1, state['page']['address'] + 0x100) or number(driver, '@ecx') != self.owner.battle:
                raise ValueError('Native action ABI differs')
        elif index == 393:
            state['logical_hex'] = (b'\x35' + memory(driver, event['sp'] + 0x10, 16)).hex()
            state['opcode_provenance'] = 'Static native queue call opcode; disconnected branch skips enqueue'
        else:
            state['controls_after'] = list(struct.unpack('<3I', memory(driver, self.owner.battle + 0xa9e9c34, 12)))
            state['return_eax'] = event['eax']
            if event['sp'] != state['entry_sp'] or event['eax'] != 1 or state['controls_after'] != [1, 0, 0]:
                raise ValueError('Native action return or control consumption differs')
            raw = bytes.fromhex(state['page']['hex'])
            if memory(driver, state['page']['address'], len(raw)) != raw:
                raise ValueError('Action input changed')
            return 'NATIVE_DISCONNECTED_ACTION_RETURNED'
        return None


def control_snapshot(driver, battle):
    """Read native grant/rearm prerequisites without changing client state."""
    from pagefile_capacity_compat import number
    return {name: number(driver, f'poi({battle + offset:x})') for name, offset in (
        ('panel', 0xa9e9c28), ('waiting', 0xa9e9c34),
        ('first_grant', 0xa9e9c38), ('second_grant', 0xa9e9c3c),
        ('counter', 0xa9e9c64), ('completed_counter', 0xa9e9c68))}


def grant_record():
    return bytes((0x86, 5, 0, 1, 0)) + bytes(12)


def action_call_page(address, battle, *, skill=False, target=14):
    call_page(address, battle)
    if type(skill) is not bool:
        raise ValueError('Explicit Boolean skill mode required')
    if type(target) is not int or not 0<=target<28:
        raise ValueError('Explicit battle target0..27 required')
    code = (b'\x68' + struct.pack('<I', address + 0x100) + b'\x6a\x01\x6a\x00\x6a'
            + bytes((3 if skill else 1,)) + b'\xb9'
            + struct.pack('<I', battle) + b'\xb8' + struct.pack('<I', BASE + 0x118e50)
            + b'\xff\xd0\xcc\x0f\x0b')
    return code.ljust(0x100, b'\0') + bytes((target,)) + b'\xff' * 13, len(code) - 3


def skill_select_call_page(address, battle):
    call_page(address, battle)
    # Native target setup writes two counts at context+4; use owned stack memory.
    code = (b'\x83\xec\x08\x31\xc0\x89\x04\x24\x89\x44\x24\x04\x8b\xc4'
            b'\x6a\x00\x50\xb9' + struct.pack('<I', battle)
            + b'\xb8' + struct.pack('<I', BASE + 0x1151a0)
            + b'\xff\xd0\x83\xc4\x08\xcc\x0f\x0b')
    return code, len(code) - 3


def diagnostic_payload(with_actors=False, with_grant=False):
    if type(with_actors) is not bool:
        raise ValueError('Explicit Boolean actor mode required')
    if type(with_grant) is not bool or (with_grant and not with_actors):
        raise ValueError('Grant requires explicit participant mode')
    prefix = b''
    if with_actors:
        from tools.strike_lab.current_offline_monster_live import identity_record
        prefix = identity_record(0) + identity_record(1)
        for kind, position, maximum, current in ((0, 0, 120, 100), (1, 0, 80, 50), (0, 14, 150, 150)):
            record = bytearray(17)
            record[:3] = bytes((0x86, kind, position))
            struct.pack_into('<II', record, 5, maximum, current)
            prefix += bytes(record)
    return prefix + diagnostic_record(with_actors) + (grant_record() if with_grant else b'')


def loop_call_page(address, battle, with_actors=False, with_grant=False):
    call_page(address, battle)  # Shared pointer guards.
    payload = diagnostic_payload(with_actors, with_grant)
    code = (b'\x68' + struct.pack('<I', len(payload)) + b'\x68' + struct.pack('<I', address + 0x100)
            + b'\xb9' + struct.pack('<I', battle + 0xa9ea4b0)
            + b'\xb8' + struct.pack('<I', BASE + 0x11d4e0) + b'\xff\xd0')
    # Writable output belongs to this lab call's own stack, not its RX page.
    code += (b'\x83\xec\x04\x8b\xc4\x50\xb9' + struct.pack('<I', battle)
             + b'\xb8' + struct.pack('<I', BASE + 0x115770) + b'\xff\xd0\x83\xc4\x04\xcc\x0f\x0b')
    return code.ljust(0x100, b'\0') + payload, len(code) - 3
