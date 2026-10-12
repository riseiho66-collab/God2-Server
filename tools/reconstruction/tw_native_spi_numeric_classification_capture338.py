"""Seal bounded338 classification source only; no target/parser/codec/DB execution."""
from pathlib import Path
import csv,json,hashlib,struct
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
IM=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(rel,b):
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(b)
def dump(rel,v):write(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
m=(IM/'native-image.bin').read_bytes();pe=(IM/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(pe)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
sections=json.loads((ROOT/'data-reference-observations.json').read_text())['sections']
def verify(raw,va):
 rva=va-0x400000;ss=[s for s in sections if s['rva']<=rva and rva+len(raw)<=s['rva']+s['raw_bytes']];assert len(ss)==1
 off=ss[0]['raw_offset']+rva-ss[0]['rva'];assert raw==m[rva:rva+len(raw)]==pe[off:off+len(raw)];return off
specs=[('classification-prefix-01','byte-classification-complete',0x550D2E,0x550DA3,[0x550D99,0x550DA2]),('whitespace-predicate-prefix-02','whitespace-predicate-complete',0x5484AF,0x5484D7,[0x5484C5,0x5484D6]),('locale-writer-prefix-03','ctype-publication-body-complete',0x553BB3,0x553DF8,[0x553DF7])]
cuts=[]
for prefix,name,start,end,returns in specs:
 source=list(csv.DictReader((ROOT/'native'/f'{prefix}.tsv').read_text().splitlines(),delimiter='\t'))
 selected=[r for r in source if start<=int(r['va'],16)<end]
 at=start;raw=b''
 for r in selected:assert int(r['va'],16)==at;b=bytes.fromhex(r['bytes']);at+=len(b);raw+=b
 assert at==end and raw==(ROOT/'native'/f'{prefix}.bin').read_bytes()[:end-start]
 assert all(any(int(r['va'],16)==v and r['mnemonic']=='ret' for r in selected)for v in returns)
 write(f'native/{name}.bin',raw)
 text='va\tbytes\tmnemonic\toperands\n'+''.join('\t'.join(r[k]for k in ['va','bytes','mnemonic','operands'])+'\n'for r in selected)
 write(f'native/{name}.tsv',text.encode())
 cuts.append(dict(name=name,span_start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=verify(raw,start),pe_equal=True,mapped_equal=True,tsv_equal=True,returns=[f'{v:08X}'for v in returns],scope='Complete direct body only; ctype-publication parent invocation/startup/authority not qualified' if start==0x553BB3 else 'Actual classification call target body; finite ASCII/EOF direct table branch qualified'))
dump('native/cuts.json',cuts)
refs=[]
def retain(p,rel,kind):
 b=p.read_bytes();write(rel,b);refs.append(dict(actual_path=p.as_posix(),retained=rel,bytes=len(b),sha256=sha(b),scope=kind));return b
prior=BASE/'round337-spi-numeric-conversion-review';ps=(prior/'seal.json').read_bytes();assert sha(ps)=='27e7b1b5c8da0458ae7966601bdb8078724515fe2dba88c83ec4ed1cf46b0cad';pm=json.loads(ps)
for name in ['native/scanner-direct-body-retained.bin','native/scanner-direct-body-retained.tsv','selected-ascii-lexical-observations.json','REPORT.md','seal.json']:
 b=retain(prior/name,'references/numeric337/'+name,'immutable prior337 selected reference; no duplicate capture or credit')
 if name!='seal.json':entry=next(x for x in pm['members']if x['path']==name);assert len(b)==entry['bytes']and sha(b)==entry['sha256']
inputroot=BASE/'tw-native-spi-numeric-input-source-338';inputseal=(inputroot/'seal.json').read_bytes();assert sha(inputseal)=='fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612'
s=json.loads(inputseal);assert s['member_count']==19 and len(s['members'])==19
n=0
for e in s['members']:
 b=(inputroot/e['path']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256'];n+=len(b)
assert n==105264
for name in ['REPORT.md','seal.json','native/cuts.json','raw-instruction-review.json']:
 p=inputroot/name
 if p.exists():retain(p,'references/input338/'+name,'sealed disjoint input worker evidence; no rerun or duplicate credit')
# Recheck all prior/new selected raw TSV records against both original inputs.
oldbin=(ROOT/'references/numeric337/native/scanner-direct-body-retained.bin').read_bytes();verify(oldbin,0x55027D)
oldrows=list(csv.DictReader((ROOT/'references/numeric337/native/scanner-direct-body-retained.tsv').read_text().splitlines(),delimiter='\t'))
assert b''.join(bytes.fromhex(r['bytes'])for r in oldrows)==oldbin
obs=json.loads((ROOT/'data-reference-observations.json').read_text())
for d in obs['data']:verify((ROOT/'data'/f'{d["label"]}.bin').read_bytes(),int(d['va'],16))
table=(ROOT/'data/initial-ctype-table-with-EOF.bin').read_bytes()
preconditions={'ctype_pointer_effective_during_call':'valid table supporting indices -1..255; values relevant to every read remain stable for entire scanner call','multibyte_value':'No requirement that current5A1D78 equals1: selected input/format bytes andEOF take same low-bit table lookup via direct or550D2E fastpath','required_bits':[dict(input=37,whitespace_mask8=False),dict(input=100,digit_mask4=False),dict(input='ASCII0..9',digit_mask4=True,whitespace_mask8=False),dict(input=-1,digit_mask4=False,whitespace_mask8=False)],'exact_PE_initial_profile':dict(pointer='005A1B76',mb=1,table_start='005A1B74',table_bytes=514,table_sha256=sha(table)),'actual_current_profile_observed':False,'all_runtime_locale_invariance_proved':False,'input_stream_dependency':'Disjoint input338 package fffa554b verifies finite49h string stream/byteinput/EOF branches; no current process invocation observed','numeric_projection_recommendation':'Only conditional selected-source value semantics under explicit stable classification/input assumptions; not general CRT, current native state, full396, owner or gameplay authority'}
dump('finite-classification-preconditions.json',preconditions)
dump('source-references.json',refs)
dump('static-validation.json',dict(images=[dict(actual_path=(IM/name).as_posix(),bytes=len(b),sha256=sha(b),copied=False)for name,b in [('native-image.bin',m),('originalPE.bin',pe)]],complete_direct_bodies=len(cuts),complete_direct_body_bytes=sum(c['bytes']for c in cuts),initial_data_bytes=sum(d['bytes']for d in obs['data']),input_worker_seal_sha256=sha(inputseal),input_worker_members=19,input_worker_bytes=n,input_worker_all_members_verified=True,actual_parent_invocations_proved=False,all_current_locale_values_qualified=False,source_repository_edits=0,native_resource_parser_codec_DB_build_test_execution=False))
write('failed-adaptive-query-note.txt',b'One read-only python -c address-reference query contained a literal backslash-n and stopped with SyntaxError before executing its body. No repository or evidence file changed. That optional caller expansion was abandoned; source statements remain bounded to retained complete direct body, without parent-invocation credit.\n')
report='''# Round338 bounded SPI numeric classification source

The finite ASCII/EOF classification child is qualified under an explicit valid/stable current-table precondition. The original PE initial table satisfies the required bits; current locale/table values are not observed or invariant. This package does not qualify general CRT semantics, a current numeric result, full396, resource bank, owned population, issuer or gameplay authority.

## Prior evidence and bounded capture

Read prior337 complete scanner direct-body records before new cuts. Reused sealed337 scanner and exact finite ASCII source observations without duplicate capture/credit. Three bounded discovery prefixes are retained with raw tails/arbitrary after-body bytes and their limited-scope metadata. Exact instruction-complete direct bodies are separately retained:550D2E..550DA2=117B,5484AF..5484D6=40B,553BB3..553DF7=581B (total738B). First two entries are actual scanner/input directCALL targets.553BB3 has a retained prologue/all paths through RET and actual global publication stores; its startup/parent invocation is not qualified or counted. Full prefix after-body methods are not credited. All selected body/TSV and518B initial data agree with actual PE section-mapped bytes and mapped149c. Images were hashed/read in place and not copied.

## Actual finite classification flow

550D2E forms32-bit(input+1), compares it UNSIGNED against100h and branchesJA to the multibyte/API path only outside -1..255. For ASCII0..255 orEOF-1 it reads WORD[currentDWORD5A1B6C+2*input], zero-extends it, ANDs formal maskDWORD and returns at550DA2.550D8C->55293E is therefore not taken for these finite values. It does not matter whether global5A1D78 currently selects the scanner's direct-byte path or550D2E: selected masks4/8 are the same low table bits.

5484AF compares5A1D78 signed<=1, then either direct lowBYTE table lookup&8 or CALL550D2E(input,8). Both paths return the same bit8 for the selected bounded inputs, conditional on a valid table. Scanner format'%' initial whitespace classification requires bit8 clear; format'd' must have digitbit4 clear so it is a specifier rather than a width digit. Nonempty source digits0..9 require bit8 clear for initial whitespace handling and bit4 set throughout accumulation. EOF-1 must have bit4/8 clear. Signed-char/general nonASCII, other formats, widths, malformed strings and other locale semantics are outside scope.

## Static initial data and actual mutability

OriginalPE/mapped DWORD5A1B6C=5A1B76, DWORD5A1D78=1. Retained514B table begins5A1B74, covering signed index-1 plus0..255. EOFWORD0000; digits0..9 allWORD0084 (bit4 set/bit8 clear); '%'WORD0010 and'd'WORD0082 (required bits clear). NULWORD0020; standard whitespace9/10/13 WORD0028 and spaceWORD0048 are data observations, not a general character-class specification. These are file initial values only.

Exact global-address octet scanning across actual physical PE sections records52 pointer and44 mode address-reference candidates. Raw references/preceding opcodes alone are not valid instruction or indirect-writer inventory. Selected writer discovery yields the complete553BB3 direct body.553C6B calls opaque[5702CC], receives a structure and rejects size>2;553C8A stores zeroextendedWORD result as mode5A1D78 before later table generation succeeds.553CCA calls opaque55293E to populate dynamically allocated classifier data;553CDD zeroes its EOFWORD.553D3A may write WORD8000 for opaque lead-byte ranges.553D5C publishes allocation+2 to5A1B6C. The distinct branch553DC0..553DF7 publishes initial5A1B76 at553DCB. Other allocation/conversion/free children are retained as opaque calls. Thus there is actual source capable of mutating both globals, and no source proof here that every generated/current table preserves ASCII bits. A lone mode==1 observation would not prove initial table identity or startup history.

## Implementation-ready condition and remaining gap

finite-classification-preconditions.json names the exact required bits and valid-table lifetime/stability across all reads.5A1D78 need not equal1: for these finite values either source branch returns the same selected table bits. The precondition may be established by a separately qualified table profile/initialization lifetime, or actual correct relevant table data; this package does not establish that a running client meets it. Do not invent a native current-locale observation or treat initial PE values as present state. The next remaining classification boundary is actual initialization/callside lifetime/concurrency or ASCII invariance of the generated table's opaqueAPI source, not a full CRT/general-language audit.

The disjoint input338 package fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612 is member-verified19/105264B and referenced without rerun. It qualifies finite49h string stream/EOF direct branches subject to the current classifier condition. Finite successful EOF scanner return follows550C31→550C37→550C89→550C8E→550C9D after matchcount1, rather than only550C9A. Prior337 sealed report's550C9A statement is a conditional return branch, not a finite successful-path claim; it stays immutable. Original451BA0 initializedlocal0/return==1 gate remains unchanged. Combined finite conditions permit exact digit arithmetic reasoning for the pinned positive<=58025 tokens/0..1 flags but do not supply unqualified current-native output or a new authority API.

No repository edit, native/VM/parser/resource/packetcodec execution/import, SQL/DB/build/compiler/tests/runtime or deployment occurred. Own Python scripts only read/hash/disassemble target bytes and do artifact bookkeeping. One optional read-only caller query stopped with a literal-newline SyntaxError; no evidence/source changed, and no caller credit was inferred. Full routes/new opcode/complete gameplay credit0. Stop after this bounded delivery.
'''
# Derive octet-hit counts directly; do not trust handwritten totals.
counts={k:len(v)for k,v in obs['address_reference_byte_hits'].items()}
report=report.replace('records52 pointer and44 mode address-reference candidates',f'records{counts["005A1B6C"]} pointer and{counts["005A1D78"]} mode address-reference candidates')
write('REPORT.md',report.encode())
files=sorted(p for p in ROOT.rglob('*')if p.is_file());members=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in files]
dump('seal.json',dict(format='god2-static-source-seal-v1',member_count=len(members),total_member_bytes=sum(x['bytes']for x in members),members=members,excludes_seal_itself=True,scope='Bounded finite classification source; current locale/profile not qualified; no gameplay credit'))
print(json.dumps(dict(member_count=len(members),total_member_bytes=sum(x['bytes']for x in members),seal_sha256=sha((ROOT/'seal.json').read_bytes()),report_sha256=sha((ROOT/'REPORT.md').read_bytes()),body_bytes=sum(c['bytes']for c in cuts),initial_data_bytes=sum(d['bytes']for d in obs['data']),candidate_counts=counts)))
