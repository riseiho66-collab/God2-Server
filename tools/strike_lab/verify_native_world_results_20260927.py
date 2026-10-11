"""Differential C++ vs pinned native arithmetic, plus isolated scene projection.

Never alters formal accounts, client files, input desktop or original evidence.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import current_damage_formula as native

ROOT=Path(__file__).resolve().parents[2]
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def run(exe,*args,input=None):
    result=subprocess.run([str(exe),*map(str,args)],input=input,capture_output=True,text=True,
                          timeout=30,creationflags=FLAGS)
    if result.returncode:raise RuntimeError(result.stderr.strip() or 'Native result verifier failed')
    return result.stdout.strip()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--database',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    exe=ROOT/'build-town-visibility/tests/Release/native-world-results.exe'
    proof=native.DamageDataflowProof();commands=[];expected=[];cases=[]
    for word in (0,1,32767,32768,65535,65506,1234):
        for selector in (0,1,2,3,4,5,7,8,9,20):
            actor=native.actor_snapshot(accumulators=(0xfffffff0,20))
            received=proof.receive(native.logical_record(word,selector),source=actor)
            result=list(struct.unpack('<2I',received.vm.mem_read(native.SOURCE+0xb60,8)))
            commands.append(f'acc {word} {selector} 4294967280 20');expected.append(result)
            cases.append({'kind':'acc','word':word,'selector':selector,'native':result})
    triples=((100,0xffffffe2,200),(10,0xffffffe2,200),(100,100,150),(0,0,0),
             (200,0,100),(0x7fffffff,1,0x7fffffff),(0xffffffff,2,100),
             (0,1,0xffffffff),(0x80000000,0,100),(0,0x80000000,100),
             (0x80000000,0x80000000,100),(0x7ffffffe,1,0x7fffffff),(0,0,0xffffffff))
    for channel in (0,1):
        for selected in (False,True):
            for current,delta,cap in triples:
                executed=proof.direct_scalar(channel,current,delta,cap,selected=selected)
                result=[executed.get32(native.TARGET+0xde8+channel*4)]
                commands.append(f'scalar {current} {delta} {cap}');expected.append(result)
                cases.append({'kind':'scalar','channel':channel,'selected':selected,
                              'current':current,'delta':delta,'cap':cap,'native':result})
    observed=[list(map(int,line.split())) for line in run(exe,'--oracle',input='\n'.join(commands)+'\n').splitlines()]
    if observed!=expected:raise ValueError('C++ disagrees with executed current native code')
    clone=args.output/'projection.db'
    with closing(sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro',uri=True)) as source:
        with closing(sqlite3.connect(clone)) as destination:source.backup(destination)
    projection=run(exe,'--projection',clone)
    report={'native_image_sha256':native.IMAGE_SHA256,'helper_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'cpp_equals_executed_native':True,'accumulator_cases':70,'scalar_cases':52,
            'projection':projection,'cases':cases,'formal_database_writes':0,'client_writes':0,
            'desktop_operations':0,'original_spawn_rows_recovered':0,
            'damage_generation_formula_recovered':False}
    (args.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
if __name__=='__main__':main()
