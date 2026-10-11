"""Pinned03 table/caller reads and terminal-write source snapshots, PHASE1 only."""
import csv
import hashlib
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView

NAME='cn-world-close-drain-01'
ROUND='20261007-cn-world-close-drain'
FUNCTIONS=('00567b50','0047d8d0','00480b10','0048fcc0','0048aa10',
           '0047d2e0','0047c5e0','004ac020')
SOURCE=('src/cn/protocol/CnPreWorldCloseReply.h','src/cn/protocol/CnPreWorldCloseControl.h',
        'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
        'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
        'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
        'tools/reconstruction/cn_world_close_drain_delivery.py',
        'docs/research/cn-world-close-drain-20261007.md')

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve sealed deliveries')
    image=CN.parent/'XJZ-CN/God2_opt.exe';raw=image.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as f:
        rows={r['address'].lower():r for r in csv.DictReader(f,delimiter='\t')}
    files=[];functions=[]
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,indent=2)+'\n').encode())
    for entry in FUNCTIONS:
        row=rows[entry];address=int(entry,16);size=int(row['bytes']);code=view.read(address-image_base,size)
        save('native/'+entry+'.bin',code,str(image)+':VA'+entry)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),str(RECOVERY/row['file']))
        save('native/'+entry+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
             for i in md.disasm(code,address))+'\n').encode())
        functions.append({'entry':entry,'metadata_bytes':size,
                          'method':'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_GLOBAL_CFG_CLOSURE'})
    branches=[]
    for name,slot,length in [('length03',0x567cb0,7),('world03',0x4929e4,22)]:
        cell=view.read(slot-image_base,4);target=struct.unpack('<I',cell)[0]
        code=view.read(target-image_base,length)
        save('native/'+name+'-slot.bin',cell,str(image)+f':VA{slot:08x}')
        save('native/'+name+'-branch.bin',code,str(image)+f':VA{target:08x}')
        branches.append({'name':name,'index':3,'slot':f'{slot:08x}','target':f'{target:08x}',
            'instructions':[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operand':i.op_str}
                            for i in md.disasm(code,target)]})
    save('native/world03-return8-caller.bin',view.read(0x48b177-image_base,0x48b1a9-0x48b177))
    dump('native03-primary-branches.json',branches)
    refs=['cn-delete-completion-lifecycle-01/native-delete-lifecycle.json',
          'cn-character-delete-identity-01/findings.json',
          'cn-login-queue-admission-01/delivery.json']
    for rel in refs:save('retained-provenance/'+rel,(base/rel).read_bytes(),str(base/rel))
    for rel in SOURCE:save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    findings={'round':ROUND,'native_sha256':PIN,'functions':functions,
        'previous_goal_turn_classification':'progress: added current native19 offered/common identity resolver and selection owner source entry',
        'native03_logical_size':3,'native03_payload_bytes_semantics_known':False,
        'close_waiter_local_return':0,'world_dispatch_local_return_before_cookie':8,
        'world_return8_caller':'0048B185..0048B1A4 ->004AC020 then EAX1/exit',
        'new_terminal_write_source_chain':1,'new_read_only_reply_views':1,
        'new_exact_world_ticket_current_query':1,
        'native03_values_supplied_or_generated':False,
        'actual_0200_0204_ingress_connected':False,'native_phase_source_bindings_added':0,
        'source_owner_chains_added':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'remaining':['Actual pre-world operation/phase owner and0200/0204 ingress plus complete source-issued03 bytes are missing; drain helper is not a hosted close route.',
          'Native19 rule/atomic common deletion/save CAS/duplicate owner/pending-offer invalidation and actual02/1E suppliers remain open.',
          'Native03 payload issuance, other caller/state variants and1E exception continuation remain unresolved; do not zero-fill or extrapolate all world03 uses.',
          'Native login/world/bootstrap/create issuers, full gameplay composition/hosting and whole-game directional/phase/state/variant denominator remain open.'],
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False,
        'whole_game_completion_percent':None,'levels_changed':False}
    dump('findings.json',findings)
    dump('native-source-manifest.json',{'files':files,'native_sha256':PIN})
    print(json.dumps({'round':ROUND,'native_function_spans':len(functions),
        'native03_logical_size':3,'terminal_write_source_chain_added':1,
        'actual_native_close_ingress_added':0,'new_complete_bidirectional_routes':0}))

if __name__=='__main__':main()
