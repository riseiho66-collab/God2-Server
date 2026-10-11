"""Bounded current-image protocol audit; JSON stdout, never a server dispatcher.

Complete byte-domain receive-length census, selected direction-qualified gaps,
and a source snapshot of formal routes. Neither a rule engine nor live proof.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
TABLE_RVA, TABLE_COUNT = 0x1324, 254
WORLD_TABLE_RVA = 0x6b5d4
# These route conclusions are a dated inspection, not a C++ call-graph analyzer.
# Refuse to carry them forward across edits to the inspected runtime bridge.
ROUTE_SOURCE_SHA256 = {
    'src/net/Session.cpp': 'efc85cea0999ff313c79f6373c5ca72a80d7a84f12595896584d7240c82f48ff',
    'src/net/Session.h': '5bf7d52a9d2185ba1191a397ef64635a28d7f47009675f70cddaf59f6a09531f',
    'src/protocol/RecoveredWorldRecords.h': 'faf7ca453b592965138cbf562dfa7d46f5ec0e0d5cf4a199e0bb5720398525c8',
    'src/protocol/RecoveredBattleCommand.h': 'f88e6ba32bb6de0753281694cdc97a89ae9867b8a885cb8bb3e81cc7bfcc221c',
    'src/protocol/RecoveredSkillCommand.h': '80ca0e5a77c31e98daa69cc90f0a5169f5a6338b63d0eac56b8164c5f55c276b',
    'src/protocol/RecoveredQuestClose.h': 'e0e6c1136a9265ea0ab3c7c10f8af01a6db1c2fa66939b8b72d8b5dc64425974',
    'src/protocol/RecoveredQuestAction.h': 'dfcc2420bbd2c3fbfee02796da1008afb5e88e1dc52be9356877ed0df1db48f3',
    'src/protocol/RecoveredMovement.h': '4924afbabc17ed26e8de05147036167c8f05d5cdb0180138a3cfb08e3733ae72',
    'src/core/Application.cpp': 'fd5edec740a94784b24252fc2915fe4db7eebf0ee93549e9a49a1b77536ea369',
    'src/handlers/RecoveredMovementService.cpp': '6fd21ea5019690613eb272eb4f4d423cfb10095e71cc046e3598786ade602419',
}
STATUS_DEFINITIONS = {
    'NATIVE_ONLY': 'Current native contract; no separately identified codec/runtime route.',
    'CODEC_ONLY': 'Offline codec/model exists; no qualified formal route in this audit.',
    'TRANSPORT_ROUTE': 'Session parses and dispatches typed records to an optional callback; Application has no authoritative handler for this operation. Not gameplay completion.',
    'RUNTIME_ROUTE': 'Inspected formal source connects framing, state gate and callback/emitter; conditional on configuration, not live acceptance.',
    'CLIENT_ACCEPTED': 'Requires a matching live current-client transaction through that formal route; never inferred from native emulation.',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def qualified_image(path=IMAGE):
    raw = Path(path).read_bytes()
    if digest(raw) != IMAGE_SHA256:
        raise ValueError('Pinned current image mismatch; requalification required')
    return raw


def coverage_status(*, codec=False, transport_route=False, runtime_route=False, acceptance_kind=None):
    if acceptance_kind not in (None, 'bounded_native', 'live_current_client'):
        raise ValueError('Unknown acceptance evidence kind')
    if acceptance_kind == 'live_current_client':
        if not runtime_route:
            raise ValueError('Client acceptance must identify the formal runtime route')
        return 'CLIENT_ACCEPTED'
    return ('RUNTIME_ROUTE' if runtime_route else 'TRANSPORT_ROUTE' if transport_route
            else 'CODEC_ONLY' if codec else 'NATIVE_ONLY')


def call_binding(raw, pc, target):
    if raw[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0] != target:
        raise AssertionError(f'Native call changed at RVA {pc:X}')
    return {'call_rva': pc, 'target_rva': target, 'hex': raw[pc:pc + 5].hex()}


def span(raw, start, end):
    return {'start_rva': start, 'end_rva_exclusive': end,
            'sha256': digest(raw[start:end])}


def producer_contracts(raw):
    contracts = []
    for opcode, payload, rva, expected, call in (
        (0x85, 6, 0x97de7, '6a06526885000000', 0x97df3),
        (0x25, 4, 0x96372, '6a04506a25', 0x9637b),
        (0x35, 16, 0x1191db, '6a10506a35', 0x1191e0),
        (0x2e, 6, 0x157af, '6a06526a2e', 0x157b8),
        (0x30, 1, 0x11764, '6a01506a30', 0x11770),
    ):
        signature = bytes.fromhex(expected)
        if raw[rva:rva + len(signature)] != signature:
            raise AssertionError('Native producer argument binding changed')
        contracts.append({'direction': 'C2S', 'layer': 'logical', 'opcode': opcode,
            'payload_size': payload, 'logical_size': payload + 1,
            'argument_rva': rva, 'argument_hex': expected,
            'queue_call': call_binding(raw, call, 0x132e0),
            'proof': 'Pinned native arguments to queue append; only quest85 is executed by this audit'})
    return contracts


class NativeLengths:
    """Unchanged x86, RX image, closed code/data ranges, explicit return budget."""
    STACK, STATE = 0x3000000, 0x3100000
    SP, RETURN = STACK + 0x800, BASE + 0x1013

    def __init__(self, raw):
        if digest(raw) != IMAGE_SHA256:
            raise ValueError('Pinned current image mismatch')
        sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
        import unicorn as uc
        from unicorn import x86_const as x86
        self.uc, self.x86, self.raw = uc, x86, raw
        self.vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        self.vm.mem_map(BASE, (len(raw) + 4095) & ~4095, uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        self.vm.mem_write(BASE, raw)
        self.vm.mem_map(self.STACK, 4096, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.vm.mem_map(self.STATE, 0x3000, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.vm.hook_add(uc.UC_HOOK_CODE, self._code)
        self.vm.hook_add(uc.UC_HOOK_MEM_READ | uc.UC_HOOK_MEM_WRITE, self._memory)

    def reg(self, name, value=None):
        register = getattr(self.x86, 'UC_X86_REG_' + name)
        if value is None:
            return self.vm.reg_read(register)
        self.vm.reg_write(register, value)

    def _code(self, vm, address, size, context):
        if address in self.stops:
            vm.emu_stop()
            return
        rva = address - BASE
        if not any(lo <= rva and rva + size <= hi for lo, hi in self.code):
            raise AssertionError(f'Unexpected native instruction {rva:X}')
        self.trace.append(rva)

    def _memory(self, vm, access, address, size, value, context):
        stack = self.SP - 64 <= address and address + size <= self.SP + 64
        data = any(lo <= address and address + size <= hi for lo, hi in self.reads)
        if not stack and (access == self.uc.UC_MEM_WRITE or not data):
            raise AssertionError(f'Unexpected native data access {address:X}/{size}')

    def execute(self, start, stops, code, reads=()):
        self.stops, self.code, self.reads, self.trace = set(stops), code, reads, []
        self.vm.emu_start(BASE + start, 0, count=64, timeout=100000)
        if self.reg('EIP') not in self.stops:
            raise AssertionError('Native instruction/time budget exhausted')
        return self.trace[:]

    def query(self, value):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected one raw u32 query argument')
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)
        self.vm.mem_write(self.SP, struct.pack('<II', self.RETURN, value))
        trace = self.execute(0x15840, (self.RETURN,),
                             ((0x15840, 0x15850), (0x1000, 0x1013), (0x1200, 0x1322)),
                             ((BASE + TABLE_RVA, BASE + TABLE_RVA + 4 * TABLE_COUNT),))
        if self.reg('ESP') != self.SP + 8:
            raise AssertionError('Native query stack imbalance')
        signed = struct.unpack('<i', struct.pack('<I', self.reg('EAX')))[0]
        return signed, trace

    def variable_guard(self, length):
        """Only after three header bytes exist; no assertion helper or I/O run."""
        if type(length) is not int or not 0 <= length <= 65535:
            raise ValueError('Expected raw header WORD')
        self.vm.mem_write(self.STATE + 0x2cc0, struct.pack('<IBH', 3, 0x7a, length))
        self.reg('ESI', self.STATE)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)
        stops = {0x13534: 'ASSERTION_BOUNDARY', 0x1359a: 'LIMIT_BRANCH',
                 0x13560: 'NEEDS_BODY_BYTE', 0x135c9: 'BUFFERED_COUNT_SATISFIED'}
        trace = self.execute(0x1351f, (BASE + r for r in stops), ((0x1351f, 0x13560),),
                             ((self.STATE + 0x2cc0, self.STATE + 0x2cc7),))
        rva = self.reg('EIP') - BASE
        return {'word': length, 'queried_length': self.reg('EDI'), 'stop_rva': rva,
                'result': stops[rva], 'trace_rvas': trace}


def native_catalog(raw):
    calls = [call_binding(raw, a, b) for a, b in (
        (0x134c8, 0x15840), (0x15845, 0x1000), (0x100a, 0x1200),
        (0x68b24, 0x13420), (0x68b47, 0x13650), (0x11431c, 0x15840))]
    if raw[0x1204:0x1209] != bytes.fromhex('3dfd000000'):
        raise AssertionError('Native table upper bound changed')
    if raw[0x120f:0x1216] != bytes.fromhex('ff248524134000'):
        raise AssertionError('Native length table address changed')
    if raw[0x68b61:0x68b68] != bytes.fromhex('ff2485d4b54600'):
        raise AssertionError('Native world dispatch table address changed')
    machine = NativeLengths(raw)
    rows = []
    for opcode in range(256):
        result, trace = machine.query(opcode)
        target = (struct.unpack_from('<I', raw, TABLE_RVA + 4 * opcode)[0] - BASE
                  if opcode < TABLE_COUNT else 0x131e)
        if target not in trace:
            raise AssertionError('Table target was not executed')
        if raw[target] == 0xb8 and raw[target + 5] == 0xc3:
            static = struct.unpack_from('<i', raw, target + 1)[0]
        elif raw[target:target + 4] == bytes.fromhex('83c8ffc3'):
            static = -1
        else:
            raise AssertionError('Unqualified native length leaf')
        if static != result or result not in (-1, -2) and result <= 0:
            raise AssertionError('Native/static length disagreement')
        world = (struct.unpack_from('<I', raw, WORLD_TABLE_RVA + 4 * opcode)[0] - BASE
                 if opcode < TABLE_COUNT else None)
        rows.append({'opcode': opcode, 'opcode_hex': f'{opcode:02X}',
                     'direction': 'S2C_RECEIVE_QUERY', 'layer': 'logical',
                     'table_entry_rva': TABLE_RVA + 4 * opcode if opcode < TABLE_COUNT else None,
                     'length_leaf_rva': target, 'native_return': result,
                     'length_kind': 'FIXED' if result > 0 else 'VARIABLE_U16' if result == -2 else 'UNSUPPORTED',
                     'logical_size': result if result > 0 else None,
                     'world_dispatch_rva': world, 'world_default': world == 0x6b517,
                     'trace_rvas': trace, 'implementation_status': 'NOT_ASSESSED',
                     'original_rules': 'UNKNOWN'})
    return {'table_rva': TABLE_RVA, 'table_entries': TABLE_COUNT,
            'byte_domain_queries': len(rows), 'counts': dict(Counter(r['length_kind'] for r in rows)),
            'call_bindings': calls,
            'spans': [span(raw, a, z) for a, z in ((0x1000, 0x1013), (0x1200, 0x1322),
                       (TABLE_RVA, TABLE_RVA + 4 * TABLE_COUNT), (0x15840, 0x15850),
                       (0x13497, 0x135c9), (0x68b1c, 0x68b68),
                       (WORLD_TABLE_RVA, WORLD_TABLE_RVA + 4 * TABLE_COUNT),
                       (0x114315, 0x114358), (0x114634, 0x1146ca))],
            'variable_guard_probes': [machine.variable_guard(n) for n in (0, 1, 2, 3, 27, 2559, 2560, 2561, 65535)],
            'variable_scope': 'WORD at logical+1 is compared as total logical length after 3 bytes. Guard slice only; short lengths are not certified valid records. 2560 takes limit branch; >2560 stops before assertion.',
            'rows': rows}


def source_snapshot(root=ROOT):
    """Bounded production call-site inventory, not a repository/corpus search."""
    paths = {Path('src/core/Application.cpp')}
    for directory in ('src/net', 'src/handlers', 'src/protocol'):
        for suffix in ('*.cpp', '*.h'):
            paths.update(p.relative_to(root) for p in (root / directory).glob(suffix))
    files = {}
    for path in sorted(paths):
        raw = (root / path).read_bytes()
        files[path.as_posix()] = {'sha256': digest(raw), 'text': raw.decode('utf-8-sig')}
    return files


def source_anchor(files, path, needle):
    text = files[path]['text']
    at = text.find(needle)
    if at < 0:
        raise AssertionError(f'Formal source anchor changed: {path}: {needle}')
    return {'path': path, 'line': text.count('\n', 0, at) + 1, 'text': needle,
            'file_sha256': files[path]['sha256']}


def runtime_references(files, symbol):
    # References are evidence to inspect, never an automatic runtime-route grant.
    result = []
    for path, item in files.items():
        if path.startswith('src/protocol/'):
            continue
        for number, line in enumerate(item['text'].splitlines(), 1):
            if re.search(r'\b' + re.escape(symbol) + r'\b', line):
                result.append({'path': path, 'line': number, 'text': line.strip()})
    return result


def formal_contracts(raw, files):
    for path, expected in ROUTE_SOURCE_SHA256.items():
        if files[path]['sha256'] != expected:
            raise AssertionError(f'Formal route snapshot changed; reaudit required: {path}')
    session = 'src/net/Session.cpp'
    movement = 'src/protocol/RecoveredMovement.h'
    application = 'src/core/Application.cpp'
    common = [source_anchor(files, p, n) for p, n in (
        (session, 'if(s.c2s0002_state==C2S0002State::WorldTailAccepted)'),
        (session, 's.feed_world(std::span<const std::uint8_t>(s.read_bytes.data(),size));return;'),
        (session, 'RecoveredWorldRecords::parse_frame('),
        (movement, 'if(decoded[i]==0x30)'), (movement, 'else if(decoded[i]==0x2e)'),
        (movement, '} else return std::nullopt;'),
        (session, 'if(!batch) { fail("World frame contract rejected");return; }'),
        (session, 'response=s.character_handlers.movement(*self,requests);'),
        (application, 'game_handlers.movement=[&]'),
        (application, 'return recovered_movement->move(session.id(),session.account_id,session.character_id,requests);'),
        (application, 'if(config.recovered_dual_connection)'),
        (application, 'if(config.recovered_world_entry)'),
        (application, 'if(config.recovered_movement)'),
        ('src/handlers/RecoveredMovementService.cpp', 'const auto ack=RecoveredMovement::ack(request.sequence);'),
        (session, 's.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});'))]
    # Fail closed on a widened parser. A new branch needs a new route audit.
    branches = re.findall(r'decoded\[i\]\s*==\s*(0x[0-9a-fA-F]+)', files[movement]['text'])
    if branches != ['0x30', '0x2e']:
        raise AssertionError('World logical dispatcher changed; reaudit required')
    world_records = 'src/protocol/RecoveredWorldRecords.h'
    cases = re.findall(r'^\s*case ([^:]+(?:::[^:]+)?):', files[world_records]['text'], re.M)
    if cases != ['0x35', '0x2e', '0x30', 'RecoveredInventoryItemRequest::opcode',
                 'RecoveredQuestAction::opcode', 'RecoveredQuestClose::opcode']:
        raise AssertionError('Typed world dispatcher changed; reaudit required')
    if re.search(r'\bworld_records\s*=', files[application]['text']):
        raise AssertionError('Application acquired typed world policy; reaudit required')
    transport = [source_anchor(files, p, n) for p, n in (
        (session, 'auto result=s.character_handlers.world_records(*self,records);'),
        (session, 'accepted=result.has_value();'),
        (session, 'accepted=accepted && valid_world_response(response);'),
        (session, 'fail("Recovered world handler unavailable");return;'),
        ('src/net/Session.h', 'Session&,std::span<const RecoveredWorldRecords::Record>)> world_records;'),
        (world_records, 'RecoveredInventoryItemRequest::decode(remaining.first(size))'),
        (world_records, 'RecoveredQuestAction::decode(remaining.first(size))'),
        (world_records, 'RecoveredQuestClose::decode(remaining.first(size))'))]
    definitions = [
        ('battle_vitals_batch', 'S2C', 0x88, 121, 'Battle; side0 slots0..13, all actor pointers required', 'RecoveredBattleVitalsBatch',
         'src/protocol/RecoveredBattleVitalsBatch.h', 'static std::optional<Record> parse_logical(',
         '118A90 continuously executes12D360,116AC0,120300,5F450 and returns under explicit inactive-resource conditions with168 actor pointers. Local slot FF; logical DWORD pairs copy into side0 DE8/DEC, cleanup preserves vitals. No live acceptance or stat generation.',
         'Recover full battle roster/authority and opaque header/tail semantics before emission; native writer dereferences missing actors unchecked.'),
        ('battle_vitals', 'S2C', 0x86, 17, 'Battle kinds 0/1; positions 0..27, enemy MP not applied', 'RecoveredBattleVitals',
         'src/protocol/RecoveredBattleVitals.h', 'static std::optional<Record> parse_logical(',
         '114332 -> 117230/1173A0 -> native setters -> E71E0; actor DE8/DEC/DF0/DF4 map to current HP/MP and maxima. Packet +9 current, +5 maximum. Format/consumer semantics, not monster values or damage rules.',
         'Establish original monster identity/value authority and battle state before emission. Enemy kind1 returns without actor lookup. Lossless codec only; caller establishes direction and battle context.'),
        ('battle_result_flags', 'S2C', 0x86, 17, 'Battle discriminator 3; positions 0..27 qualified subset', 'RecoveredBattleResultFlags',
         'src/protocol/RecoveredBattleResultFlags.h', 'static std::optional<Record> parse_logical(',
         '114332 -> 114464 -> 117480 -> 12C3E0; bit-0 normalization and entity field copies only. Not C2S86 dialogue close, damage computation or authoritative flag construction.',
         'Recover battle authority and state before installing an S2C emitter. This owning lossless codec has no runtime route; callers must establish direction and battle context.'),
        ('npc_record', 'S2C', 0x72, 21, 'World', 'RecoveredNpcRecord',
         'src/protocol/RecoveredNpcRecord.h', 'static std::optional<RecoveredNpcRecord> parse(',
         'World receive table -> 6A68B; 6AA89 -> CC380. Resource selectors/placement/eligibility and bytes 5..16 are not server construction rules.',
         'Session::Impl world S2C queue; RecoveredWorldFrame::encode; account/scene-owned NPC projection before emitting RecoveredNpcRecord::encode.'),
        ('quest_journal', 'S2C', 0xdb, 13, 'World; subtypes 4/5 only', 'RecoveredQuestSync',
         'src/protocol/RecoveredQuestSync.h', 'static std::optional<SlotUpdate> decode(',
         'World receive table -> 6B44E -> 854F0; C9670 stores journal projection. Authoritative slot values, acceptance, completion, rewards and persistence unknown.',
         'Session::RecoveredCharacterHandlers needs quest callback/state; emit encodeSlotLogical/clearSlotLogical through RecoveredWorldFrame only after authoritative transition.'),
        ('instance_update', 'S2C', 0x3b, 25, 'World; slot 0..49 codec subset', 'RecoveredInstanceUpdate',
         'src/protocol/RecoveredInstanceUpdate.h', 'static std::optional<Record> parse_logical(',
         'World receive table -> 6A029 -> 98DD0; store at 98E2B. Opaque 20-byte instance construction, ownership and gameplay transitions unknown.',
         'Formal game service must own instance state and produce qualified bytes before a Session S2C route; encode_logical is lossless only.'),
        ('inventory_projection', 'S2C', 0x41, 5, 'World', 'RecoveredInventory',
         'src/protocol/RecoveredInventory.h', 'struct RecoveredInventory',
         'World receive table -> 6A04D -> 991E0. Visible slot projection does not prove inventory authority, item use, grants or persistence.',
         'Add owned inventory projection service and recovered S2C queue path; reuse RecoveredInventory only after state is established.'),
        ('battle_experience', 'S2C', 0x89, 57, 'Battle receive dispatcher', 'RecoveredBattleExperience',
         'src/protocol/RecoveredBattleExperience.h', 'static std::optional<Record> parse_logical(',
         'Battle mapped selector -> 114582 -> 118BF0; received display values, not reward formula or persistence authority.',
         'Recovered battle-result callback/service is absent from Session::RecoveredCharacterHandlers; establish awards before encode_logical and send.'),
        ('inventory_request', 'C2S', 0x25, 5, 'WorldTailAccepted; optional typed transport, Application policy absent', 'RecoveredInventoryItemRequest',
         'src/protocol/RecoveredInventoryItemRequest.h', 'static std::optional<Request> decode(',
         '96350 -> 132E0 queues opcode plus four bytes; receive table returns -1 for 25. Item operation/ownership/consumption/response rules unknown.',
         'Supply recovered ownership/operation rules in an Application-owned typed world handler; Session transport now exists but default movement mode rejects this operation.'),
        ('basic_attack_request', 'C2S', 0x35, 17, 'WorldTailAccepted and InBattle; optional typed transport, Application combat policy absent', 'RecoveredBattleCommand',
         'src/protocol/RecoveredBattleCommand.h', 'static std::optional<BasicAttackRequest> parse_logical(',
         '118E50 -> 1191E0 -> 132E0; action 1 subset. Receive-table 35 is four bytes, not this request. Turn/target/ownership/damage/result rules unknown.',
         'Install authoritative battle ownership/turn/target/result policy before enabling Application combat. Transport does not create battles or call fixture BattleHandler opcode 1040.'),
        ('battle_control_request', 'C2S', 0x35, 17, 'WorldTailAccepted and InBattle; optional typed transport, Application combat policy absent', 'RecoveredBattleCommand',
         'src/protocol/RecoveredBattleCommand.h', 'static std::optional<ControlRequest> parse_control_logical(',
         '115AD8 -> 118E50 -> 132E0; action 0B uses the common 17-byte producer without the action1 grant gate. Fields stay opaque; no acknowledgement or turn progression is inferred.',
         'Recover authoritative control-command policy before Application wiring. Typed transport preserves action identity and does not advance a battle.'),
        ('skill_request', 'C2S', 0x35, 17, 'WorldTailAccepted and InBattle; bounded kind 0 actions 03/83 sequence staging, no cast authority', 'RecoveredSkillCommand',
         'src/protocol/RecoveredSkillCommand.h', 'static std::optional<Sequence> parse_sequence(',
         '118E50 kind-0 path to 1191E0 -> 132E0; continuation sequence codec. Cast ownership, costs, turn legality and effects unknown.',
         'Session stages matching sequences up to14 records with a fixed deadline. Establish battle epoch, replay protection, ownership, costs and effects before Application wiring.'),
    ]
    contracts = []
    for key, direction, opcode, length, state, symbol, path, needle, evidence, next_step in definitions:
        refs = runtime_references(files, symbol)
        if refs and (key not in ('basic_attack_request', 'battle_control_request', 'skill_request') or
                     any(ref['path'] != session for ref in refs)):
            raise AssertionError(f'{symbol} acquired runtime references; inspect before classifying: {refs}')
        contracts.append(dict(id=key, direction=direction, layer='logical', opcode=opcode,
            logical_size=length, state=state, status=coverage_status(codec=True),
            codec_anchor=source_anchor(files, path, needle), runtime_references=refs,
            evidence=evidence, next_integration=next_step))
        if key == 'inventory_request':
            contracts[-1].update(status='TRANSPORT_ROUTE', transport_anchors=transport,
                                 application_policy_installed=False)
        if key == 'skill_request':
            skill_anchors = [source_anchor(files, p, n) for p, n in (
                (world_records, 'RecoveredSkillCommand::parse_logical(remaining.first(size))'),
                (session, 'RecoveredSkillCommand::same_sequence(*first_skill,*skill)'),
                (session, 'world_pending_records=std::move(records);'),
                (session, 'arm_timer(*skill_deadline-std::chrono::steady_clock::now());read();return;'),
                (session, 'std::holds_alternative<RecoveredSkillCommand::Record>(record)'),
                (session, 'if(has_battle_command && self->state()!=SessionState::InBattle)'))]
            contracts[-1].update(status='TRANSPORT_ROUTE',
                                 transport_anchors=transport + skill_anchors,
                                 runtime_sequence_assembly=True,
                                 application_policy_installed=False)
        if key in ('basic_attack_request', 'battle_control_request'):
            battle_anchors = [source_anchor(files, p, n) for p, n in (
                (world_records, 'RecoveredBattleCommand::parse_logical(remaining.first(size))'),
                (world_records, 'RecoveredBattleCommand::parse_control_logical(remaining.first(size))'),
                (session, 'std::holds_alternative<RecoveredBattleCommand::BasicAttackRequest>(record)'),
                (session, 'std::holds_alternative<RecoveredBattleCommand::ControlRequest>(record)'),
                (session, 'if(has_battle_command && self->state()!=SessionState::InBattle)'))]
            contracts[-1].update(status='TRANSPORT_ROUTE',
                                 transport_anchors=transport + battle_anchors,
                                 application_policy_installed=False)
    for key, opcode, size, path, needle, evidence, state, next_step in (
        ('skill_bank_state', 0x38, 2, 'tools/strike_lab/current_skill_selection.py', 'def apply_selection_record(',
         'Battle 114332 mapped selector -> 114525 -> 117560 -> 11C7F0.', 'Battle selector snapshot; not a C2S command',
         'Add explicit S2C emitter after authoritative bank state is recovered; Python model is not a formal server handler.'),
        ('skill_identity', 0x87, 3, 'src/protocol/RecoveredSkillCommand.h', 'static std::optional<StateIdentity> parse_state_word(',
         'Battle mapped selector -> 114518 -> 117540 -> 11C520. Codec parses following WORD only.', 'Battle selector snapshot',
         'Recover authority for skill identity/learning before a recovered battle service emits opcode plus WORD.'),
        ('progression_scalar', 0x31, 29, 'tools/strike_lab/current_progression_source.py', "'packet_scalar_writer': (0xaa200, 0xaa2af)",
         'Receive callback and world table -> 69FA9 -> AA200; bounded packed-scalar/UI model.', 'World; matching actor required',
         'Recover authoritative scalar construction and selected-character state; Session::Impl::accept_world_tail is not authority to replay a snapshot.'),
    ):
        if path not in files:
            data = (ROOT / path).read_bytes()
            files[path] = {'text': data.decode('utf-8'), 'sha256': digest(data)}
        contracts.append(dict(id=key, direction='S2C', layer='logical', opcode=opcode,
            logical_size=size, state=state, status=coverage_status(codec=True),
            codec_anchor=source_anchor(files, path, needle), evidence=evidence,
            next_integration=next_step, original_rules='Authoritative producer, eligibility and state values UNKNOWN'))
    contracts.extend([
        dict(id='quest_dialogue', direction='S2C', layer='logical', opcode=0x7a,
             logical_size=None, state='World receive; only mode-1 header slice executed',
             status='NATIVE_ONLY', evidence='World table 6ABD7 -> C7F10; variable receive size. current_quest_action.fixture is synthetic decoded input, not a wire encoder.',
             next_integration='Recover C7F10/C8780/C8920 field/page construction before an S2C dialogue emitter; no automatic request/reply inference.'),
        dict(id='quest_request', direction='C2S', layer='logical', opcode=0x85,
             logical_size=7, state='WorldTailAccepted; optional typed transport, default movement-only Application policy rejects it',
             status='TRANSPORT_ROUTE', transport_anchors=transport, application_policy_installed=False,
             codec_anchor=source_anchor(files, 'src/protocol/RecoveredQuestAction.h', 'static std::optional<Request> decode('),
             evidence='97DE7 pushes payload size 6; 97DEA pushes 85; 97DF3 calls 132E0. Sixth payload byte is untouched stack storage.',
             next_integration='Recover pending dialogue context/ownership/replay and transitions before installing an Application typed world handler. No quest acceptance/reward mutation yet.'),
        dict(id='quest_close_request', direction='C2S', layer='logical', opcode=0x86,
             logical_size=5, state='WorldTailAccepted; optional typed transport, default movement policy rejects it',
             status='TRANSPORT_ROUTE', transport_anchors=transport, application_policy_installed=False,
             codec_anchor=source_anchor(files, 'src/protocol/RecoveredQuestClose.h', 'static std::optional<Request> decode('),
             evidence='C8350 -> C83A2 -> 132E0; four payload bytes: source low word and saved this-pointer high word. No required 85/86 pairing.',
             next_integration='Recover original dialogue ownership/cancellation policy and source meaning. Native 86 or 86/85 production is not server acceptance or a reward rule.'),
    ])
    for key, direction, opcode, length, evidence in (
        ('movement_request', 'C2S', 0x2e, 7, '15790 -> 157B8 -> 132E0, payload length 6; opaque stack tail.'),
        ('periodic_tick', 'C2S', 0x30, 2, '11750 -> 11770 -> 132E0, one zero byte; 11777 flushes. Runtime consumes tick without gameplay callback/reply.'),
        ('movement_ack', 'S2C', 0x5d, 2, 'World receive table -> 692FA; formal RecoveredMovementService::move emits RecoveredMovement::ack.'),
    ):
        contracts.append(dict(id=key, direction=direction, layer='logical', opcode=opcode,
             logical_size=length, state='WorldTailAccepted; recovered dual connection + world entry + movement enabled',
             status=coverage_status(codec=True, runtime_route=True), route_anchors=common,
             evidence=evidence, original_rules='Current local movement policy exists; original speed/eligibility policy and live client acceptance UNKNOWN'))
    for row in contracts:
        row['client_acceptance'] = {'status': 'UNKNOWN', 'evidence': None}
        row.setdefault('original_rules', 'UNKNOWN beyond stated bounded native contract; not completed by this audit')
        if row['status'] != 'RUNTIME_ROUTE':
            row['formal_route_gap_anchors'] = common[:7]
        if row['direction'] == 'S2C' and row['opcode'] < TABLE_COUNT:
            row['world_dispatch_rva'] = struct.unpack_from('<I', raw, WORLD_TABLE_RVA + row['opcode'] * 4)[0] - BASE
        if row['id'] in ('skill_bank_state', 'skill_identity', 'battle_experience', 'battle_result_flags', 'battle_vitals_batch'):
            selector = raw[0x11465c + row['opcode'] - 0x1c]
            row['battle_selector'] = selector
            row['battle_dispatch_rva'] = struct.unpack_from('<I', raw, 0x114634 + selector * 4)[0] - BASE
    return contracts


def route_drift_report(files=None):
    """Discovery only: never carry stale route or missing-handler conclusions."""
    files=source_snapshot() if files is None else files
    changes=[]
    for path,expected in ROUTE_SOURCE_SHA256.items():
        actual=files.get(path,{}).get('sha256')
        if actual!=expected:
            changes.append({'path':path,'audited_sha256':expected,'current_sha256':actual,
                            'status':'MISSING' if actual is None else 'CHANGED'})
    world=files.get('src/protocol/RecoveredWorldRecords.h',{}).get('text','')
    cases=re.findall(r'^\s*case ([^:]+(?:::[^:]+)?):',world,re.M)
    symbols=('RecoveredNpcInteraction','RecoveredQuestAction','RecoveredQuestClose',
             'RecoveredInventoryItemRequest','RecoveredTargetItemRequest',
             'RecoveredBattleCommand','RecoveredSkillCommand','RecoveredInstanceUpdate')
    return {'schema':'current-protocol-route-drift-v1',
            'status':'REAUDIT_REQUIRED' if changes else 'PINNED_SNAPSHOT_UNCHANGED',
            'changed_sources':changes,'inspected_pins':len(ROUTE_SOURCE_SHA256),
            'current_world_case_labels':cases,
            'runtime_references':{symbol:runtime_references(files,symbol) for symbol in symbols},
            'all_original_packets_wired':False,'runtime_acceptance_granted':False,
            'source_snapshot':[{'path':p,'sha256':v['sha256']} for p,v in sorted(files.items())],
            'limitations':['Textual references and case labels are discovery, not a C++ call graph.',
                'Unchanged pins do not imply client acceptance or full audit completion.',
                'Review ownership, state, config, persistence and live evidence before renewing conclusions.']}


def build_report(path=IMAGE):
    raw = qualified_image(path)
    catalog = native_catalog(raw)
    files = source_snapshot()
    contracts = formal_contracts(raw, files)
    sys.path.insert(0, str(ROOT))
    from tools.strike_lab import current_quest_action
    from tools.strike_lab import current_quest_close
    quest = current_quest_action.build_report(path)
    close = current_quest_close.build_report(path)
    producer_calls = [call_binding(raw, a, b) for a, b in (
        (0x97df3, 0x132e0), (0xc83a2, 0x132e0), (0x9637b, 0x132e0), (0x1191e0, 0x132e0),
        (0x157b8, 0x132e0), (0x11770, 0x132e0), (0x6abe9, 0xc7f10),
        (0x6a031, 0x98dd0), (0x6a055, 0x991e0), (0x6b464, 0x854f0),
        (0x114528, 0x117560), (0x11451b, 0x117540), (0x11754c, 0x11c520),
        (0x11756f, 0x11c7f0), (0x11459a, 0x118bf0), (0x6aa89, 0xcc380),
        (0x69fb1, 0xaa200))]
    frame_anchors = [source_anchor(files, p, n) for p, n in (
        ('src/protocol/RecoveredC2S0002.h', 'std::uint8_t expected_opcode=4'),
        ('src/protocol/RecoveredC2S0002.h', 'if(expected_opcode!=4 && expected_opcode!=0)'),
        ('src/protocol/RecoveredC2S0002.h', 'if(wire.size()!=176 || wire[0]!=176 || wire[1]!=0)'),
        ('src/protocol/Opcode.h', 'These opcode values are placeholders.'),
        ('src/net/Session.cpp', 'auto result = s.protocol.try_decode(s.input, packets);'),
        ('src/net/Session.cpp', 'if(is_recovered(mode)) { fail("Fixture packet refused in recovered mode");return; }'),
        ('src/protocol/RecoveredWorldFrame.h', '// Envelope for the existing zero-seed recovered lab connection only.'),
        ('src/net/Session.cpp', '// values or a reply to this tail. Keep the old replay diagnostic-only.'))]
    return {'schema': 'current-protocol-coverage-v1', 'audit_date': '2026-09-19',
        'image': {'path': str(Path(path).resolve()), 'sha256': IMAGE_SHA256, 'base': BASE},
        'scope': 'Complete native receive-size table and byte-domain query; SELECTED current contract/runtime audit, not all packet semantics, all modes or original rules.',
        'original_rules_complete': False, 'all_original_packets_wired': False,
        'status_definitions': STATUS_DEFINITIONS, 'native_catalog': catalog,
        'contracts': contracts, 'contract_status_counts': dict(Counter(r['status'] for r in contracts)),
        'producer_call_bindings': producer_calls,
        'native_producers': producer_contracts(raw),
        'quest_close_native_probe': {
            'acceptance_kind': 'bounded_native', 'requires_85_then_86': close['requires_85_then_86'],
            'sequences': [s['result']['appended_hex'] for s in close['scenarios']]},
        'quest_native_probe': {'appended_hex': quest['action']['appended_hex'],
            'queued_bytes': quest['action']['queue_count_after'], 'stop_rva': quest['action']['stop_rva'],
            'boundary': quest['boundary'], 'acceptance_kind': 'bounded_native'},
        'frame_distinction': {'capture_stage_label': 'C2S0002', 'layer': 'outer_frame/stage',
            'logical_opcode': None, 'implemented_logical_opcodes': [0, 4], 'wire_size': 176,
            'note': 'The C2S0002 label is not logical opcode 02. Native receive 02 independently returns 23; no C2S02 producer claimed.',
            'anchors': frame_anchors},
        'source_snapshot': [{'path': p, 'sha256': v['sha256']} for p, v in sorted(files.items())],
        'limitations': ['No live client, sockets, deployment, server behavior change or server-rule completion.',
            'World table default does not exclude battle/other state dispatch; length alone establishes no consumer semantics.',
            'C2S producers are a selected anchored set, not a complete producer census.',
            'Source route status is conditional/static; absent routes are bounded to inspected recovered Session path and source snapshot.',
            'RecoveredWorldFrame is the zero-seed lab envelope; Session::send(Packet) refuses recovered mode and is not an available recovered S2C route.',
            'No fixture OpcodeDispatcher labels or historical snapshot values qualify current-native packet direction or authority.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--json', action='store_true', help='JSON is always emitted; retained for explicit invocation')
    parser.add_argument('--route-drift', action='store_true',
                        help='List all stale source pins without issuing route classifications; exit2 on drift')
    args = parser.parse_args(argv)
    if args.route_drift:
        report=route_drift_report()
        print(json.dumps(report,indent=2))
        return 2 if report['changed_sources'] else 0
    print(json.dumps(build_report(args.image), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
