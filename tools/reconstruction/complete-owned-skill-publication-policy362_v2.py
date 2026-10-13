from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-owned-skill-bootstrap-write-362';sha=lambda b:hashlib.sha256(b).hexdigest()
expected=[('src/core/Application.cpp',735180,'da82cc321fe4888ebbdf816e281f57251916adc2f8b94715b55e98fbc3d7e985'),('src/handlers/RecoveredBattleService.h',9053,'6b72768cb05b77c8c064f17d814dec62650bc226db9ad668144f29d58d637fc5'),('src/handlers/RecoveredBattleService.cpp',48477,'5a19c0bd5398e08817e69601e3ac9e39cb96e57cc9d4ba7519055a0a4834d87c')]
pins=[]
for p,n,h in expected:
 b=(S/p).read_bytes();assert len(b)==n and sha(b)==h;pins.append(dict(path=p,bytes=n,sha256=h))
assert len(json.loads((S/'docs/custom-designs.json').read_bytes())['designs'])==138
assert (S/'AGENTS.md').read_bytes().startswith((D/'before'/'AGENTS.md').read_bytes())
doc=S/'docs/research/common-owned-skill-bootstrap-20261013.md';text=doc.read_text(encoding='utf-8');oldtext='controlled actor, bound policy keys and response identity checked around the\nsaved-state observer.';newtext='controlled actor, bound policy keys and response identity checked around the\nsaved-state observer. The original observation tuple is fenced immediately\nbefore the existing `set_state(InBattle)`, then only that transition actual\nresult epoch is retained for capture/bind/final checks. It is independent of\ncosmetic pose state; no generation increment or observer rebase is assumed.';assert text.count(oldtext)==1;doc.write_bytes(text.replace(oldtext,newtext).encode())
with (D/'final-Cplusplus-source-pins.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(pins,f,indent=2);f.write('\n')
with (D/'policy-custody.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(dict(custom_designs_before=137,custom_designs_after=138,new_id='CUSTOM-0140',prior_design_records_preserved=True,agents_old_prefix_exact=True,agents_append_bytes=len((S/'AGENTS.md').read_bytes())-len((D/'before'/'AGENTS.md').read_bytes())),f,indent=2);f.write('\n')
print(json.dumps(dict(final_sources=len(pins),source_bytes=sum(x['bytes'] for x in pins),custom_designs=138,new_id='CUSTOM-0140',source_only=True)))
