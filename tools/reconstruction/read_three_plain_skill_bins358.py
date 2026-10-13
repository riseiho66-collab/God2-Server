from pathlib import Path
import hashlib,json,struct
from collections import Counter
O=Path(__file__).resolve().parent;S=Path('C:/Users/risei/Desktop/God2/God2-Server');h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
sources=[('tw_original',S/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/client/Data2/Fight/Spg/cbspec2.bin','7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'),('tw_installed',Path('C:/Users/risei/Desktop/God2/God2/Data2/Fight/Spg/cbspec2.bin'),'3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7'),('cn_original',Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Fight/Spg/cbspec2.bin'),'857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004')]
refs=[];records={}
for label,p,pin in sources:
 b=p.read_bytes();assert len(b)==112660 and h(b)==pin and b[:4]==b'1.03';counts=[struct.unpack_from('<I',b,4+k*0x6e04)[0] for k in range(4)];rows={}
 for kind,count in enumerate(counts):
  assert 0<=count<=255
  for ident in range(1,count+1):
   off=8+kind*0x6e04+(ident-1)*110;r=b[off:off+110];assert len(r)==110 and r[:2]==bytes([ident,kind]);rows[(kind,ident)]=dict(kind=kind,id=ident,offset=off,bytes=110,sha256=h(r),raw_hex=r.hex())
 records[label]=rows;put('raw/'+label+'/cbspec2.bin',b);refs.append(dict(label=label,actual_path=p.as_posix(),retained='raw/'+label+'/cbspec2.bin',bytes=len(b),sha256=h(b),counts=counts,declared_records=len(rows),scope='original pinned' if label!='tw_installed' else 'installed owner-modified separate source'))
 out('records/'+label+'.json',list(rows.values()))
out('source-references.json',refs);pairs=[]
for a,b in [('tw_original','cn_original'),('tw_installed','cn_original'),('tw_original','tw_installed')]:
 keys=set(records[a])&set(records[b]);freq=Counter();rows=[]
 for key in sorted(keys):
  ra=bytes.fromhex(records[a][key]['raw_hex']);rb=bytes.fromhex(records[b][key]['raw_hex']);diff=[i for i in range(110) if ra[i]!=rb[i]];freq.update(diff)
  rows.append(dict(kind=key[0],id=key[1],different_offsets=diff,identical_full110=not diff,bytes_2_through_65_equal=ra[2:66]==rb[2:66],bytes_66_through_109_equal=ra[66:]==rb[66:],word42_equal=ra[0x42:0x44]==rb[0x42:0x44]))
 name=a+'--'+b;out('comparisons/'+name+'.json',rows)
 pairs.append(dict(left=a,right=b,shared_keys=len(keys),union_keys=len(set(records[a])|set(records[b])),left_only=[list(k) for k in sorted(set(records[a])-set(records[b]))],right_only=[list(k) for k in sorted(set(records[b])-set(records[a]))],full110_equal=sum(r['identical_full110'] for r in rows),raw_region_2_to65_equal=sum(r['bytes_2_through_65_equal'] for r in rows),raw_region_66_to109_equal=sum(r['bytes_66_through_109_equal'] for r in rows),word42_equal=sum(r['word42_equal'] for r in rows),offset_difference_frequency={str(k):v for k,v in sorted(freq.items())},scope='raw physical bytes only; text fields/numeric semantics/formula equality not assumed'))
out('tri-comparison-summary.json',pairs)
print(json.dumps(dict(sources=refs,comparisons=[{k:v for k,v in r.items() if k!='offset_difference_frequency'} for r in pairs]),ensure_ascii=False))
