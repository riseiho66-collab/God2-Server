"""Four current fruit-quest NPC appearance resources: isolated native loader.

Source catalog -> actual CSV/ROMZ/ROM loader/cache. No client/server process,
placement, scene geometry, packet emission or live rendered acceptance.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE
from . import current_npc_resources as native
from .omega_assets import decode_csvz
from .current_memory_catalog_layout_20260927 import CLIENT_SHA, MAPPED_SHA, GAME_SHA, PLAIN_SHA

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    client=ROOT.parent/'God2';out=ROOT/'artifacts/research/fruit-npc-resources-20260927';out.mkdir(parents=True,exist_ok=True)
    raw=(client/'God2.exe').read_bytes();require(sha(raw)==CLIENT_SHA,'Current EXE')
    current=pefile.PE(data=raw).get_memory_mapped_image()
    mapped=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(mapped)==MAPPED_SHA,'Mapped image')
    game=(client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes();plain=decode_csvz(game)
    require(sha(game)==GAME_SHA and sha(plain)==PLAIN_SHA,'Gamedata source')
    lines=plain.splitlines();start=next(i for i,r in enumerate(lines) if r.startswith(b'NPCAppearData,'))
    count=int(lines[start].split(b',')[1]);rows={int(r.split(b',')[0]):r for r in lines[start+1:start+count+1]}
    csvraw=(client/'Data2/Patch/NPC.csvZ').read_bytes();csvplain=decode_csvz(csvraw);csvlines=csvplain.splitlines()
    csvstart=int(csvlines[0].split(b',')[2])-1
    selected=[];assets={}
    for selector,expected in ((2936,23),(2937,22),(2938,37),(2939,33)):
        row=rows[selector];fields=row.split(b',');code=int(fields[2]);require(code==expected and fields[3:5]==[b'0',b'1'],'Source prefix')
        ordinal=code-1;resource=csvlines[csvstart+ordinal];path=resource.split(b',')[1].decode('ascii')
        name=Path(path.replace('\\','/')).stem.lower();assetpath=client/Path(path.replace('\\','/')).with_suffix('.ROMZ')
        packed=assetpath.read_bytes();decoded=decode_csvz(packed,limit=1024*1024)
        assets[ordinal]=(name,sha(packed),sha(decoded))
        selected.append(dict(selector=selector,source_row_hex=row.hex(),source_row_sha256=sha(row),
            code=code,flags=0x4000,resource_ordinal=ordinal,npc_csv_line=csvstart+ordinal+1,
            resource_row_hex=resource.hex(),path=path,rom_sha256=sha(packed),decoded_sha256=sha(decoded)))
    vm=Uc(UC_ARCH_X86,UC_MODE_32);vm.mem_map(native.BASE,(len(mapped)+4095)&~4095,UC_PROT_READ|UC_PROT_EXEC)
    vm.mem_write(native.BASE,mapped);vm.mem_map(native.MANAGER&~4095,4096)
    verified=set()
    def check_instruction(v,address,size,unused):
        if native.BASE<=address<native.BASE+len(mapped):
            r=address-native.BASE
            require(mapped[r:r+size]==current[r:r+size],'Executed native instruction differs from current PE: '+hex(address))
            verified.add(address)
    vm.hook_add(UC_HOOK_CODE,check_instruction)
    prior=native.ASSETS
    try:
        native.ASSETS=assets
        n=native.NativeNpcResources(vm,client,extended_decode_budget=True)
        require(n.load_csv(csvplain)==319,'Native resource catalog row count');n.configure_empty_bank()
        for slot,r in enumerate(selected):
            ordinal=r['resource_ordinal'];entry=native.TABLE+0x244e4+76*ordinal
            require(n.string(entry,64).lower()==r['path'].encode().lower(),'Native resource path')
            require(n.call(0x5f190,0,ordinal)==0xffffffff,'Expected actual unloaded native state')
            require(n.load_ordinal(ordinal)==1,'Native ROM load failed')
            require(n.call(0x5f190,0,ordinal)==slot,'Native cache slot mismatch')
            r['native_cache_slot']=slot;r['record76_hex']=bytes(vm.mem_read(entry,76)).hex()
            r['rom_header_hex']=bytes(vm.mem_read(native.ROM+slot*0x1514,0x10)).hex()
            opens=len(n.opens);require(n.load_ordinal(ordinal)==1 and len(n.opens)==opens,'Native cache hit reopens asset')
            require(not n.handles,'Native file handle leak')
        result=dict(status='PASS',client_sha256=CLIENT_SHA,mapped_sha256=MAPPED_SHA,
            gamedata_sha256=GAME_SHA,npc_csv_sha256=sha(csvraw),npc_csv_decoded_sha256=sha(csvplain),
            cases=selected,native_decodes=n.native_decodes,files_opened=n.opens,verified_instruction_addresses=len(verified),
            native_game_callee_stubs=0,platform_adapters='existing bounded CRT file I/O/decimal/malloc/free and Win32 no-files SEH namespace',
            scope='Complete native resource load/cache only. No S2C72 scene placement/render/device/click/live server-route acceptance.')
    finally:native.ASSETS=prior
    (out/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'cases':len(selected),'output':str(out)}))
if __name__=='__main__':main()
