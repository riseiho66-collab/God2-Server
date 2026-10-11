"""Recover previously uncreated combat functions in a transient Ghidra session.

Read-only saved project; generated decompilation belongs to a separate evidence
directory. Never patches the client or saves changes to the analysis project.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
RECON=ROOT.parent.parent/'God2-解殼EXE原始碼重建'
SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
JAVA=r'''
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.nio.charset.StandardCharsets;
public class CombatGapProducers extends GhidraScript {
 String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
 String clean(Object s){return String.valueOf(s).replace('\t',' ').replace('\n',' ');}
 public void run() throws Exception {
  String[] a=getScriptArgs();
  if(a.length!=2 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))throw new IOException("Program identity mismatch");
  File dir=new File(a[0]);DecompInterface decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
  long[] entries={0x519b40L,0x519e30L,0x51a980L};
  try(PrintWriter funcs=new PrintWriter(new File(dir,"functions.tsv"),StandardCharsets.UTF_8);
      PrintWriter instructions=new PrintWriter(new File(dir,"instructions.tsv"),StandardCharsets.UTF_8);
      PrintWriter refs=new PrintWriter(new File(dir,"references.tsv"),StandardCharsets.UTF_8)) {
   funcs.println("entry\tend\tbody_bytes\tcreated_transiently\tdecompile_completed");
   instructions.println("function\taddress\tbytes\tinstruction");refs.println("target\tfrom\tfunction\ttype");
   for(long value:entries){
    Address at=toAddr(value);Function function=getFunctionAt(at);boolean created=false;
    Function containing=getFunctionContaining(at);
    if(function==null && containing!=null)
      throw new IOException("Interior block is not a function entry: "+at+" belongs to "+containing.getEntryPoint());
    if(function==null){disassemble(at);function=createFunction(at,"RECOVERED_COMBAT_GAP_"+at);created=true;}
    if(function==null)throw new IOException("Function recovery failed "+at);
    DecompileResults result=decompiler.decompileFunction(function,90,monitor);
    funcs.printf("%s\t%s\t%d\t%b\t%b%n",at,function.getBody().getMaxAddress(),function.getBody().getNumAddresses(),created,result.decompileCompleted());
    if(result.decompileCompleted())try(PrintWriter code=new PrintWriter(new File(dir,at+".c"),StandardCharsets.UTF_8)){
      code.println("/* Transient reconstructed pseudocode, not original C++ or gameplay authority. */");code.println(result.getDecompiledFunction().getC());
    }
    InstructionIterator iterator=currentProgram.getListing().getInstructions(function.getBody(),true);
    while(iterator.hasNext()){Instruction i=iterator.next();instructions.printf("%s\t%s\t%s\t%s%n",at,i.getAddress(),hex(i.getBytes()),clean(i));}
    ReferenceIterator incoming=currentProgram.getReferenceManager().getReferencesTo(at);
    while(incoming.hasNext()){Reference r=incoming.next();Function caller=getFunctionContaining(r.getFromAddress());refs.printf("%s\t%s\t%s\t%s%n",at,r.getFromAddress(),caller==null?"UNDEFINED":caller.getEntryPoint().toString(),r.getReferenceType());}
   }
  }
  try(PrintWriter out=new PrintWriter(new File(dir,"coefficient-address-candidates.tsv"),StandardCharsets.UTF_8)){
   out.println("function\taddress\tbytes\tinstruction");InstructionIterator all=currentProgram.getListing().getInstructions(true);
   while(all.hasNext()){Instruction instruction=all.next();boolean hit=false;
    for(int op=0;op<instruction.getNumOperands();op++)for(Object item:instruction.getOpObjects(op))if(item instanceof Scalar){long v=((Scalar)item).getUnsignedValue();if(v>=0xa9ea4f0L&&v<0xa9ea640L)hit=true;}
    if(hit){Function f=getFunctionContaining(instruction.getAddress());out.printf("%s\t%s\t%s\t%s%n",f==null?"UNDEFINED":f.getEntryPoint(),instruction.getAddress(),hex(instruction.getBytes()),clean(instruction));}
   }
  }
  decompiler.dispose();try(PrintWriter receipt=new PrintWriter(new File(dir,"complete.txt"),StandardCharsets.UTF_8)){receipt.println(currentProgram.getExecutableSHA256());receipt.println("TRANSIENT_READONLY_NO_PROJECT_SAVE");}
 }
}
'''
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--entries', help='Comma-separated verified candidate hexadecimal VAs')
    a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    client=ROOT.parent/'God2/God2.exe'
    if hashlib.sha256(client.read_bytes()).hexdigest()!=SHA:raise ValueError('Current client changed')
    script=JAVA
    if a.entries:
        entries=[int(value,16) for value in a.entries.split(',')]
        if not entries or len(entries)>64 or any(not 0x401000<=entry<0x570000 for entry in entries):
            raise ValueError('Invalid bounded code candidates')
        script=script.replace('0x519b40L,0x519e30L,0x51a980L',','.join(hex(entry)+'L' for entry in entries))
    (out/'CombatGapProducers.java').write_text(script,encoding='utf-8')
    java=Path('C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin/java.exe')
    utility=Path('C:/Users/risei/.codex/tools/reverse-engineering/ghidra/ghidra_12.1.2_PUBLIC/Ghidra/Framework/Utility/lib/Utility.jar')
    command=[str(java),'-Xmx3G','-Djava.awt.headless=true','-Djava.system.class.loader=ghidra.GhidraClassLoader','-Dfile.encoding=UTF8',
        '--enable-native-access=ALL-UNNAMED','-cp',str(utility),'ghidra.Ghidra','ghidra.app.util.headless.AnalyzeHeadless',
        str(RECON/'analysis-project'),'God2-current','-process','God2.exe','-readOnly','-noanalysis','-scriptPath',str(out),
        '-postScript','CombatGapProducers.java',str(out),SHA,'-log',str(out/'ghidra.log'),'-scriptlog',str(out/'script.log')]
    (out/'command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'stdout.log').open('wb') as log:
        subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,timeout=240)
    if (out/'complete.txt').read_text('utf-8').splitlines()!=[SHA,'TRANSIENT_READONLY_NO_PROJECT_SAVE']:raise ValueError('No completed transient receipt')
    print((out/'functions.tsv').read_text('utf-8'))
if __name__=='__main__':main()
