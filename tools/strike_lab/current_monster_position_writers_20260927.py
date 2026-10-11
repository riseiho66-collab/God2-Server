"""Bounded read-only current monster-pool and movement reference census.

No client execution, project analysis/mutation, runtime or database writes.
The prior NPC census supplies only the generic Java exporter template.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from current_npc_position_writers_20260927 import JAVA, ROOT, RECON, CLIENT, SHA, IMAGE, IMAGE_SHA

TARGETS = (0x415790,0x415ab0,0x45a000,0x45a0a0,0x45a120,0x45fd80,
           0x466950,0x466b00,0x468950,0x468ae0,0x46c6a0,0x46cc00,
           0x4c3a70,0x4c3c20,0x4c3e30,0x4fadc0,0x5011c0,
           0x5024c0,0x502570,0x502700,0x5029a0,0x502b90,0x502bf0,
           0x5035b0,0x503640,0x5036b0,0x503700)
GAPS = (0x4ccec0,0x4cd0e0,0x4cd130,0x4cd200,0x4cd270,0x4cd6a0,
        0x4cd860,0x4cd8a0,0x4cd960,0x5028f0,0x502ee0,0x502f20,
        0x503010,0x5030a0,0x46cd60,0x46cd80)
GAP_RANGES = {0x46cd60:0x46cd79,0x46cd80:0x46cd8c,0x5028f0:0x502995,
              0x502ee0:0x502f1f,0x502f20:0x502fe1,0x503010:0x503093,
              0x5030a0:0x5035a9}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/research/monster-position-writers-20260927')
    p.add_argument('--reuse-export',action='store_true')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if hashlib.sha256(CLIENT.read_bytes()).hexdigest()!=SHA:raise RuntimeError('Client SHA changed')
    if hashlib.sha256(IMAGE.read_bytes()).hexdigest()!=IMAGE_SHA:raise RuntimeError('Mapped evidence SHA changed')
    if not a.reuse_export:
        if (out/'complete.txt').exists():raise RuntimeError('Choose new output; stale receipt prohibited')
        java=JAVA.replace('NpcPositionWriters','MonsterPositionWriters').replace(
            '||va==0x467cd0||va==0x461010',''.join('||va=='+hex(x) for x in TARGETS))
        (out/'MonsterPositionWriters.java').write_text(java,encoding='utf-8')
        command=['C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin/java.exe','-Xmx3G',
            '-Djava.awt.headless=true','-Djava.system.class.loader=ghidra.GhidraClassLoader','-Dfile.encoding=UTF8',
            '--enable-native-access=ALL-UNNAMED','-cp',
            'C:/Users/risei/.codex/tools/reverse-engineering/ghidra/ghidra_12.1.2_PUBLIC/Ghidra/Framework/Utility/lib/Utility.jar',
            'ghidra.Ghidra','ghidra.app.util.headless.AnalyzeHeadless',str(RECON/'analysis-project'),'God2-current',
            '-process','God2.exe','-readOnly','-noanalysis','-scriptPath',str(out),'-postScript',
            'MonsterPositionWriters.java',str(out),SHA,'-log',str(out/'ghidra.log'),'-scriptlog',str(out/'script.log')]
        (out/'command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2),encoding='utf-8')
        with (out/'stdout.log').open('wb') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=180)
    receipt=(out/'complete.txt').read_text().splitlines()
    if receipt[0]!=SHA:raise RuntimeError('Receipt identity mismatch')
    sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
    import pefile
    import capstone
    pe=pefile.PE(str(CLIENT));mapped=pe.get_memory_mapped_image();prior=IMAGE.read_bytes()
    result={'client_sha256':SHA,'mapped_sha256':IMAGE_SHA,'exported_functions':int(receipt[1]),
        'verified_instruction_rows':0,'functions':{},'references':[],'raw_calls':[],
        'scope':'Selected saved functions, raw E8 calls in original .text plus executable sections; not computed-call closure.'}
    for filename in ('instructions.tsv','reference-context.tsv','pool-instruction-references.tsv'):
        for row in csv.DictReader((out/filename).open(encoding='utf-8'),delimiter='\t'):
            rva=int(row['address'],16)-0x400000;raw=bytes.fromhex(row['bytes'])
            if mapped[rva:rva+len(raw)]!=raw or prior[rva:rva+len(raw)]!=raw:raise RuntimeError('Instruction mismatch '+row['address'])
            result['verified_instruction_rows']+=1
            if filename=='instructions.tsv':result['functions'].setdefault(row['function'],[]).append(row)
    result['references']=list(csv.DictReader((out/'references.tsv').open(encoding='utf-8'),delimiter='\t'))
    targets=set(TARGETS)|set(GAPS)|{int(x,16) for x in result['functions']}
    known={(int(x['from'],16),int(x['target'],16)) for x in result['references']}
    for sec in pe.sections:
        if sec.Name.rstrip(b'\0')!=b'.text' and not sec.Characteristics&0x20000000:continue
        data=mapped[sec.VirtualAddress:sec.VirtualAddress+sec.Misc_VirtualSize]
        for offset in range(len(data)-4):
            if data[offset]!=0xe8:continue
            va=0x400000+sec.VirtualAddress+offset
            target=(va+5+struct.unpack_from('<i',data,offset+1)[0])&0xffffffff
            if target in targets:result['raw_calls'].append({'from':hex(va),'target':hex(target),'saved_reference':(va,target) in known})
    for entry,rows in list(result['functions'].items()):
        first=int(rows[0]['address'],16);end=int(rows[-1]['address'],16)+len(bytes.fromhex(rows[-1]['bytes']))
        data=mapped[first-0x400000:end-0x400000]
        result['functions'][entry]={'start':hex(first),'end_exclusive':hex(end),'raw_offset':hex(pe.get_offset_from_rva(first-0x400000)),
            'range_sha256':hashlib.sha256(data).hexdigest(),'instructions':len(rows)}
    result['pointer_occurrences']={}
    for target in (0x4cb120,0x4cb720,0x46c6a0,0x46cc00,0x4ccec0,0x415790):
        needle=struct.pack('<I',target);hits=[];at=mapped.find(needle)
        while at>=0:hits.append(hex(0x400000+at));at=mapped.find(needle,at+1)
        result['pointer_occurrences'][hex(target)]=hits
    result['qualified_gap_ranges']={};listing=[]
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    for start,end in GAP_RANGES.items():
        raw=mapped[start-0x400000:end-0x400000]
        if raw!=prior[start-0x400000:end-0x400000]:raise RuntimeError('Gap bytes differ')
        instructions=list(dis.disasm(raw,start))
        if sum(i.size for i in instructions)!=len(raw):raise RuntimeError('Gap instruction boundary mismatch')
        result['qualified_gap_ranges'][hex(start)]={'end_exclusive':hex(end),'raw_offset':hex(pe.get_offset_from_rva(start-0x400000)),
            'sha256':hashlib.sha256(raw).hexdigest(),'instruction_count':len(instructions)}
        listing.extend([f'{i.address:08x}\t{i.bytes.hex()}\t{i.mnemonic} {i.op_str}' for i in instructions])
    (out/'qualified-gap-instructions.tsv').write_text('\n'.join(listing),encoding='utf-8')
    table=mapped[0x102fe4:0x103004]
    result['direction_table']={'va':'0x502fe4','raw_offset':hex(pe.get_offset_from_rva(0x102fe4)),
        'sha256':hashlib.sha256(table).hexdigest(),'targets':[hex(x) for x in struct.unpack('<8I',table)],
        'meaning':'Eight direction branch addresses for 502F20; NOT instructions or monster selection.'}
    result['world_dispatch']={hex(op):hex(struct.unpack_from('<I',mapped,0x6b5d4+op*4)[0])
        for op in (0x2a,0x3a,0x5d,0x5e,0x5f,0x6f,0x70,0x71,0x73,0x74,0x78,0x82)}
    result['unresolved_adjacent_ranges']=[r for r in csv.DictReader((RECON/'decompiled/unresolved-code-ranges.tsv').open(encoding='utf-8'),delimiter='\t')
        if any(int(r['start'],16)<=b and int(r['end'],16)>=a for a,b in ((0x46c6a0,0x46ce00),(0x4ca680,0x4ce140),(0x5024c0,0x503720)))]
    # Execute original movement builder to the unmodified queue entry. Sixth
    # payload byte is untouched stack memory, deliberately poisoned here.
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX
    vectors=[]
    for poison in (0x00,0x5a,0xff):
        for x,y,mode in ((0,0,0),(126,127,1),(32767,32768,8),(65535,65535,255)):
            uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(0x400000,(len(mapped)+4095)&~4095);uc.mem_write(0x400000,mapped)
            uc.mem_map(0x30000000,0x20000);uc.mem_write(0x30000000,bytes([poison])*0x20000)
            esp=0x30010000;uc.mem_write(esp,struct.pack('<4I',0x60000000,x,y,mode));uc.reg_write(UC_X86_REG_ESP,esp)
            uc.emu_start(0x415790,0x4132e0,count=100)
            if uc.reg_read(UC_X86_REG_EIP)!=0x4132e0:raise RuntimeError('Builder did not reach queue bound')
            args=struct.unpack('<4I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),16));raw=bytes(uc.mem_read(args[2],args[3]))
            if args[1]!=0x2e or args[3]!=6 or raw!=struct.pack('<HHBB',x,y,mode,poison):raise RuntimeError('Movement wire mismatch')
            vectors.append({'x':x,'y':y,'mode':mode,'stack_poison':poison,'opcode':args[1],'payload_hex':raw.hex()})
    result['movement_builder_vectors']=vectors
    constructors=[]
    for entry,existing_stop,new_stop in ((0x4cb120,0x4cb265,0x4cb492),(0x4cb720,0x4cb841,0x4cba6b)):
        for existing in (False,True):
            for facing in range(8):
                for x,y in ((0,0),(126,127),(32767,32767),(32768,65535)):
                    uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(0x400000,(len(mapped)+4095)&~4095);uc.mem_write(0x400000,mapped)
                    uc.mem_map(0x30000000,0x20000);uc.mem_map(0x20000000,0x20000)
                    pool=0x20000000;slot=3 if existing else 0;record=pool+0x70+slot*0x1d8
                    for i in range(256):uc.mem_write(pool+0x70+i*0x1d8,struct.pack('<I',0xffffffff))
                    if existing:
                        uc.mem_write(record,struct.pack('<I',123))
                        uc.mem_write(record+8,struct.pack('<H',0xffff))
                    payload=struct.pack('<5I',123|(facing<<29),0,(((x&0x7fff)|((y&0x7fff)<<15))<<2)&0xffffffff,0,0)
                    uc.mem_write(0x30011000,payload);esp=0x30010000
                    uc.mem_write(esp,struct.pack('<8I',0x60000000,0x30012000,0x30011000,0,0,0,0,0))
                    uc.reg_write(UC_X86_REG_ESP,esp);uc.reg_write(UC_X86_REG_ECX,pool)
                    stop=existing_stop if existing else new_stop
                    uc.emu_start(entry,stop,count=10000)
                    if uc.reg_read(UC_X86_REG_EIP)!=stop:raise RuntimeError('Constructor instruction bound')
                    actual_id=struct.unpack('<I',uc.mem_read(record,4))[0]
                    actual_facing=struct.unpack('<H',uc.mem_read(record+8,2))[0]
                    xy=struct.unpack('<2I',uc.mem_read(record+0x10,8))
                    if (actual_id,actual_facing,xy)!=(123,facing,(x&0x7fff,y&0x7fff)):raise RuntimeError('Constructor decode mismatch')
                    constructors.append({'entry':hex(entry),'existing':existing,'facing':facing,'input_xy':[x,y],
                        'stored_xy':xy,'identity':actual_id,'stop_before_map_render':hex(stop)})
    result['native_constructor_prefix_vectors']=constructors
    (out/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'functions':result['exported_functions'],'verified_rows':result['verified_instruction_rows'],
        'references':len(result['references']),'raw_calls':len(result['raw_calls']),'native_vectors':len(vectors)+len(constructors)},ensure_ascii=False))

if __name__=='__main__':main()
