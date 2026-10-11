"""Current CityI2 six exact resource joins; CUSTOM-0052 walking policy.

Source selectors/points are derived from current CAN/MDL/HMD. Parent Island03
has no entry trigger and remains explicitly unresolved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from .current_monster_binary_producer import parse_mdl
from .current_town_doors_20260927 import pairs
from .indoor_navigation import parse_hmd,navigation_inputs,dump_input
from .omega_assets import decode_csvz
from .world_scenes import build_scenes

ROOT=Path(__file__).resolve().parents[2]
ENCODED='cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc'
DECODED='bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f'

def build(client,executable):
    source=client/'Data2/map/island03/cityi2/cityi2.mdlZ'
    raw=source.read_bytes();data=decode_csvz(raw)
    if hashlib.sha256(raw).hexdigest()!=ENCODED or hashlib.sha256(data).hexdigest()!=DECODED:
        raise ValueError('Current Kunlun source changed')
    mdl=parse_mdl(data,allow_parent_rom=True)
    refs=[p for p in mdl['placements'] if p['attached_reference'] and '/indoor/' in p['attached_reference'].replace('\\','/').lower()]
    if len(refs)!=6:raise ValueError('Current Kunlun room count changed')
    catalog={s['scene']:s for s in build_scenes(client)['scenes'] if s['area']==4}
    outdoor=json.loads((ROOT/'artifacts/world-atlas/kunlun-4-3.json').read_text())
    def values(point):
        x,y=point
        return sorted({w['cells_hex'][2*((y-w['origin_y'])*63+x-w['origin_x']):2*((y-w['origin_y'])*63+x-w['origin_x'])+2]
          for i,w in enumerate(outdoor['windows']) if outdoor['block_present'][i] and
          w['origin_x']<=x<w['origin_x']+63 and w['origin_y']<=y<w['origin_y']+63})
    routes=[];navigation=[]
    for index,p in enumerate(refs):
        scene=index+4;row=catalog[scene]
        if p['attached_reference'].replace('\\','/').lower().split('/')[-1]!=row['asset_relative'].lower().split('/')[-1]:
            raise ValueError('Kunlun ordinal resource mismatch')
        variants=row['asset_variants']
        if not variants or len({v['decoded_sha256'] for v in variants})!=1:raise ValueError('Room variants mismatch')
        variant=variants[0];raw=(client/variant['path']).read_bytes()
        asset=parse_hmd(decode_csvz(raw) if variant['path'].lower().endswith('z') else raw)
        base,overlays=navigation_inputs(asset)
        output=subprocess.check_output([str(executable.resolve()),'--dump'],input=dump_input(base,overlays),text=True,timeout=10).split()
        side=int(output[0]);cells=bytes.fromhex(output[1])
        town=pairs(mdl['models'][p['fields'][0]]['extra_8_ints'],p['fields'][3:5])
        room=pairs(asset['models'][asset['placements'][0]['model']]['portal_fields'],[side-1-base['width']+(base['width']&1),0])
        route_pairs=[]; observations=[]
        for i in range(2):
            if any(point is None for point in (town[i],town[i+2],room[i],room[i+2])):raise ValueError('Incomplete doorway')
            for x,y in (room[i],room[i+2]):
                if not 0<=x<side or not 0<=y<side or cells[y*side+x]==0:raise ValueError('Blocked room point')
            tv,av=values(town[i]),values(town[i+2])
            if not tv or not set(tv)<= {'01','02'} or av!=['01']:raise ValueError('Outdoor point not unanimously passable')
            observations.append({'trigger':tv,'arrival':av})
            route_pairs.append({'town_trigger':town[i],'town_arrival':town[i+2], 'indoor_arrival':room[i],'indoor_trigger':room[i+2]})
        routes.append({'area':4,'outdoor_scene':3,'scene':scene,'kind':2,'pairs':route_pairs,'navigation_eligible':True,
          'placement_offset':p['offset'],'placement_sha256':p['sha256'],'attached_reference':p['attached_reference'],
          'can_offset':row['source_offset'],'can_sha256':row['source_sha256'],'town_point_values':observations,
          'point_origin':'NATIVE_SOURCE_DERIVED_49BB0','selector_join_origin':'CUSTOM-0052_ORDINAL_EXACT_RESOURCE_MATCH',
          'trigger_origin':'CUSTOM-0052_MOVEMENT_ONTO_POINT'})
        navigation.append({'area':4,'scene':scene,'kind':2,'source':{'asset':variant['path'],'asset_sha256':variant['sha256'],
          'decoded_sha256':variant['decoded_sha256']},'base':base,'overlays':overlays,'grid':{'side':side,'cells_hex':output[1]}})
    return {'schema':'god2-current-kunlun-doors-v1','custom_design':'CUSTOM-0052','area':4,'outdoor_scene':3,
      'outdoor_kind':0,'mdl_sha256':ENCODED,'mdl_decoded_sha256':DECODED,'routes':routes,'navigation':navigation,
      'unresolved':[{'placement_offset':63905,'destination_area':4,'destination_scene':0,'destination_anchor':[327,351],
        'reason':'NO_SOURCE_ENTRY_TRIGGER_POINT; trace current click/action producer'}],
      'counts':{'house_references':6,'point_pairs':12,'directed_point_routes':24},'current_client_accepted':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--client',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lua-output',type=Path,required=True);a=p.parse_args()
    for path in (a.output,a.lua_output):
        if path.resolve().is_relative_to(a.client.resolve()):raise ValueError('Cannot write client source')
    report=build(a.client.resolve(),a.executable)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
    lines=['-- CUSTOM-0052: current area4/scene3 exact resource joins; walking policy is custom.','return {']
    for route in report['routes']:
        for pair in route['pairs']:
            lines.append('    {'+','.join(map(str,[route['scene'],*pair['town_trigger'],*pair['town_arrival'],*pair['indoor_arrival'],*pair['indoor_trigger']]))+'},')
    a.lua_output.write_text('\n'.join(lines+['}','']),encoding='ascii')
    print(json.dumps(report['counts']))

if __name__=='__main__':main()
