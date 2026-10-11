"""209 file/Capstone-only reconciliation of retained Taiwan initial2A fields."""
from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-entry-material-source-01/agents/tw-entry-native-fields'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
PE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,d):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copies(paths,folder):
    result=[]
    for i,rel in enumerate(paths):
        p=ROOT/rel;b=p.read_bytes();copy=f'{folder}/{i:02d}-{p.name}'
        q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        result.append(dict(path=str(p.resolve()),copy=copy,bytes=len(b),sha256=sha(b)))
    return result
def main():
    if (OUT/'seal.json').exists():raise RuntimeError('Do not modify sealed209')
    OUT.mkdir(parents=True,exist_ok=True)
    guides=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
    sources=['src/protocol/RecoveredWorldEntry.h','src/protocol/RecoveredWorldEntryView.h',
        'src/game/SharedTaiwanWorldEntrySource.h','src/game/SharedTaiwanWorldEntrySource.cpp']
    docs=['docs/research/current-2a-da-baseline-20260926.md',
        'docs/research/current-offline-world-entry-audit-20260920.md',
        'docs/research/recovered-world-entry-20260919.md',
        'docs/research/current-world-appearance-20260919.md',
        'docs/research/current-owned-appearance-20260919.md',
        'docs/research/current-world-role-resources-20260919.md',
        'docs/research/current-world-actor-20260919.md',
        'docs/research/current-world-initialization-sequence-20260919.md',
        'docs/research/shared-taiwan-world-lifecycle-20261007.md',
        'docs/research/tw-native-host-composition-source-20261008.md']
    tools=['tools/strike_lab/current_2a_da_baseline_20260926.py',
           'tools/strike_lab/current_world_actor.py',
           'tools/reconstruction/shared_taiwan_world_lifecycle_delivery.py']
    own='tools/reconstruction/tw_native_entry_fields209.py'
    current=copies(guides+[own]+sources,'current')
    originals=current+copies(docs+tools+['tests/fixtures/recovered-world-entry.json'],'originals')
    dump('current-source-origins.json',current);dump('original-inputs.json',originals)
    contexts=copies(['docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-progress-latest.json'],'read-epoch-context')
    dump('context-origins.json',contexts)
    legacy=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
    raw=PE.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Actual full PE hash does not match retained Taiwan master')
    dump('native-input-references.json',[dict(path=str(PE.resolve()),bytes=len(raw),sha256=sha(raw),
        full_inplace_hash=True,copied=False,historical_original_path=str(legacy),
        historical_original_currently_present=legacy.exists(),
        installed_font_restored_image_sha256='99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25',
        identity_scope='Mapped native master; installed modified image and historical6bf75e audit identity remain distinct.')])
    md=Cs(CS_ARCH_X86,CS_MODE_32);spans=[];instructions=[]
    # Re-read only retained original initializer. Calls remain boundaries; no callee followed.
    for name,start,end in [('retained-normal-initializer',0x68160,0x688d0)]:
        data=raw[start:end];ins=list(md.disasm(data,0x400000+start))
        if sum(i.size for i in ins)!=len(data):raise RuntimeError('Incomplete bounded static instruction table')
        copy=f'native/{name}.bin';q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
        rows=[dict(va=f'{i.address:08X}',file_offset=i.address-0x400000,bytes=i.bytes.hex(),
                   mnemonic=i.mnemonic,operands=i.op_str) for i in ins]
        instructions+=rows;dump(f'native/{name}.instructions.json',rows)
        spans.append(dict(name=name,va=f'{0x400000+start:08X}',end_exclusive_va=f'{0x400000+end:08X}',
            file_offset=start,bytes=len(data),sha256=sha(data),copy=copy,instructions=len(rows),
            classification='Retained known initializer re-capture; not new native coverage. No claim all bytes previously existed in a sealed bounded span.'))
    dump('native-spans.json',spans)
    table=raw[0x68924:0x68944];(OUT/'native/selector-table.bin').write_bytes(table)
    targets=[f'{int.from_bytes(table[i:i+4],"little"):08X}' for i in range(0,len(table),4)]
    dump('data-sites.json',[dict(path=str(PE.resolve()),file_offset=0x68924,va='00468924',bytes=32,
        sha256=sha(table),copy='native/selector-table.bin',targets=targets,
        classification='Retained initializer8-way switch raw data; not server permission or learned classification.')])
    fields=[
        dict(body=[0,1,2,3],logical=[1,2,3,4],width='DWORD',
             masks={'actor_handle':'0x00003FFF','raw_status':'0x0000C000','resource_selector':'0x007F0000',
                    'normalized_selector':'0x03800000','entry_flag':'0x80000000'},
             stores=['low14->R+0','bits14..15->R+4694','bit31->out argument/W+A7F2F3C',
                     'bits16..22 qualified against signed native count-1, then -1 or0 ->R+4C',
                     'bits23..25 1..7 ->value-1 else0 ->R+38',
                     'bits16..22 and bits23..25 also contribute packedR+44'],
             va=['004681EB','004681FD','0046826B','004685EB','00468629','004686D0']),
        dict(body=[4,5,6,7],logical=[5,6,7,8],width='DWORD',
             masks={'selector_switch':'0x00000007','raw_field94':'0x000000F8','normalized_field54':'0x00000700',
                    'raw_field4590':'0x0000F800','resource_selector':'0x00FF0000','raw_fieldFC':'0xFF000000'},
             stores=['low3 ->8-way switch R+24 values[7,0,1,2,3,4,5,6]',
                     'bits3..7->R+94 WORD','bits8..10 1..6 ->value-1 else0 ->R+54',
                     'bits11..15 raw->R+4590 BYTE;1..8 ->value-1 else0 ->R+90 WORD',
                     'BYTE6->resource61270 selector and1..91 ->value-1 else0 ->R+2C',
                     'bits16..23 also toR+44 bits18..25','highBYTE->R+FC'],
             va=['0046820A','004684CD','00468564','00468689','0046870A','0046875B','004687FB']),
        dict(body=[8,9,10,11],logical=[9,10,11,12],width='4 opaque bytes',masks={},
             stores=['No separate operand read in this bounded normal initializer; kept unchanged. No global unused/dead field claim.'],va=[]),
        dict(body=list(range(12,20)),logical=list(range(13,21)),width='2 complete DWORDs / four packed WORD components',
             masks={'variants':'each odd BYTE high3','resource_keys':'remaining packed component bits retained'},
             stores=['B12DWORD->R+4584;B16DWORD->R+4588','B13>>5->R+28',
                     'normal branch61270 input all8; native component selection retained',
                     'normal component variants high3 each oddbyte; overrideW1539AD70 bit10 forces7',
                     'profile32->B13 high3/profile36 high3->B15 high3 only for qualified normal branch; not whole profile serializer'],
             va=['00468328','0046833F','004684D6','0046851A','00468527']),
        dict(body=[20,21,22,23],logical=[21,22,23,24],width='complete DWORD',masks={},
             stores=['complete B20DWORD->R+458C; actor appearance/HUD fields in historical separate evidence; all input bytes preserved'],
             va=['00468322','00468370']),
        dict(body=[24,25],logical=[25,26],width='LE WORD inside a DWORD load',
             masks={'area':'0x003F','scene':'0xFFC0'},
             stores=['area requires1..16;->R+18 WORD','scene=WORD>>6 ->R+14 DWORD','actual scene/resource helper arguments'],
             va=['004681CF','004681D8','004681E5','0046865C']),
        dict(body=[26,27],logical=[27,28],width='upper WORD of complete B24 DWORD',masks={},
             stores=['Loaded with B24DWORD and retained in some scene helper arguments; no independent named geometry meaning recovered. Not declared unread.'],
             va=['004681CF','00468290','004682F1']),
        dict(body=[28,29,30,31],logical=[29,30,31,32],width='LE DWORD',
             masks={'kind':'0x00000003','x':'0x0001FFFC','y':'0xFFFE0000'},
             stores=['kind->R+10 BYTE/W+22C;kind==2->W+AA25EC4','x=(value>>2)&7FFF->R+8','y=value>>17->R+C'],
             va=['00468636','0046863F','00468650','0046867D']),
        dict(body=[32,33],logical=[33,34],width='LE WORD',masks={},
             stores=['completeWORD->W+1539AED2 (R+4696)','nonzero and actual45C100 predicate chooses resource substitution; otherwise normal61270 path',
                     'actual resource45C000/45A0A0 result supplies temporary components, not a default actor transformation grant'],
             va=['0046836C','00468376','00468386','004683A3','00468558']),
        dict(body=[34],logical=[35],width='BYTE',masks={},stores=['raw->R+4695 (independent semantic unknown)'],va=['0046827B','00468284']),
        dict(body=[35],logical=[36],width='BYTE',masks={},stores=['raw->R+4698 (independent semantic unknown)'],va=['0046827B','0046828A'])]
    dump('field-groups.json',fields)
    every=[dict(logical_offset=0,body_offset=None,field='opcode2A',mask='FF')]
    for body in range(36):
        field=next(f for f in fields if body in f['body'])
        every.append(dict(logical_offset=body+1,body_offset=body,frame_decoded_offset=body+3,
                          group_body_offsets=field['body'],width=field['width'],masks=field['masks'],stores=field['stores']))
    dump('logical37-byte-map.json',every)
    fixture=json.loads((ROOT/'tests/fixtures/recovered-world-entry.json').read_bytes())
    dump('historical-candidate-scope.json',dict(body_sha256=fixture['body_sha256'],fixture=fixture,
        not_current_owned_material=True,legacy_original_not_accessed=True,historical_acceptance_not_refreshed=True,
        note='Standalone40 frame is current zero-seed reframing, not historical standalone capture. Legacy source exists only as fixture provenance; no old source authority restored.'))
    dump('findings.json',dict(round=209,phase='STATIC file/hash/Capstone only',
        original_image_sha256=PIN,logical_bytes=37,body_bytes=36,standalone_frame_bytes=40,
        sources=[r['path'] for r in originals],
        full_owned_frame_supplier=dict(actual_source='SharedTaiwanWorldEntrySource.cpp',
            existing_checks='Full selected root/profile/name properties + exact saved area/scene/x/y/revision + map row before/after actual supplier and mandatory Current; no truncation larger characterID.',
            required='Real lifetime-owned full native frame/profile/resource/status issuer. Return exact saved complete frame with provenance/current. Preserve opaque bytes and actual resource generation. Repository/map geometry qualification alone does not own unknown historic selectors.',
            not_a_supplier='RecoveredWorldEntry historical_body with replacedID/variants/map bits remains historical candidate; cannot fabricate all other bytes as selected character state.',
            wire_kind_relation='Map catalog kind and low2 wire kind remain independently qualified; no guessed equality.',
            frame_scope='Immutable full40 retained; static source read does not execute encoder/decoder/checksum or claim client accepted.'),
        unqualified=['B8..11 meaning','B26..27 passed scene argument semantics','raw R4694/R4695/R4698/status and packedselectors server ownership',
                     'complete saved-profile-to-native entry serializer','nonzero transform resource eligibility','actual scene overlay/window/resource/peer initial material',
                     'full original server issuer/current lifecycle and Main factory hosting'],
        external_inputs='Native initialization also consumes caller role/name/out-flag pointers and preloaded banks. Actor name atR+B7 is an external argument, not one of37logical bytes.',
        alias_warning='VA468xxx means base400000 + RVA68xxx; old audit6bf75e build pin and installed99c font-restored pin are not promoted to current native master.',
        old_native_evidence_reused=True,new_native_coverage_bytes=0,new_opcodes=0,new_complete_routes=0,
        captured_retained_span_bytes=sum(s['bytes'] for s in spans),whole_game_percentage=None,
        no_runtime=True,no_tests=True,no_DB=True,no_Cplusplus_changes=True))
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p!=OUT/'seal.json' and p!=OUT/'LIST.json':
            b=p.read_bytes();members.append(dict(path=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
    dump('LIST.json',members);b=(OUT/'LIST.json').read_bytes()
    members.append(dict(path='LIST.json',bytes=len(b),sha256=sha(b)))
    dump('seal.json',dict(members=sorted(members,key=lambda r:r['path']),count=len(members),bytes=sum(r['bytes'] for r in members),
        excludes='Top-level seal.json only'))
    print(json.dumps(dict(members=len(members),files=len(members)+1,current=len(current),originals=len(originals),
        seal_sha256=sha((OUT/'seal.json').read_bytes()),tool_sha256=sha(Path(__file__).read_bytes()),
        native_span_bytes=sum(s['bytes'] for s in spans),native_instructions=len(instructions)),indent=2))
if __name__=='__main__':main()
