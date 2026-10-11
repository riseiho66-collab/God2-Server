"""Round175 file-only CN06 catalog Location to local summary branch.

Recover actual fields/getters; do not name unknown gameplay values or issue
default server data. This is the final delegated round before the requested stop.
"""
from pathlib import Path
import csv
import io
import json

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-resource-selection-source-01/agents/cn-location-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_account_location_frontier175.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
    'tools/reconstruction/cn_receiver_owner_frontier169.py',
    'src/cn/protocol/CnAccountReplies.h', 'src/cn/protocol/CnAccountReplies.cpp',
    'src/cn/protocol/CnCharacterSummary.h', 'src/cn/protocol/CnCatalogRoute.h',
    'src/cn/auth/SharedAccountSelection.cpp', 'src/cn/auth/SharedCommonCharacterSummarySource.cpp',
    'src/cn/protocol/CnCreationLocationProjection.h',
    'tools/reconstruction/cn_owned_creation_location_delivery.py', OWN]
NEW = {'0047c6c0', '0047c760', '0047f630', '0047f650', '0047f670'}
OLD = {'00445b40', '0047fe30', '0047d1c0', '0047c900', '0047faa0'}
READ_C = NEW | OLD | {'00443080', '00443640', '00444fe0', '0047f690',
                      '0044d5f0', '00448f20', '004490f0'}


