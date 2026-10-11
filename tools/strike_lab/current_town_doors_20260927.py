"""Current CityI1 doorway points and explicit CUSTOM-0052 selector joins.

Only current assets are read. CAN does not encode an authoritative server
edge; ordinal selector joins and walk triggers remain custom policy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from .current_monster_binary_producer import parse_mdl
from .indoor_navigation import parse_hmd, navigation_inputs, dump_input
from .omega_assets import decode_csvz
from .town_navigation import MDL_SHA, MDL_DECODED_SHA, pinned
from .world_scenes import build_scenes


def project(x, y):
    return [x - int(y / 2), x + int((y + 1) / 2)]


def pairs(values, anchor):
    result = []
    for offset in range(0, 8, 2):
        point = values[offset:offset+2]
        if point[0] == -1:
            result.append(None)
        else:
            xy = project(*point)
            result.append([anchor[0]+xy[0], anchor[1]+xy[1]])
    return result


def build(client, executable):
    root = Path(client).resolve()
    source = root/'Data2/map/island01/CityI1/cityI1.mdlZ'
    decoded = decode_csvz(pinned(source, MDL_SHA))
    if hashlib.sha256(decoded).hexdigest() != MDL_DECODED_SHA:
        raise ValueError('Current town source changed')
    mdl = parse_mdl(decoded, allow_parent_rom=True)
    scenes = {s['scene']: s for s in build_scenes(root)['scenes'] if s['area']==2}
    placements = [p for p in mdl['placements'] if p['attached_reference'] and
                  '/indoor/' in p['attached_reference'].replace('\\','/').lower()]
    if len(placements) != 26:
        raise ValueError('Current town house count changed')
    routes, unresolved, navigation = [], [], []
    # Independent existing town export retains all source-window observations.
    # Never turn a contradictory point into an authoritative trigger.
    town_grid=json.loads((Path(__file__).resolve().parents[2]/'artifacts/world-atlas/town-2-4.json').read_text())
    def town_values(point):
        x,y=point
        return {w['cells_hex'][2*((y-w['origin_y'])*63+x-w['origin_x']):2*((y-w['origin_y'])*63+x-w['origin_x'])+2]
                for w in town_grid['windows'] if w['origin_x']<=x<w['origin_x']+63 and w['origin_y']<=y<w['origin_y']+63}
    for index, placement in enumerate(placements):
        scene = 5+index
        row = scenes[scene]
        attached = placement['attached_reference'].replace('\\','/').lower().split('/')[-1]
        if attached != row['asset_relative'].lower().split('/')[-1]:
            unresolved.append({'placement_offset': placement['offset'], 'scene_candidate':scene,
                               'attached_reference':placement['attached_reference'],
                               'can_asset':row['asset_relative'], 'reason':'RESOURCE_MISMATCH_NO_ROUTE'})
            continue
        variants = row['asset_variants']
        if not variants or len({v['decoded_sha256'] for v in variants}) != 1:
            raise ValueError('Missing/divergent current indoor source')
        variant = variants[0]
        raw = (root/variant['path']).read_bytes()
        data = decode_csvz(raw) if variant['path'].lower().endswith('z') else raw
        asset = parse_hmd(data)
        base, overlays = navigation_inputs(asset)
        output = subprocess.check_output([str(Path(executable).resolve()), '--dump'],
            input=dump_input(base, overlays), text=True, timeout=10).split()
        side, hex_cells = int(output[0]), output[1]
        cells = bytes.fromhex(hex_cells)
        if len(cells) != side*side:
            raise ValueError('Indoor grid compiler length mismatch')
        outdoor = pairs(mdl['models'][placement['fields'][0]]['extra_8_ints'], placement['fields'][3:5])
        anchor = side-1-base['width']+(base['width']&1)
        indoor = pairs(asset['models'][asset['placements'][0]['model']]['portal_fields'], [anchor,0])
        route_pairs = []
        for i in range(2):
            if outdoor[i] is None:
                continue
            if outdoor[i+2] is None or indoor[i] is None or indoor[i+2] is None:
                raise ValueError('Door pair incomplete')
            for x,y in (indoor[i], indoor[i+2]):
                if not 0<=x<side or not 0<=y<side or cells[y*side+x]==0:
                    raise ValueError('Door point not on qualified indoor navigation')
            route_pairs.append({'town_trigger':outdoor[i], 'town_arrival':outdoor[i+2],
                                'indoor_arrival':indoor[i], 'indoor_trigger':indoor[i+2]})
        boolean_point=scene==7 and all(p['town_trigger']==[82,46] and town_values(p['town_trigger'])=={'01','02'} for p in route_pairs)
        eligible=all((town_values(p['town_trigger'])=={'02'} or boolean_point) and town_values(p['town_arrival'])=={'01'} for p in route_pairs)
        routes.append({'scene':scene, 'pairs':route_pairs, 'navigation_eligible':eligible,
                       'boolean_navigation_qualification':'NATIVE_46FF0_102BF0_41350_POINT82_46' if boolean_point else None,
                       'town_point_values':[{'trigger':sorted(town_values(p['town_trigger'])),
                                            'arrival':sorted(town_values(p['town_arrival']))} for p in route_pairs],
                       'placement_offset':placement['offset'],
                       'placement_sha256':placement['sha256'], 'attached_reference':placement['attached_reference'],
                       'can_offset':row['source_offset'], 'can_sha256':row['source_sha256'],
                       'point_origin':'NATIVE_SOURCE_DERIVED_49BB0',
                       'selector_join_origin':'CUSTOM-0052_ORDINAL_RESOURCE_MATCH',
                       'trigger_origin':'CUSTOM-0052_MOVEMENT_ONTO_POINT'})
        navigation.append({'area':2,'scene':scene,'kind':2,'source':{
            'asset':variant['path'],'asset_sha256':variant['sha256'],
            'decoded_sha256':variant['decoded_sha256']},'base':base,'overlays':overlays,
            'grid':{'side':side,'cells_hex':hex_cells}})
    return {'schema':'god2-current-town-doors-v1','custom_design':'CUSTOM-0052',
            'town_mdl_sha256':MDL_SHA,'town_mdl_decoded_sha256':MDL_DECODED_SHA,
            'routes':routes,'unresolved':unresolved,'navigation':navigation,
            'counts':{'house_references':26,'resource_matched_routes':len(routes),
                      'directed_scene_edges':2*len(routes),'unresolved_resource_mismatches':len(unresolved),
                      'navigation_eligible_scenes':sum(r['navigation_eligible'] for r in routes),
                      'navigation_eligible_point_pairs':sum(len(r['pairs']) for r in routes if r['navigation_eligible'])},
            'current_client_accepted_scenes':[15], 'other_scenes_current_client_accepted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lua-output',type=Path,required=True)
    args=p.parse_args()
    for out in (args.output,args.lua_output):
        if out.resolve().is_relative_to(args.client.resolve()):
            p.error('Do not write into current client sources')
    report=build(args.client,args.executable)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
    lines=['-- CUSTOM-0052: generated from current MDL/HMD points; selector joins and triggers are custom.',
           'local doors = {']
    for route in report['routes']:
        if not route['navigation_eligible']:continue
        for pair in route['pairs']:
            fields=[route['scene'],*pair['town_trigger'],*pair['town_arrival'],
                    *pair['indoor_arrival'],*pair['indoor_trigger']]
            lines.append('    {'+','.join(map(str,fields))+'},')
    lines+=['}', 'return doors', '']
    args.lua_output.write_text('\n'.join(lines),encoding='ascii')
    print(json.dumps(report['counts']))


if __name__=='__main__':
    main()
