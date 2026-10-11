"""Bind selected existing protocol evidence to the supplied unpacked TW PE."""
import argparse
import hashlib
import json
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT.parent / 'God2/God2.unpacked.exe'
REFERENCE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
EXE_SHA = '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
REFERENCE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SLICES = (
    ('battle_command_builder_prefix', 0x118e50, 0x1191ee),
    ('battle_hp_consumer_region', 0x117230, 0x1173a0),
    ('battle_mp_consumer_region', 0x1173a0, 0x117540),
    ('outbound_queue_prefix', 0x132e0, 0x13340),
    ('logical_dispatch_table', 0x6b5d4, 0x6b9d4),
    ('selected_skill_mp_predicate', 0xa9070, 0xa90c2),
    ('indexed_skill_mp_predicate', 0xa90d0, 0xa9110),
    ('projection_arithmetic_candidate', 0x11a08f, 0x11a10e),
    ('received_skill_action_producer', 0x12c520, 0x12cc39),
    ('received_effect_consumer', 0x12b060, 0x12b847),
    ('client_rng_core_not_critical_formula', 0x147d84, 0x147da1),
)


def compare(executable, reference):
    pe = pefile.PE(data=executable, fast_load=True)
    try:
        rows = []
        for name, start, end in SLICES:
            expected = reference[start:end]
            actual = pe.get_data(start, end - start)
            complete = len(expected) == len(actual) == end - start
            rows.append({'name': name, 'start_rva': hex(start), 'end_rva_exclusive': hex(end),
                         'size': end - start, 'complete': complete,
                         'match': complete and actual == expected,
                         'exe_slice_sha256': hashlib.sha256(actual).hexdigest(),
                         'reference_slice_sha256': hashlib.sha256(expected).hexdigest()})
        source_sha = hashlib.sha256(executable).hexdigest()
        reference_sha = hashlib.sha256(reference).hexdigest()
        identity = source_sha == EXE_SHA and reference_sha == REFERENCE_SHA
        layout = pe.OPTIONAL_HEADER.ImageBase == 0x400000 and pe.FILE_HEADER.Machine == 0x14c
        return {'status': 'MATCHED_SELECTED_PROTOCOL_REGIONS' if identity and layout and all(r['match'] for r in rows) else 'NOT_QUALIFIED',
                'source_sha256': source_sha, 'reference_sha256': reference_sha,
                'pinned_identity_match': identity, 'layout_match': layout, 'regions': rows,
                'scope': 'Exact bytes in listed regions only; not whole-program equivalence, original formulas, or live client acceptance.',
                'runtime_gameplay_enabled_by_audit': False}
    finally:
        pe.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    parser.add_argument('--reference', type=Path, default=REFERENCE)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/research/current-unpacked-protocol-match.json')
    args = parser.parse_args()
    report = compare(args.exe.read_bytes(), args.reference.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['status'] == 'MATCHED_SELECTED_PROTOCOL_REGIONS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
