"""23 current model point pairs; CUSTOM-0036 side/order join, no invented cells."""
import argparse
import hashlib
import json
from pathlib import Path
from .current_monster_binary_producer import parse_mdl
from .current_town_doors_20260927 import pairs
from .island01_entry_navigation import build, MDL_SHA
from .omega_assets import decode_csvz
from .town_navigation import MDL_SHA as TOWN_SHA, pinned


def points(source, digest, suffix):
    mdl=parse_mdl(decode_csvz(pinned(source,digest)),allow_parent_rom=True)
    result=[]
    for placement in mdl['placements']:
        ref=(placement['attached_reference'] or '').replace('\\','/').lower()
        if not ref.endswith(suffix):continue
        all_points=pairs(mdl['models'][placement['fields'][0]]['extra_8_ints'],placement['fields'][3:5])
        if all_points[0] is not None or all_points[1] is None or all_points[3] is None:
            raise ValueError('Current parent point shape changed')
        result.append({'trigger':all_points[1],'arrival':all_points[3],
                       'placement_offset':placement['offset'],'placement_sha256':placement['sha256']})
    if len(result)!=23:raise ValueError('Current parent reference count changed')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--routes-output',type=Path,required=True)
    p.add_argument('--lua-output',type=Path,required=True)
    a=p.parse_args()
    folder=a.client/'Data2/map/island01'
    town=points(folder/'CityI1/cityI1.mdlZ',TOWN_SHA,'/island01.mdt')
    island=points(folder/'Island01.mdlZ',MDL_SHA,'/cityi1.mdt')
    report=build(a.client,a.executable,tuple((x,y) for y in range(8,12) for x in range(21,27)))
    report['schema']='god2-recovered-island01-all-boundaries-navigation-v1'
    report['scope']='24_STATIC_WINDOWS_AROUND_ALL_23_CITYI1_BOUNDARY_POINTS'
    def values(x,y):
        return {w['cells_hex'][2*((y-w['origin_y'])*63+x-w['origin_x']):2*((y-w['origin_y'])*63+x-w['origin_x'])+2]
                for w in report['windows'] if w['origin_x']<=x<w['origin_x']+63 and w['origin_y']<=y<w['origin_y']+63}
    def direction(row):return tuple(t-a for t,a in zip(row['trigger'],row['arrival']))
    joined=[]
    for d in [(-1,0),(1,0),(0,1)]:
        left=sorted([r for r in town if direction(r)==d],key=lambda r:(r['trigger'][1],r['trigger'][0]))
        right=sorted([r for r in island if direction(r)==tuple(-v for v in d)],key=lambda r:(r['trigger'][1],r['trigger'][0]))
        if len(left)!=len(right) or not left:raise ValueError('Parent boundary side count mismatch')
        for t,i in zip(left,right):
            trigger_values=values(*i['trigger']);arrival_values=values(*i['arrival'])
            joined.append({'town':t,'island':i,'point_origin':'NATIVE_SOURCE_DERIVED_49BB0',
                           'join_and_trigger_origin':'CUSTOM-0036_SIDE_ORDER_PAIRING',
                           'island_trigger_values':sorted(trigger_values),'island_arrival_values':sorted(arrival_values),
                           'navigation_eligible':trigger_values=={'02'} and arrival_values=={'01'}})
    if len(joined)!=23:raise ValueError('Unjoined parent boundary point')
    for out in [a.output,a.routes_output,a.lua_output]:
        if out.resolve().is_relative_to(a.client.resolve()):p.error('Do not modify client source')
        out.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
    a.routes_output.write_text(json.dumps({'schema':'god2-current-island-boundaries-v1','custom_design':'CUSTOM-0036',
        'town_mdl_sha256':TOWN_SHA,'island_mdl_sha256':MDL_SHA,'pairs':joined,
        'counts':{'paired_boundaries':23,'directed_point_routes':46,
                  'navigation_eligible_pairs':sum(r['navigation_eligible'] for r in joined)},
        'prior_current_client_accepted_scene_edges':2,
        'individual_point_pairs_current_client_accepted':None,
        'new_east_south_current_client_accepted':False},indent=2)+'\n',encoding='ascii')
    lines=['-- CUSTOM-0036: all current model point pairs; side/order join and triggers are custom.','return {']
    for r in joined:
        if not r['navigation_eligible']:continue
        f=[*r['town']['trigger'],*r['town']['arrival'],*r['island']['trigger'],*r['island']['arrival']]
        lines.append('    {'+','.join(map(str,f))+'},')
    a.lua_output.write_text('\n'.join(lines+['}','']),encoding='ascii')
    print(json.dumps({'pairs':len(joined),'windows':len(report['windows']),
        'coordinates':report['cross_window']['covered_coordinates'],'conflicts':len(report['cross_window']['conflicts']),
        'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
