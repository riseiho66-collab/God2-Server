"""Pinned town static navigation export; no live acceptance or movement grant."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .outdoor_mbd import parse_mbd, project_base_window, apply_model_pass, apply_model_points

MBD_SHA='cf4a4f14f9e5377fa47b4f115d44b1fc90c5c9dff0e3e0f358d781ab8c1030ae'
MDL_SHA='bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618'
MDL_DECODED_SHA='59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pinned(path, expected):
    if path.stat().st_size > 4*1024*1024:
        raise ValueError('Town source exceeds bound')
    raw=path.read_bytes()
    if digest(raw)!=expected:
        raise ValueError('Town source identity changed: '+str(path))
    return raw


def canonical_points(values):
    if len(values)!=8:
        raise ValueError('Expected four point pairs')
    points=[(-1,-1)]*4
    for i in range(4):
        pair=tuple(values[2*i:2*i+2])
        if pair[0]==-1 or pair not in points:
            points[i]=pair
    return points[:2]


def build_navigation(client, executable):
    root=Path(client).resolve()
    relative='Data2/map/island01/CityI1/'
    mbd=parse_mbd(pinned(root/(relative+'cityi1.mbd'),MBD_SHA))
    decoded=decode_csvz(pinned(root/(relative+'cityI1.mdlZ'),MDL_SHA),limit=4*1024*1024)
    if digest(decoded)!=MDL_DECODED_SHA:
        raise ValueError('Town decode identity changed')
    mdl=parse_mdl(decoded,allow_parent_rom=True)
    if (mbd['width'],mbd['height'],len(mdl['models']),len(mdl['placements']))!=(9,9,167,362):
        raise ValueError('Town structure changed')
    for model in mdl['models']:
        if any(layer[0]!=-1 for layer in model['layers'][1:]) or model['layers'][0][0]<0:
            raise ValueError('Only qualified town single-layer models')
    groups={}
    for placement in mdl['placements']:
        groups.setdefault(tuple(placement['block']),[]).append(placement)
    def order(p):
        model=mdl['models'][p['fields'][0]]
        tile,_,dy=model['layers'][0]
        return p['fields'][2]+mdl['tiles'][tile]['fields'][2]+dy
    for group in groups.values():group.sort(key=order)
    windows=[]
    for cy in range(9):
        for cx in range(9):
            blocks=[]
            for y in range(cy-1,cy+2):
                for x in range(cx-1,cx+2):
                    blocks.append(mbd['blocks'][y*9+x] if 0<=x<9 and 0<=y<9 else None)
            expected=project_base_window(blocks,bytes([255])*3969)
            objects=[]
            if blocks[4] is not None:
                for gy in range(cy-2,cy+2):
                    for gx in range(cx-2,cx+2):
                        for p in groups.get((gx,gy),[]):
                            f=p['fields'];model=mdl['models'][f[0]];grid=model['grids'][f[5]]
                            cells=bytes(map(int,decoded[grid['start']:grid['end_exclusive']].split()))
                            points=canonical_points(model['extra_8_ints'])
                            x,y=f[3]-cx*21+21,f[4]-cy*21+21
                            expected=apply_model_pass(expected,x,y,grid['width'],grid['height'],cells)
                            expected=apply_model_points(expected,x,y,points)
                            objects.append([x,y,grid['width'],grid['height'],*points[0],*points[1],*cells])
            tokens=[]
            for block in blocks:
                tokens.append(int(block is not None))
                if block is not None:tokens.extend(block)
            tokens.append(len(objects))
            for obj in objects:tokens.extend(obj)
            output=subprocess.check_output([str(Path(executable).resolve()),'--dump'],
                input=' '.join(map(str,tokens)),text=True,timeout=10).strip()
            reference=''.join('??' if v==255 else f'{v:02x}' for v in expected)
            if output!=reference:
                raise ValueError('C++ town navigation differs at '+str((cx,cy)))
            windows.append({'block_x':cx,'block_y':cy,'origin_x':cx*21-21,'origin_y':cy*21-21,
                            'cells_hex':output,'known_cells':sum(v!=255 for v in expected),
                            'sha256':digest(output.encode('ascii'))})
    return {'schema':'god2-recovered-town-navigation-v2','area':2,'scene':4,'kind':0,
            'side':63,'block_width':9,'block_height':9,'unknown_marker':'??',
            'block_present':[block is not None for block in mbd['blocks']],
            'sources':{'mbd':relative+'cityi1.mbd','mbd_sha256':MBD_SHA,
                       'mdl':relative+'cityI1.mdlZ','mdl_sha256':MDL_SHA,'mdl_decoded_sha256':MDL_DECODED_SHA},
            'qualification':'STATIC_CPP_PYTHON_MATCH; native tests separate',
            'dynamic_occupancy_included':False,'runtime_validated':False,'windows':windows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,required=True)
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.is_relative_to(args.client.resolve()):
        parser.error('Output must not modify original client')
    data=build_navigation(args.client,args.executable)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,indent=2)+'\n',encoding='ascii')
    print(json.dumps({'windows':len(data['windows']),'runtime_validated':False,'output':str(output)}))


if __name__=='__main__':main()