def dump(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes()
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    return {'path': path.relative_to(SERVER).as_posix() if repository else str(path),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve previous round175 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN original changed')
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in NEW | OLD]
    original_rows = [r for r in metadata if r['address'].lower() in READ_C]
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for name in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + name, RECOVERY / name))
    for row in original_rows:
        originals.append(retain('native-original-inputs/' + row['address'].lower() + '.c',
                                RECOVERY / row['file']))
    dump('native-original-inputs.json', originals)
    dump('before-source-origins.json', [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE])
    dump('new-source-absence.json', {'new_absent_from_root_before1252': [OWN], 'existing_cpp_edits': []})
    prior = [ROOT / 'cn-account-catalog-layout-01/findings.json',
             ROOT / 'cn-account-selection-owner-01/integration-manifest.json',
             ROOT / 'cn-owned-creation-location-01/findings.json',
             ROOT / 'cn-owned-creation-location-01/native-creation-location-references.json',
             ROOT / 'tw-native-rom-geometry-source-01/agents/cn-slot-frontier/findings.json',
             ROOT / 'tw-native-rom-geometry-source-01/agents/cn-slot-frontier/seal.json']
    dump('retained-prior/originals.json', [retain('retained-prior/' + str(i) + '-' + p.name, p)
                                        for i, p in enumerate(prior)])
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    dump('native/selected-original-metadata.json', selected)
    instructions, new_sites, old_sites = {}, [], []
    for row in selected:
        address = row['address'].lower()
        lo, size = int(address, 16), int(row['bytes'])
        offset, body = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                    'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                   for i in md.disasm(body, lo)]
        instructions.update({r['va']: r for r in decoded})
        section = 'new-location-getter-spans' if address in NEW else 'retained-caller-catalog-spans'
        path = OUT / ('native/' + section + '/' + address + '.bin')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(body)
        dump('native/' + section + '/' + address + '.json', decoded)
        item = {'owner': address, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{lo+size:08x}',
                'file_offset': offset, 'raw_bytes': body.hex(), 'sha256': sha(body),
                'decoded_instruction_count': len(decoded),
                'decoded_bytes': sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
                'new_round175_span': address in NEW,
                'phase_opcode_inventory_increment': False}
        (new_sites if address in NEW else old_sites).append(item)
    dump('native/new-sites.json', new_sites)
    dump('native/retained-caller-catalog-sites.json', old_sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/selected-original-calls.json', [r for r in calls
        if any(v.lower() in NEW | OLD for v in r.values())])

    def relation(identifier, scope, vas, old_vas=(), **fields):
        return {'id': identifier, 'scope': scope,
                'rawsites': [instructions[v] for v in vas],
                'retained_original_witness_sites_not_recounted': [instructions[v] for v in old_vas],
                **fields}

    relations = [
        relation('catalog-first-nonzero-location-byte1-getter',
            'Actual0047C6C0 scans10 nodes with30h stride and10 locations with4-byte stride in selected group/server. First nonzero BYTE+0 selects the row; MOVZX BYTE at same row+1 returns unsigned8. No matching summary routing key or semantic map lookup occurs in this function.',
            ['0047c6cc','0047c6d5','0047c6db','0047c6e7','0047c6ea','0047c6ed',
             '0047c6f0','0047c6f6','0047c6f9','0047c707','0047c70d','0047c710','0047c712','0047c715','0047c700'],
            table='009ee1c0[group]', server_stride='0x260', node_stride='0x30',
            location_stride='0x04', field_offset='0x01', load_width_bits=8, zero_extended=True,
            empty_scan_return_bits=0, field_gameplay_semantics=None),
        relation('catalog-first-nonzero-location-word2-getter',
            'Actual0047C760 independently repeats first-nonzero routing-key scan and MOVZX WORD from same selected location+2. Its native unsigned16 width and source are recovered, but not field meaning or authoritative issuance.',
            ['0047c76c','0047c775','0047c77b','0047c787','0047c78a','0047c78d',
             '0047c790','0047c796','0047c799','0047c7a7','0047c7ad','0047c7b0','0047c7b2','0047c7b5','0047c7a0'],
            table='009ee1c0[group]', server_stride='0x260', node_stride='0x30',
            location_stride='0x04', field_offset='0x02', load_width_bits=16, zero_extended=True,
            empty_scan_return_bits=0, field_gameplay_semantics=None),
        relation('three-actual-wrapper-callees-and-argument-widths',
            'F630/F650/F670 pass exactly first two explicit DWORD stack arguments and add104 to ECX before calling C6C0/C760/C900. Each wrapper pops12 bytes; third summary pointer is not passed or read. The actual two new base getters use global table and explicit group/server, ignoring ECX in their retained complete spans.',
            ['0047f633','0047f636','0047f63c','0047f63f','0047f645',
             '0047f653','0047f656','0047f65c','0047f65f','0047f665',
             '0047f673','0047f676','0047f67c','0047f67f','0047f685'],
            ['0047c924','0047c926','0047c928','0047c945'],
            wrapper_targets={'0047f630':'0047c6c0','0047f650':'0047c760','0047f670':'0047c900'},
            third_argument_consumed=False, inferred_owner_phase=None),
        relation('state1a-projects-catalog-fields-into-selected-local-summary',
            'Previously retained00445B40 has actual state0x1A branch distinct from state0x18 creation projection. It reads selected group/server as signedWORD, scene second owner as ECX, invokes three getters, writes AL/AL/AX to selected character-row offsets+0x20/+0x21/WORD+0x22 (payload offsets+0x22/+0x23/WORD+0x24), then uses same selected summary for FAA0 endpoint selection. This is local cache mutation, not original07 producer or authoritative server data.',
            ['0047f63f','0047f65f','0047f67f'],
            ['00445c9c','00445c9f','00445cab','00445cb2','00445cb9','00445cc1',
             '00445cc6','00445ccd','00445cd0','00445cd6','00445ce7','00445cf6','00445d0b',
             '00445d1c','00445d2b','00445d30','00445d37','00445d38','00445d3b','00445d41',
             '00445d73','00445d7a','00445d81','00445d97'],
            actual_state_predicate='0x1a', summary_payload_pointer_scene_offset='0x1792d0',
            selected_row_scene_offset='0x1792d4', character_stride='0x24',
            actual_summary_payload_offsets=['0x22','0x23','0x24'],
            character_row_offsets=['0x20','0x21','0x22'], store_width_bits=[8,8,16],
            actual_owner_scene_offset='0x16180', original_received07_modified_on_server=False,
            phase_or_packet_binding_added=False),
        relation('existing06-storage-to-new-opaque-getter-source-lineage',
            'Previously recovered06 consumer copies original4 payload bytes at catalog+0xCC+server*0x260+node*0x30+location*0x04. New getters load +0xCD BYTE and +0xCE WORD of that identical computed row. Previously recoveredD1C0 matches only nonzero+0xCC against character-row+0x20 (payload+0x22); state0x1A therefore supplies fallback tuple before endpoint matching, without explaining map/area/spawn or current original issuer.',
            ['0047c6cc','0047c6d5','0047c6e7','0047c715','0047c76c','0047c775','0047c787','0047c7b5'],
            ['00480428','00480434','00480439','00480449','0048044f','00480452','00480455','0048045b',
             '0047d20e','0047d238','0047d23a','0047d23e','0047fb60'],
            complete_native_location_field_widths=[8,8,16],
            catalog_origin='existing account S2C06 raw four-byte record',
            recovered_byte1_semantics=None, recovered_word2_semantics=None,
            scene_map_spawn_join_proven=False, official_issuer_rules_proven=False),
    ]
    findings = {'round':175, 'version_scope':'cn', 'native_sha256':PIN,
        'new_native_relations':relations, 'new_bounded_native_spans':len(new_sites),
        'new_bounded_native_bytes':sum(int(r['bytes']) for r in selected if r['address'].lower() in NEW),
        'retained_old_caller_catalog_spans_not_recounted':len(old_sites),
        'old169_to174_spans_or_relations_recounted':0, 'old_creation_catalog_spans_recounted':0,
        'receiver_contexts':14, 'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'address':a,'phase':None,'slot':None,'producer_pair':None}
                              for a in ('0047de70','004812b0')],
        'new_phase_opcode_bindings':0, 'new_formal_source_owner_chains':0,
        'new_complete_bidirectional_routes':0, 'new_cpp_files':0,
        'location_byte1_meaning':None, 'location_word2_meaning':None,
        'authoritative_location_issuer_recovered':False,
        'whole_game_route_total':None, 'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'native_run':False,'emulation_run':False,
        'database_access':False,'deployed':False,'user_requested_stop_after_round':True}
    dump('findings.json',findings)
    dump('stage-accounting.json',{'direction':'existing-account06-to-local-summary-state1A',
        'new_actual_location_relations':len(relations), 'new_bounded_native_spans':len(new_sites),
        'retained_old_spans_not_recounted':len(old_sites), 'new_receiver_contexts':0,
        'new_opcode_inventory':0,'complete_routes_added':0})
    dump('gaps.json',[
        'Byte1 and WORD+2 source/width/local projection are established, but field gameplay names, map/scene/resource joins and authoritative06/07 issuance remain unknown; never manufacture zero/default server values from native empty-scan return.',
        'The three getters run separate scans; static code does not establish snapshot atomicity or authorize a common record/source mutation policy.',
        'State1A summary edits are local receiving-client cache; do not replace immutable server native07 metadata with these values or call an account/world gameplay route complete.',
        'Next exact original trace root: callers entering00445B40 state1A and writers of scene1792DC=1A establish the actual no-existing-character fallback situation. Then trace independent world02 area/scene source to determine whether any equality exists; names alone cannot join them.',
        'Prior creation state18 packed-word projection is retained history; this branch does not imply byte1 range0..3 or WORD+2 range0..1023 for arbitrary06 bytes.',
        'No retry of155 title/capacity chain, locale-table candidate study, oldhelper lock/gate or global79/3735 occurred. Parent must stop work after this final round.',
    ])
    print(json.dumps({'artifact':str(OUT),'new_spans':len(new_sites),'new_bytes':findings['new_bounded_native_bytes'],
        'new_relations':len(relations),'retained_old_spans':len(old_sites),'native_original_count':len(originals)}))


def capture():
    if not (OUT/'findings.json').is_file() or (OUT/'seal.json').exists():
        raise RuntimeError('No unsealed delivery')
    dump('current-source-origins.json',[retain('current/'+rel,SERVER/rel,True) for rel in SOURCE])
    listing=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing+['LIST.txt'])+'\n').encode())
    rows=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
          for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json',{'kind':'immutable round175 CN account location source frontier','files':rows,
        'native_input_sha256':PIN,'source_original_count':len(SOURCE),'complete_routes_added':0,
        'build_run':False,'tests_run':False,'native_run':False,'database_access':False,
        'user_requested_stop_after_round':True})
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(rows),
        'current_source_originals':len(SOURCE),'tool_sha256':sha((SERVER/OWN).read_bytes())}))


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--capture-after-batchfinal']:capture()
    elif not sys.argv[1:]:main()
    else:raise SystemExit('Only file-only extraction or BATCHFINAL capture is supported')
