from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
report='''PASS for bounded static custody/non-qualification357; genuine canonical
row8560D..F/full25/native1215 material source remains OPEN.

No server tracked source change. PHASE1 bytes/manual PE/Capstone only; no native,
CRT/API/VM/emulator/parser/codec/SQL/compiler/build/test/product function executed.
Mapped149c and physicalPE5fcf inputs are hashed in place, never copied wholesale.
Every cut/window below equals both image inputs; no program observation is made.

Prior355 native70/77600B and356 native54/92377B were individually verified with
containment, integer byte lengths/count/sums and hashes:124/169977B unchanged.
Additional35250/153368B and34827/84522B source packages were likewise verified
in place. Total201/407867B. Their known whole bodies, reset/getters, packet5D,
3B/41, auxiliary banks and savedUI routines are referenced, not recaptured or
recredited. Prior49D2E0 resets supplied-object85AC0 savedUI, not8560D..F.

Closest retained literal alias leads are32 historical352 LEA candidates whose
fixed displacement is8560C. Those historical entries themselves are unaligned
raw discovery, not authentic xrefs. This review selected seven finite windows
(1264B) from that existing set/materialization vicinity; arbitrary decoding has
353 sites but ZERO qualified sites. Several windows start inside instructions
and their first bytes can decode incorrectly. No nearest padding is promoted to
an authentic entry, and no arbitrary window is a complete native method.

Raw47D512 vicinity suggests canonical row count/key selection, followed by slot/
count operands and supplied object to quantity/action children. It does not show
that a canonical prefix destination is forwarded. Raw49F905 vicinity shows five
DWORDs from canonical row+4 to savedUI85AD4: OUTWARD full20, with separate savedUI
fields. It is not a reverse full24 or original full25 population supplier.
Raw49C399,49D402,4CA367 and49F9FA materialize a row pointer and pass it to the
already qualified49B850; some raw windows suggest only row count/lowkey stores.
49D370/4CA2xx apparent routines are deliberately NOT closed as new reset/count
body coverage: no new qualifying prefix flow was demonstrated to warrant it.
Raw4994C7 keeps canonical-base alias in a stack cell amid UI construction; the
selected window does not establish a child destination. None of these raw
interpretations is a complete caller/phase/owner/wire proof or global absence.

Known authentic348 full49B850656B/224sites is referenced IN PLACE and rechecked
against both current images. The real3B caller supplies a canonical row pointer,
but the known callee reads it and supplies keys, own-stack output addresses or
UI/control arguments downstream. There is no newly demonstrated canonical row
WRITE destination forwarded to a new authentic direct child. Expanding opaque
UI/render children solely because the screen changes would not qualify material.
No duplicate full49B850 or353/354/355 body capture was made.

New authentic whole bodies/code/data/sites all ZERO. Discovery7windows1264B and
353 arbitrary decoded sites are recorded separately and receive no method,
opcode, format, authoritative source or full-route credit. Computed/indirect/
bulk destinations, other object origins and original.imprec tail remain outside
this finite review; all seven PE EXECUTE flags clear do not mean no native code.
No global writer-absence or zero-prefix initialization/entitlement is asserted.

A real next qualification still needs demonstrated INWARD full24 destination or
specific stores to canonical row+1..3, an authentic caller/object and true input
phase/wire lineage. Independent common instance/definition/original acquisition,
server issuer/rights, full25/full1215/freshfull50 acceptance do not follow from
client savedUI, offer banks, display helpers or a server fixture. No inferred
prefix, default fill, fake material factory or arbitrary UI forest was added.

Three static discovery/proof helpers and this seal helper each succeed once.
Initial read-only rg wildcard/nonexistent guessed prior child filename failures
are narrow console reads only, no helper/product failure or source mutation.
Successful previous helpers were not rerun; no prior sealed artifact was changed.
Owner stop instruction is retained: complete357 native and later root-staged
canonical review only, then stop; no358 or scope extension begins here.
'''
put('REPORT.md',report.encode())
metadata=[]
for n in ['inspect_existing_row_lineage357.py','inspect_finite_followup357.py','close_finite_source_scope357.py','seal_finite_source357.py']:
 b=(O/n).read_bytes();assert b'\r' not in b
 metadata.append(dict(path=n,bytes=len(b),sha256=h(b),successful_execution_count=1))
out('successful-LF-helper-metadata.json',metadata)
rows=[]
for p in sorted(O.rglob('*')):
 if not p.is_file():continue
 assert p.resolve().is_relative_to(O.resolve()) and p!=O/'seal.json'
 b=p.read_bytes();rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=h(b)))
seal=dict(verdict='PASS bounded static custody; material source unqualified',member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),members=rows,excludes='seal.json',native_methods_credited=0,qualified_new_code_bytes=0,data_bytes=0,new_qualified_sites=0,discovery_windows=7,discovery_bytes=1264)
out('seal.json',seal)
for r in rows:
 b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
print(json.dumps(dict(seal_sha256=h((O/'seal.json').read_bytes()),seal_bytes=(O/'seal.json').stat().st_size,members=len(rows),member_bytes=seal['member_bytes'],report_sha256=h((O/'REPORT.md').read_bytes()),report_bytes=(O/'REPORT.md').stat().st_size,qualified_code=0,qualified_sites=0,data=0,discovery=1264)))
