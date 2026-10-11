"""Build-matched original x86 occupied bank swap; emulator is not server authority."""
import hashlib,json,struct
import pefile
from pathlib import Path
from tools.strike_lab.current_bank_items_20261002 import ItemsOracle,ROOT
from tools.strike_lab.current_party_20261002 import UI,BODY
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths

def prove():
    raw=qualified_image();exe=(ROOT.parent/'God2/God2.exe').read_bytes()
    mapped=pefile.PE(data=exe).get_memory_mapped_image()
    regions=((0x471610,0x471760),(0x4719b0,0x471ce0),(0x471e50,0x472210),(0x497510,0x497650))
    for a,b in regions:assert mapped[a-0x400000:b-0x400000]==raw[a-0x400000:b-0x400000],hex(a)
    assert NativeLengths(raw).query(0x48)[0]==29
    cases=[]
    def passed(case,**kw):cases.append({'case':case,**kw})
    def oracle():
        o=ItemsOracle(raw)
        # Qualified external item catalog fixture, not reconstructed authority.
        o.put(0x32000000+0xb2d40+3108*4,'<I',0x33000000)
        return o
    def cell(item,quantity,source,seed):
        meta=struct.pack('<HH',item,0)+bytes((seed+i)%256 for i in range(4,20))
        return bytes([quantity,source,seed,seed+1])+meta
    def apply(o,page,slot,record):
        body=bytes([page,0x91,0x92,0x93,record[0],slot,0x81,0x82])+record[4:]
        o.call(0x471e50,BODY,body=body)
    for page in (0,1,2):
        for source,dest in ((2,3),(3,2),(2,49),(49,2)):
            for quantities in ((3,7),(127,1),(1,127),(127,127)):
                for same_id in (False,True):
                    o=oracle();o.put(UI+0x839a4,'<I',page);o.put(UI+0x83994,'<h',source)
                    left=cell(3107,quantities[0],source,0x21)
                    right=cell(3107 if same_id else 3108,quantities[1],dest,0x41)
                    o.vm.mem_write(o.cell(page,source),left);o.vm.mem_write(o.cell(page,dest),right)
                    o.call(0x4719b0,dest,1)
                    request=b'\x65'+struct.pack('<HBBBB',3793,page,source,dest,1)
                    assert o.queued==[request]
                    assert o.read(o.cell(page,source),24)==right and o.read(o.cell(page,dest),24)==left
                    assert not o.visible(8)
                    passed('65_occupied_swap_complete24_not_merge',page=page,source=source,destination=dest,counts=quantities,same_id=same_id,request=request.hex(),left=left.hex(),right=right.hex())
                    # Accepted absolute48 corrects slot marker, replaces full20meta,
                    # keeps native opaque reserved bytes inherited through swap.
                    apply(o,page,source,right);apply(o,page,dest,left)
                    a=o.read(o.cell(page,source),24);b=o.read(o.cell(page,dest),24)
                    assert a==bytes([right[0],source])+right[2:] and b==bytes([left[0],dest])+left[2:]
                    passed('48_accept_full20meta_count_and_canonical_slot',page=page,source=source,destination=dest)
                    # Rejection restores authority-controlled qty/id/full20meta
                    # and index; raw2/3 are opaque native fields, not on wire48.
                    apply(o,page,source,left);apply(o,page,dest,right)
                    a=o.read(o.cell(page,source),24);b=o.read(o.cell(page,dest),24)
                    assert a==left[:2]+right[2:4]+left[4:]
                    assert b==right[:2]+left[2:4]+right[4:]
                    passed('48_reject_restores_wire_fields_reserved2_3_remain_native',page=page,source=source,destination=dest)
    o=oracle();o.put(UI+0x83994,'<h',2)
    left=cell(3107,3,2,0x21);right=cell(3108,7,3,0x41)
    o.vm.mem_write(o.cell(0,2),left);o.vm.mem_write(o.cell(0,3),right)
    for source,dest in ((2,3),(3,2),(2,3),(3,2)):
        o.put(UI+0x83994,'<h',source);o.call(0x4719b0,dest,1)
    assert o.read(o.cell(0,2),24)==left and o.read(o.cell(0,3),24)==right
    passed('four_native_reverse_swaps_no_loss_all24')
    result={'scope':'original x86 emulator only; external catalog/presentation helpers are fixtures; not server authority or live acceptance',
      'passed':len(cases),'failed':0,'cases':cases,'client_sha256':hashlib.sha256(exe).hexdigest(),'mapped_sha256':hashlib.sha256(raw).hexdigest(),
      'matched_regions':[[hex(a),hex(b)] for a,b in regions],
      'contract':'65 logical7 targetWORD pageBYTE sourceBYTE destinationBYTE marker1; actual4719B0 swaps whole24-byte records even occupied, no merge',
      '48_restore_scope':'qtyBYTE and canonical slotBYTE plus complete20metadata replaced; bytes2/3 reserved not carried by48 and remain native',
      'unproved':['server authority eligibility and provenance','original merge rules','live UI sprite/count acceptance']}
    out=ROOT/'artifacts/research/native-bank-swap-20261002/oracle.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps({'passed':len(cases),'failed':0,'evidence':str(out)}));return result
if __name__=='__main__':prove()
