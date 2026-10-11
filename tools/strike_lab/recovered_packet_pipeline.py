"""Recovered byte-opcode identification, separate from placeholder game handlers."""
import csv
import hashlib
import json
from pathlib import Path


def pet2_fields(logical):
    """Structural FB fields; no metadata lookup, ownership or wild-stat claim.

    Offsets are pinned by the native receiver and petegg.romZ panel bindings.
    Differential tests compare these values with the C++ codec and native UI.
    """
    if len(logical) != 73 or logical[0] != 0xfb or not 42 <= logical[3] <= 44:
        return None
    key = int.from_bytes(logical[1:3], 'little')
    if not 0x6d61 <= key < 0x7f58:
        return None
    offsets = (
        ('physical_attack', 0x10), ('physical_defense', 0x12),
        ('magical_attack', 0x14), ('magical_defense', 0x16),
        ('strength', 0x24), ('constitution', 0x26),
        ('intelligence', 0x28), ('speed', 0x2a),
        ('metal', 0x18), ('wood', 0x1a), ('water', 0x1c),
        ('fire', 0x1e), ('earth', 0x20),
    )
    return {'metadata_key': key, 'slot': logical[3],
            'level': logical[4],
            'vitals': {
                'current_hp': int.from_bytes(logical[5:9], 'little') & 0x3fff,
                'maximum_hp': int.from_bytes(logical[13:17], 'little') & 0x3fff,
                'current_mp': (int.from_bytes(logical[5:9], 'little') >> 14) & 0x7ff,
                'maximum_mp': (int.from_bytes(logical[13:17], 'little') >> 14) & 0x7ff},
            'star_rank': logical[12] >> 4,
            'star_rating': logical[12] & 15,
            'category_selector': {'group': logical[61], 'index': logical[45] & 15},
            # Native panel 004A4151 masks FB body+8 to 24 bits. This
            # percentage display value is not a next-level EXP threshold.
            'progress_display_raw24': int.from_bytes(logical[9:12], 'little'),
            'progress_display_unit': 'PERCENT_HUNDREDTHS_NOT_EXP_POINTS',
            'values': {name: int.from_bytes(logical[offset + 1:offset + 3], 'little')
                       for name, offset in offsets},
            'qualification': 'STRUCTURAL_DECODE_ONLY',
            'metadata_resolved': False, 'instance_ownership_verified': False,
            'wild_monster_values_verified': False, 'database_promotion_eligible': False}


class FrameParser:
    @staticmethod
    def parse(plain):
        if not 4 <= len(plain) <= 258:
            raise ValueError('frame bounds')
        if int.from_bytes(plain[:2], 'little') != len(plain):
            raise ValueError('frame header/length')
        if sum(value + 0x3c for value in plain[:-1]) & 255 != plain[-1]:
            raise ValueError('frame checksum')
        return {'opcode': plain[2], 'payload_length': len(plain) - 4,
                'checksum': plain[-1], 'frame_pass': True}


