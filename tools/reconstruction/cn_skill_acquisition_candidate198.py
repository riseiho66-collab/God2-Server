"""Bounded original-file C56/C26 candidate reading; never executes client code."""
from pathlib import Path
import hashlib,json
import pefile,capstone
from .cn_pe_import_directory import FileView
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-skill-acquisition-frontier-01/root-native'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(p,v):save(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def main():
 raw=EXE.read_bytes()
 if sha(raw)!=PIN:raise RuntimeError('Pinned native file differs')
 pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 dump(OUT/'native-origin.json',dict(path=str(EXE),bytes=len(raw),sha256=sha(raw),full_file_hashed=True,full_file_copied=False,scope='Only declared bounded raw windows below are copied/disassembled; full PE identity is not full semantic recovery'))
 definitions=[('part_0010/004b1ca0_FUN_004b1ca0.c',0x4b1ca0,69,'Complete emitter code: raw56 supplied WORD, owner1C9010/11/12 BYTEs and one unwritten body byte; no learning interpretation'),
 ('part_0010/004b0790_FUN_004b0790.c',0x4b0790,117,'Complete emitter code: selected target WORD, owner41AE8/41AEA item/slot in ordinary26 or separateAD12 branch. Supplied WORD is not proven common actor identity'),
 ('part_0008/0048c200_FUN_0048c200.c',0x48c200,138,'Full canonical C retained; only bounded initial owner3/2/param2=-13/-12 actual emitter calls raw code recovered. Later switch/actions are not expanded')]
 originals=[];spans=[];sites=[]
 for i,(relative,va,length,scope) in enumerate(definitions):
  p=RECOVERY/relative;c=p.read_bytes();copy='original-%02d.c'%i;save(OUT/copy,c)
  originals.append(dict(path=str(p),copy=copy,bytes=len(c),sha256=sha(c),semantic_scope=scope))
  rva=va-pe.OPTIONAL_HEADER.ImageBase;offset=pe.get_offset_from_rva(rva);b=view.read(rva,length);name='window-%02d.bin'%i;save(OUT/name,b)
  ins=list(md.disasm(b,va));decoded=sum(x.size for x in ins)
  row=dict(va=f'{va:08X}',rva=rva,file_offset=offset,bytes=len(b),sha256=sha(b),copy=name,scope=scope,linear_decoded_bytes=decoded,remaining_bounded_tail_bytes=len(b)-decoded,linear_disassembly_is_complete_CFG=False)
  spans.append(row)
  current=[dict(span=i,address=f'{x.address:08X}',bytes=x.bytes.hex(),mnemonic=x.mnemonic,operand=x.op_str) for x in ins];sites+=current
  save(OUT/('window-%02d.asm'%i),('\n'.join(f"{x['address']} {x['bytes']} {x['mnemonic']} {x['operand']}" for x in current)+'\n').encode())
 dump(OUT/'original-inputs.json',originals);dump(OUT/'span-manifest.json',spans);dump(OUT/'instruction-sites.json',sites)
 p=ROOT/'artifacts/integration/packet-connections-20261006/endpoint-catalog197/inputs/cn-queue-sites.json';b=p.read_bytes();save(OUT/'retained-queue-sites197.json',b)
 dump(OUT/'retained-queue-origin.json',dict(path=str(p),copy='retained-queue-sites197.json',bytes=len(b),sha256=sha(b)))
 selected=[r for r in json.loads(b) if r['opcode_candidate'] in (0x26,0x56)]
 dump(OUT/'retained-selected-sites.json',selected)
 facts=dict(raw56_body_bytes=6,raw56_logical_bytes=7,raw56_body_fields=[dict(offset=0,width=2,source='supplied WORD'),dict(offset=2,width=1,source='owner+1C9010'),dict(offset=3,width=1,source='owner+1C9011'),dict(offset=4,width=1,source='owner+1C9012'),dict(offset=5,width=1,source='not written by4B1CA0; preserve raw storage')],
  raw56_common_identity_qualified=False,raw56_learning_semantics_qualified=False,raw26_all_TW_semantics_qualified=False,phase_assignment_complete=False,new_opcode_values=0,new_phase_bindings=0,new_complete_gameplay_routes=0,
  canonical_51887D_case21_is_full5188E3_producer=False,root_source_originals=3,raw_window_bytes=sum(r['bytes'] for r in spans),raw_window_count=len(spans),instruction_sites=len(sites),
  recovery_scope='New focused operand/caller qualification of existing census candidates, not unique global native-byte coverage. No full PE copy or runtime recovery.',
  build_test_runtime_native_codec_API_DB_SQL_deploy=False)
 dump(OUT/'findings.json',facts);print(json.dumps(facts))
if __name__=='__main__':main()
