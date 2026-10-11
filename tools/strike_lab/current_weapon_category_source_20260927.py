"""Pinned source declaration audit; no inferred item-to-DA mapping or writes to client."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .current_equipment_20260926 import EquipmentOracle, PIN, require, ROOT
from .omega_assets import decode_csvz

SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
EXPECTED = {
    'WPN': '刀,劍,斧,杖,槍,鞭,弓,飛刀,任務武器,新手包裝備,封測獎勵裝備'.split(','),
    'TWP': '刀,劍,斧,杖,槍,鞭,弓,飛刀,超精粹武器,測試用武器,神裝類,二代裝類'.split(','),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    raw = (ROOT.parent/'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(digest(raw)==SOURCE_SHA, 'Current gamedata source mismatch')
    decoded = decode_csvz(raw)
    require(digest(decoded)==DECODED_SHA, 'Decoded gamedata mismatch')
    rows = [r.rstrip(b'\r') for r in decoded.split(b'\n')]
    require(rows[0]==b'GameData,1,2,38106', 'GameData header changed')
    require(rows[1]==b'RowDesc,1' and rows[2].split(b',')[1].decode('cp950')=='類別代碼',
            'Column1 source declaration changed')
    require(rows[9]==b'ItemType,46', 'ItemType declaration changed')
    def record(index):
        data=rows[index]
        return dict(source_line=index+1, raw_hex=data.hex(), text_cp950=data.decode('cp950'))
    groups=[]
    for family,count,type_line in (('WPN',630,11),('TWP',629,46)):
        declaration=rows[type_line-1].split(b',')
        require(declaration[2].decode()==family, 'Wrong ItemType source row')
        names=[s.decode('cp950') for s in declaration[4:]]
        require(names==EXPECTED[family], 'Source category names changed')
        start=next(i for i,r in enumerate(rows) if r.split(b',')[0]==family.encode())
        require(rows[start]==f'{family},{count}'.encode(), 'Wrong item section count')
        items=[r.split(b',') for r in rows[start+1:start+1+count]]
        require(all(len(f)==32 and f[1].isdigit() and int(f[1])<len(names) for f in items),
                'Item category outside declared label sequence')
        counts=Counter(int(f[1]) for f in items)
        examples=[]
        for code in range(len(names)):
            # Retain every distinct description for special groups; these show
            # classification is not a unique physical weapon/art category.
            candidates=[(start+1+i,f) for i,f in enumerate(items) if int(f[1])==code]
            seen=set()
            for index,f in candidates:
                if f[8] in seen: continue
                seen.add(f[8])
                if code<8 and len(seen)>1: break
                examples.append(dict(code=code, declared_label=names[code], key=int(f[0]),
                                     **record(index)))
        groups.append(dict(family=family, declaration=record(type_line-1),
            category_labels=[dict(code=i,label=name,actual_rows=counts[i]) for i,name in enumerate(names)],
            section=record(start), previous_30_rows=[record(i) for i in range(start-30,start)],
            actual_rows=len(items), examples=examples))
    current=EquipmentOracle()
    image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(digest(image)==IMAGE_SHA,'Current native image mismatch')
    spans=[]
    for a,b in ((0x459150,0x459380),(0x459380,0x459420),(0x459420,0x459960),(0x4599b0,0x459a60)):
        lo,hi=a-0x400000,b-0x400000
        require(current.image[lo:hi]==image[lo:hi],f'Current code span mismatch {a:x}')
        spans.append(dict(start=hex(a),end_exclusive=hex(b),sha256=digest(current.image[lo:hi])))
    return dict(schema='current-weapon-category-source-20260927',
        status='SOURCE_DECLARATION_QUALIFIED_DA_MAPPING_UNRESOLVED',
        client_sha256=PIN,source_sha256=SOURCE_SHA,decoded_sha256=DECODED_SHA,
        native_image_sha256=IMAGE_SHA,source_header=[record(i) for i in range(56)],
        groups=groups,current_code_spans=spans,
        scope='Pinned source labels,1259 category bounds,static build-matched native loader correspondence. No native execution, item-to-DA formula, suffix mapping or graphical acceptance.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS source audit: 1259 rows; WPN11/TWP12 declared labels; DA mapping unresolved; '+str(a.output))


if __name__=='__main__':main()
