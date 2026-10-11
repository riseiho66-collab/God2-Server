"""Static test itinerary only; the original client still executes each path call."""
from collections import deque


def agreement_window(atlas):
    presence=atlas['block_present']
    masks=[0]*(189*189)
    for w in atlas['windows']:
        cx,cy=w['block_x'],w['block_y']
        if not all(0<=x<9 and 0<=y<9 and presence[y*9+x]
                   for y in range(cy-1,cy+2) for x in range(cx-1,cx+2)):continue
        for i in range(3969):
            value=w['cells_hex'][i*2:i*2+2]
            x,y=w['origin_x']+i%63,w['origin_y']+i//63
            if value!='??' and 0<=x<189 and 0<=y<189:masks[y*189+x]|=1<<int(value,16)
    return {'origin_x':0,'origin_y':0,'side':189,
            'cells_hex':''.join({1:'00',2:'01',4:'02'}.get(mask,'??') for mask in masks)}


def east_detour(window,start,target_x=100,target_y=None):
    ox,oy=window['origin_x'],window['origin_y']
    cells=window['cells_hex']
    side=window.get('side',63)
    if side not in (63,189) or len(cells)!=side*side*2:raise ValueError('Invalid town window')
    def walkable(point):
        x,y=point[0]-ox,point[1]-oy
        return 0<=x<side and 0<=y<side and cells[(y*side+x)*2:(y*side+x)*2+2]=='01'
    if not walkable(start) or not ox<=target_x<ox+side:raise ValueError('Invalid route endpoints')
    if target_y is not None and not walkable((target_x,target_y)):
        raise ValueError('Point target is not an ordinary source-qualified cell')
    pending=deque([start]);parents={start:None}
    while pending:
        current=pending.popleft()
        if (current[0]>=target_x if target_y is None else current==(target_x,target_y)):
            route=[]
            while current is not None:
                route.append(current);current=parents[current]
            return list(reversed(route))
        for dx,dy in ((1,0),(0,1),(0,-1),(-1,0)):
            neighbor=(current[0]+dx,current[1]+dy)
            if neighbor not in parents and walkable(neighbor):
                parents[neighbor]=current;pending.append(neighbor)
    raise ValueError('No source-qualified route in fixed window')
