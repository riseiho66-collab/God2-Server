"""Source-only current-window reachability; never launches or modifies a client."""
import hashlib
import json
from collections import deque
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
NAV=ROOT/'artifacts/world-atlas/kunlun-4-3.json'
PIN='d429b1f94a9c1e2cf1bb8d0194213a25de22b9bb86c036a335d5c6952ddd95aa'
START=(126,126);GOAL=(50,124)

def main():
    raw=NAV.read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
    j=json.loads(raw);present=j['block_present'];windows={}
    for row in j['windows']:
        h=row['cells_hex'];windows[row['block_x'],row['block_y']]=bytes(255 if h[i:i+2]=='??' else int(h[i:i+2],16) for i in range(0,len(h),2))
    def available(cx,cy):
        return all(0<=x<12 and 0<=y<12 and present[y*12+x] for y in range(cy-1,cy+2) for x in range(cx-1,cx+2))
    def select(p,offset=0):
        cx,cy=p[0]//21,(p[1]+offset)//21
        if available(cx,cy):return cx,cy
        for y in range(cy-1,cy+2):
            for x in range(cx-1,cx+2):
                if available(x,y):return x,y
        return None
    def cell(center,p):
        if center is None:return None
        x=p[0]-center[0]*21+21;y=p[1]-center[1]*21+21
        if not 0<=x<63 or not 0<=y<63:return None
        v=windows[center][y*63+x];return None if v==255 else v
    def variants(point):
        result=[]
        for center in windows:
            if not present[center[1]*12+center[0]]:continue
            value=cell(center,point)
            if value is not None:result.append({'center':list(center),'value':value,'complete_neighborhood':available(*center)})
        return result
    def bfs(mode):
        previous={START:None};q=deque([START]);selected={}
        while q:
            before=q.popleft()
            if before==GOAL:break
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if not (dx or dy):continue
                    p=before[0]+dx,before[1]+dy
                    if p in previous or not (0<=p[0]<252 and 0<=p[1]<252):continue
                    source=p if mode.startswith('target') else before
                    if mode.endswith('floor'):center=source[0]//21,source[1]//21
                    else:center=select(source,-1 if mode.endswith('minus1') else 0)
                    if cell(center,p) not in (1,2):continue
                    previous[p]=before;selected[p]=center;q.append(p)
        path=[];p=GOAL if GOAL in previous else None
        while p is not None:path.append(p);p=previous[p]
        path.reverse();steps=[];differences=[];blocked_frontier=[]
        for p in previous:
            if p==START:continue
            observations=variants(p)
            if len({r['value'] for r in observations})>1:
                before=previous[p];center=selected[p]
                differences.append({'before':list(before),'target':list(p),'center':list(center),'byte':cell(center,p),'covering_windows':observations})
        for before in previous:
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    p=before[0]+dx,before[1]+dy
                    if not (dx or dy) or p in previous or not (0<=p[0]<252 and 0<=p[1]<252):continue
                    source=p if mode.startswith('target') else before
                    center=(source[0]//21,source[1]//21) if mode.endswith('floor') else select(source,-1 if mode.endswith('minus1') else 0)
                    blocked_frontier.append({'before':list(before),'target':list(p),'center':list(center) if center else None,'byte':cell(center,p),'distance_to_goal':max(abs(p[0]-GOAL[0]),abs(p[1]-GOAL[1]))})
        blocked_frontier.sort(key=lambda r:(r['distance_to_goal'],r['target'],r['before']))
        for before,p in zip(path,path[1:]):
            center=selected[p];observations=variants(p)
            steps.append({'before':list(before),'target':list(p),'center':list(center),'byte':cell(center,p),
                'covering_windows':observations,'byte_conflict':len({r['value'] for r in observations})>1,
                'crosses_floor_center':(before[0]//21,before[1]//21)!=(p[0]//21,p[1]//21)})
        return {'path_exists':bool(path),'displaced_steps':max(0,len(path)-1),'visited_cells':len(previous),'path':[list(p) for p in path],'steps':steps,
                'reachable_conflict_cells':differences,'nearest_blocked_frontier':blocked_frontier[:16]}
    results={mode:bfs(mode) for mode in ('current_floor','target_floor','current_native_selector','target_native_selector','current_native_selector_minus1')}
    # Execute original41350/414E0 and original46FF0 for every retained shortest
    # path step. Its native window was independently exported, not emulated here.
    sys.path.insert(0,str(ROOT/'tests/research'))
    import test_current_route_advertisement as routes
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EIP
    image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest()==routes.IMAGE_SHA
    call=routes.CurrentRouteAdvertisementTests.call
    instance=routes.CurrentRouteAdvertisementTests('runTest')
    instance.image=image;vm=instance.vm()
    mbd=(ROOT.parent/'God2/Data2/map/island03/cityi2/cityi2.mbd').read_bytes()
    assert hashlib.sha256(mbd).hexdigest()==j['sources']['mbd_sha256']
    vm.mem_write(routes.NET+8,struct.pack('<III',12,12,routes.BODY));vm.mem_write(routes.BODY,mbd[16:16+144*4])
    manager=0x3900000;owner=0x3a00000;vm.mem_map(manager,0x2000);vm.mem_map(owner,0x1000)
    vm.mem_write(manager+0x30,bytes(4));vm.mem_write(manager+0xfdc+4*4,struct.pack('<I',owner))
    checked=0
    for mode,result in results.items():
        if 'native_selector' not in mode:continue
        for step in result['steps']+result['reachable_conflict_cells']:
            p=step['target'] if mode.startswith('target') else step['before'];y=p[1]-(1 if mode.endswith('minus1') else 0)
            vm.mem_write(routes.OUTPUT,b'\xa5'*8)
            call(instance,vm,0x41350,p[0],y,routes.OUTPUT,routes.OUTPUT+4,this=routes.NET)
            assert vm.reg_read(UC_X86_REG_EIP)==routes.RETURN and vm.reg_read(UC_X86_REG_EAX)==1
            center=list(struct.unpack('<ii',vm.mem_read(routes.OUTPUT,8)));assert center==step['center']
            vm.mem_write(manager+0x103c,struct.pack('<II',center[0]*21,center[1]*21));vm.mem_write(manager+0x50,windows[tuple(center)])
            call(instance,vm,0x46ff0,*step['target'],this=manager)
            assert vm.reg_read(UC_X86_REG_EIP)==routes.RETURN and vm.reg_read(UC_X86_REG_EAX)==step['byte']
            checked+=1
    result={'schema':'god2-kunlun-parent-window-reachability-20260927-v1','source':str(NAV.relative_to(ROOT)),'source_sha256':PIN,
        'mapped_sha256':routes.IMAGE_SHA,'start':list(START),'goal':list(GOAL),'authority':'source-only window/selector/getter execution; no streaming timing, whole A* or client journey acceptance',
        'selector_contract':'original41350 signed /21; original414E0 complete3x3; fallback ascendingY thenX',
        'caller_y_contract':'original101F90 passes player(x,y+1) to459F0, which subtracts1 before41350; this caller uses player y without adjustment. Other callers differ.',
        'native_selector_getter_pairs_checked':checked,'results':results}
    output=ROOT/'artifacts/world-atlas/kunlun-parent-window-reachability-20260927.json';output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'native_steps_checked':checked,'variants':{k:{a:v[a] for a in ('path_exists','displaced_steps','visited_cells')} for k,v in results.items()}}))

if __name__=='__main__':main()
