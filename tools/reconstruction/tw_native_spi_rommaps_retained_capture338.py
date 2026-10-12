from pathlib import Path
import hashlib,json

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round338-spi-rommaps-retained-source-audit')
BASE=OUT.parent
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OLD=BASE/'tw-native-resource-custody-and-remote-opaque-314'
SOURCE=OLD/'source-entry/inputs/exact-restored/gamedata.csvZ.decoded'
sha=lambda b:hashlib.sha256(b).hexdigest()
OUT.mkdir(parents=True,exist_ok=True)
refs=[]
def reference(path,scope):
    raw=path.read_bytes();refs.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),scope=scope,copied=False));return raw
def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8',newline='\n')
raw=reference(SOURCE,'Historical original decoded source in place; no full copy')
assert len(raw)==2783008 and sha(raw)=='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
# Fixed literal source-byte/physical-line cuts only. No project parser import,
# CSV resource decoder, numeric conversion, VM or native code is invoked.
lines=raw.splitlines(keepends=True)
assert lines[56].startswith(b'RomMaps,57,') and sum(line.startswith(b'RomMaps,') for line in lines)==1
offsets=[];offset=0
for line in lines:
    offsets.append(offset);offset+=len(line)
assert offset==len(raw)
selected=lines[56:114]
start=offsets[56];end=offsets[114]
window=raw[start:end]
assert window==b''.join(selected) and len(selected)==58
(OUT/'rommaps-header-and57-raw-lines.bin').write_bytes(window)
rows=[]
for ordinal in range(57):
    i=57+ordinal;line=lines[i]
    assert line.endswith(b'\r\n')
    body=line[:-2];fields=body.split(b',')
    assert fields[0]==str(ordinal).encode('ascii') and len(fields)==5
    assert all(c in b'0123456789' for field in fields[:3] for c in field)
    rows.append(dict(source_order_ordinal=ordinal,source_line=i+1,decoded_offset=offsets[i],raw_line_bytes=len(line),raw_line_sha256=sha(line),raw_body_bytes=len(body),raw_body_sha256=sha(body),raw_line_cp950_hex=line.hex(),raw_body_fields_hex=[field.hex() for field in fields],source_token0_ascii=fields[0].decode('ascii'),source_token1_ascii=fields[1].decode('ascii'),source_token2_ascii=fields[2].decode('ascii'),source_token3_ascii=fields[3].decode('ascii'),source_token4_ascii=fields[4].decode('ascii'),line_ending_hex='0d0a'))
save('rommaps57-source-line-cuts.json',rows)
prior_rows=json.loads(reference(BASE/'tw-native-petroom-key-membership-source-336/rows.json','Immutable336 normalized raw22 members in place; old NULL offsets unchanged'))
assert lines[8176]==b'SPI,737\r\n'
spi_rows=[]
for prior in prior_rows:
    i=prior['source_line']-1;line=lines[i]
    assert 8695<=i+1<=8716 and line.endswith(b'\r\n')
    body=line[:-2];fields=body.split(b',')
    assert body==bytes.fromhex(prior['raw_record_hex'])
    assert sha(body)==prior['source_record_sha256']
    assert [field.hex() for field in fields]==prior['raw_fields_hex'] and len(fields)==26
    assert fields[0]==str(prior['native_key']).encode('ascii')
    assert prior['source_record_index']==i-8177 and prior['decoded_offset'] is None
    spi_rows.append(dict(native_key=prior['native_key'],source_record_index=prior['source_record_index'],source_line=i+1,newly_qualified_historical_decoded_offset=offsets[i],line_bytes=len(line),line_sha256=sha(line),body_bytes=len(body),body_sha256=sha(body),line_ending_hex='0d0a',body_equal336=True,all_fields_equal336=True,original336_decoded_offset=None))
assert len(spi_rows)==22
spi_start=offsets[8694];spi_end=offsets[8716];spi_window=raw[spi_start:spi_end]
(OUT/'spi22-source-raw-lines8695-8716.bin').write_bytes(spi_window)
save('spi22-new-historical-source-offsets.json',dict(source=str(SOURCE),source_sha256=sha(raw),spi_header_source_line=8177,spi_header_decoded_offset=offsets[8176],spi_header_raw_cp950_hex=lines[8176].hex(),window_start_offset=spi_start,window_end_exclusive_offset=spi_end,window_bytes=len(spi_window),window_sha256=sha(spi_window),rows=spi_rows,scope='New exact historical75c3 input equality; original336 NULL-offset records preserved unchanged'))
for rel in ['source-entry/inputs.json','source-entry/seal.json','native-entry/game-restoration-receipt.json','native-entry/game-plaintext-facts.json','native-entry/input-manifest.json','native-entry/REPORT.md']:
    p=OLD/rel;content=reference(p,'Existing314 source-byte custody metadata only; no archive restoration/query rerun')
    dest=OUT/'provenance314'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content);refs[-1]['copied']=True;refs[-1]['retained']=dest.relative_to(OUT).as_posix()
for rel,start_line,end_line in [('tools/strike_lab/current_item_metadata.py',1,82),('tools/strike_lab/recover_companion_growth.py',17,23),('tools/strike_lab/recover_combat_rules.py',19,32)]:
    p=ROOT/rel;content=reference(p,'Strike_lab text/provenance only; never imported or run')
    excerpt=b''.join(content.splitlines(keepends=True)[start_line-1:end_line])
    dest=OUT/'source-text'/(p.stem+f'-{start_line}-{end_line}.txt');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(excerpt)
    refs[-1]['excerpt_retained']=dest.relative_to(OUT).as_posix();refs[-1]['excerpt_bytes']=len(excerpt);refs[-1]['excerpt_sha256']=sha(excerpt)
current=Path('C:/Users/risei/Desktop/God2/God2/Data2/Patch/Comm/gamedata.csvZ')
current_raw=reference(current,'Current encoded material hashed only; not decoded or equated with historical source')
assert sha(current_raw)=='ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2'
original_path=ROOT/'artifacts/research/client-file-unpack-20260928-01/decoded/Data2/Patch/Comm/gamedata.csvZ.decoded'
save('source-window-facts.json',dict(source=str(SOURCE),source_bytes=len(raw),source_sha256=sha(raw),header_source_line=57,header_decoded_offset=start,header_raw_cp950_hex=lines[56].hex(),header_declared_count_ascii='57',observed_selected_rows=len(rows),window_start_offset=start,window_end_exclusive_offset=end,window_bytes=len(window),window_sha256=sha(window),first_row_line=58,last_row_line=114,first_row_offset=rows[0]['decoded_offset'],last_row_offset=rows[-1]['decoded_offset'],source_token0_exact_sequence='0..56',source_physical_order_preserved=True,after_window_line_number=115,after_window_raw_cp950_hex=lines[114].hex(),historical_original_workspace_path=str(original_path),historical_original_workspace_path_exists=original_path.exists(),current_encoded_sha256=sha(current_raw),current_encoded_decoding_performed=False,current_native_bank_observed=False,full_decoded_source_copied=False,new_native_output=False))
save('references.json',refs)
print(json.dumps(dict(rows=len(rows),header_offset=start,window_end=end,window_bytes=len(window),window_sha256=sha(window),first_row_offset=rows[0]['decoded_offset'],last_row_offset=rows[-1]['decoded_offset'],native_parser_codec_sql_execution=0)))
