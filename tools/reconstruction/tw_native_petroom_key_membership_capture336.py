"""Read retained source JSON/raw octets only; no resource/VM/codec/SQL imports."""
from pathlib import Path
import hashlib, json, struct

ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Users/risei/Desktop/God2/God2-Server')
ATLAS=REPO/'artifacts/world-atlas'
P335=ROOT.parent/'tw-native-f4-list-definition-key-source-335'
ENCODED='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
PARSER='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ITEMS_SHA='3c21cc86d1072aafc6fa24fc80644a9d093454bfc45e66bf49829123cc9ae9bc'
COMPANIONS_SHA='e75442ce039273f6dd3cf1af88c8b72853af444145bf2d3969102c4f6d4890c3'
def sha(data):return hashlib.sha256(data).hexdigest()
def emit(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[]
def read(path,expected=None):
    raw=path.read_bytes();digest=sha(raw)
    if expected and digest!=expected:raise ValueError(f'Changed source: {path}')
    refs.append(dict(path=str(path),bytes=len(raw),sha256=digest))
    return raw
items=json.loads(read(ATLAS/'items.json',ITEMS_SHA))
companions=json.loads(read(ATLAS/'companions.json',COMPANIONS_SHA))
for source in [items['source'],companions['sources']['Data2/Patch/Comm/gamedata.csvZ']]:
    if source['sha256']!=ENCODED or source['decoded_sha256']!=DECODED:
        raise ValueError('Historical source epoch changed')
if len(items['records'])!=16127:raise ValueError('Definition inventory changed')
types=items['types']
category=next(t for t in types if t['section']=='SPI')
ordinal=types.index(category)
independent=companions['sections']['ItemType']['records'][ordinal]
if ordinal!=9 or category['source_line']!=20 or independent['decoded_offset']!=1213:
    raise ValueError('Category provenance changed')
category_fields=[bytes.fromhex(x) for x in category['raw_fields_hex']]
category_body=b','.join(category_fields)
if sha(category_body)!=category['source_record_sha256']:
    raise ValueError('Category raw field hash mismatch')
if category['raw_fields_hex']!=independent['fields_hex']:
    raise ValueError('Independent category tokens differ')
category_raw=bytes.fromhex(independent['raw_record_hex'])
if category_raw.rstrip(b'\r\n')!=category_body or sha(category_raw)!=independent['sha256']:
    raise ValueError('Independent category exact bytes differ')
if category_fields[:3]!=[b'5501',b'6400',b'SPI']:raise ValueError('SPI range changed')
rows=[];bank=[];all_matches=[]
for record in items['records']:
    key=int(bytes.fromhex(record['raw_fields_hex'][0]))
    if key!=record['client_item_id']:raise ValueError('Cached key differs from raw token0')
    if record['section']=='SPI':bank.append(record)
    if 6177<=key<=6200:
        all_matches.append(record)
        fields=[bytes.fromhex(x) for x in record['raw_fields_hex']]
        body=b','.join(fields)
        if sha(body)!=record['source_record_sha256']:raise ValueError('Original row hash mismatch')
        rows.append(dict(section=record['section'],native_key=key,
            source_record_index=record['source_record_index'],source_line=record['source_line'],
            decoded_offset=None,source_record_sha256=record['source_record_sha256'],
            raw_record_hex=body.hex(),raw_record_bytes=len(body),field_count=len(fields),
            raw_fields_hex=record['raw_fields_hex'],cached_cp950_name_display=record['client_name'],
            display_is_identity=False,full396_available=False,runtime_eligible=False))
rows.sort(key=lambda r:r['native_key'])
if len(rows)!=22 or any(r['section']!='SPI' for r in rows):raise ValueError('Target membership changed')
if len(bank)!=737 or sorted(r['source_record_index'] for r in bank)!=list(range(737)):
    raise ValueError('SPI bank source index coverage changed')
if any(r['source_line']!=8178+r['source_record_index'] for r in bank):
    raise ValueError('SPI source line ordering changed')
expected_keys=list(range(6177,6181))+list(range(6183,6201))
if [r['native_key'] for r in rows]!=expected_keys:raise ValueError('Target keys changed')
if [r['source_record_index'] for r in rows]!=list(range(517,539)):
    raise ValueError('Native bank order changed')
if [r['source_line'] for r in rows]!=list(range(8695,8717)):
    raise ValueError('Line provenance changed')

# Canonical atom recipe: every atom is prefixed by its unsigned LE32 byte length.
# ASCII decimal numbers have no whitespace or leading zeroes; hashes lowercase ASCII.
# Fields themselves are the exact token octets, not their hex/display encoding.
atoms=[b'god2-native-petroom-key-source-336-v1',b'Data2/Patch/Comm/gamedata.csvZ',
       ENCODED.encode(),DECODED.encode(),PARSER.encode(),ITEMS_SHA.encode(),COMPANIONS_SHA.encode(),
       b'16127',b'737',b'SPI',b'9',b'20',b'1213',category['source_record_sha256'].encode(),category_body,
       b'22',b'6181',b'6182']
for r in rows:
    atoms.extend([r['section'].encode(),str(r['native_key']).encode(),
        str(r['source_record_index']).encode(),str(r['source_line']).encode(),
        r['source_record_sha256'].encode(),str(r['field_count']).encode()])
    atoms.extend(bytes.fromhex(x) for x in r['raw_fields_hex'])
canonical=b''.join(struct.pack('<I',len(a))+a for a in atoms)
(ROOT/'canonical-fingerprint-input.bin').write_bytes(canonical)
emit('rows.json',rows)
emit('category-source.json',dict(source_ordinal_zero_based=ordinal,source_line=20,decoded_offset=1213,
    item_atlas_category=category,independent_companion_category=independent,
    normalized_raw_record_hex=category_body.hex(),normalized_sha256=sha(category_body),
    generic_native_selector=0,selector_condition='SPI has no match in pinned36tag table; historical calloc precondition at category+63D remains0'))
emit('membership.json',dict(source_file='Data2/Patch/Comm/gamedata.csvZ',encoded_sha256=ENCODED,
    decoded_sha256=DECODED,parser_image_sha256=PARSER,inventory_total=16127,spi_bank_total=737,
    range_low=6177,range_high=6200,found_keys=expected_keys,missing_keys_in_retained_inventory=[6181,6182],
    target_rows=22,raw_row_bytes=sum(r['raw_record_bytes'] for r in rows),
    target_full396_available=0,decoded_row_offsets_available=0,
    record_index_basis='Zero-based ordinal within SPI bank, distinct from item key, array slot and compact UI label.',
    canonical_atom_count=len(atoms),canonical_bytes=len(canonical),canonical_sha256=sha(canonical),
    canonical_recipe='ASCII metadata atoms in capture script order, then key-ascending rows; each row: section,key,index,line,rowSHA,fieldCount,all raw field octets. Each atom length-prefixed unsignedLE32. No display strings.',
    authority='Historical source records only; no livebank, ownership, acquisition, eligiblepopulation, timer, state or action pairing.'))
table=json.loads(read(P335/'native/category-tag-strings.json'))
if any(bytes.fromhex(r['raw_hex'])[:3]==b'SPI' for r in table):raise ValueError('SPI unexpectedly has native tag')
read(P335/'seal.json','c44c9c7c97f7f889600303fcb2758177bdfed74fc5f10f91f4c298dc89bd17af')
native_pins=json.loads(read(P335/'input-references.json'))
for pin in native_pins:read(Path(pin['path']),pin['sha256'])
for name in ['category-loader-complete.bin','category-lookup-complete.bin',
             'row-loader-complete.bin','lookup-complete.bin','generic-record-parser-complete.bin']:
    read(P335/'native'/name)
provenance_tool=read(REPO/'tools/strike_lab/recover_items.py')
read(REPO/'tools/strike_lab/recover_companions.py')
read(REPO/'docs/research/pet-incubation-evidence-20260919.md')
read(ATLAS/'pet-incubation.json')
emit('source-references.json',refs)
emit('provenance-excerpts.json',dict(
    exact_recover_items_excerpts=[dict(
        start_symbol='def lines_of',raw_hex=provenance_tool[provenance_tool.index(b'def lines_of'):provenance_tool.index(b'def section')].hex()),dict(
        start_symbol='def provenance',raw_hex=provenance_tool[provenance_tool.index(b'def provenance'):provenance_tool.index(b'def display')].hex())],
    recovery_rule='recover_items.lines_of removes one terminalCR per sourceLF line; provenance hashes that normalized raw line and stores all raw.split(comma) fields. Exactjoin(comma) reconstruction matches retained rowSHA for all22.',
    category_rule='Companion exact raw_record_hex is retained independently; its terminal CR/LF is explicitly preserved separately from normalized ItemType body. Both field arrays agree.',
    permitted_reads='Plain existing JSON/text/bin only. Historical pack/SQLite index seen but never queried or opened for recovery. Encoded/live csvZ not decoded. Strike_lab scripts read solely for provenance, not imported/executed.',
    unknown='No full396 target metadata is retained in these inputs. No row decoded offsets, direct live source bytes, actual live loading history, owner/acquisition or issuer qualified.'))
print(json.dumps(dict(rows=len(rows),raw_row_bytes=sum(r['raw_record_bytes'] for r in rows),
                     canonical_sha256=sha(canonical),canonical_bytes=len(canonical))))
