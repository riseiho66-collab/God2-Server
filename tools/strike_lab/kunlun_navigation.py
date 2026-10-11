"""Pinned CityI2 static passability windows; candidate coordinates are not native spawn rules."""
import argparse
from collections import Counter,deque
import hashlib
import json
from pathlib import Path
import re
import subprocess

from .omega_assets import decode_csvz
from .outdoor_mbd import parse_mbd,project_base_window,apply_model_pass,apply_model_points
from .town_navigation import canonical_points,pinned
from .world_atlas import parse_catalog

ROOT=Path(__file__).resolve().parents[2]
FOLDER='Data2/map/Island03/CityI2/'
PINS={'cityi2.mbd':'eba7aa7ae1ddc0381c7fe30d452fa251345aa9310386948b5eaf080c37d78e59',
      'cityi2.mbdZ':'e6e12fd3ffe4d87d91205d9d00c02b8960238609c1248ad0e488de4eb8630ce2',
      'cityi2.mdlZ':'cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc',
      'cityi2.mdtZ':'292d0011561d97214fd77adcd0e0121a31b491b13bb26309c96fe4617630695e'}
MDL_DECODED='bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f'
CATALOG_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
NATIVE_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)

def parse_city_mdl(raw):
    """Same observed v1.6 grammar as town parser, retaining actual zero-size grids.

    Zero-size grids are not replaced with fake cells. Used empty grids are
    accepted only when both special points are inactive; native47440 then has
    neither a pass-cell write nor a point write for that placement.
    """
    require(len(raw)<4*1024*1024 and b'\0' not in raw,'MDL bounds')
    lines=raw.splitlines(keepends=True)
    require(all(row.endswith(b'\r\n') and len(row)<=4096 for row in lines),'MDL lines')
    at=0
    def line():
        nonlocal at
        require(at<len(lines),'Truncated MDL')
        result=lines[at][:-2];at+=1;return result
    def ints(row,count=None):
        tokens=row.split()
        require((count is None or len(tokens)==count) and all(re.fullmatch(rb'-?[0-9]{1,10}',t) for t in tokens),'MDL integers')
        values=list(map(int,tokens));require(all(-2**31<=v<2**31 for v in values),'MDL integer range');return values
    def section(name,maximum):
        fields=line().split();require(len(fields)==2 and fields[0]==name,'MDL section')
        count=ints(fields[1],1)[0];require(0<count<=maximum,'MDL section count');return count
    require(line()==b'MDL v1.6','MDL version')
    roms=[line() for _ in range(section(b'ROMFILE',128))]
    require(all(re.fullmatch(rb'[A-Za-z0-9_]+\.[Rr][Oo][Mm]',s) for s in roms),'ROM path')
    tiles=[]
    for _ in range(section(b'TileModel',512)):
        fields=line().split();require(len(fields)==6,'Tile shape')
        values=ints(b' '.join(fields[1:]),5);require(0<=values[3]<len(roms),'ROM index');tiles.append(values)
    models=[]
    for _ in range(section(b'ModelDat',512)):
        layers=[ints(line(),3) for _ in range(3)]
        require(all(-1<=l[0]<len(tiles) for l in layers),'Layer index')
        frames=ints(line());require(frames and 1<=frames[0]<=10 and len(frames)==1+2*frames[0],'Frames')
        points=canonical_points(ints(line(),8));require(line()==b'Pass','Pass marker');grids=[]
        for _ in range(frames[0]):
            width,height=ints(line(),2);require(0<=width<=512 and 0<=height<=512,'Pass dimensions')
            cells=[]
            for _ in range(height):cells.extend(ints(line(),width))
            require(all(0<=v<=255 for v in cells),'Pass byte')
            grids.append((width,height,bytes(cells)))
        models.append(dict(layers=layers,points=points,grids=grids))
    require(line()==b'Model','Model marker');placements=[]
    while at<len(lines):
        x,y,count=ints(line(),3);require(0<=x<128 and 0<=y<128 and 0<count<=4096,'Block')
        for _ in range(count):
            fields=line().split();require(len(fields) in (10,11),'Placement shape')
            values=ints(b' '.join(fields[:9]),9)+ints(fields[-1],1)
            require((values[8]==0 and len(fields)==10) or
                    (values[8]==1 and len(fields)==11 and re.fullmatch(rb'[A-Za-z0-9_\\./-]{1,255}',fields[9])),'Attachment')
            require(0<=values[0]<len(models) and 0<=values[5]<len(models[values[0]]['grids']),'Placement model/frame')
            placements.append(dict(block=(x,y),fields=values))
    require(len(placements)<=20000,'Placement bound')
    return tiles,models,placements

