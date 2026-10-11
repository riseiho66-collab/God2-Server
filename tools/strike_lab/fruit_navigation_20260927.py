"""Source-pinned fruit village collision windows, not original spawn policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from .town_navigation import pinned,canonical_points
from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .outdoor_mbd import parse_mbd,project_base_window,apply_model_pass,apply_model_points

FOLDER='Data2/map/North002/Cityjiu02/'
MBD='fb778d644244aafb610b6fd79d9b3da81e74e65b30d6bf412e93dc9b2ed2f393'
MDL='27daff308f33ad9aafd5b3a988386b19975cdbc2d5912e2013e7a8e7f1e53847'
DECODED='3b0fe3750b44b1d5eb4d2e6f44ea298e4c2921c71bff69c2b5e29f03ad9f7b10'

def build(client,executable):
    mbd=parse_mbd(pinned(client/(FOLDER+'cityjiu02.mbd'),MBD))
    decoded=decode_csvz(pinned(client/(FOLDER+'Cityjiu02.mdlZ'),MDL))
    if hashlib.sha256(decoded).hexdigest()!=DECODED:raise ValueError('MDL decode pin')
    mdl=parse_mdl(decoded,allow_parent_rom=True)
    if (mbd['width'],mbd['height'],len(mdl['models']),len(mdl['placements']))!=(9,9,110,424):raise ValueError('Fruit map structure')
    if any(m['layers'][0][0]<0 or any(l[0]!=-1 for l in m['layers'][1:]) for m in mdl['models']):raise ValueError('Unqualified multilayer model')
    groups={}
    for p in mdl['placements']:groups.setdefault(tuple(p['block']),[]).append(p)
    def order(p):
        tile,_,dy=mdl['models'][p['fields'][0]]['layers'][0]
        return p['fields'][2]+mdl['tiles'][tile]['fields'][2]+dy
    for g in groups.values():g.sort(key=order)
    windows=[];coverage={}
    for cy in range(9):
        for cx in range(9):
            blocks=[mbd['blocks'][y*9+x] if 0<=x<9 and 0<=y<9 else None for y in range(cy-1,cy+2) for x in range(cx-1,cx+2)]
            expected=project_base_window(blocks,bytes([255])*3969);objects=[]
            if blocks[4] is not None:
                for gy in range(cy-2,cy+2):
                    for gx in range(cx-2,cx+2):
                        for p in groups.get((gx,gy),[]):
                            f=p['fields'];model=mdl['models'][f[0]];grid=model['grids'][f[5]]
                            cells=bytes(map(int,decoded[grid['start']:grid['end_exclusive']].split()))
                            points=canonical_points(model['extra_8_ints']);x,y=f[3]-cx*21+21,f[4]-cy*21+21
                            expected=apply_model_pass(expected,x,y,grid['width'],grid['height'],cells)
                            expected=apply_model_points(expected,x,y,points)
                            objects.append([x,y,grid['width'],grid['height'],*points[0],*points[1],*cells])
            tokens=[]
            for block in blocks:
                tokens.append(int(block is not None))
                if block is not None:tokens.extend(block)
            tokens.append(len(objects))
            for obj in objects:tokens.extend(obj)
            actual=subprocess.check_output([str(executable.resolve()),'--dump'],input=' '.join(map(str,tokens)),text=True,timeout=10).strip()
            if actual!=''.join('??' if v==255 else f'{v:02x}' for v in expected):raise ValueError(f'CPP projector mismatch {cx}/{cy}')
            windows.append({'block_x':cx,'block_y':cy,'origin_x':cx*21-21,'origin_y':cy*21-21,'cells_hex':actual})
            if mbd['blocks'][cy*9+cx] is not None:
                for i,v in enumerate(expected):
                    x,y=cx*21-21+i%63,cy*21-21+i//63
                    if 0<=x<189 and 0<=y<189 and v!=255:coverage.setdefault((x,y),set()).add(v)
    cells=[255]*35721
    for (x,y),values in coverage.items():cells[y*189+x]=next(iter(values)) if len(values)==1 else 254
    return {'schema':'god2-recovered-fruit-navigation-v1','area':13,'scene':12,'kind':0,'width':189,'height':189,
        'dynamic_occupancy_included':False,'cells_hex':bytes(cells).hex(),'windows':windows,
        'sources':{'mbd_sha256':MBD,'mdl_sha256':MDL,'decoded_mdl_sha256':DECODED},
        'qualification':'CPP/PYTHON static projector equality81windows; unknown/conflict reject; not NPC facing/spawn authority'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--client',type=Path,required=True);ap.add_argument('--executable',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();result=build(a.client,a.executable);a.output.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(result,indent=2)+'\n').encode('ascii');a.output.write_bytes(raw)
    print(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'windows':len(result['windows']),'coords':[(x,y,bytes.fromhex(result['cells_hex'])[y*189+x]) for x,y in ((108,110),(113,69),(69,72),(68,116))]}))
if __name__=='__main__':main()
