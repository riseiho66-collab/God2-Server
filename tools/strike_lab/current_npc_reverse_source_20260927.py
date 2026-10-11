"""Read-only NPC setter interior reachability and world-owner source frontier.

Exports selected saved instructions without analysis or project writes. Raw
relative/pointer scans are candidate censuses, not automatic code discovery.
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

START, END = 0x4ccec0, 0x4ccf75
TARGETS=(0x464910,0x46bcc0,0x4ca680,0x4ca730,0x45aa70,0x461c40,
         0x460e50,0x4619d0,0x460bf0,0x4617c0,0x45f0e0,0x45eec0,
         0x4bd9f0,0x4cdaa0)
EXTRA_JAVA=r'''
   try(PrintWriter candidates=new PrintWriter(new File(dir,"candidate-context.tsv"),StandardCharsets.UTF_8)) {
    candidates.println("candidate\tfunction\taddress\tbytes\tinstruction");
    for(long at:new long[]{0x4cce7fL,0x4cfa7dL,0x47ac02L,0x47aba6L,0x4cceb0L}) {
     Instruction i=currentProgram.getListing().getInstructionContaining(toAddr(at));
     if(i==null)continue;Function f=getFunctionContaining(i.getAddress());
     for(int k=0;k<3;k++){Instruction p=i.getPrevious();if(p==null)break;i=p;}
     for(int k=0;k<9&&i!=null;k++,i=i.getNext())candidates.printf("%08x\t%s\t%s\t%s\t%s%n",at,f==null?"UNDEFINED":f.getEntryPoint(),i.getAddress(),hex(i.getBytes()),clean(i));
    }
    candidates.flush();if(candidates.checkError())throw new IOException("Candidate context failed");
   }
   try(PrintWriter rr=new PrintWriter(new File(dir,"interior-references.tsv"),StandardCharsets.UTF_8);
       PrintWriter flows=new PrintWriter(new File(dir,"interior-flow-instructions.tsv"),StandardCharsets.UTF_8)) {
    rr.println("target\tfrom\tfunction\ttype");
    flows.println("function\taddress\tbytes\tinstruction");
    for(long at=0x4ccec0L;at<0x4ccf75L;at++) {
     ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(toAddr(at));
     while(it.hasNext()){Reference r=it.next();Function f=getFunctionContaining(r.getFromAddress());
      rr.printf("%s\t%s\t%s\t%s%n",r.getToAddress(),r.getFromAddress(),f==null?"UNDEFINED":f.getEntryPoint(),r.getReferenceType());}
    }
    InstructionIterator it=currentProgram.getListing().getInstructions(true);
    while(it.hasNext()) {
     Instruction i=it.next();boolean hit=false;
     for(Address a2:i.getFlows())if(a2.getOffset()>=0x4ccec0L&&a2.getOffset()<0x4ccf75L)hit=true;
     for(int k=0;k<i.getNumOperands();k++)for(Object o:i.getOpObjects(k)) {
      if(o instanceof Scalar){long n=((Scalar)o).getUnsignedValue();if(n>=0x4ccec0L&&n<0x4ccf75L)hit=true;}
      if(o instanceof Address){long n=((Address)o).getOffset();if(n>=0x4ccec0L&&n<0x4ccf75L)hit=true;}
     }
     if(hit){Function f=getFunctionContaining(i.getAddress());flows.printf("%s\t%s\t%s\t%s%n",f==null?"UNDEFINED":f.getEntryPoint(),i.getAddress(),hex(i.getBytes()),clean(i));}
    }
    rr.flush();flows.flush();if(rr.checkError()||flows.checkError())throw new IOException("Interior output failed");
   }
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/research/npc-reverse-source-20260927')
    p.add_argument('--reuse-export',action='store_true');a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if hashlib.sha256(CLIENT.read_bytes()).hexdigest()!=SHA or hashlib.sha256(IMAGE.read_bytes()).hexdigest()!=IMAGE_SHA:
        raise RuntimeError('Pinned input changed')
    if not a.reuse_export:
        if (out/'complete.txt').exists():raise RuntimeError('Stale receipt: choose new output')
        java=JAVA.replace('NpcPositionWriters','NpcReverseSource').replace(
            '(va>=0x4ca680 && va<=0x4ce130)||va==0x467cd0||va==0x461010','||'.join('va=='+hex(v) for v in TARGETS))
        java=java.replace('   ins.flush();refs.flush();ctx.flush();',EXTRA_JAVA+'\n   ins.flush();refs.flush();ctx.flush();')
        (out/'NpcReverseSource.java').write_text(java,encoding='utf-8')
        cmd=['C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin/java.exe','-Xmx3G','-Djava.awt.headless=true',
            '-Djava.system.class.loader=ghidra.GhidraClassLoader','-Dfile.encoding=UTF8','--enable-native-access=ALL-UNNAMED','-cp',
            'C:/Users/risei/.codex/tools/reverse-engineering/ghidra/ghidra_12.1.2_PUBLIC/Ghidra/Framework/Utility/lib/Utility.jar',
            'ghidra.Ghidra','ghidra.app.util.headless.AnalyzeHeadless',str(RECON/'analysis-project'),'God2-current',
            '-process','God2.exe','-readOnly','-noanalysis','-scriptPath',str(out),'-postScript','NpcReverseSource.java',str(out),SHA,
            '-log',str(out/'ghidra.log'),'-scriptlog',str(out/'script.log')]
        (out/'command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2),encoding='utf-8')
        with (out/'stdout.log').open('wb') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=180)
    receipt=(out/'complete.txt').read_text().splitlines()
    if receipt[0]!=SHA:raise RuntimeError('Saved program identity mismatch')
    sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
    import pefile
    import capstone
    pe=pefile.PE(str(CLIENT));m=pe.get_memory_mapped_image();prior=IMAGE.read_bytes()
    e={'client_sha256':SHA,'mapped_sha256':IMAGE_SHA,'functions':{},'verified_instruction_rows':0}
    for name in ('instructions','reference-context','pool-instruction-references','interior-flow-instructions','candidate-context'):
        rows=list(csv.DictReader((out/(name+'.tsv')).open(encoding='utf-8'),delimiter='\t'))
        for row in rows:
            va=int(row['address'],16);raw=bytes.fromhex(row['bytes']);rva=va-0x400000
            if m[rva:rva+len(raw)]!=raw or prior[rva:rva+len(raw)]!=raw:raise RuntimeError('Bytes differ '+row['address'])
            e['verified_instruction_rows']+=1
            if name=='instructions':e['functions'].setdefault(row['function'],[]).append(row)
    for entry,rows in list(e['functions'].items()):
        lo=int(rows[0]['address'],16);hi=int(rows[-1]['address'],16)+len(bytes.fromhex(rows[-1]['bytes']))
        e['functions'][entry]={'start':hex(lo),'end_exclusive':hex(hi),'raw_offset':hex(pe.get_offset_from_rva(lo-0x400000)),
            'sha256':hashlib.sha256(m[lo-0x400000:hi-0x400000]).hexdigest(),'instruction_count':len(rows)}
    e['saved_interior_references']=list(csv.DictReader((out/'interior-references.tsv').open(encoding='utf-8'),delimiter='\t'))
    raw=m[START-0x400000:END-0x400000]
    if raw!=prior[START-0x400000:END-0x400000]:raise RuntimeError('Setter changed')
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    setter=list(dis.disasm(raw,START));boundaries={i.address for i in setter}
    e['setter']={'start':hex(START),'end_exclusive':hex(END),'raw_offset':hex(pe.get_offset_from_rva(START-0x400000)),
        'sha256':hashlib.sha256(raw).hexdigest(),'instruction_count':len(setter)}
    (out/'setter-instructions.tsv').write_text('\n'.join(f'{i.address:08x}\t{i.bytes.hex()}\t{i.mnemonic} {i.op_str}' for i in setter),encoding='utf-8')
    e['raw_control_candidates']=[];e['pointer_candidates']=[]
    for sec in pe.sections:
        if sec.Name.rstrip(b'\0')!=b'.text' and not sec.Characteristics&0x20000000:continue
        data=m[sec.VirtualAddress:sec.VirtualAddress+sec.Misc_VirtualSize]
        for at in range(len(data)-6):
            op=data[at];va=0x400000+sec.VirtualAddress+at;target=None;kind=''
            if op in (0xe8,0xe9):target=(va+5+struct.unpack_from('<i',data,at+1)[0])&0xffffffff;kind='call-rel32' if op==0xe8 else 'jmp-rel32'
            elif op==0xeb or 0x70<=op<=0x7f or 0xe0<=op<=0xe3:
                target=va+2+struct.unpack_from('<b',data,at+1)[0];kind='short-control'
            elif op==0x0f and 0x80<=data[at+1]<=0x8f:
                target=(va+6+struct.unpack_from('<i',data,at+2)[0])&0xffffffff;kind='jcc-rel32'
            if target is not None and START<=target<END:
                e['raw_control_candidates'].append({'from':hex(va),'target':hex(target),'kind':kind,
                    'source_inside_setter':START<=va<END,'source_setter_boundary':va in boundaries,'target_setter_boundary':target in boundaries})
    # Include pointers to ANY interior byte, plus RVA-form values, in every
    # mapped section. A matching integer is a candidate, not pointer authority.
    for target in range(START,END):
        for value,kind in ((target,'absolute-VA'),(target-0x400000,'RVA')):
            needle=struct.pack('<I',value);at=m.find(needle)
            while at>=0:
                e['pointer_candidates'].append({'from':hex(0x400000+at),'target':hex(target),'kind':kind,'target_boundary':target in boundaries})
                at=m.find(needle,at+1)
    # The three RVA-shaped integers are instruction-byte coincidences, not
    # embedded pointer tables. Boundary proof comes from saved Ghidra context.
    e['candidate_qualification']={
        '0x4cce7f':'Final displacement byte of MOV AX,[ESI+7C] at 4CCE7C; not a short branch.',
        '0x4ccee0':'Final displacement byte of LEA ESI,[EDI+EAX*8+70] at 4CCEDD; not a short branch.',
        '0x4cfa7d':'RVA-shaped DWORD overlaps CALL 4D0750 opcode and relative operand.',
        '0x47ac02':'RVA-shaped DWORD is relative displacement of CALL 547AF7 at 47AC01.',
        '0x47aba6':'RVA-shaped DWORD is relative displacement of CALL 547AF7 at 47ABA5.'}
    pad=m[0xcceb1:0xccec0]
    if pad!=prior[0xcceb1:0xccec0] or pad!=b'\x90'*15:raise RuntimeError('Preceding padding differs')
    e['preceding_boundary']={'return_va':'0x4cceae','return_bytes':'c20400','nop_start':'0x4cceb1','nop_count':15,
        'conclusion':'Previous function returns before padding; no normal fallthrough into setter.'}
    # Pure setter prefix: proves actual arguments and signedness without map,
    # render, resource stubs or broad replay of already-qualified S2C72.
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
    vectors=[]
    for slot in (0,255,256,0xffff):
        for upper in (0,0xabcd):
            for x,y in ((126,127),(0xffff,0x8000)):
                u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,(len(m)+4095)&~4095);u.mem_write(0x400000,m)
                u.mem_map(0x20000000,0x30000);u.mem_map(0x30000000,0x20000)
                pool=0x20001000;slot_signed=struct.unpack('<h',struct.pack('<H',slot))[0];record=pool+0x70+slot_signed*0x1d8
                u.mem_write(record,bytes([0xa5])*0x1d8);esp=0x30010000
                u.mem_write(esp,struct.pack('<4I',0x60000000,slot|(upper<<16),x|(upper<<16),y|(upper<<16)))
                u.reg_write(UC_X86_REG_ESP,esp);u.reg_write(UC_X86_REG_ECX,pool)
                u.emu_start(START,0x4cceec,count=100)
                if u.reg_read(UC_X86_REG_EIP)!=0x4cceec:raise RuntimeError('Prefix bound')
                xy=struct.unpack('<2i',u.mem_read(record+0x10,8));expected=tuple(struct.unpack('<h',struct.pack('<H',v))[0] for v in (x,y))
                expected_record=bytearray([0xa5]*0x1d8);struct.pack_into('<2i',expected_record,0x10,*expected)
                if bytes(u.mem_read(record,0x1d8))!=bytes(expected_record):raise RuntimeError('Unexpected record mutation')
                vectors.append({'slot_low16':slot,'slot_signed':slot_signed,'ignored_upper16':upper,'xy_low16':[x,y],
                    'stored_xy':xy,'record_delta':hex(record-pool),'writes_only_offsets':[0x10,0x14],
                    'qualification':'synthetic mapped memory; slots -1/256 demonstrate missing guard, not valid gameplay slots'})
    e['setter_argument_vectors']=vectors
    (out/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'functions':len(e['functions']),'verified_rows':e['verified_instruction_rows'],
        'saved_interior_refs':len(e['saved_interior_references']),'raw_control_candidates':len(e['raw_control_candidates']),
        'pointer_candidates':len(e['pointer_candidates']),'setter_vectors':len(vectors)},ensure_ascii=False))

if __name__=='__main__':main()
