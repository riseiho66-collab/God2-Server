from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
texts=json.loads((O/'candidate-literal-text-views.json').read_bytes());proof=json.loads((O/'installed-custom-augmentation-byte-proof.json').read_bytes());pairs=json.loads((O/'nine-selected-difference-and-extra-keys.json').read_bytes());refs=json.loads((O/'text-and-consumer-source-references.json').read_bytes())
for r in refs:
 b=(O/r['retained']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'] and b==Path(r['actual_path']).read_bytes()
assert proof['custom126']['raw_matches_current_owner_recipe'] and len(proof['reserved'])==4
result=dict(status='source/byte proof completed; original helper console cp950 encoding failure preserved',strict_text_errors=sum(bool(v[k]['strict_decode_error']) for v in texts for k in ['name_candidate','short_text_candidate']),reserved4_match=True,custom126_match=True,three_original_numeric_differences=[dict(kind=r['kind'],id=r['id'],versions={v:None if x is None else {k:x[k] for k in ['name','short_text','W3E','W40','W42','B44','B45','W46','W48','W4A','tail66to6D_hex']} for v,x in r['versions'].items()}) for r in pairs[:3]])
with (O/'text-custom-proof-readback.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(result,ensure_ascii=True))
