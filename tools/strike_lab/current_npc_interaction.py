"""Original NPC range path and post-clock request; staged state, no live UI."""
import struct
from . import current_quest_action as q

WORLD=0x60000000
POOL=WORLD+0x1539aed8


def range_path(raw, *, slot=0, identity=42, x=10, y=10, role_x=10, role_y=10, hit=0x37,
               logical_spawn=None):
    n=q.NativeAction(raw)
    n.vm.mem_map(WORLD,4096)
    n.vm.mem_map((WORLD+0xa7e05c8)&~4095,4096)
    n.vm.mem_map(POOL&~4095,0x1f000)
    n.vm.mem_map(0x51000000,0x13000)
    n.write(WORLD+0x224,'<ii',role_x,role_y)
    n.write(WORLD+0xa7e05c8,'<I',0x51000000)
    for index in range(256):n.write(POOL+0x70+index*0x1d8,'<I',0xffffffff)
    if 0<=slot<256:
        n.write(POOL+0x70+slot*0x1d8,'<I',identity)
        n.write(POOL+0x80+slot*0x1d8,'<ii',x,y)
    spawn_fields=None
    if logical_spawn is not None:
        if not 0<=slot<256 or len(logical_spawn)!=21 or logical_spawn[0]!=0x72:
            raise ValueError('Exact72 record and existing bounded slot required')
        n.vm.mem_write(q.PACKET,bytes(logical_spawn))
        n.vm.mem_protect(q.PACKET,4096,1)
        actor=POOL+0x70+slot*0x1d8
        n.setreg('ESP',q.SP);n.setreg('EDI',q.PACKET+1);n.setreg('ESI',actor);n.setreg('EBX',slot)
        n.phase='npc_spawn_scalars'
        n.run(0xcc621,q.BASE+0xcc690)
        spawn_fields=dict(identity=n.read(actor,'<I')[0],
                          coordinates=list(n.read(actor+0x10,'<II')))
    n.write(q.SP+0x10,'<I',slot)
    n.setreg('ESP',q.SP);n.setreg('ESI',WORLD);n.setreg('EBP',POOL);n.setreg('EDI',hit)
    n.phase='npc_range'
    end=n.run(0x66d75,q.BASE+0x96750,q.BASE+0x66e20)
    return dict(reached_producer=end==q.BASE+0x96750,stop_rva=end-q.BASE,spawn_fields=spawn_fields,
                target=n.read(n.getreg('ESP')+4,'<I')[0] if end==q.BASE+0x96750 else None,
                ui=n.getreg('ECX') if end==q.BASE+0x96750 else None)


def producer_after_clock(raw, *, target=42, now=1001, previous=0, pending=False):
    n=q.NativeAction(raw)
    n.write(q.SP,'<II',q.RETURN,target)
    n.write(q.SP-12,'<III',0x11111111,0x22222222,0x33333333)
    n.write(q.UI+0x86878,'<I',previous)
    n.write(q.GLOBALS,'<I',1 if pending else 0)
    n.write(q.GLOBALS+12,'<HH',2,0x1234)
    n.write(q.UI+q.CONTEXT,'<B',0x9a)
    n.setreg('ESP',q.SP-12);n.setreg('EDI',target);n.setreg('ESI',q.UI);n.setreg('EAX',now)
    n.phase='npc_producer_after_clock'
    # Starts after the unexecuted OS tick call with an explicit clock value.
    end=n.run(0x96763,q.RETURN)
    count=n.read(q.QUEUE+q.QUEUE_COUNT,'<I')[0]
    return dict(returned=end==q.RETURN,esp=n.getreg('ESP'),
                queued_hex=bytes(n.vm.mem_read(q.QUEUE+q.QUEUE_BYTES,count)).hex(),
                calls=n.calls,last_tick=n.read(q.UI+0x86878,'<I')[0],
                selected=n.read(q.UI+0x85ac0,'<I')[0],
                pending=n.read(q.GLOBALS,'<I')[0])