class OpcodeDispatcher:
    """Identification only; never executes placeholder gameplay handlers."""
    @staticmethod
    def identify(plain, direction, state_before=None):
        frame = FrameParser.parse(plain)
        opcode = frame['opcode']
        identity = 'UNKNOWN'
        expected = None
        bounds = False
        details = {}
        if direction == 'C2S' and len(plain) == 6 and plain == bytes.fromhex('0600a60000d8'):
            identity, expected, bounds = 'CAPTURED_SERVER_SELECTION', 'SERVER_LIST_READY', True
        elif direction == 'C2S' and len(plain) == 176 and opcode == 4:
            identity, expected = 'CREDENTIAL_REQUEST', 'POST_SEED_ACCEPTED'
            bounds = (plain[26] == 0 and plain[158] == 0 and plain[169] == 0xc8
                      and int.from_bytes(plain[167:169], 'little') < 1000)
        elif direction == 'S2C' and len(plain) == 176 and opcode == 29:
            identity, expected = 'REQUEST_STRUCTURE_ACK', 'CREDENTIAL_REQUEST_SENT'
            # Matching the actual outstanding request is a separate parser check.
            bounds = plain[26] == 0 and plain[158] == 0
        elif direction == 'S2C' and len(plain) == 8 and opcode == 4:
            identity, expected = 'SERVER_LIST_ENTRY', 'LOGIN_RESPONSE_WAIT'
            bounds = plain[3:7] == bytes.fromhex('00000100')
        elif direction == 'S2C' and len(plain) == 20 and opcode == 10:
            identity, expected = 'LOGIN_TERMINAL', 'LOGIN_RESPONSE_WAIT'
            bounds = plain[3:19] == bytes(16)
        elif direction == 'S2C' and len(plain) == 5 and opcode == 1:
            identity, expected, bounds = 'POST_SEED', 'SEED_EXCHANGE_ACCEPTED', plain[3] == 0x53
        elif direction == 'C2S' and len(plain) == 10 and opcode == 0x85:
            identity, bounds = 'QUEST_DIALOGUE_ACTION', True
            details['quest_action'] = {
                'request_word': int.from_bytes(plain[3:5], 'little'),
                'reply_word': int.from_bytes(plain[5:7], 'little'),
                'context_byte': plain[7], 'opaque_tail': plain[8],
                'qualification': 'STRUCTURAL_DECODE_ONLY',
                'conversation_authorized': False,
            }
            # Native production/transport does not prove authoritative quest state.
            details['required_client_context'] = 'WORLD_DIALOGUE'
        elif direction == 'C2S' and len(plain) == 8 and opcode == 0x37:
            identity,bounds='NPC_INTERACTION_REQUEST',True
            details['npc_interaction']={
                'raw_target':int.from_bytes(plain[3:7],'little'),
                'qualification':'STRUCTURAL_DECODE_ONLY',
                'target_authorized':False,
            }
            details['required_client_context']='WORLD_NPC'
        elif direction == 'S2C' and len(plain) == 76 and opcode == 0xfb:
            identity = 'PET2_STATS_RECORD_CANDIDATE'
            fields = pet2_fields(plain[2:-1])
            bounds = fields is not None
            details['required_client_context'] = 'WORLD'
            if bounds:
                details['pet2'] = fields
            # Capture state names do not yet bind the native world dispatcher.
            # Keep expected/state consistency unknown, not an invented live pass.
        return {**frame, **details, 'identification': identity, 'known_bounds_pass': bounds,
                'expected_state': expected, 'state_before': state_before,
                'state_consistent': None if state_before is None or expected is None else state_before == expected,
                'parser_qualification': 'STATIC_CONSTRAINTS_ONLY',
                'client_parser_runtime_validated': False, 'CRYPTO_RECOVERED': False}


def record_packet(run, sequence, report, *, direction, socket, caller_rva, state_before=None):
    if direction not in ('C2S', 'S2C') or type(sequence) is not int or sequence < 0:
        raise ValueError('invalid packet identity')
    run = Path(run).resolve()
    directory = run / 'crypto-private'
    directory.mkdir(exist_ok=True)
    base = directory / f'packet-{sequence:04}'
    metadata = {**report, 'direction': direction, 'socket': socket, 'caller_rva': caller_rva,
                'session': run.name, 'sequence': sequence, 'CRYPTO_RECOVERED': False}
    # Sensitive binary evidence stays separate; no plaintext or key bytes in JSON/CSV.
    metadata.pop('plain_frame_hex', None)
    metadata.pop('wire_hex', None)
    for field, suffix in (('wire_file', '.wire.bin'), ('plain_file', '.plain.bin')):
        path = Path(str(base) + suffix)
        if field in report and Path(report[field]).resolve() != path:
            raise ValueError('packet evidence path mismatch')
        if path.exists():
            data = path.read_bytes()
            metadata[field] = path.name
            metadata[field.replace('_file', '_sha256')] = hashlib.sha256(data).hexdigest()
            if field == 'plain_file' and report.get('decoded') is True:
                try:
                    metadata['pipeline'] = OpcodeDispatcher.identify(data, direction, state_before)
                except ValueError as error:
                    metadata['pipeline'] = {'frame_pass': False, 'error': str(error)}
    path = Path(str(base) + '.json')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(metadata, stream, indent=2, allow_nan=False)
    core = directory / 'protocol-core.csv'
    fields = ('sequence', 'direction', 'socket', 'caller_rva', 'wire_len', 'plain_len',
              'opcode', 'crypto_key_id', 'identification', 'frame_pass', 'state_consistent',
              'client_parser_runtime_validated', 'packet_json')
    new = not core.exists()
    row = {name: metadata.get(name) for name in fields}
    for name in ('identification', 'frame_pass', 'state_consistent', 'client_parser_runtime_validated'):
        row[name] = metadata.get('pipeline', {}).get(name)
    row['packet_json'] = path.name
    with core.open('a', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if new:
            writer.writeheader()
        writer.writerow(row)
    return str(path.relative_to(run))
