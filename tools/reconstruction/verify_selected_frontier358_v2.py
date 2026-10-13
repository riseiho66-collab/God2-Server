from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;A=O.parent;h=lambda b:hashlib.sha256(b).hexdigest()
def out(n,v):
 p=O/n
 b=(json.dumps(v,indent=2)+'\n').encode()
 if p.exists():assert p.read_bytes()==b;return
 with p.open('xb') as f:f.write(b)
rows=[]
for name,dig,count,total in [('round355-native-canonical-writer-source','ec5b6b0267ca992595de5c22c7433fcd279d823a0081f2c7adaf50e48a970b82',70,77600),('round356-native-movement-ack-source','d7245c2f401ace0bf901230dbf5ec5755bed6c7ca873703d1eb6c5dbde50eeed',54,92377)]:
 root=A/name;sb=(root/'seal.json').read_bytes();assert h(sb)==dig;z=json.loads(sb);seen=set()
 for m in z['members']:
  rel=m.get('path') or m.get('name');p=root/rel;assert p.resolve().is_relative_to(root.resolve()) and rel not in seen;seen.add(rel);b=p.read_bytes();assert type(m['bytes']) is int and len(b)==m['bytes'] and h(b)==m['sha256']
 assert len(z['members'])==count and sum(m['bytes'] for m in z['members'])==total
 rows.append(dict(root=root.as_posix(),seal_sha256=dig,members=count,member_bytes=total,individual_members=z['members']))
out('prior355-356-extra-individual-verification.json',rows)
indices=[]
for root,rel,kind in [(A/'round353-native-item-computed-writer-source','qualified-spans.json','353'),(A/'round355-native-canonical-writer-source','qualified/qualified-spans.json','355'),(A/'round356-native-movement-ack-source','qualified/qualified-spans.json','356')]:
 obj=json.loads((root/rel).read_bytes());spans=obj['code'] if isinstance(obj,dict) and 'code' in obj else obj
 if isinstance(spans,dict):spans=[spans]
 for s in spans:
  start=s.get('start_va') or s.get('begin') or s.get('start')
  end=s.get('end_exclusive_va') or s.get('end_exclusive') or s.get('end')
  if start and end:
   lo=int(start,16);hi=int(end,16);overlap=max(0,min(hi,0x49e19d)-max(lo,0x49e0c0));assert overlap==0
   indices.append(dict(package=kind,name=s.get('name',start),start=start,end=end,overlap_newbody_bytes=overlap))
out('selected-qualified-frontier-overlap-proof.json',dict(inspected_existing_spans=indices,newbody='0049E0C0..0049E19D',new_code_bytes=221,overlap_existing_qualified_bytes=0,scope='selected353/355/356 qualified spans only;357 no qualifiedwhole; no global corpus novelty claim',coverage_method_credit=1,canonical_material_credit=0,grant_authority_credit=0,new_opcode_format_route_credit=0))
print(json.dumps(dict(extra_members=124,extra_bytes=169977,all_prior_members=200,all_prior_bytes=449227,selected_existing_ranges=len(indices),newbody_nonoverlap=221)))