def build_navigation(client,executable):
    client=Path(client).resolve();binary=Path(executable).resolve()
    sources={name:pinned(client/FOLDER/name,pin) for name,pin in PINS.items()}
    require(decode_csvz(sources['cityi2.mbdZ'])==sources['cityi2.mbd'],'Plain/compressed MBD differ')
    decoded=decode_csvz(sources['cityi2.mdlZ']);require(sha(decoded)==MDL_DECODED,'MDL decode pin')
    mdt=decode_csvz(sources['cityi2.mdtZ']);require(b'MAPNUM 12 12\r\n' in mdt,'MDT dimensions')
    catalog=parse_catalog(decode_csvz(pinned(client/'Data2/Patch/Comm/gamedata.csvZ',CATALOG_SHA)))
    rows=[row for row in catalog if (row['area'],row['scene'])==(4,3)]
    require(len(rows)==1 and rows[0]['kind']==0 and rows[0]['asset_stem'].lower()=='cityi2' and
            rows[0]['mdt_relative'].lower()=='data2/map/island03/cityi2/cityi2.mdt','Kunlun selector changed')
    mbd=parse_mbd(sources['cityi2.mbd']);require((mbd['width'],mbd['height'])==(12,12),'MBD size')
    tiles,models,placements=parse_city_mdl(decoded)
    require(all(m['layers'][0][0]>=0 and all(l[0]==-1 for l in m['layers'][1:]) for m in models),'Only qualified single-layer models')
    groups={};empty=[]
    for p in placements:
        model=models[p['fields'][0]];w,h,_=model['grids'][p['fields'][5]]
        if w==0 or h==0:
            require(all(point[0]<0 for point in model['points']),'Empty grid has active point: needs C++ support')
            empty.append(p);continue
        groups.setdefault(p['block'],[]).append(p)
    for group in groups.values():group.sort(key=lambda p:p['fields'][2]+tiles[models[p['fields'][0]]['layers'][0][0]][2]+models[p['fields'][0]]['layers'][0][2])
    windows=[];coverage={}
    for cy in range(12):
        for cx in range(12):
            blocks=[mbd['blocks'][y*12+x] if 0<=x<12 and 0<=y<12 else None
                    for y in range(cy-1,cy+2) for x in range(cx-1,cx+2)]
            expected=project_base_window(blocks,bytes([255])*3969);objects=[]
            if blocks[4] is not None:
                for gy in range(cy-2,cy+2):
                    for gx in range(cx-2,cx+2):
                        for p in groups.get((gx,gy),[]):
                            f=p['fields'];m=models[f[0]];w,h,cells=m['grids'][f[5]]
                            x,y=f[3]-cx*21+21,f[4]-cy*21+21
                            expected=apply_model_points(apply_model_pass(expected,x,y,w,h,cells),x,y,m['points'])
                            objects.append([x,y,w,h,*m['points'][0],*m['points'][1],*cells])
            tokens=[]
            for block in blocks:
                tokens.append(int(block is not None))
                if block is not None:tokens.extend(block)
            tokens.append(len(objects))
            for obj in objects:tokens.extend(obj)
            cpp=subprocess.run([str(binary),'--dump'],input=' '.join(map(str,tokens)),text=True,capture_output=True,check=True,timeout=15).stdout.strip()
            require(cpp==''.join('??' if v==255 else f'{v:02x}' for v in expected),f'C++ projection mismatch {cx},{cy}')
            windows.append(dict(block_x=cx,block_y=cy,origin_x=cx*21-21,origin_y=cy*21-21,cells_hex=cpp,
                known_cells=sum(v!=255 for v in expected),sha256=sha(cpp.encode('ascii'))))
            for y in range(63):
                for x in range(63):
                    ax,ay=cx*21-21+x,cy*21-21+y;value=expected[y*63+x]
                    if blocks[4] is not None and value!=255 and 0<=ax<252 and 0<=ay<252:
                        coverage.setdefault((ax,ay),set()).add(value)
    consistent={xy:next(iter(values)) for xy,values in coverage.items() if len(values)==1}
    eligible=[]
    for (x,y),value in consistent.items():
        if value==1 and all(consistent.get((x+dx,y+dy))==1 for dx in range(-2,3) for dy in range(-2,3)):
            eligible.append((abs(x-126)+abs(y-126),x,y))
    require(eligible,'No qualified central 5x5 candidate')
    _,sx,sy=min(eligible);queue=deque([(sx,sy)]);connected={(sx,sy)}
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            xy=(x+dx,y+dy)
            if xy not in connected and consistent.get(xy)==1:connected.add(xy);queue.append(xy)
    import pefile
    current=(client/'God2.exe').read_bytes();require(sha(current)==CLIENT_SHA,'Current EXE pin')
    old=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(old)==NATIVE_SHA,'Native image pin');pe=pefile.PE(data=current)
    native=pe.get_data(0x47440,0x310);require(native==old[0x47440:0x47750],'Static projector instructions changed')
    return dict(schema='god2-recovered-kunlun-navigation-v1',area=4,scene=3,kind=0,side=63,
        block_width=12,block_height=12,unknown_marker='??',block_present=[b is not None for b in mbd['blocks']],
        sources=dict(mbd=FOLDER+'cityi2.mbd',mbd_sha256=PINS['cityi2.mbd'],mdl=FOLDER+'cityi2.mdlZ',
            mdl_sha256=PINS['cityi2.mdlZ'],mdl_decoded_sha256=MDL_DECODED,asset_pins=PINS,
            catalog_sha256=CATALOG_SHA,catalog_row=rows[0],cpp_projector_sha256=sha(binary.read_bytes()),
            current_client_sha256=CLIENT_SHA,native_image_sha256=NATIVE_SHA,static_projector_rva='47440..47750',
            static_projector_span_sha256=sha(native)),
        structure=dict(tiles=len(tiles),models=len(models),placements=len(placements),single_layer_models_verified=True,
            zero_grid_noop_placements=len(empty),zero_grid_noop_details=[dict(model=p['fields'][0],
                frame=p['fields'][5],x=p['fields'][3],y=p['fields'][4],
                dimensions=list(models[p['fields'][0]]['grids'][p['fields'][5]][:2]),
                points=models[p['fields'][0]]['points']) for p in empty]),
        cross_window=dict(known_coordinates=len(coverage),consistent_coordinates=len(consistent),
            conflicts=[dict(x=x,y=y,values=sorted(values)) for (x,y),values in sorted(coverage.items()) if len(values)>1],
            consistent_value_counts=dict(Counter(consistent.values()))),
        candidate=dict(x=sx,y=sy,selection='Nearest geometric center with consistent native static value1 throughout 5x5',
            connected_cardinal_value1_cells=len(connected),native_birth_coordinate=False,
            scope='ISOLATED_LAB_CANDIDATE_NOT_NATIVE_BIRTH'),
        qualification='STATIC_CPP_PYTHON_MATCH; EXISTING_NATIVE_PROJECTOR_BYTES_MATCH; NO_LIVE_ACCEPTANCE',
        dynamic_occupancy_included=False,runtime_validated=False,windows=windows)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--client',type=Path,required=True)
    ap.add_argument('--executable',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();require(not args.output.resolve().is_relative_to(args.client.resolve()),'Output within client')
    report=build_navigation(args.client,args.executable);args.output.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(report,indent=2)+'\n').encode('ascii');args.output.write_bytes(raw)
    print(json.dumps(dict(sha256=sha(raw),windows=len(report['windows']),candidate=report['candidate'],structure=report['structure'],
        conflicts=len(report['cross_window']['conflicts']),known=report['cross_window']['known_coordinates'])))

if __name__=='__main__':main()
