"""Bounded static constant-materialization/indirect-reference closure for CN.

No native execution. Candidate transfers never establish a selector/owner/phase.
"""
import csv
import io
import json
from collections import Counter
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_REG, X86_OP_IMM, X86_OP_MEM
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-computed-receiver-references-01'
ROUND='20261007-cn-computed-receiver-references'
TARGETS={'0047de70':(0x47de70,0x47e05a),'004812b0':(0x4812b0,0x48138e)}
SOURCES=['tools/reconstruction/cn_computed_receiver_references.py',
    'docs/research/cn-computed-receiver-references-20261007.md']
FULL={'eax','ebx','ecx','edx','esi','edi','ebp','esp'}
MASK=0xffffffff

def canonical(name):
    for root,aliases in {'eax':{'ax','al','ah'},'ebx':{'bx','bl','bh'},'ecx':{'cx','cl','ch'},
        'edx':{'dx','dl','dh'},'esi':{'si'},'edi':{'di'},'ebp':{'bp'},'esp':{'sp'}}.items():
        if name==root or name in aliases:return root
    return name

def scan(pe,rows):
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    counts=Counter();candidates=[];seen=set()
    bounds={}
    for name,(lo,hi) in TARGETS.items():
        bounds[name]={i.address for i in md.disasm(pe.get_data(lo-pe.OPTIONAL_HEADER.ImageBase,hi-lo),lo)}
    def value(op,registers):
        if op.type==X86_OP_IMM:return (op.imm&MASK,[])
        if op.type==X86_OP_REG and op.size==4:return registers.get(md.reg_name(op.reg))
        return None
    def record(owner,ins,result,kind):
        if result is None:return
        address,history=result
        for name,(lo,hi) in TARGETS.items():
            if lo<=address<hi:
                key=(owner,ins.address,address,kind)
                if key in seen:return
                seen.add(key)
                candidates.append({'owner':owner,'site':f'{ins.address:08x}','target':f'{address:08x}',
                    'helper':name,'kind':kind,'target_instruction_boundary':address in bounds[name],
                    'derivation':history,'phase_proven':False,'ecx_owner_proven':False})
    for row in rows:
        if row['status']!='ok':counts['metadata_not_ok']+=1;continue
        size=int(row['bytes']);base=int(row['address'],16)
        if not size:counts['empty_spans']+=1;continue
        if size>1024*1024:counts['over_1mib_span_skipped']+=1;continue
        code=pe.get_data(base-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:counts['incomplete_mapped_span']+=1;continue
        counts['function_spans_scanned']+=1;counts['native_bytes_in_scanned_spans']+=size
        registers={};stack=[];decoded=0
        for ins in md.disasm(code,base):
            decoded+=ins.size;counts['instructions']+=1
            ops=ins.operands;mn=ins.mnemonic;trace={'va':f'{ins.address:08x}','bytes':ins.bytes.hex(),
                'instruction':mn+' '+ins.op_str}
            if mn in ('call','jmp') and ops and ops[0].type==X86_OP_REG:
                counts['register_indirect_transfers']+=1
                result=value(ops[0],registers)
                if result is not None:counts['constant_resolved_register_transfers']+=1
                record(row['address'],ins,result,'register_indirect_transfer')
            if mn.startswith('ret') and stack:
                record(row['address'],ins,stack[-1],'push_constant_ret_candidate')
            # No branch joins/interprocedural execution are inferred. End of
            # basic-block clears symbolic constants and stack, including calls.
            if mn.startswith('j') or mn.startswith('ret') or mn in ('call','loop','loope','loopne','int','int3'):
                registers.clear();stack.clear();continue
            assigned=None;dest=md.reg_name(ops[0].reg) if ops and ops[0].type==X86_OP_REG else None
            if dest in FULL and ops[0].size==4:
                old=registers.get(dest)
                if mn=='mov' and len(ops)==2:assigned=value(ops[1],registers)
                elif mn=='lea' and len(ops)==2 and ops[1].type==X86_OP_MEM:
                    mem=ops[1].mem
                    b=(0,[]) if not mem.base else registers.get(md.reg_name(mem.base))
                    i=(0,[]) if not mem.index else registers.get(md.reg_name(mem.index))
                    if b is not None and i is not None:assigned=((b[0]+i[0]*mem.scale+mem.disp)&MASK,b[1]+i[1])
                elif mn=='xor' and len(ops)==2 and ops[1].type==X86_OP_REG and ops[1].reg==ops[0].reg:
                    assigned=(0,[])
                elif mn in ('add','sub','xor','and','or','shl','sal','shr','rol','ror') and len(ops)==2:
                    right=value(ops[1],registers)
                    if old is not None and right is not None:
                        a,b=old[0],right[0];n=b&31
                        calculated={'add':lambda:a+b,'sub':lambda:a-b,'xor':lambda:a^b,'and':lambda:a&b,
                            'or':lambda:a|b,'shl':lambda:a<<n,'sal':lambda:a<<n,'shr':lambda:a>>n,
                            'rol':lambda:(a<<n)|(a>>(32-n)) if n else a,
                            'ror':lambda:(a>>n)|(a<<(32-n)) if n else a}[mn]()
                        assigned=(calculated&MASK,old[1]+right[1])
                elif mn in ('inc','dec','not','neg') and old is not None:
                    a=old[0];assigned=({'inc':a+1,'dec':a-1,'not':~a,'neg':-a}[mn]&MASK,old[1])
                elif mn=='imul' and len(ops)==3:
                    a,b=value(ops[1],registers),value(ops[2],registers)
                    if a is not None and b is not None:assigned=((a[0]*b[0])&MASK,a[1]+b[1])
                elif mn=='pop' and stack:assigned=stack.pop()
            if mn=='push' and ops:stack.append(value(ops[0],registers));stack=stack[-32:]
            elif mn=='pop' and dest not in FULL:stack.clear()
            # Partial writes and all unmodeled writes invalidate the canonical
            # register. Never treat unknown live/loaded memory as a PE constant.
            _,writes=ins.regs_access()
            for register in writes:
                name=canonical(md.reg_name(register));registers.pop(name,None)
                if name=='esp' and mn not in ('push','pop'):stack.clear()
            if assigned is not None and dest in FULL:
                assigned=(assigned[0],(assigned[1]+[trace])[-32:]);registers[dest]=assigned
                if len(assigned[1])>1:record(row['address'],ins,assigned,'computed_address_materialization')
        counts['decoded_bytes']+=decoded
        if decoded!=size:counts['decode_incomplete_spans']+=1
    return dict(counts),candidates

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve prior computed-reference scan')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Pinned CN native PE changed')
    pe=pefile.PE(data=raw,fast_load=True)
    metadata_path=RECOVERY/'functions.tsv';metadata=metadata_path.read_bytes()
    rows=list(csv.DictReader(io.StringIO(metadata.decode('utf8')),delimiter='\t'))
    counts,candidates=scan(pe,rows)
    evidence_path=ROOT/'cn-receiver-reachability-agent-01/findings.json';earlier=evidence_path.read_bytes()
    expected=ledger['cn_account_admission_evidence'].get('cn-receiver-reachability-agent-01',{})
    if expected and sha(earlier)!=expected['artifact_sha256']['findings.json']:raise ValueError('Prior findings differ')
    snapshots=[]
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,ledger_path);save('prior-reachability-findings.json',earlier,evidence_path)
    save('metadata/functions.tsv',metadata,metadata_path)
    native=[]
    for address,(lo,hi) in TARGETS.items():
        source_path=RECOVERY/'part_0007'/(address+'_FUN_'+address+'.c')
        code=pe.get_data(lo-pe.OPTIONAL_HEADER.ImageBase,hi-lo);source=source_path.read_bytes()
        save('native/'+address+'.bin',code,exe);save('native/'+address+'.c',source,source_path)
        native.append({'address':address,'bytes':len(code),'native_sha256':sha(code),'source_sha256':sha(source)})
    limitations=['Straight-line recovered-function spans only; no CFG joins, interprocedural propagation, memory/encoded pointer tables, relocations/loader mutation or runtime-module closure.',
        'Candidate address/indirect transfers do not prove ECX selector ownership or a live network phase. No candidate and no direct caller does not prove dead code.',
        'All source-hosting/gameplay variants and whole-game directional/state/variant denominator remain open.']
    result={'client_sha256':PIN,'function_metadata_sha256':sha(metadata),'counts':counts,
        'computed_candidates':candidates,'confirmed_additional_phases':0,'unreachable_proven':False,
        'new_complete_routes':0,'limitations':limitations,'build_run':False,'tests_run':False,'runtime_run':False}
    dump(out/'computed-reference-scan.json',result)
    manifest={'kind':'bounded primary native straight-line constant/indirect target recovery for two unresolved receivers',
        'source_paths':SOURCES,'snapshots':snapshots,'native_spans':native,'scan':result,'new_cpp_files':0,
        'new_source_files':0,'new_research_tools':1,'source_owner_chains_added':0,'new_phase_opcode_bindings':0,
        'new_complete_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'previous_goal_turn_classification':'progress: native path completion source and catalog28 sealed',
        'remaining':limitations,'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN two unresolved receivers computed constant/reference frontier',
        'version_scope':'cn','status':'靜態常數傳播/間接跳轉候選追查；未證明額外phase或完整路徑',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':limitations})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Follow actual selector registrations, encoded/memory/loader pointer sources beyond this bounded constant scan; keep both helpers phase-unresolved.']+limitations
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'counts':counts,'computed_candidates':len(candidates),
        'new_confirmed_phases':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
