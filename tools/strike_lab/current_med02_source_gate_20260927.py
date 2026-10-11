"""Complete current MED02 text-declaration fingerprint, no supply rules."""
import argparse,hashlib,json,struct
from pathlib import Path
from . import import_native_med02_recovery as native
from .recover_items import build_items

ROOT=Path(__file__).resolve().parents[2]
CATALOG_SHA='ebb3882ce833ac8bd45f5b6c341a67ff17039ea3fd30ab31a715d2d6985c4d9b'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def fingerprint(rows):
    digest=hashlib.sha256()
    for row in rows:
        for value in row:
            raw=value if isinstance(value,bytes) else str(value).encode('ascii')
            digest.update(struct.pack('<I',len(raw)));digest.update(raw)
    return digest.hexdigest()
def audit(client):
    require(sha((client/'God2.exe').read_bytes())==CLIENT_SHA,'Current client changed')
    rows=native.pinned_rows(client)
    require(fingerprint([native.SOURCE_ROW,*rows])==CATALOG_SHA,'Complete source catalog changed')
    catalog=build_items(client)
    all_rows=[r for r in catalog['records'] if r['section']=='MED02']
    require(len(all_rows)==100,'Full native MED02 count changed')
    selected={r[3] for r in rows}
    groups=[[list(native.SOURCE_ROW)],[[v.hex() if isinstance(v,bytes) else v for v in row] for row in rows]]
    return {'schema':'god2-current-med02-source-gate-v1','client_sha256':CLIENT_SHA,
        'catalog_sha256':CATALOG_SHA,'source_rows':100,'eligible_text_declarations':71,
        'eligible_ids':sorted(selected),'unmatched_ids':[r['client_item_id'] for r in all_rows if r['client_item_id'] not in selected],
        'authority':'NATIVE_CLIENT_TEXT','gameplay_rules_verified':False,
        'fingerprint_encoding':'source9 then71 rows11 in source_record_index order; each value LEu32 byte length then bytes; numbers decimal ASCII; raw/tooltip exact CP950',
        'groups':groups,'boundary':[{'item_id':r['client_item_id'],'source_record_index':r['source_record_index'],
            'source_line':r['source_line'],'tooltip_hex':r['raw_fields_hex'][8],
            'flags':r['client_flags'],'fixed_amount_text_eligible':r['client_item_id'] in selected} for r in all_rows]}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--client',type=Path,default=ROOT.parent/'God2');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();require(not a.output.resolve().is_relative_to(a.client.resolve()),'Refuse client-tree output')
    result=audit(a.client);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','catalog_sha256':CATALOG_SHA,'cache_sha256':sha(a.output.read_bytes())}))
if __name__=='__main__':main()
