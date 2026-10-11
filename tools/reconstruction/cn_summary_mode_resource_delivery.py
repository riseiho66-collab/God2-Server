"""Bind native normal-selection mode branch to the correct text/resource owner.

Static file-byte/CFG/CSV/source work; no builds/tests/native/server/SQL execution.
"""
import csv
import io
import hashlib
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-summary-mode-resource-01'
ROUND='20261007-cn-summary-mode-resource'
FUNCTIONS=('00428c80','0042c3a0','00446bd0','00481640','00450170','00450620',
    '00407d70','00435cd0','00435c40','00409c00')
SOURCES=('src/cn/protocol/CnCharacterSummary.h','tools/reconstruction/cn_summary_mode_resource_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py','docs/research/cn-summary-mode-resource-20261007.md')


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve historical evidence')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before source changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    original=base/'cn-summary-opaque-agent-01'
    manifest=json.loads((original/'delivery-manifest.json').read_text(encoding='utf-8'))
    pins={r['file']:r['sha256'] for r in manifest['files']}
    raw=(original/'findings.json').read_bytes()
    if sha(raw)!=pins['findings.json']:raise RuntimeError('Historical opaque-summary receipt changed')
    save('retained-source/cn-summary-opaque-agent-01/findings.json',raw)
    save('retained-source/cn-summary-opaque-agent-01/delivery-manifest.json',(original/'delivery-manifest.json').read_bytes())
    prior=base/'cn-delete-caller-seh-frontier-01';m=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    p={r['path']:r['sha256'] for r in m['files']};raw=(prior/'qualified-ui-switches.json').read_bytes()
    if not m['sealed'] or sha(raw)!=p['qualified-ui-switches.json']:raise RuntimeError('Qualified switches changed')
    switches=json.loads(raw);save('retained-source/qualified-ui-switches.json',raw)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes();save('native/functions.tsv',metadata)
    rows={r['address'].lower():r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    native=[];contexts=[];decoded={}
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']));tables={}
        for table in switches:
            if table['function']!=entry:continue
            guard=bytes.fromhex(table['guard_bytes'])
            if view.read(int(table['guard'],16)-ib,len(guard))!=guard:raise RuntimeError('Primary guard changed')
            targets=struct.unpack('<'+'I'*table['entries'],view.read(int(table['table'],16)-ib,4*table['entries']))
            if [f'{t:08x}' for t in targets]!=table['targets']:raise RuntimeError('Primary switch changed')
            tables[int(table['dispatch'],16)]=targets
            save('native/tables/'+table['table']+'.bin',view.read(int(table['table'],16)-ib,4*table['entries']))
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),tables);decoded[entry]=ins
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes());dump('native/'+entry+'.cfg.json',cfg)
        native.append({'entry':entry,'metadata_bytes':len(code),'source':row['file'],'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'overlap':cfg['instruction_overlap_found']})
        ordered=sorted(ins.values(),key=lambda i:i.address)
        for n,i in enumerate(ordered):
            hit=any(op.type==capstone.x86_const.X86_OP_MEM and op.mem.disp in
                (0xb2f58,0xb2f5c,0x4d74,0x1617c,0x1792d0,0x4200) for op in i.operands)
            hit|=any(op.type==capstone.x86_const.X86_OP_IMM and op.imm in (0x7ee9a0,0x4d8) for op in i.operands)
            if hit:contexts.append({'entry':entry,'site':f'{i.address:08x}','context':[
                {'site':f'{j.address:08x}','bytes':j.bytes.hex(),'mnemonic':j.mnemonic,'operand':j.op_str}
                for j in ordered[max(0,n-5):n+8]]})
    dump('native/index.json',native);dump('native/owner-resource-accesses.json',contexts)
    if view.string(0x7ee9a0-ib)!='SystemMessage':raise RuntimeError('Native section literal changed')
    save('native/SystemMessage-007ee9a0.bin',b'SystemMessage\0')
    resource=base/'cn-directory-display-fields-01/native/resources'
    receipt_raw=(resource/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed=(CN.parent/'XJZ-CN/Data2/Patch/Comm/message.csvZ').read_bytes();plain=(resource/'message.csv').read_bytes()
    if receipt['client_sha256']!=PIN or receipt['asset']['codepage']!=936 or \
       sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Pinned resource receipt differs')
    save('resources/message.csvZ',packed);save('resources/message.csv',plain)
    save('resources/prior-account-phase-evidence.json',receipt_raw)
    csvrows=list(csv.reader(io.StringIO(plain.decode('cp936'))));sections={}
    for name in ('SystemMessage','ProgramMsg'):
        start=next(i for i,r in enumerate(csvrows) if r and r[0]==name);count=int(csvrows[start][1])
        values={}
        for i,r in enumerate(csvrows[start+1:start+1+count],start+2):
            ident=int(r[0])
            if ident in values:raise RuntimeError('Duplicate resource ID')
            values[ident]={'csv_row':i,'id':ident,'cells':r,'cells_cp936_hex':[c.encode('cp936').hex() for c in r]}
        sections[name]={'declared_rows':count,'minimum_id':min(values),'maximum_id':max(values),
            'row1240_exists':1240 in values,'selected':{str(k):values[k] for k in (231,505,1240) if k in values}}
    selected=sections['SystemMessage']['selected']['1240']
    dump('resources/selected-section-rows.json',sections)
    relations={'native_summary_route':'00481640 accepted07 ->flags bit0 AND1 ->account network4200 ->normal UI state4',
        'state4_target':'004477DD guarded switch index4 ->00447A5B',
        'empty_branch':'count0 AND account network4200==1 ->resource owner UI+16188 ->table owner+B2F58; signedWORD maximum+B2F5C >=1240 ->table+4D74 ->message ->004497F0(1)',
        'correct_section':'00428C80 compares literal SystemMessage at429A3A, matches into its inlined loader429A72, allocates16-byte rows429A80 and stores table pointer at owner+B2F58 at429A85; row ID decremented429ADA. Standalone0042C3A0 independently implements the same one-based16-byte layout/first text pointer+4; not a claimed direct call from428C80.',
        'offset_identity':{'offset_hex':'4D74','calculation':'16*(1240-1)+4','selector':0,'section':'SystemMessage','id':1240},
        'native_text':selected['cells'][2],'text_cp936_hex':selected['cells_cp936_hex'][2],
        'nonempty_controls':'450170 forwards group0/control8 or9/resource selectors99/100 through407D70 ->409C00 resource lookup and tile updates; these are not ProgramMsg IDs99/100',
        'input_state_source':'450620 writes control+8BC and calls435CD0(value nonzero) or435C40(zero), which set existing18h-stride input record state2 or1; no server entitlement recovered',
        'correction':'Historical cn-summary-opaque-agent-01/findings.json described ProgramMsg row1240. Retain old receipt; new primary table/loader/resource relation proves SystemMessage1240.',
        'view':'CnCharacterSummary native_normal_selection_path describes normal UI state4 only; no request/reply emitted, flags/opaque bytes preserved, not server create permission',
        'no_character_mode0':'442A20 then UI state5 unless already stateB; observing this branch is not server authorization',
        'levels_changed':False,'server_mode_issuance_recovered':False,'native_business_entitlement_recovered':False}
    dump('source-relations.json',relations)
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed actual07 queue/publication/drain source matched current files',
        'native_metadata_envelopes_retained':len(native),'resource_owner_corrections':1,
        'native_empty_selection_read_only_branch_views_added':1,'system_message_ids_bound':[1240],
        'system_message_declared_rows':sections['SystemMessage']['declared_rows'],
        'program_message_declared_rows':sections['ProgramMsg']['declared_rows'],
        'current_packed_resource_sha256':sha(packed),'retained_decoded_resource_sha256':sha(plain),
        'native_fields_newly_recovered':0,'new_packet_values':0,'new_native_phase_source_bindings':0,
        'new_source_owner_chains':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':[
            'Actual native07 mode/flags/opaque18/inactive rows and visibility/common-ID mapping issuer; resource wording alone does not supply server policy.',
            'Full native auth/directory/world00-1F/02/18/03 suppliers, configured common hosting and durable recovery.',
            'Transfer/reconnect/standalone variants, all gameplay/numeric wire/object/display and complete phase/state/indirect denominator.']}
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# CN normal-selection mode and corrected SystemMessage owner\n\n'
            'PHASE1 static primary PE/CFG/resource/source work only; no build/test/native/runtime/server/DB/migration/deployment. Levels stay unchanged. The previous queue/publication/drain source round made progress and its sealed current files matched before this round.\n\n'
            'Ten actual metadata-bounded envelopes retain primary bytes, entry-rooted CFG, raw assembly and navigation C. Qualified guarded UI switch tables are reread from the pinned CN EXE. State4 at004477DD targets00447A5B. The established accepted07 path writes flags&1 into the account network4200. In state4, count0 plus mode1 enters the message/reset branch; nonempty rows take their existing selection UI, while count0/mode0 calls442A20 and advances to state5 unless stateB. No global variant/reachability closure is claimed.\n\n'
            'Correction: cn-summary-opaque-agent-01/findings.json called the mode1 empty-list text ProgramMsg1240. Its actual UI+16188 resource owner uses the table pointer at owner+B2F58, highest loaded ID at owner+B2F5C and offset4D74 within that table. Primary00428C80 compares the SystemMessage literal007EE9A0 at429A3A and matches into its inlined loader429A72:429A80 allocates16-byte rows,429A85 stores the exact table pointer and429ADA decrements the row ID. Standalone0042C3A0 independently constructs the same one-based16-byte layout; there is no claimed direct call from428C80 to42C3A0. Offset4D74 equals16*(1240-1)+4, the first text pointer for SystemMessage1240. The current packed CP936 message.csvZ matches its original asset pin; retained decoded CSV matches its prior decoded pin. No loaded native resource code ran.\n\n'
            'SystemMessage1240 reads 您在牧野服务器中没有角色数据。 The separate ProgramMsg section has no1240 row in this snapshot. The old mistaken receipt remains unchanged and is retained with this additive correction; it is not silently refreshed. This proves the client-facing label for the scoped branch, not why an official server sets mode1, native visibility/account policy, regional eligibility, create permission or actual meaning of every other flag bit. Do not rename bit0 to a server entitlement or hardcode it from this text.\n\n'
            'For nonempty rows,450170 forwards group0, controls8/9 and selectors99/100 to407D70. That function stores the selector and follows409C00 resource lookup/tile update; these numbers are not ProgramMsg text IDs99/100.450620 writes control+8BC and delegates to435CD0/435C40, setting an existing18h-stride input record state2/1. These source relationships describe UI behavior only; image naming/full resource semantics and authoritative permissions remain separate.\n\n'
            'CnCharacterSummary now exposes a read-only NativeNormalSelectionPath for this exact normal state4 branch and the correctly scoped SystemMessage ID. It preserves every native byte, emits no packet, invents no field/default/rule and is not installed as an authoritative handler. Native level/progression/display fields and all frozen functionality remain unchanged.\n\n'
            'Increment: resource-owner correction1 and scoped read-only client branch view1; new native fields/opcodes/phase/owner/full routes0. The native07 issuer and actual common server providers/hosting, durable recovery, standalone/transfer variants, all gameplay/numeric extensions and whole-game denominator remain open. Whole-game count/completed/percentage null.\n')
    dump('findings.json',findings)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','native_metadata_envelopes_retained','resource_owner_corrections','native_empty_selection_read_only_branch_views_added','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
