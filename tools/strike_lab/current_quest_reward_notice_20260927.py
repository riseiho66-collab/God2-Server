"""Compiled C++ reward notice -> current native world02 consumer/chat rings.

Notification only, not total EXP/reputation or progression synchronization.
No game process, server, DB, screenshot or desktop operation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
from .current_equipment_rejection_20260927 import (
    RejectionOracle, NativeItemMetadata, PIN, pefile, require, UI, SLOTS,
    PACKET, SP, ROLE, VISIBLE, CATALOG, UC_PROT_READ, UC_PROT_WRITE,
    MESSAGE_SHA, DECODED_SHA, decode_csvz, x)
from .current_item_transition import COMPANION

def compile_codec(out):
    out.mkdir(parents=True,exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installation=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True,timeout=30).strip()
    require(bool(installation),'MSVC installation')
    vcvars=Path(installation)/'VC/Auxiliary/Build/vcvars64.bat'
    settings=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True,timeout=30)
    env=dict(line.split('=',1) for line in settings.splitlines() if '=' in line and not line.startswith('='))
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    require(bool(compiler),'MSVC compiler')
    exe=out/'reward-notice.exe'
    result=subprocess.run([compiler,'/nologo','/std:c++20','/EHsc','/W4','/WX','/I'+str(ROOT/'src'),
        str(ROOT/'tests/test_recovered_quest_reward_notice.cpp'),'/Fe:'+str(exe),'/Fo:'+str(out/'reward-notice.obj')],
        cwd=out,env=env,capture_output=True,text=True,timeout=60)
    require(result.returncode==0,result.stdout+result.stderr)
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
    require(result.returncode==0 and result.stdout.strip()=='PASS reward notice codec','C++ standalone gate')
    return exe

def verify(exe):
    raw=(ROOT.parent/'God2/God2.exe').read_bytes();require(hashlib.sha256(raw).hexdigest()==PIN,'Current PE')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    require(struct.unpack_from('<I',image,0x1324+8)[0]==0x401234 and image[0x1234:0x123a]==bytes.fromhex('b817000000c3'),'02 length23')
    source=(ROOT.parent/'God2/Data2/Patch/Comm/message.csvZ').read_bytes();plain=decode_csvz(source)
    require(hashlib.sha256(source).hexdigest()==MESSAGE_SHA and hashlib.sha256(plain).hexdigest()==DECODED_SHA,'Source identity')
    lines=plain.splitlines();start=lines.index(b'SystemMessage,1950')
    templates={};sources=[]
    for key,expected in ((626,'得到 %s 名聲值'),(644,'你獲得 %s 經驗值。')):
        row=lines[start+key];parts=row.split(b',')
        require(parts[:2]==[str(key).encode(),b'1'] and parts[2]==expected.encode('cp950'),'Qualified message row')
        templates[key]=parts[2];sources.append(dict(id=key,line=start+key+1,row_hex=row.hex(),sha256=hashlib.sha256(row).hexdigest()))
    loader=NativeItemMetadata()
    definitions={key:loader.item_row('WPN',key-1) for key in (1,2)}
    n=RejectionOracle(image,definitions,templates[626]);v=n.vm
    v.mem_protect(CATALOG,0x20000,UC_PROT_READ|UC_PROT_WRITE)
    for i,(key,template) in enumerate(templates.items()):
        at=CATALOG+0x11000+i*0x1000
        v.mem_write(at,template+b'\0');v.mem_write(CATALOG+(key-1)*16,struct.pack('<IIII',1,at,at,at))
    v.mem_protect(CATALOG,0x20000,UC_PROT_READ)
    # Distinct poisoned role, companions and 50 item slots are preservation
    # sentinels, not valid character progression values or player grants.
    v.mem_write(ROLE,bytes((i*7+19)&255 for i in range(0x5000)))
    cases=[]
    for key,template in templates.items():
        for amount in (1,400,1500,2000,3000,999999999999999):
            logical=bytes.fromhex(subprocess.check_output([str(exe),'--dump',str(key),str(amount)],text=True,timeout=5).strip())
            require(len(logical)==23,'Compiled codec logical width')
            for private in (0,1):
                n.reset_chat(private);n.set_pending(1)
                role=bytes(v.mem_read(ROLE,0x5000));slots=bytes(v.mem_read(SLOTS,1200))
                god_pet=bytes(v.mem_read(COMPANION,0x22000))
                v.mem_write(PACKET,logical);v.reg_write(x.UC_X86_REG_EBP,UI-0xa7f2f6c)
                v.reg_write(x.UC_X86_REG_EBX,PACKET);v.reg_write(x.UC_X86_REG_ESP,SP)
                v.emu_start(0x46929e,0x46b517,count=500000)
                require(v.reg_read(x.UC_X86_REG_EIP)==0x46b517 and v.reg_read(x.UC_X86_REG_ESP)==SP,'Native world return')
                expected=template.replace(b'%s',b'/c3'+str(amount).encode()+b'/c9')
                require(n.formatted==[(4,0xff80ff,expected)],'Native notice bytes')
                archive=n.ring(UI+0x39e20);visible=n.ring(VISIBLE)
                require(archive['count']==1 and archive['rows'][0]['raw_hex']==(b'1A4'+expected).hex(),'Native archive')
                require(visible==archive if private==0 else visible['count']==0,'Visible/private delivery')
                require(bytes(v.mem_read(ROLE,0x5000))==role and bytes(v.mem_read(SLOTS,1200))==slots and n.pending()==1,'Unexpected state mutation')
                require(bytes(v.mem_read(COMPANION,0x22000))==god_pet,'Unexpected God/pet cache mutation')
                cases.append(dict(message=key,amount=amount,private_chat=private,logical_hex=logical.hex(),formatted_hex=expected.hex(),archive=archive))
    return dict(status='PASS',client_sha256=PIN,codec_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        source_sha256=MESSAGE_SHA,decoded_sha256=DECODED_SHA,source_rows=sources,cases=cases,
        native_game_callee_stubs=0,total_exp_or_reputation_synchronized=False,
        scope='Compiled C++ output -> complete native world02/format/archive/visible-ring; widget absent sentinel. No live-client acceptance; no role/God/pet progression mutation.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--codec',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/research/quest-reward-notice-20260927')
    a=p.parse_args();exe=a.codec or compile_codec(a.output/'build');r=verify(exe)
    a.output.mkdir(parents=True,exist_ok=True);(a.output/'evidence.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':r['status'],'cases':len(r['cases']),'output':str(a.output)}))
if __name__=='__main__':main()
