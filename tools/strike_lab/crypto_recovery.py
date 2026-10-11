"""Bounded offline recovery. Candidate reports never qualify runtime behavior.

Manifest: engine request fields at top level, plus optional ``dll`` and
``runtime_evidence``. Packets additionally require a strictly increasing ``seq``
and may carry ``packet_id`` and ``session_id`` (which must match the session).
Those provenance fields are removed before calling the engine. State values are
opaque bounded labels; they are not
evidence of execution. No client is launched and no fallback brute search exists.
"""

import argparse
import ctypes
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_JSON = 2 * 1024 * 1024
MAX_PACKETS = 256
MAX_FRAME = 258
MAX_EVIDENCE = 8 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]


class ValidationError(ValueError):
    """Errors contain fixed descriptions, never input values."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def label(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', value) is not None


def hex_bytes(value, minimum, maximum):
    require(isinstance(value, str) and minimum * 2 <= len(value) <= maximum * 2
            and len(value) % 2 == 0 and re.fullmatch('[0-9a-fA-F]+', value) is not None,
            'Invalid bounded hexadecimal field')
    return bytes.fromhex(value)


def state(value):
    require(label(value), 'Invalid state label')
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON member')
        result[key] = value
    return result


def parse_json(data):
    require(len(data) <= MAX_JSON, 'JSON size limit exceeded')
    try:
        return json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValidationError('Nonfinite JSON value')))
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise ValidationError('Invalid JSON document') from None


def read_bounded(path, limit):
    with Path(path).open('rb') as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, 'File size limit exceeded')
    return data


def validate_manifest(manifest):
    require(isinstance(manifest, dict), 'Manifest must be an object')
    required = {'session_id', 'model', 'tx_key_hex', 'rx_key_hex', 'packets'}
    require(required <= set(manifest) <= required | {'dll', 'runtime_evidence'},
            'Missing or unknown manifest fields')
    require(label(manifest['session_id']), 'Invalid session identity')
    require(manifest['model'] == 'packet_reset',
            'Only the statically supported packet_reset model is permitted')
    for name in ('tx_key_hex', 'rx_key_hex'):
        hex_bytes(manifest[name], 256, 256)
    packets = manifest['packets']
    require(isinstance(packets, list) and 1 <= len(packets) <= MAX_PACKETS, 'Invalid packet count')
    request = {k: manifest[k] for k in required - {'packets'}}
    request['packets'] = []
    seen = set()
    objects = {}
    last_seq = -1
    for packet in packets:
        fields = {'direction', 'wire_hex', 'state_before', 'state_after', 'seq'}
        optional = {'session_id', 'packet_id', 'codec_object_id', 'known_plaintext_hex', 'allowed_opcodes',
                    'constants', 'expected_state_before'}
        require(isinstance(packet, dict) and fields <= set(packet) <= fields | optional,
                'Missing or unknown packet fields')
        require(packet.get('session_id', manifest['session_id']) == manifest['session_id'],
                'Mixed sessions are forbidden')
        seq = packet['seq']
        require(integer(seq, 0, 2**32 - 1) and seq > last_seq, 'Invalid packet sequence')
        last_seq = seq
        identity = packet.get('packet_id', str(seq))
        require(label(identity) and identity not in seen, 'Invalid or repeated packet identity')
        seen.add(identity)
        if 'codec_object_id' in packet:
            require(label(packet['codec_object_id']), 'Invalid codec object identity')
        direction = packet['direction']
        require(isinstance(direction, str) and direction in ('C2S', 'S2C'), 'Invalid direction')
        if 'codec_object_id' in packet:
            identity = packet['codec_object_id']
            require(objects.get(direction, identity) == identity, 'Codec changed within a directional session')
            objects[direction] = identity
            if objects.get('C2S') == objects.get('S2C'):
                require(manifest['tx_key_hex'].lower() == manifest['rx_key_hex'].lower(),
                        'Same codec object cannot have inconsistent simultaneous keys')
        wire = hex_bytes(packet['wire_hex'], 4, MAX_FRAME)
        require(int.from_bytes(wire[:2], 'little') == len(wire), 'Invalid frame length')
        before, after = state(packet['state_before']), state(packet['state_after'])
        if 'expected_state_before' in packet:
            require(state(packet['expected_state_before']) == before, 'Expected state mismatch')
        plain = None
        if 'known_plaintext_hex' in packet:
            plain = hex_bytes(packet['known_plaintext_hex'], len(wire), len(wire))
            require(plain[:2] == wire[:2], 'Known plaintext length mismatch')
            require(sum(v + 0x3c for v in plain[:-1]) % 256 == plain[-1],
                    'Known plaintext checksum mismatch')
        if 'allowed_opcodes' in packet:
            opcodes = packet['allowed_opcodes']
            require(isinstance(opcodes, list) and 1 <= len(opcodes) <= 256
                    and all(integer(v, 0, 255) for v in opcodes)
                    and len(set(opcodes)) == len(opcodes), 'Invalid allowed opcodes')
            require(plain is None or plain[2] in opcodes, 'Conflicting plaintext opcode')
        if 'constants' in packet:
            constants = packet['constants']
            require(isinstance(constants, list) and len(constants) <= len(wire), 'Invalid constants')
            offsets = set()
            for constant in constants:
                require(isinstance(constant, dict) and set(constant) == {'offset', 'value'}
                        and integer(constant['offset'], 0, len(wire) - 1)
                        and integer(constant['value'], 0, 255), 'Invalid constant')
                offset = constant['offset']
                require(offset not in offsets, 'Repeated constant offset')
                offsets.add(offset)
                require(plain is None or plain[offset] == constant['value'], 'Conflicting plaintext constant')
        request['packets'].append({k: v for k, v in packet.items()
                                   if k not in {'seq', 'session_id', 'packet_id', 'codec_object_id'}})
    return request


def recover_native(request, dll_path):
    """Use the cdecl size-query ABI, with one bounded allocation and no retries."""
    library = ctypes.CDLL(str(Path(dll_path).resolve()))
    function = library.God2RecoverCrypto
    function.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    payload = json.dumps(request, separators=(',', ':'), allow_nan=False).encode('ascii')
    require(len(payload) <= MAX_JSON, 'Request size limit exceeded')
    required = function(payload, None, 0)
    require(integer(required, 2, MAX_JSON), 'DLL recovery failed or returned invalid size')
    output = ctypes.create_string_buffer(required)
    written = function(payload, output, required)
    require(written == required and output.raw[-1:] == b'\0'
            and b'\0' not in output.raw[:-1], 'DLL response size or terminator mismatch')
    result = parse_json(output.raw[:-1])
    require(isinstance(result, dict), 'DLL response must be an object')
    return result


def candidate_report(result, packet_count):
    """Whitelist bounded diagnostics, never keys, plaintext or verified verdicts."""
    require(isinstance(result, dict), 'Invalid engine report')
    candidates = result.get('candidates', [])
    require(isinstance(candidates, list) and len(candidates) <= 65536, 'Invalid candidate list')
    rows = []
    for index, candidate in enumerate(candidates):
        require(isinstance(candidate, dict), 'Invalid candidate entry')
        rows.append({'candidate_index': index, 'verified': False})
    report = {'status': 'CANDIDATES_ONLY', 'verified': False, 'packet_count': packet_count,
            'model': 'packet_reset',
            'reported_candidate_count': len(rows), 'candidates': rows,
            'sensitive_fields_omitted': True,
            'reason': 'Engine candidates and checksum matches do not establish runtime validity.'}
    allowed_status = {'INSUFFICIENT_CONSTRAINTS', 'NO_CANDIDATES', 'UNIQUE_CANDIDATE', 'AMBIGUOUS'}
    if result.get('status') in allowed_status:
        report['status'] = result['status']
    report['CRYPTO_RECOVERED'] = False
    report['directions'] = {}
    counters = {'tested', 'survivors', 'rejected_length', 'rejected_header', 'rejected_checksum',
                'rejected_known_plaintext', 'rejected_opcode', 'rejected_state', 'rejected_bounds'}
    candidate_numbers = {'feedback', 'key_offset', 'cross_packet_score', 'packets_survived',
                         'sequence', 'bytes_consumed'}
    candidate_flags = {'checksum_pass', 'length_pass', 'header_pass', 'opcode_plausible',
                       'opcode_constraint_applied', 'known_plaintext_match', 'state_consistent'}
    for direction, source in result.get('directions', {}).items():
        require(direction in ('C2S', 'S2C') and isinstance(source, dict), 'Invalid direction report')
        target = {'verified': False, 'candidates': [], 'stats': {}}
        for field in ('candidate_count', 'packet_count', 'distinct_packet_count', 'serialization_limit'):
            require(integer(source.get(field), 0, 65536), 'Invalid direction count')
            target[field] = source[field]
        target['truncated'] = source.get('truncated') is True
        rounds = source.get('rounds', [])
        require(isinstance(rounds, list) and len(rounds) <= MAX_PACKETS, 'Invalid packet rounds')
        target['rounds'] = []
        for round_record in rounds:
            require(isinstance(round_record, dict) and all(integer(round_record.get(k), 0, 65536)
                    for k in ('packet_index', 'tested', 'survivors')), 'Invalid packet round')
            target['rounds'].append({k: round_record[k] for k in ('packet_index', 'tested', 'survivors')})
        for field in counters:
            require(integer(source.get('stats', {}).get(field), 0, 65536), 'Invalid rejection count')
            target['stats'][field] = source['stats'][field]
        source_rows = source.get('candidates')
        require(isinstance(source_rows, list) and len(source_rows) <= 256, 'Invalid survivors')
        for candidate in source_rows:
            entry = {'verified': False}
            for field in candidate_numbers:
                require(integer(candidate.get(field), 0, 2**32 - 1), 'Invalid candidate counter')
                entry[field] = candidate[field]
            for field in candidate_flags:
                require(type(candidate.get(field)) is bool, 'Invalid candidate check')
                entry[field] = candidate[field]
            ds = candidate.get('directional_state', {})
            entry['directional_state'] = {field: ds[field] for field in
                ('key_offset', 'feedback', 'sequence', 'bytes_consumed')
                if integer(ds.get(field), 0, 2**32 - 1)}
            target['candidates'].append(entry)
        differential = source.get('differential', {})
        target['differential'] = {field: differential.get(field) for field in
            ('first_differing_offset', 'next_distinguishing_key_index')
            if differential.get(field) is None or integer(differential.get(field), 0, 258)}
        target['differential']['need_next_real_constraint'] = differential.get('need_next_real_constraint') is True
        if differential.get('status') in {'no_survivors', 'REDACTED_CREDENTIAL_FRAME',
                'equivalent_plaintext', 'plaintext_differs', 'mathematically_equivalent_states', 'unique'}:
            target['differential']['status'] = differential['status']
        report['directions'][direction] = target
    report['reported_candidate_count'] = sum(d['candidate_count'] for d in report['directions'].values()) if report['directions'] else len(rows)
    return report


@dataclass(frozen=True)
class EvidenceReference:
    """A checked file reference is provenance, not proof of a runtime claim."""

    role: str
    path: Path
    sha256: str

    @classmethod
    def read(cls, record, base):
        require(isinstance(record, dict) and set(record) == {'role', 'path', 'sha256'},
                'Evidence requires typed file provenance')
        require(record['role'] in ('raw_packet', 'logical_packet', 'runtime_trace', 'parser_check'),
                'Invalid evidence role')
        require(isinstance(record['path'], str) and 0 < len(record['path']) <= 512,
                'Invalid evidence path')
        digest = record['sha256']
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) is not None,
                'Invalid evidence hash')
        root = Path(base).resolve()
        path = (root / record['path']).resolve()
        require(path.is_relative_to(root) and path.is_file(), 'Evidence must be a local referenced file')
        data = read_bounded(path, MAX_EVIDENCE)
        require(bool(data) and hashlib.sha256(data).hexdigest() == digest, 'Evidence hash mismatch')
        return cls(record['role'], path, digest)


def audit_runtime(evidence, recovery_session, base):
    """Separate qualification boundary; current capture schemas cannot certify.

    Hashes authenticate referenced bytes only. No adapter currently binds those
    bytes to target PID/thread/sequence, parser checks, and a fresh runtime
    session. Even complete references therefore cannot produce VERIFIED.
    """
    reasons = []
    references = []
    try:
        require(isinstance(evidence, dict), 'Fresh runtime evidence is missing')
        require(set(evidence) == {'session_id', 'target_pid', 'thread_id', 'seq', 'references'},
                'Runtime claims require typed provenance; booleans cannot qualify')
        require(label(evidence['session_id']) and evidence['session_id'] != recovery_session,
                'Runtime evidence must use a different session')
        require(integer(evidence['target_pid'], 1, 2**32 - 1)
                and integer(evidence['thread_id'], 1, 2**32 - 1)
                and integer(evidence['seq'], 0, 2**32 - 1), 'Runtime identity is missing or invalid')
        records = evidence['references']
        require(isinstance(records, list) and 4 <= len(records) <= 16, 'Missing bounded evidence references')
        references = [EvidenceReference.read(record, base) for record in records]
        require({r.role for r in references} == {'raw_packet', 'logical_packet', 'runtime_trace', 'parser_check'},
                'Raw, logical, trace and parser evidence are required')
        require(len({r.path for r in references}) == len(references), 'Repeated evidence reference')
    except (ValidationError, OSError, ValueError, TypeError):
        reasons.append('Missing or invalid fresh-session typed evidence; supplied claims are not proof.')
    reasons.append('Current artifact schemas cannot safely bind raw/logical packet hashes to a fresh '
                   'runtime trace with matching target PID, thread, sequence, different-key evidence '
                   'and read-only live-client parser-check evidence.')
    return {'status': 'RUNTIME_VALIDATION_REQUIRED', 'verified': False,
            'checked_reference_count': len(references), 'reasons': reasons}


def recover(manifest_path, output_dir, dll_path=None):
    """Offline parent entry point. Return sanitized reports; raise on invalid input.

    Writes decrypt-candidates.json and the independent runtime-qualification.json.
    The manifest DLL path is relative to the manifest directory; an explicit DLL
    argument takes precedence. This function never launches a client.
    """
    manifest_path, output_dir = Path(manifest_path), Path(output_dir)
    manifest = parse_json(read_bounded(manifest_path, MAX_JSON))
    request = validate_manifest(manifest)
    configured = manifest.get('dll')
    require(configured is None or isinstance(configured, str) and 0 < len(configured) <= 512,
            'Invalid DLL path')
    dll = dll_path or (manifest_path.parent / configured if configured else
                       ROOT / 'build-strike-lab/Release/God2Probe.dll')
    report = candidate_report(recover_native(request, dll), len(request['packets']))
    audit = audit_runtime(manifest.get('runtime_evidence'), request['session_id'], manifest_path.parent)
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, document in (('decrypt-candidates.json', report), ('runtime-qualification.json', audit)):
        with (output_dir / filename).open('x', encoding='utf-8') as stream:
            json.dump(document, stream, indent=2, allow_nan=False)
    return {'candidates': report, 'qualification': audit}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recover-crypto', action='store_true', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dll', type=Path)
    args = parser.parse_args(argv)
    try:
        recover(args.manifest, args.output, args.dll)
        return 0
    except (ValidationError, OSError, AttributeError, TypeError, RecursionError):
        print('Crypto recovery failed: invalid input, unavailable DLL, or invalid engine response.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
