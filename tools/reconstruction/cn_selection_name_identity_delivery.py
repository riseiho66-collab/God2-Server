"""File-only CN normal name-prompt/07 ordinal and common identity source receipt."""
import csv
import hashlib
import io
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-selection-name-identity-01'
ROUND='20261007-cn-selection-name-identity'
FUNCTIONS=('00446bd0','00440b20','00440ae0','00446150','00434180',
    '00433b00','0047f750','00480650','0043d640')
SOURCES=('src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/auth/SharedAccountSelectionName.cpp','src/cn/protocol/CnCharacterSummary.h',
    'tools/reconstruction/cn_selection_name_identity_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py','docs/research/cn-selection-name-identity-20261007.md')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before source receipt required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Original source receipt changed')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json',
            'docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    prior=base/'cn-selection-name-submit-01'
    seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in seal['files']}
    data=(prior/'qualified-switches.json').read_bytes()
    if not seal['sealed'] or sha(data)!=pins['qualified-switches.json']:raise RuntimeError('Prior switch receipt changed')
    switches=json.loads(data);save('retained-source/qualified-switches.json',data)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN pinned image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes();save('native/functions.tsv',metadata)
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    error_table=view.read(0x480aa4-ib,72);error_targets=struct.unpack('<18I',error_table)
    error_map=view.read(0x480aec-ib,35)
    if max(error_map)>=len(error_targets):raise RuntimeError('Primary error map outside retained table')
    save('native/tables/00480aa4.bin',error_table);save('native/tables/00480aec.bin',error_map)
    native=[];decoded={};qualified=[]
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']));tables={}
        for t in [t for t in switches if t['function']==entry]:
            guard=bytes.fromhex(t['guard_bytes'])
            if view.read(int(t['guard'],16)-ib,len(guard))!=guard:raise RuntimeError('Primary guard changed')
            data=view.read(int(t['table'],16)-ib,t['entries']*4)
            targets=struct.unpack('<'+'I'*t['entries'],data)
            if [f'{x:08x}' for x in targets]!=t['targets']:raise RuntimeError('Primary target table differs')
            tables[int(t['dispatch'],16)]=targets;qualified.append(t)
            save('native/tables/'+t['table']+'.bin',data)
        if entry=='00480650':
            guard=view.read(0x480659-ib,9)
            if guard.hex()!='83f8220f87ff030000':raise RuntimeError('Primary error selector guard differs')
            tables[0x480669]=error_targets
            qualified.append({'function':entry,'dispatch':'00480669','guard':'00480659',
                'guard_bytes':guard.hex(),'selector_map':'00480aec','map_entries':35,
                'target_table':'00480aa4','target_entries':18,'selector':'unsigned BYTE<=0x22 then map BYTE'})
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),tables);decoded[entry]=ins
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes());dump('native/'+entry+'.cfg.json',cfg)
        native.append({'entry':entry,'metadata_file':row['file'],'bytes':len(code),'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'overlap':cfg['instruction_overlap_found']})
    dump('native/index.json',native);dump('qualified-switches.json',qualified)
    ins=decoded['00446bd0']
    marker_sites=(0x447c7d,0x447c84,0x447c87,0x447c90,0x447cab,0x447cb1,
        0x447cb6,0x447cc1,0x447cca,0x447ce0,0x447d0c,0x4476fb,0x44770a)
    dump('native/name-prompt-primary-sites.json',[
        {'site':f'{at:08x}','bytes':ins[at].bytes.hex(),'mnemonic':ins[at].mnemonic,'operand':ins[at].op_str}
        for at in marker_sites])
    resource=base/'cn-directory-display-fields-01/native/resources'
    data=(resource/'account-phase-evidence.json').read_bytes();receipt=json.loads(data)
    packed=(CN.parent/'XJZ-CN/Data2/Patch/Comm/message.csvZ').read_bytes();plain=(resource/'message.csv').read_bytes()
    if receipt['client_sha256']!=PIN or sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Pinned resource differs')
    save('resources/message.csvZ',packed);save('resources/message.csv',plain);save('resources/prior-resource-receipt.json',data)
    cr=list(csv.reader(io.StringIO(plain.decode('cp936'))));start=next(i for i,r in enumerate(cr) if r and r[0]=='SystemMessage')
    messages={int(r[0]):{'csv_row':i+1,'cells':r} for i,r in enumerate(cr)
        if start<i<=start+int(cr[start][1])}
    # Entry CFG includes the mapped switch blocks. Retain the actual CX
    # resource guard in each branch, rather than decompiled case names alone.
    errors=[]
    for selector,table_index in enumerate(error_map):
        target=error_targets[table_index];message=None;sites=[]
        for at in sorted(decoded['00480650']):
            if not target<=at<target+28:continue
            i=decoded['00480650'][at]
            sites.append({'site':f'{at:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operand':i.op_str})
            if i.mnemonic=='mov' and i.op_str.startswith('ecx, 0x'):
                message=i.operands[1].imm
        errors.append({'payload0':selector,'table_index':table_index,'target':f'{target:08x}',
            'primary_entry_sites':sites,'system_message_id':message,
            'message_row':messages.get(message),'server_issuance_rule_proven':False})
    dump('resources/native-error-selector-map.json',{'entries':errors,
        'payload0_above34':'unsigned guard ->default branch SystemMessage195',
        'scope':'480650 shared client formatter; nativeD3 waiter passes accepted1E payload; not official server name rules'})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed D3/native07 lineage and actual shared saved-name CAS source',
        'native_metadata_envelopes_retained':len(native),'native_error_selector_entries_not_packets':len(errors),
        'common_published_account_offer_readers_added':1,'cn_published_name_identity_resolvers_added':1,
        'native_name_prompt_marker_views_added':1,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,
        'new_packet_values':0,'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'existing_sources_unchanged':unchanged,'levels_changed':False,'build_run':False,'tests_run':False,
        'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':['Native name rules/equivalence/uniqueness/replay operation and common-name projection; no D3 ingress handler or actual full07 reply issuer.',
            'Identity current() observes the original full root set; it is a pre-mutation proof, not a post-staged-name SQL BeforeCommit predicate. Actual mutation owner must observe staged roots and native lease separately.',
            'Fresh offered07 publication/recovery after actual COMMIT; no guessed success or repeated stale-name mutation.',
            'Configured full native auth/catalog/world hosting, all gameplay/numeric extensions and phase/state/variant/indirect/deferred denominator.']}
    dump('findings.json',findings)
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# CN published selection-name identity and primary UI marker\n\n'
            'PHASE1 file-only primary PE/resource/source integration. No build, tests, DLL/native/emulator/server execution, database access or deployment. Previous sealed name-submit/CAS turn was progress. Levels remain unchanged.\n\n'
            'Nine metadata envelopes retain primary bytes/assembly/entry CFG/navigation C. Prior guarded UI switches are independently read again from the pinned image. Normal UI state13 dispatch447C32 loads signedWORD UI1792D4, multiplies it by36 and selects the row from raw07 payload UI1792D0.447CB1 requires name byte length>=3;447CB6 and447CC1 compare first/last bytes to25h. Only that marker path calls440AE0 and goes to state31; ordinary names go to state20.440AE0 opens the existing name prompt, clears its existing edit owner through434180 and selects input6 through446150. This describes native UI branching, not server permission. CnCharacterSummary::Character now exposes this exact marker without conversion or normalization.\n\n'
            'Retained440B20/out-of-line and446BD0/inlined event0 use433B00 max14 raw bytes/nonempty then directly call47F750 with ACCOUNT UI1617C and unsignedWORD UI1792D4. The independently retained ordinary-create43D640 filter is not called in these bounded prompt submission branches. This is not global absence or a reason to apply invented permissive name rules. Native declared imports/loaded implementations are not executed.\n\n'
            '480650 primary unsignedBYTE<=34 guard,35-byte selector map and18-DWORD target table are separately retained. Entry CFG expands actual switch targets; resource guards select original SystemMessage rows from the current pinned CP936 message resource. Payload values/text remain client error formatting evidence, not proof of official server emission, permission or business rules. The D3 waiter accepts1E into this formatter and07 into its exact raw summary; no packet values or server replies are added.\n\n'
            'Actual source integration: SharedAccountSelection retains its final immutable NativeSummary through the existing queue publication barrier using an aliasing shared_ptr, and publishes that pointer plus its original QueuedSelection identity only after exact selection queue COMMIT. Full07 including flags/inactive/opaque bytes, ordered common IDs, complete original common account roots and mandatory issuer observer remain together. Earlier aggregate summaries do not become the current source. Ordinary account/world/auth/send paths keep their existing behavior.\n\n'
            'SharedWorldAdmission::selected_account_offer returns a registry-bound read-only token only from the original queue-publication token, with its exact verified account, generation, account session, revision, published Selected stage, target, unexpired deadline and uninvalidated full source. Current checks require the same revision even when reselection bytes/IDs are identical; queued, detached, reserved/world-owned, expired or invalidated attempts cannot qualify. No world reservation/mutation is performed.\n\n'
            'SharedAccountSelection::resolve_name_submission uses only this actual published source and native D3 ordinal to resolve common character identity. It requires the scoped observed D3 shape, active row, exact retained full07/ordered IDs, raw marker, mandatory actual observing phase and mandatory native issuer NameSubmission check; full common account roots are read and compared before/after issuer observation. It never looks up submitted name or treats ordinal as slot/ID. NameIdentity retains the controller/source/token, and current() rechecks connection, registry, generation/revision, complete saved roots and observers. expected_roots() supplies the original CAS snapshot, not a new permission.\n\n'
            'This is pre-mutation identity proof. Do not reuse current() as a SQL BeforeCommit check after staged name replacement: the captured old full roots intentionally differ then. The actual native mutation owner must qualify staged roots and its native lease/replay/permissions separately. Existing SharedCharacterNameReplacement remains the saved-name/offer writer; no D3 receiver calls it, no native decision or reply is fabricated, and no fresh07 or crash recovery is completed here.\n\n'
            'Increment: published account-offer reader1, concrete published07-to-common name identity resolver1, raw marker view1. Full native name rules/common projection/reply issuer/hosting stay open. These strengthen an existing source segment; new phase bindings, packet values, owner chains and complete bidirectional routes0. Whole-game denominator and completion remain unknown.\n')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','native_metadata_envelopes_retained','common_published_account_offer_readers_added','cn_published_name_identity_resolvers_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
