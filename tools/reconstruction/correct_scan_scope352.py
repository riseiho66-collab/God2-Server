"""Additive PE/mapped extent correction; prior discovery outputs stay unchanged."""
from pathlib import Path
import hashlib,json,struct
import pefile
O=Path(__file__).resolve().parent
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert hashlib.sha256(m).hexdigest()=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert hashlib.sha256(r).hexdigest()=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);sections=[]
for s in pe.sections:
    lo=s.VirtualAddress;hi=lo+s.SizeOfRawData
    tail_start=max(lo,len(m));tail=max(0,hi-tail_start)
    item=dict(name=s.Name.rstrip(b'\0').decode(),rva=lo,raw_size=s.SizeOfRawData,mapped_scan_start=min(lo,len(m)),mapped_scan_end=min(hi,len(m)),original_raw_offset=s.PointerToRawData,omitted_mapped_tail_bytes=tail,execute_flag=bool(s.Characteristics&0x20000000))
    hits=[]
    if tail:
        blob=r[s.PointerToRawData+tail_start-lo:s.PointerToRawData+s.SizeOfRawData]
        for value in range(0x8560c,0x8560c+1200):
            n=struct.pack('<I',value);at=blob.find(n)
            while at>=0:
                hits.append(dict(original_raw_offset=s.PointerToRawData+tail_start-lo+at,nominal_va=hex(0x400000+tail_start+at),literal=hex(value),qualification='originalPE raw tail only; no mapped bytes/equality/code claim'))
                at=blob.find(n,at+1)
    item['raw_tail_literal_hits']=hits;sections.append(item)
out=dict(correction='Original ALL physical-backed wording means mapped intersection only. Original .imprec physical raw bytes do not exist in pinned mapped file. Retained early wording is superseded additively, not rewritten.',sections=sections,omitted_mapped_tail_bytes=sum(x['omitted_mapped_tail_bytes'] for x in sections),raw_tail_hit_count=sum(len(x['raw_tail_literal_hits']) for x in sections),limits='No global absence. Raw scan excludes computed bias/aliases, unknown object identities, implicit bulk destination derivations and indirect/dynamic targets.')
p=O/'scan-scope-correction.json'
if p.exists():raise RuntimeError('preserve')
p.write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps(dict(omitted_mapped_tail_bytes=out['omitted_mapped_tail_bytes'],raw_tail_hit_count=out['raw_tail_hit_count'])))
