from pathlib import Path
import hashlib,json
import pefile
D=Path(__file__).resolve().parent;P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);strings=[]
for va,expected in [(0x7f5cd8,b'HP %+d'),(0x7f760c,b'%+d'),(0x7f7604,b'%s %+d'),(0x7ee88c,b'')]:
 off=pe.get_offset_from_rva(va-pe.OPTIONAL_HEADER.ImageBase);n=raw[off:off+64].index(0);b=raw[off:off+n+1];assert b==expected+b'\0';rel=f'literals/{va:08x}.bin';put(rel,b);strings.append(dict(va=f'{va:08X}',file_offset=off,bytes=len(b),sha256=sha(b),retained=rel,ASCII_before_NUL=expected.decode('ascii')))
out('native-ASCII-format-literal-proof.json',strings)
report="""# Round360 CN original S83 delta consumer source

PASS for bounded static source closure only. Original God2_opt.exe is hash-referenced in place:47,541,760 bytes, SHA582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8. No full-image copy or independent mapped-memory proof exists. N359 all64 sealed members/186,882 bytes were read and individually verified; its partial664-byte5634E0 prefix is unchanged and equals the beginning of this full cut.

The authentic entry5634E0 has a normal EBP frame and the actual sealed556D40 CALL sites556E92/55707F/55715B. Full own code is5634E0..563C19 exclusive:1,849 bytes/540 aligned sites, all540 reached by the finite branch/table CFG. The sole return563C16 is RET20h. Every direct branch reaches an aligned own instruction; the sole indirect switch563771 has all nine exact DWORD target cells563C1C..563C40 (36 data bytes). Three-byte NOP563C19..1C is excluded code. Next563C40 genuine55/8BEC prologue is retained only as17-byte boundary witness. Extension is1,185 bytes beyond the historical664, not new method/global novelty. Discovery's3,500-byte envelope/linear candidates are explicitly not whole-function proof and include later unrelated code/data.

Actual S83 action type3 and17h (decimal23) share parent target556F7B. Decimal17 goes to the original default5573CE and is not this skill arm. Original sealed54C510→556D40→5634E0 context Q=Main+149DF8 is retained by reference, not relabelled new authority. Whole DWORD upper bits of some side/position arguments remain unqualified; this body narrows formal1/2/3/4 to BYTE. For each actor pointer it enforces side<2,position<14, otherwise producesNULL (diagnostic children may return). First actor A comes from Q+38+24*(14*BYTEformal1+BYTEformal2); second B similarly from formal3/4. Both must exist or own cleanup is taken. A's render WORD1A<1000h, or live Astate3 plus opaque55E390 success, and B's render WORD1A<1000h are necessary. Pointer/frame/lifetime/readability and opaque child-return premises are explicit; no server ownership follows.

Formal5 is read as WORD intoSI at563518. Type3 parent55706D MOVZXbodyWORD8 (logicalWORD9) forwards unchanged bits; its upper16 is unused. Formal6 is a separate WORD at+1Ch used by state5 formatting and is literal0 on the selected type3/17h parent. Formal7/8 are lowBYTE reads at5634F0/+20h and5634FF/+24h. Type3 parent pushes logicalBYTE13 toformal7 andlogicalBYTE14 toformal8. These are raw modifiers, not an inferred success/death/immunity enumeration.

After opaque render/position/buffer children, live BYTE A+1E9 is compared at563686/68F to03h/17h. These selected states enter563A3E. At563A45 native writes rawSI WORD to A+28A+2*BYTE(A+239). There is no index bound here beyond its rawBYTE; valid allocated array/lifetime remains a premise. This body does not add this value to a current-HP field, clampHP, create death, or evaluate a skill damage coefficient. Its own arithmetic changes UI positions; that is separate from health arithmetic. The27 direct memory destinations are retained independently; opaque callees may have unqualified effects.

The selected state3/17h path confirms signed display interpretation: MOVSXSI at563A6C/563A84 for marker8 ranges7..11/12..15 (unsigned BYTE range arithmetic) forwards signed16 to formatting. For marker8 ranges25h..29h or30h..42h, or A resourcekind2, an empty native format is used. Other cases deriveCX from rawSI except second actorB state9 substitutes0/empty. A resourcekind3 passes MOVSXCX at563AF2; otherwise563B26/563B3D passes MOVSXCX. Exact original native strings are 'HP %+d' at7F5CD8, '%+d' at7F760C and '%s %+d' at7F7604, with allNUL bytes retained; native empty7EE88C is separate. Marker8==22h or marker7<=5 selects the HP-labelled format in the ordinary fallback; other markers can select number-only format. This proves low16 signed HP-labelled display input, not complete opaque formatter/runtime output nor signed HP mutation.

Selected direct display/cache writes continue in call order: prior A+2D8+2*BYTE239 handle may be sent to opaque408700 then setFFFF; opaque555D40 AX replaces that WORD; live A+1E9 is copied to A+1EC+BYTE239, then opaque555EC0/5566D0 display paths run. Raw live index/state can be reread after opaque calls and cannot be treated as one immutable snapshot. Formal6/markers are not authoritative damage rules.

Closest genuine continuation remains the already-known parent55709E CALL562510 after5634E0, passing source/markers/action but no direct delta argument. Whether it or another real reader ofA+28A applies currentHP is OPEN; no child was expanded here. Native signed32/64 health accumulation, currentHP clamp/lethality, outcome mapping, actual damage producer, MP debit/learned rights and CN custom126/150 resource/visual adoption remain OPEN. This body does not justify a64-bit extension or TW signed-loss wire equivalence by itself.

Accounting:1 known method fully closed locally; new known/global method credit0, new opcode/format/handler/phase/fullroute0. Complete code1,849 bytes; target-table data36 plus ASCII/NUL data20; boundary-only next-entry17 and padding3 are separate. Native/static helpers only; no client/CRT/API/VM/parser/codec/resource execution, SQL/DB import, build/compiler/tests or canonical source edit. Successful discovery/capture/seal helpers executed once and all output members read back individually. No source wrapper or server policy was added.
"""
put('REPORT.md',report.encode());out('PASS.json',dict(verdict='PASS bounded original native consumer source',code_bytes=1849,sites=540,data_table_bytes=36,ASCII_NUL_bytes=sum(m['bytes'] for m in strings),old_partial_overlap_bytes=664,source_extension_bytes=1185,complete_function_count=1,new_global_method_credit=0,new_route_credit=0,independent_mapped_memory_proof=False,signed_HP_display_low16_proven=True,actual_HP_mutation_or_clamp_proven=False,product_execution=0,tracked_edits=0))
helpers=[]
for name in ['discover_health_consumer360.py','capture_health_consumer360.py','seal_health_consumer360.py']:
 b=(D/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(path=(D/name).as_posix(),bytes=len(b),sha256=sha(b),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers)
assert sha(P.read_bytes())==PIN;assert not(D/'seal.json').exists();members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
for m in members:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
out('seal.json',dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),members=members))
for m in json.loads((D/'seal.json').read_bytes())['members']:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
print(json.dumps(dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),seal_bytes=len((D/'seal.json').read_bytes()),seal_sha256=sha((D/'seal.json').read_bytes()),helpers=helpers)))
