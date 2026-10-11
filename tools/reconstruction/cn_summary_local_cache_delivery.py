"""Retain file-only CN07/local-cache/1F lineage; never execute game code."""
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT, CN, PIN
from .cn_pe_import_directory import FileView
import pefile

NAME = 'cn-summary-local-cache-01'
ROUND = '20261007-cn-summary-local-cache'
SOURCES = ('src/cn/protocol/CnCharacterSummary.h',
           'tools/reconstruction/cn_summary_local_cache_delivery.py',
           'docs/research/cn-summary-local-cache-20261007.md',
           'tools/reconstruction/dual_client_route_catalog.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    base = ROOT/'artifacts/integration/packet-connections-20261006'
    out = base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh captured sources; preserve previous delivery')
    before = json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    preserved = []
    for row in before:
        raw = (out/'before'/row['path']).read_bytes()
        if sha(raw) != row['sha256']:
            raise RuntimeError('Before snapshot changed')
        if row['path'] not in SOURCES:
            if raw != (ROOT/row['path']).read_bytes():
                raise RuntimeError('Existing gameplay source changed: '+row['path'])
            preserved.append(row)
    raw = (CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw) != PIN:
        raise RuntimeError('Pinned native image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    view = FileView(pe, raw)
    index = json.loads((out/'native/index.json').read_text(encoding='utf-8'))
    for row in index['functions']:
        code = view.read(int(row['entry'], 16)-pe.OPTIONAL_HEADER.ImageBase, row['bytes'])
        if sha(code) != row['raw_sha256'] or code != (out/f"native/{row['entry']}.bin").read_bytes():
            raise RuntimeError('Primary native snapshot differs')
    fields = [
        {'source': '07 payload0', 'local_offset': 0, 'meaning': 'count',
         'copy_sites': ['004817ef', '0047f938']},
        {'source': '07 row0..NUL within16', 'local_offset': '4+40*i', 'meaning': 'raw name including terminator',
         'copy_sites': ['00481810..0048181b', '0047f950..0047f95b']},
        {'source': '07 row16', 'local_offset': '32+40*i', 'meaning': 'unchanged BYTE level',
         'copy_sites': ['0048181d/00481824', '0047f95d/0047f965']},
        {'source': '07 row17', 'local_offset': '33+40*i', 'meaning': 'profession code',
         'copy_sites': ['00481827/0048182b', '0047f967/0047f96b']},
        {'source': '07 row18', 'local_offset': '36+40*i', 'meaning': 'opaque; business meaning and issuance unknown',
         'copy_sites': ['0048182e/00481832', '0047f96e/0047f972']},
        {'source': '07 row19 &7', 'local_offset': '38+40*i', 'meaning': 'native slot, no common-ID equivalence inferred',
         'copy_sites': ['00481835/0048183c/00481841', '0047f975/0047f97c/0047f97e']},
    ]
    relations = {'local_clear_bytes': 124, 'local_clear_sites': ['004817e0..004817e5', '0047f929..0047f92e'],
        'fields': fields, 'flags': 'payload1 &1 stored separately in network+4200; absent from local cache',
        'omitted_fields': ['flags upper bits', 'reincarnation upper bits', 'portrait', 'appearance', 'location', 'inactive07 rows'],
        'raw_summary_preserved': True,
        'normal_owner': '00449310 passes optional-output NULL;00444FE0 reads07 payload15+36*selected-row, masks7, calls004813C0',
        'normal_slot_primary_sites': ['00444ffc', '00445001', '00445013'],
        'transfer_owner': '0044D5F0 passes dialog+668 as optional cache; later passes same pointer to0047E060',
        'transfer_overwrite': '0047E16A/16D/173/178 copy31 DWORDs from accepted1F payload to cache',
        'transfer_slot_owner': '0044D240 reads independently overwritten cache38+40*07-selected-row',
        'normal_and_transfer_slot_sources_interchangeable': False,
        'local_zeroes_authorize_server_packet_zeroes': False,
        'count_bounds': 'existing CnCharacterSummary::read count<=2 and active names terminated within16',
        'native_decode_scope': '8 metadata envelopes, entry-rooted CFG; calls/exception/indirect/open edges not closed',
        'new_wire_serializer': False}
    findings = {'round': ROUND, 'native_sha256': PIN,
        'previous_goal_turn_classification': 'no progress: level clarification only; this round takes available native/source action',
        'read_only_local_cache_projections_added': 1, 'native_metadata_envelopes_retained': len(index['functions']),
        'newly_recovered_native_fields': 0,
        'existing_native_projection_first_implemented_as_source_view': True,
        'prior_projection_evidence': 'cn-world-list-consumers-agent-01/findings.json',
        'new_source_owner_chains': 0, 'new_native_phase_source_bindings': 0,
        'new_packet_values': 0, 'new_complete_bidirectional_routes': 0,
        'native_handler_connected_this_round': False, 'server_summary_issuance_rule_recovered': False,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'preserved_existing_sources': preserved, 'levels_changed': False,
        'build_run': False, 'tests_run': False, 'runtime_run': False, 'database_access': False, 'deployed': False,
        'remaining': ['Actual07 flags/opaque18 and version-qualified common character data issuer.',
            'Independent full native1F issuer, actual account/world providers and shared production host.',
            'Native permission/mutation/guild/replay/durable receipts, CN1E and all gameplay.',
            'Whole-game directional/state/variant/indirect/deferred denominator.']}
    doc = ROOT/SOURCES[2]
    with doc.open('x', encoding='utf-8') as stream:
        stream.write('# CN07 local selection-cache lineage\n\n'
            'PHASE1 static source work. No builds, tests, game execution, DB access or deploy. Native levels unchanged. Pinned CN SHA256 '+PIN+'.\n\n'
            'The optional output of00481640 and0047F750 is a124-byte LOCAL cache. Both primary functions explicitly clear it, copy count, then copy each active name through its terminator to4+40*i, level to32+40*i, profession to33+40*i, opaque row18 to36+40*i and low3 slot bits to38+40*i. Names are raw bytes: no decoding, display conversion or identity matching. The expression at00481815/0047F955 writes using an already incremented source cursor minus1D; its first destination is4, not3. Native code itself is not capacity-safe; the server view retains its existing count<=2/name-NUL qualification.\n\n'
            'Flags are stored separately as payload1&1 at network+4200. Upper flags, reincarnation, portrait, appearance, location and inactive rows are absent from this projection but retained in record_bytes(). Their omission is not an issuance rule. The explicit memset establishes only local unused bytes, never permission to manufacture a zero-filled S2C1F. Opaque18 remains unnamed and does not become a native server permission.\n\n'
            'Normal00449310 passes NULL for optional local output.00444FE0 reads raw07 payload15+36*selected-row, masks7, and calls004813C0. Transfer0044D5F0 passes dialog+668 for the optional local cache, then later sends the same pointer to0047E060;0047E16A..178 overwrites all124 bytes using31 DWORDs from accepted1F.0044D240 subsequently uses the selected07 ordinal against38+40*i in this overwritten1F. Byte36 after that overwrite is not proven to be the earlier07 opaque18. Normal and transfer remain separate authorities, as existing NativeOffer mapping already requires.\n\n'
            'CnCharacterSummary now exposes local_selection_cache_bytes() as a read-only derived snapshot. It uses only previously qualified full07 input and does not mutate raw input or native level fields. Existing selection/account/world handlers and independent CnWorldCharacterList are byte-identical; no handler or reply generator was added. The projection documents an additional exact local layout for source integration and peer use, and is not counted as a completed gameplay connection.\n\n'
            'Eight primary metadata envelopes and conservative entry-rooted CFG snapshots accompany the field relation. Calls are not followed; open edges are retained. Server07 flags/row18, actual common-state native issuers, full independent1F, hosting, all gameplay and whole-game denominator remain open. New complete routes0; total and percentage null.\n')
    dump(out/'local-cache-source-relations.json', relations)
    dump(out/'findings.json', findings)
    for rel in SOURCES:
        p = out/'source'/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','read_only_local_cache_projections_added','native_metadata_envelopes_retained','new_complete_bidirectional_routes')}))


if __name__ == '__main__':
    main()
