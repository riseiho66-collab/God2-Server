"""Read-only Ghidra/current-PE NPC writer and incoming-reference inventory.

Uses the existing saved project with -readOnly -noanalysis. Emits solely into
the dedicated evidence directory. Instruction bytes must match pinned live PE.
The reference census is bounded to saved Ghidra analysis; indirect calls and
unanalysed code are not silently claimed exhausted.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
RECON=ROOT.parent.parent/'God2-解殼EXE原始碼重建'
CLIENT=ROOT.parent/'God2/God2.exe'
SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
IMAGE=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
EXTRA_RANGES={0x4ccec0:0x4ccf75,0x4cd0e0:0x4cd121,0x4cd130:0x4cd1fb,
    0x4cd200:0x4cd265,0x4cd270:0x4cd39e,0x4cd6a0:0x4cd756,
    0x4cd860:0x4cd892,0x4cd8a0:0x4cd8ce,0x4cd960:0x4cd987,
    0x4cdbc0:0x4cdbdf,0x4cdea0:0x4cdeb9,0x4cdec0:0x4cdecc}
JAVA=r'''
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.nio.charset.StandardCharsets;
public class NpcPositionWriters extends GhidraScript {
 String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
 String clean(Object s){return String.valueOf(s).replace('\t',' ').replace('\n',' ');}
 public void run() throws Exception {
  String[] a=getScriptArgs();
  if(a.length!=2 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))throw new IOException("Saved program SHA mismatch");
  File dir=new File(a[0]);
  try(PrintWriter ins=new PrintWriter(new File(dir,"instructions.tsv"),StandardCharsets.UTF_8);
      PrintWriter refs=new PrintWriter(new File(dir,"references.tsv"),StandardCharsets.UTF_8);
      PrintWriter ctx=new PrintWriter(new File(dir,"reference-context.tsv"),StandardCharsets.UTF_8)) {
   ins.println("function\taddress\tbytes\tinstruction");refs.println("target\tfrom\tfunction\ttype");ctx.println("target\tfrom\tfunction\taddress\tbytes\tinstruction");
   FunctionIterator fs=currentProgram.getFunctionManager().getFunctions(true);int count=0;
   while(fs.hasNext()) {
    Function f=fs.next();long va=f.getEntryPoint().getOffset();
    if(!((va>=0x4ca680 && va<=0x4ce130)||va==0x467cd0||va==0x461010))continue;
    count++;
    InstructionIterator ii=currentProgram.getListing().getInstructions(f.getBody(),true);
    while(ii.hasNext()){Instruction i=ii.next();ins.printf("%s\t%s\t%s\t%s%n",f.getEntryPoint(),i.getAddress(),hex(i.getBytes()),clean(i));}
    ReferenceIterator rr=currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
    while(rr.hasNext()) {
     Reference r=rr.next();Function caller=getFunctionContaining(r.getFromAddress());String c=caller==null?"UNDEFINED":caller.getEntryPoint().toString();
     refs.printf("%s\t%s\t%s\t%s%n",f.getEntryPoint(),r.getFromAddress(),c,r.getReferenceType());
     Instruction i=getInstructionAt(r.getFromAddress());if(i==null)continue;
     Instruction start=i;
     for(int k=0;k<20;k++){Instruction prev=start.getPrevious();if(prev==null||caller==null||!caller.getBody().contains(prev.getAddress()))break;start=prev;}
     while(start!=null && start.getAddress().compareTo(i.getAddress())<=0){ctx.printf("%s\t%s\t%s\t%s\t%s\t%s%n",f.getEntryPoint(),r.getFromAddress(),c,start.getAddress(),hex(start.getBytes()),clean(start));start=start.getNext();}
    }
   }
   try(PrintWriter pools=new PrintWriter(new File(dir,"pool-instruction-references.tsv"),StandardCharsets.UTF_8)) {
    pools.println("function\taddress\tbytes\tinstruction");
    InstructionIterator all=currentProgram.getListing().getInstructions(true);
    while(all.hasNext()) {
     Instruction i=all.next();boolean match=false;
     for(int op=0;op<i.getNumOperands();op++)for(Object obj:i.getOpObjects(op))if(obj instanceof Scalar) {
      long v=((Scalar)obj).getUnsignedValue();if(v>=0x1539aed8L && v<0x153d5fd8L)match=true;
     }
     if(match){Function f=getFunctionContaining(i.getAddress());pools.printf("%s\t%s\t%s\t%s%n",f==null?"UNDEFINED":f.getEntryPoint(),i.getAddress(),hex(i.getBytes()),clean(i));}
    }
    pools.flush();if(pools.checkError())throw new IOException("Pool output failed");
   }
   ins.flush();refs.flush();ctx.flush();
   if(ins.checkError()||refs.checkError()||ctx.checkError())throw new IOException("Write failed");
   try(PrintWriter done=new PrintWriter(new File(dir,"complete.txt"),StandardCharsets.UTF_8)){done.println(a[1]);done.println(count);}
  }
 }
}
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/research/npc-position-writers-20260927')
    parser.add_argument('--reuse-export',action='store_true');args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if hashlib.sha256(CLIENT.read_bytes()).hexdigest()!=SHA:raise RuntimeError('Current PE changed')
    if hashlib.sha256(IMAGE.read_bytes()).hexdigest()!=IMAGE_SHA:raise RuntimeError('Mapped evidence changed')
    if not args.reuse_export:
        if (output/'complete.txt').exists():raise RuntimeError('Refusing stale receipt reuse; choose new output or --reuse-export')
        (output/'NpcPositionWriters.java').write_text(JAVA,encoding='utf-8')
        java=Path('C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin/java.exe')
        utility=Path('C:/Users/risei/.codex/tools/reverse-engineering/ghidra/ghidra_12.1.2_PUBLIC/Ghidra/Framework/Utility/lib/Utility.jar')
        command=[str(java),'-Xmx3G','-Djava.awt.headless=true','-Djava.system.class.loader=ghidra.GhidraClassLoader',
            '-Dfile.encoding=UTF8','--enable-native-access=ALL-UNNAMED','-cp',str(utility),'ghidra.Ghidra',
            'ghidra.app.util.headless.AnalyzeHeadless',str(RECON/'analysis-project'),'God2-current',
            '-process','God2.exe','-readOnly','-noanalysis','-scriptPath',str(output),'-postScript',
            'NpcPositionWriters.java',str(output),SHA,'-log',str(output/'ghidra.log'),'-scriptlog',str(output/'script.log')]
        (output/'command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2),encoding='utf-8')
        with (output/'stdout.log').open('wb') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=180)
    receipt=(output/'complete.txt').read_text().splitlines()
    if receipt[0]!=SHA:raise RuntimeError('Export receipt mismatch')
    sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
    import pefile
    pe=pefile.PE(str(CLIENT));mapped=pe.get_memory_mapped_image();prior=IMAGE.read_bytes()
    evidence={'client_sha256':SHA,'mapped_evidence_sha256':IMAGE_SHA,'ghidra_functions':int(receipt[1]),
        'scope':'Saved analysed instructions/references only; no claimed complete indirect-call coverage',
        'verified_instructions':0,'functions':{},'references':[]}
    for file in ('instructions.tsv','reference-context.tsv','pool-instruction-references.tsv'):
        with (output/file).open(encoding='utf-8') as stream:
            for row in csv.DictReader(stream,delimiter='\t'):
                va=int(row['address'],16);raw=bytes.fromhex(row['bytes']);rva=va-0x400000
                if mapped[rva:rva+len(raw)]!=raw or prior[rva:rva+len(raw)]!=raw:raise RuntimeError('Native instruction changed at '+row['address'])
                evidence['verified_instructions']+=1
                if file=='instructions.tsv':
                    evidence['functions'].setdefault(row['function'],[]).append(row)
    with (output/'references.tsv').open(encoding='utf-8') as stream:evidence['references']=list(csv.DictReader(stream,delimiter='\t'))
    for entry,rows in list(evidence['functions'].items()):
        start=int(rows[0]['address'],16);end=int(rows[-1]['address'],16)+len(bytes.fromhex(rows[-1]['bytes']))
        evidence['functions'][entry]={'instruction_count':len(rows),'va_start':hex(start),'va_end_exclusive':hex(end),
            'raw_file_offset':hex(pe.get_offset_from_rva(start-0x400000)),
            'range_sha256':hashlib.sha256(mapped[start-0x400000:end-0x400000]).hexdigest()}
    # Search raw executable bytes independently of recovered instruction coverage.
    # These are candidates, not newly certified instruction boundaries.
    known={(int(r['from'],16),int(r['target'],16)) for r in evidence['references']}
    targets={int(x,16) for x in evidence['functions']}|set(EXTRA_RANGES)
    raw_calls=[];pool_constants=[]
    for section in pe.sections:
        # This unpacked PE retains RW flags on original .text; relying solely
        # on IMAGE_SCN_MEM_EXECUTE would skip the entire native game image.
        if section.Name.rstrip(b'\0')!=b'.text' and not section.Characteristics&0x20000000:continue
        start=section.VirtualAddress;data=mapped[start:start+section.Misc_VirtualSize]
        for at in range(len(data)-4):
            if data[at]==0xe8:
                target=(0x400000+start+at+5+struct.unpack_from('<i',data,at+1)[0])&0xffffffff
                if target in targets:raw_calls.append({'from':hex(0x400000+start+at),'target':hex(target),
                    'saved_direct_reference':(0x400000+start+at,target) in known})
            value=struct.unpack_from('<I',data,at)[0]
            if 0x1539aed8<=value<0x153d5fd8:pool_constants.append({'operand_byte_va':hex(0x400000+start+at),
                'value':hex(value),'qualification':'raw immediate/displacement candidate; instruction context required'})
    evidence['raw_scan_sections']='Original .text (RW PE flags) plus any IMAGE_SCN_MEM_EXECUTE sections'
    evidence['raw_executable_calls']=raw_calls
    evidence['raw_pool_displacements']=pool_constants
    import capstone
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    evidence['additional_machine_code_ranges']={}
    listing=[]
    for start,end in EXTRA_RANGES.items():
        data=mapped[start-0x400000:end-0x400000]
        if data!=prior[start-0x400000:end-0x400000]:raise RuntimeError('New gap bytes differ')
        instructions=list(dis.disasm(data,start))
        if sum(i.size for i in instructions)!=len(data):raise RuntimeError('New function not fully decoded')
        pointer=struct.pack('<I',start);hits=[];offset=mapped.find(pointer)
        while offset>=0:hits.append(hex(0x400000+offset));offset=mapped.find(pointer,offset+1)
        evidence['additional_machine_code_ranges'][hex(start)]={'end_exclusive':hex(end),
            'sha256':hashlib.sha256(data).hexdigest(),'raw_offset':hex(pe.get_offset_from_rva(start-0x400000)),
            'raw_pointer_occurrences':hits,'instruction_count':len(instructions)}
        listing.extend([hex(start)]+[f'{i.address:08x}\t{i.bytes.hex()}\t{i.mnemonic} {i.op_str}' for i in instructions])
    (output/'additional-native-instructions.tsv').write_text('\n'.join(listing),encoding='utf-8')
    with (RECON/'decompiled/unresolved-code-ranges.tsv').open(encoding='utf-8') as stream:
        evidence['unresolved_adjacent_ranges']=[r for r in csv.DictReader(stream,delimiter='\t')
            if int(r['start'],16)<=0x4ce140 and int(r['end'],16)>=0x4ca680]
    # Execute only the local-marker payload builder through the first callee,
    # with no game-callee replacements. Stop before resource resolution/rendering.
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
    vectors=[]
    for kind in (0,1,255):
        for x,y in ((0,0),(1,2),(126,127),(32767,32767),(65535,65535)):
            uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(0x400000,(len(mapped)+4095)&~4095);uc.mem_write(0x400000,mapped)
            uc.mem_map(0x30000000,0x20000);esp=0x30010000
            uc.mem_write(esp,struct.pack('<4I',0x60000000,kind,x,y));uc.reg_write(UC_X86_REG_ESP,esp);uc.reg_write(UC_X86_REG_ECX,0x10000000)
            uc.emu_start(0x467cd0,0x467d33,count=1000)
            if uc.reg_read(UC_X86_REG_EIP)!=0x467d33:raise RuntimeError('Marker slice instruction bound')
            raw=bytes(uc.mem_read(uc.reg_read(UC_X86_REG_ESP)+0x18,20))
            expected=struct.pack('<5I',(-kind-1)&0xffff,0,0,0,(((x&0x7fff)|((y&0xffff)<<15))<<2)&0xffffffff)
            if raw!=expected:raise RuntimeError('Local marker builder mismatch')
            vectors.append({'kind':kind,'x_input':x,'y_input':y,'record20_hex':raw.hex(),'direction':raw[8]>>5,
                'stop_va':'0x467d33','scope':'builder before resource lookup; not full spawn renderer'})
    evidence['native_marker_builder_vectors']=vectors
    setter=[]
    for slot,x,y in ((0,126,127),(255,32767,0),(3,65535,32768)):
        uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(0x400000,(len(mapped)+4095)&~4095);uc.mem_write(0x400000,mapped)
        uc.mem_map(0x30000000,0x20000);uc.mem_map(0x20000000,0x20000);uc.mem_map(0x21000000,0x1000)
        esp=0x30010000;uc.mem_write(esp,struct.pack('<4I',0x60000000,slot,x,y));uc.mem_write(0x20000000,struct.pack('<I',0x21000000))
        uc.reg_write(UC_X86_REG_ESP,esp);uc.reg_write(UC_X86_REG_ECX,0x20000000)
        uc.emu_start(0x4ccec0,0x4ccf6b,count=1000)
        if uc.reg_read(UC_X86_REG_EIP)!=0x4ccf6b:raise RuntimeError('Setter slice instruction bound')
        actual=struct.unpack('<2i',uc.mem_read(0x20000000+0x70+slot*0x1d8+0x10,8))
        expected=tuple(struct.unpack('<h',struct.pack('<H',n))[0] for n in (x,y))
        if actual!=expected:raise RuntimeError('Unindexed setter mismatch')
        setter.append({'slot':slot,'x_arg':x,'y_arg':y,'stored_xy':actual,'stop_before':'0x4ccf6b renderer call'})
    evidence['native_unindexed_setter_vectors']=setter
    evidence['bounded_constant_tables']={}
    evidence['world_dispatch_entries']={hex(op):hex(struct.unpack_from('<I',mapped,0x6b5d4+op*4)[0])
        for op in (0x5f,0x60,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78)}
    for va,length,label in ((0x571250,128,'eight movement delta/direction rows'),(0x58a58c,2,'local marker resource selector')):
        raw=mapped[va-0x400000:va-0x400000+length]
        if raw!=prior[va-0x400000:va-0x400000+length]:raise RuntimeError('Constant table mismatch')
        evidence['bounded_constant_tables'][hex(va)]={'label':label,'bytes_hex':raw.hex(),
            'raw_offset':hex(pe.get_offset_from_rva(va-0x400000)),'sha256':hashlib.sha256(raw).hexdigest()}
    (output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'functions':len(evidence['functions']),'references':len(evidence['references']),
        'verified_instruction_rows':evidence['verified_instructions']}))


if __name__=='__main__':main()
