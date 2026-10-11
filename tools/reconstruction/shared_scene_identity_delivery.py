"""Recover cross-version scene identity from pinned native resource bytes.

Static extraction and source generation only; no DB/client/server/build/tests.
Map catalogue equality is not geometry, placement or playable-route equality.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from tools.strike_lab.omega_assets import decode_csvz
from .archive_inputs import ArchivedInputs
from .cn_wrapper_route_frontier import ROOT as SERVER,CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='shared-scene-identity-01'
TW_PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
TW_RESOURCE='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CN_RESOURCE='8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a'

def digest(data):return hashlib.sha256(data).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def section(plain):
    lines=plain.splitlines(keepends=True)
    found=[i for i,line in enumerate(lines) if line.startswith(b'Map_City_Coordniate,')]
    if len(found)!=1:raise ValueError('Ambiguous native catalogue')
    start=found[0];count=int(lines[start].strip().split(b',')[1])
    if count!=144 or start+count>=len(lines):raise ValueError('Different native source scope')
    raw=b''.join(lines[start:start+count+1])
    parsed=[]
    for ordinal,line in enumerate(lines[start+1:start+count+1]):
        row=line.rstrip(b'\r\n');fields=row.split(b',')
        if len(fields)<14:raise ValueError('Incomplete native catalogue row')
        # Nativebyte delimiters, not localization or path normalization.
        parsed.append({'ordinal':ordinal,'area':int(fields[3])&0x3f,
            'scene':int(fields[5])&0x3ff,'declared_kind':int(fields[4])&3,
            'mdt_path_bytes':fields[10].hex(),'row_sha256':digest(row)})
    return raw,parsed

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve prior immutable scene identity delivery')
    atlas_path=SERVER/'artifacts/world-atlas/current-maps.json'
    atlas=json.loads(atlas_path.read_text(encoding='utf-8'))
    cn_path=CN/'artifacts/native/20261006-cn-scene-assets-01/scene-catalog.json'
    cn_catalog=json.loads(cn_path.read_text(encoding='utf-8'))
    tw_encoded_relative='artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/gamedata.csvZ'
    tw_encoded_path=SERVER/tw_encoded_relative
    cn_encoded_path=CN.parent/'XJZ-CN/Data2/Patch/Comm/gamedata.csvZ'
    if cn_encoded_path.stat().st_size>4*1024*1024:
        raise ValueError('Encoded analysis bound')
    archive=ArchivedInputs()
    try:tw_encoded=archive.read(tw_encoded_relative,limit=4*1024*1024)
    finally:archive.close()
    encoded=[tw_encoded,cn_encoded_path.read_bytes()]
    if [digest(raw) for raw in encoded]!=[TW_RESOURCE,CN_RESOURCE]:raise ValueError('Native resource pin changed')
    if digest((CN.parent/'XJZ-CN/God2_opt.exe').read_bytes())!=PIN:raise ValueError('Native CN executable pin changed')
    decoder=CN/'tools/reverse/recover_cn_login.py'
    spec=importlib.util.spec_from_file_location('readonly_cn_config_decoder',decoder)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    plain=[decode_csvz(encoded[0],limit=8*1024*1024),module.unpack_config(encoded[1],max_plain_bytes=8*1024*1024)]
    if digest(plain[0])!=atlas['source']['decoded_sha256'] or digest(plain[1])!=cn_catalog['decoded_sha256']:
        raise ValueError('Native decoded resource differs from evidence')
    sections=[section(value) for value in plain]
    tw_rows,cn_rows=sections[0][1],sections[1][1]
    joined=[];keys=set()
    for t,c,a,s in zip(tw_rows,cn_rows,atlas['maps'],cn_catalog['rows'],strict=True):
        if (t['area'],t['scene']) in keys:raise ValueError('Duplicate common catalogue key')
        keys.add((t['area'],t['scene']))
        for field in ['ordinal','area','scene','declared_kind','mdt_path_bytes']:
            if t[field]!=c[field]:raise ValueError('Cross-version native identity mismatch '+field)
        if (a['area'],a['scene'],a['kind'],a['raw_fields_hex'][10],a['source_record_sha256'])!=(
            t['area'],t['scene'],t['declared_kind'],t['mdt_path_bytes'],t['row_sha256']):
            raise ValueError('TW catalogue index does not match current raw bytes')
        if (s['family'],s['area_index'],s['declared_mode'],s['native_mdt_path'].encode('ascii').hex())!=(
            c['area'],c['scene'],c['declared_kind'],c['mdt_path_bytes']):
            raise ValueError('CN catalogue index does not match current raw bytes')
        joined.append({**t,'tw_row_sha256':t['row_sha256'],'cn_row_sha256':c['row_sha256'],
            'native_mdt_path':bytes.fromhex(t['mdt_path_bytes']).decode('ascii')})
    out.mkdir();snapshots=[]
    def save(rel,data,source):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        snapshots.append({'path':rel,'source':str(source),'bytes':len(data),'sha256':digest(data)})
    save('native-tw/Map_City_Coordniate.csv.native-bytes',sections[0][0],tw_encoded_path)
    save('native-cn/Map_City_Coordniate.csv.native-bytes',sections[1][0],cn_encoded_path)
    for label,path in [('tw-map-index.json',atlas_path),('cn-map-index.json',cn_path),('cn-decoder.py',decoder),
        ('tw-decoder.py',SERVER/'tools/strike_lab/omega_assets.py'),
        ('cn-loader-0042d910.c',CN/'artifacts/native/20261006-cn-scene-assets-01/0042d910.c'),
        ('cn-lookup-00428430.c',CN/'artifacts/native/20261006-cn-scene-assets-01/00428430.c'),
        ('tw-world-map-fields.md',SERVER/'docs/research/current-world-map-fields-20260921.md'),
        ('tool.py',Path(__file__))]:save('inputs/'+label,path.read_bytes(),path)
    include='// Pinned TW/CN catalogue identity join: shared-scene-identity-01.\n'
    include+='// Native raw paths retained, including ordinal143 leading separator.\n'
    include+='// Matching keys/path/kind do not prove common geometry or spawn rules.\n'
    include+=''.join('{'+f'{r["area"]},{r["scene"]},{r["declared_kind"]},'+
        json.dumps(r['tw_row_sha256'])+','+json.dumps(r['native_mdt_path'])+'},\n' for r in joined)
    generated=SERVER/'src/cn/world/SharedSceneIdentity.inc'
    if generated.exists():raise ValueError('Preserve previous generated scene identity source')
    generated.parent.mkdir(parents=True,exist_ok=True);generated.write_text(include,encoding='utf-8')
    save('source/SharedSceneIdentity.inc',generated.read_bytes(),generated)
    dump(out/'joined-scenes.json',joined)
    dump(out/'integration-manifest.json',{
        'kind':'TW/CN native catalogue identity for existing shared NativeMapCatalog keys',
        'tw_native_sha256':TW_PIN,'cn_native_sha256':PIN,'tw_resource_sha256':TW_RESOURCE,'cn_resource_sha256':CN_RESOURCE,
        'matching_native_keys_paths_declared_kinds':len(joined),'snapshots':snapshots,
        'join_rule':'Exact native numeric fields and raw ASCII MDT bytes per source row; no translated name, normalized path or codepage join.',
        'raw_path_exception':'Ordinal143 begins with backslash in both raw resources. Preserve it; normalized TW display path alone concealed this byte.',
        'shared_storage':'Existing NativeMapCatalog/current-map-catalog-v1 area/scene keys can identify these144 catalogued scenes for both adapters; no separate CN gameplay table or migration.',
        'remaining':['World ownership, native2A full data, scene-mode issuance, positions/spawns, geometry/collision and asset-version loading require actual authoritative preparation.',
                     'Catalogue category is not the2A low2-bit actor scene mode; never derive that mode from declared_kind here.',
                     'TW native dataset provenance must be matched on current DB reads; this artifact never reads/writes SQLite or refreshes its source baseline.'],
        'original_tw_resource':'Exact historical native resource read selectively from verified archive; installed TW resource has distinct EF297A84 hash and is preserved.',
        'archive_manifest_readonly':True,'historical_baseline_updated':False,
        'new_complete_routes':0,'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_modified':False,
    })
    print(json.dumps({'artifact':str(out),'shared_scene_identities':len(joined),'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
