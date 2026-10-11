"""Pinned 97D40 producer candidate; not yet identified as NPC dialogue."""
import json
import struct
from . import current_quest_action as q


def execute(raw, selector, target, residue):
    if not 0<=selector<=0xffffffff or not 0<=target<=0xffffffff or not 0<=residue<=255:
        raise ValueError('32-bit arguments and byte residue required')
    n=q.NativeAction(raw)
    n.vm.mem_write(q.STACK,bytes([residue])*0xf000)
    n.vm.mem_write(q.SP,struct.pack('<III',q.RETURN,selector,target))
    n.setreg('ECX',q.UI);n.setreg('ESP',q.SP)
    n.phase='interaction_producer'
    end=n.run(0x97d40,q.RETURN,q.BASE+0x13370,q.BASE+0x11970,q.BASE+0x11990)
    count=n.read(q.QUEUE+q.QUEUE_COUNT,'<I')[0]
    if count>0xa00:raise AssertionError('Original queue exceeded capacity')
    return dict(returned=end==q.RETURN,stop_rva=None if end==q.RETURN else end-q.BASE,
                esp=n.getreg('ESP'),calls=n.calls,
                queued_hex=bytes(n.vm.mem_read(q.QUEUE+q.QUEUE_BYTES,count)).hex())


def report():
    raw=q.evidence()
    # Only retain independently decoded instruction boundaries, not raw E8 scans.
    callers=(0x66274,0x66642,0x7b738,0x1130a8)
    for caller in callers:
        if raw[caller]!=0xe8 or caller+5+struct.unpack_from('<i',raw,caller+1)[0]!=0x97d40:
            raise AssertionError('Pinned caller no longer targets producer')
    cases=[]
    for target in (0,1,0x12345678,0x7fffffff,0x80000000,0xffffffff):
        for residue in (0,0xa5):
            result=execute(raw,0x101,target,residue)
            expected=(b'\x6e\x01'+bytes([residue])*3+struct.pack('<I',target)
                      if target<0x80000000 else b'')
            if not result['returned'] or result['esp']!=q.SP+12 or result['queued_hex']!=expected.hex():
                raise AssertionError('Native candidate producer contract changed')
            cases.append(dict(target=target,residue=residue,**result))
    return dict(image_sha256=q.IMAGE_SHA,producer_rva='97D40',
                verified_direct_call_rvas=[f'{caller:X}' for caller in callers],cases=cases,
                scope='ORIGINAL_PRODUCER_SYNTHETIC_ARGUMENTS_NOT_NPC_IDENTIFICATION',
                open=['Meaning of operation selector and target identity',
                      'World action selection and NPC ownership/range checks',
                      'Real client interaction and server response'])


if __name__=='__main__':
    print(json.dumps(report(),indent=2))
