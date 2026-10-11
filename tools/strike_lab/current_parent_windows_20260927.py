"""Source-pinned selected outdoor windows for native parent map joins.

Static C++/Python projection equality only; never enables a server transition.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .outdoor_mbd import parse_mbd,project_base_window,apply_model_pass,apply_model_points
from .town_navigation import canonical_points
from .world_scenes import build_scenes
from .world_atlas import parse_catalog

ROOT=Path(__file__).resolve().parents[2]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def build(client,binary,area,scene,points,all_windows=False):
    evidence=json.loads((ROOT/'artifacts/research/monster-map-placement-join-20260927/evidence.json').read_text())
    row=next(s for s in build_scenes(client)['scenes'] if (s['area'],s['scene'])==(area,scene))
    stem=row['asset_relative'].lower().rsplit('.',1)[0]
    pin=next(p for p in evidence['source_mdl_pins'] if p['file'].lower().removesuffix('z').rsplit('.',1)[0]==stem)
    raw=(client/pin['file']).read_bytes();decoded=decode_csvz(raw) if pin['file'].lower().endswith('z') else raw
    if sha(raw)!=pin['source_sha256'] or sha(decoded)!=pin['decoded_sha256']:raise ValueError('Current MDL pin changed')
    mdl=parse_mdl(decoded,allow_parent_rom=True)
    mbd_path=(client/pin['file']).with_suffix('.mbd');mbd_raw=mbd_path.read_bytes();mbd=parse_mbd(mbd_raw)
    compressed=Path(str(mbd_path)+'Z')
    if compressed.exists() and decode_csvz(compressed.read_bytes())!=mbd_raw:raise ValueError('MBD plain/compressed mismatch')
    # Native placement ordering is qualified only for current single layers.
    if any(m['layers'][0][0]<0 or any(l[0]>=0 for l in m['layers'][1:]) for m in mdl['models']):
        raise ValueError('Multi-layer outdoor projection needs separate qualification')
    groups={}
    for p in mdl['placements']:
        m=mdl['models'][p['fields'][0]];g=m['grids'][p['fields'][5]]
        if not g['width'] or not g['height']:
            if any(point[0]>=0 for point in canonical_points(m['extra_8_ints'])):raise ValueError('Empty pass with active points needs native qualification')
            continue
        groups.setdefault(tuple(p['block']),[]).append(p)
    for group in groups.values():
        group.sort(key=lambda p:p['fields'][2]+mdl['tiles'][mdl['models'][p['fields'][0]]['layers'][0][0]]['fields'][2]+mdl['models'][p['fields'][0]]['layers'][0][2])
    centers=([(x,y) for y in range(mbd['height']) for x in range(mbd['width'])] if all_windows else
      sorted({(x//21+dx,y//21+dy) for x,y in points for dy in (-1,0,1) for dx in (-1,0,1)}))
    windows=[]
    for cx,cy in centers:
        blocks=[mbd['blocks'][y*mbd['width']+x] if 0<=x<mbd['width'] and 0<=y<mbd['height'] else None
          for y in range(cy-1,cy+2) for x in range(cx-1,cx+2)]
        expected=project_base_window(blocks,bytes([255])*3969);objects=[]
        if blocks[4] is not None:
            for gy in range(cy-2,cy+2):
                for gx in range(cx-2,cx+2):
                    for p in groups.get((gx,gy),[]):
                        f=p['fields'];m=mdl['models'][f[0]];g=m['grids'][f[5]]
                        cells=bytes(map(int,decoded[g['start']:g['end_exclusive']].split()));native_points=canonical_points(m['extra_8_ints'])
                        x,y=f[3]-cx*21+21,f[4]-cy*21+21
                        expected=apply_model_points(apply_model_pass(expected,x,y,g['width'],g['height'],cells),x,y,native_points)
                        objects.append([x,y,g['width'],g['height'],*native_points[0],*native_points[1],*cells])
        tokens=[]
        for b in blocks:
            tokens.append(int(b is not None))
            if b is not None:tokens.extend(b)
        tokens.append(len(objects))
        for o in objects:tokens.extend(o)
        actual=subprocess.check_output([str(binary.resolve()),'--dump'],input=' '.join(map(str,tokens)),text=True,timeout=20).strip()
        if actual!=''.join('??' if v==255 else f'{v:02x}' for v in expected):raise ValueError('Outdoor native projection port mismatch')
        windows.append({'block_x':cx,'block_y':cy,'origin_x':cx*21-21,'origin_y':cy*21-21,'cells_hex':actual,'block_present':blocks[4] is not None})
    observations=[]
    for x,y in points:
        values={w['cells_hex'][2*((y-w['origin_y'])*63+x-w['origin_x']):2*((y-w['origin_y'])*63+x-w['origin_x'])+2]
          for w in windows if w['block_present'] and w['origin_x']<=x<w['origin_x']+63 and w['origin_y']<=y<w['origin_y']+63}
        observations.append({'point':[x,y],'values':sorted(values),'unanimous_nonzero':bool(values) and values<={'01','02'}})
    catalog_raw=(client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    if sha(catalog_raw)!='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731':raise ValueError('Current map selector catalog changed')
    catalog=parse_catalog(decode_csvz(catalog_raw))
    selector=next(r for r in catalog if (r['area'],r['scene'])==(area,scene))
    return {'schema':'god2-current-parent-full-navigation-v1' if all_windows else 'god2-current-parent-selected-windows-v1',
      'area':area,'scene':scene,'kind':selector['kind'],'block_width':mbd['width'],'block_height':mbd['height'],
      'source_mdl_pin':pin,'mbd_file':mbd_path.relative_to(client).as_posix(),'mbd_sha256':sha(mbd_raw),
      'can_sha256':row['source_sha256'],'can_offset':row['source_offset'],'windows':windows,
      'point_observations':observations,'runtime_route_verified':False,'dynamic_occupancy_included':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--client',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True);p.add_argument('--area',type=int,required=True);p.add_argument('--scene',type=int,required=True)
    p.add_argument('--point',type=int,nargs=2,action='append',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--all-windows',action='store_true');a=p.parse_args()
    if a.output.resolve().is_relative_to(a.client.resolve()):raise ValueError('Cannot overwrite native client sources')
    r=build(a.client.resolve(),a.executable,a.area,a.scene,a.point,a.all_windows)
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='ascii');print(json.dumps(r['point_observations']))

if __name__=='__main__':main()
