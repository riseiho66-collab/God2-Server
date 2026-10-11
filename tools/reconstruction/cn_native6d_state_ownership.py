"""Static CN receive/renderer-state/6D relationship recovery, not gameplay tests."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import capstone
import pefile
from tools.reconstruction.cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.round):
        raise SystemExit('Invalid round')
    out=ROOT/'artifacts/integration/packet-connections-20261006'/args.round
    if out.exists():raise SystemExit('Preserve prior evidence')
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise SystemExit('CN build changed')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as f:
        funcs={r['address']:r for r in csv.DictReader(f,delimiter='\t')}
    with (RECOVERY/'calls.tsv').open(encoding='utf-8-sig') as f:
        calls=list(csv.DictReader(f,delimiter='\t'))
    selected=['0040a1b0','0040c420','00457c20','00457c50','00457cd0','00457f00',
              '00458110','00458200','004582b0','00458340','004584f0','00458530',
              '00458570','0048caa0','0048fcc0','004ac850','00536a10','00536cf0',
              '00537d10','00537d40','005385f0','005395e0','00519d60']
    out.mkdir(parents=True);manifest=[]
    def save(name,b,source=None):
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        manifest.append({'path':name,'source':str(source) if source else None,
                         'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    def dump(name,data):save(name,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
    sources={}
    for address in selected:
        source=RECOVERY/funcs[address]['file'];b=source.read_bytes()
        sources[address]=b.decode('utf-8-sig')
        save('source/'+address+'.c',b,source)
        va=int(address,16)
        if int(funcs[address]['bytes'])<2500:
            code=pe.get_data(va-base,int(funcs[address]['bytes']))
            save('instructions/'+address+'.asm',('\n'.join(
                f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
                for i in md.disasm(code,va))+'\n').encode(),f'God2_opt.exe VA {address}')
    dump('known-call-edges.json',[r for r in calls if r['target'] in selected and r['caller'] in selected])
    # Native addresses and field-level observations; intentionally no invented
    # gameplay names, monster attributes, or server success policy.
    ownership={
        'client_sha256':PIN,
        'root_member':'parent+a69f28',
        'state_member':'parent+a69f4c == root_member+24',
        'formal_owner_alias':'4AC850 assigns owner+1b938 from argument record[14]; 48CAA0 local record[14] is parent+a69f28',
        'state_width_bits':32,
        'associated_renderer_handles':'five u16 handles at object+4,+6,+8,+A,+C; native bound0x1000',
        'observed_writers':[
            {'function':'00457c20','writes':'24=0,28=0','context':'constructor'},
            {'function':'004584f0','writes':'24=0,28=0','context':'bind/reset handle owner'},
            {'function':'00458110','writes':'24=0,28=0','context':'clear/reset handles'},
            {'function':'00458200','writes':'24=0,28=0','context':'renderer reset path'},
            {'function':'004582b0','writes':'24=1,28=1 when primary handle valid and state0; invokes458340','context':'renderer state switch'},
            {'function':'00458340','writes':'24=1,28=1 at completion and assertion exit','context':'secondary handle state switch'},
            {'function':'00457cd0','writes':'24=arg5,28=arg5','context':'configure coordinates/handles'},
            {'function':'00458570','writes':'24=0/28=0 for arg0, otherwise final24=arg/28=arg','context':'renderer switch with explicit argument'}],
        'predicate':'458530 returns state24==0',
        'field_semantics_scope':'client renderer control; precise gameplay feature name unresolved',
        'not_server_authoritative_stats':True,
        'writer_search_exhaustive':False}
    dump('state-ownership.json',ownership)
    contracts=[
        {'id':'cn:world:s2c36:owned-render-state','direction':'S2C','opcode':'36',
         'dispatch_callsite':'00490e63','handler':'00536cf0',
         'owner_gate':'(u16(logical+7)&0x3fff)==parent+1478084',
         'payload':'handler receives logical+1',
         'branches':[{'condition':'signed8(payload+4)>=0','effect':'<101 ->457c50; otherwise decode via482ec0 and457f00; then4582b0 sets renderer state1'},
                     {'condition':'signed8(payload+4)<0','effect':'458200 clears renderer state0'}],
         'direct_c2s_emission':False,
         'relation_to6d':'changes field read by6D trigger paths; does not prove which C2S causedS2C36'},
        {'id':'cn:world:s2cda:owned-refresh','direction':'S2C','opcode':'da',
         'dispatch_callsite':'004905cf','handler':'00536a10',
         'owner_gate':'u16(logical+1)==parent+1478084',
         'refresh_callsites':['00536a8e','00536cd6'],
         'refresh_inputs':'parent+1478084 role and parent+14780c8 flags',
         'branches':'nonzero signed16(payload+2) with430d70 success uses first call; alternate path reaches second call',
         'relation_to6d':'5385f0 may conditionally issue6D after renderer reconstruction'},
        {'id':'cn:world:s2c4a:refresh','direction':'S2C','opcode':'4a',
         'direct_or_deferred_owner':'48FCC0 direct when parent+30!=8; otherwise cache flag89b244 until5395E0/5393B0==1',
         'refresh_function':'005385f0',
         'ordered_early_returns':[{'mask':'02','native_resource':'e8'},
                                  {'mask':'04','native_resource':'e9'},
                                  {'mask':'08','native_resource':'ea'}],
         'normal_path':'flags&0x0e==0; snapshot state+a69f4c retained before renderer reset; reach end and snapshot!=0 ->C2S6D payload00',
         'server_reply_pairing':None}]
    for contract in contracts:
        contract.update(source_runtime_connected=False,complete_bidirectional_route=False,runtime_acceptance=False)
    dump('receive-state-contracts.json',contracts)
    # Keep the actual source lines supporting field spelling and return gates
    # separately so subsequent work can revisit decompiler/type uncertainty.
    excerpts=[]
    for address,source in sources.items():
        ls=source.splitlines()
        for n,line in enumerate(ls):
            if any(t in line for t in ('param_1[9] =','param_1[10] =','+ 0x24) =','a69f4c','0x1b938) =','(uVar6 & 2)','(uVar6 & 4)','(uVar6 & 8)')):
                excerpts.append({'function':address,'line':n+1,'context':ls[max(0,n-1):n+3]})
    dump('field-and-gate-excerpts.json',excerpts)
    save('recovery-tool.py',Path(__file__).read_bytes(),Path(__file__))
    summary={'client_sha256':PIN,'source_functions':len(selected),'observed_state_writer_functions':8,
             'receive_state_contracts':3,'new_reviewed_receive_families':['36','da'],
             'new_4a_early_return_masks':['02','04','08'],'formal_owner_alias_recovered':True,
             'new_opcode_values':0,'new_complete_routes':0,'whole_game_route_total':None,
             'next':['Trace53_6CF0 render-resource bindings to identify feature without guessing.',
                     'Determine server causality ofC2S6D and original authority rules; receive-trigger evidence is insufficient.',
                     'Continue whole-game phase/state/variant inventory beyond these conditional refresh paths.'],
             'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False}
    dump('summary.json',summary);dump('source-manifest.json',manifest.copy())
    print(json.dumps({'out':str(out),**summary}))


if __name__=='__main__':main()
