"""Current monster/map evidence audit; never invent or activate spawn points."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import pefile
from .current_monster_inventory import pinned_catalog,SOURCE,SOURCE_SHA
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog

ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
def audit(client):
    client=client.resolve();catalog=pinned_catalog(client)
    source=decode_csvz((client/SOURCE).read_bytes());maps=parse_catalog(source)
    map_rows={(row['area'],row['scene']):row for row in maps}
    records=[]
    for original in catalog['records']:
        row=dict(original)
        try:row['name']=bytes.fromhex(row['name_bytes_hex']).decode('cp950')
        except UnicodeDecodeError:row['name']=None
        # Lookup grouping is distinct from authoritative encounter/spawn area.
        row['qualification']='NATIVE_DISPLAY_LOOKUP_NOT_WORLD_SPAWN'
        row['world_spawn']={'area':None,'scene':None,'x':None,'y':None,'direction':None,
                            'respawn_seconds':None,'encounter_weight':None}
        records.append(row)
    groups=[]
    for (area,scene),entries in sorted(catalog['groups'].items()):
        native_map=map_rows.get((area,scene))
        groups.append({'display_area':area,'display_scene':scene,'visible_display_entries':len(entries),
            'map_catalog_record':native_map,'qualification':'LOOKUP_NAMESPACE_JOIN_NOT_SPAWN_AUTHORITY'})
    models=[]
    for path in sorted((client/'Data2/map').rglob('*.mdlZ')):
        packed=path.read_bytes();plain=decode_csvz(packed);lines=plain.splitlines()
        if len(lines)<2 or lines[0]!=b'MDL v1.6':raise ValueError('Unqualified MDL header')
        header=lines[1].split()
        if len(header)!=2 or header[0]!=b'ROMFILE':raise ValueError('Missing ROMFILE section')
        count=int(header[1])
        if not 1<=count<=128 or len(lines)<count+2:raise ValueError('Invalid ROMFILE count')
        refs=lines[2:count+2]
        models.append({'file':path.relative_to(client).as_posix(),'source_sha256':sha(packed),
            'decoded_sha256':sha(plain),'rom_reference_raw_hex':[value.hex() for value in refs],
            'enemy_named_rom_references':[value.decode('ascii') for value in refs
                if b'eny' in value.lower() or b'monster' in value.lower()],
            'qualification':'MODEL_RESOURCE_REFERENCE_NOT_MONSTER_ID_OR_SPAWN_RECORD'})
    resource_files=[]
    for relative in ('Data2/Patch/eny.csvZ','Data2/Patch/FightEny.csvZ','Data2/Fight/Spg/cbspec2.bin'):
        path=client/relative;packed=path.read_bytes()
        resource_files.append({'file':relative,'sha256':sha(packed),'length':len(packed),
            'qualification':'GRAPHICS_RESOURCE_NOT_QUALIFIED_WORLD_SPAWN',
            'decoded_prefix_hex':decode_csvz(packed)[:512].hex() if path.suffix.lower()=='.csvz' else None})
    reference=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    exe=client/'God2.exe';image=pefile.PE(str(exe)).get_memory_mapped_image();ranges=[]
    for name,start,end in [('enemy_name_lookup',0x5a0a0,0x5a1a0),
            ('enemy_name_loader',0x5a1a0,0x5a560),('fight_enemy_resource_loader',0x54210,0x54478),
            ('battle_participant_resource_choice',0x115c90,0x116080)]:
        if image[start:end]!=reference[start:end]:raise ValueError('Current EXE monster path changed: '+name)
        ranges.append({'name':name,'start_rva':hex(start),'end_rva':hex(end),'sha256':sha(image[start:end])})
    return {'schema':'god2-current-native-monster-placement-evidence-v1','source_sha256':SOURCE_SHA,
        'client_exe_sha256':sha(exe.read_bytes()),'counts':{'source_lookup_occurrences':len(records),
        'lookup_visible_occurrences':sum(row['lookup_visible'] for row in records),
        'visible_lookup_groups':len(groups),'map_catalog_records':len(maps),'mdl_reference_sections':len(models),
        'fully_qualified_world_spawn_records':0,'spawn_records_written':0},
        'records':records,'display_groups_with_map_catalog':groups,'map_model_sources':models,
        'graphics_sources':resource_files,'current_exe_verified_ranges':ranges,
        'blocked_test_encounter':{'trigger_area':2,'trigger_scene':15,'trigger_x':18,'trigger_y':12,
        'borrowed_display_key':[1,0,1],'authority':'CUSTOM_TEST_NOT_NATIVE'},
        'missing_source':'Original server monster-to-world-location/encounter-region assignment, exact coordinates or region bounds, and spawn/respawn conditions. Display slot14 is a battle position, not map x/y.'}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--client',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):raise ValueError('Output must be outside client')
    result=audit(args.client);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['counts']));return 0
if __name__=='__main__':raise SystemExit(main())
