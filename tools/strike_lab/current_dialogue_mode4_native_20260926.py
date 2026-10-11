"""Bounded current-PE mode4 MultiMessage1434 evidence; no game/DB operations.
Run as python -m tools.strike_lab.current_dialogue_mode4_native_20260926 --output PATH.
Requires pefile and unicorn (scoped artifacts/tooling/crypto-oracle-python supported).
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
import pefile
from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn import x86_const as R
from .omega_assets import decode_csvz
SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
SOURCE_SHA='441b2828b6edccdb36098c3aba9d6e631ae351d82e685969d34758b67fe6c10f'
BASE,UI,RESOURCE,TABLE,STRINGS,PACKET,STACK,QUEUE=0x400000,0x10000000,0x20000000,0x20100000,0x20200000,0x30000000,0x40000000,0x50000000
SP,RETURN=STACK+0x18000,STACK+0x1f000
KEY=1434
TABLE_COUNT=2995
SOURCE_PINS={'MultiMessage01.csvZ':'0d573b607f477c0da53c2efa7aeb1881bcb1d38941cf36472cd9a506d13f9985','MultiMessage02.csvZ':SOURCE_SHA,'MultiMessage03.csvZ':'e0551afec2108f478f27f2364bd15bd8d7ff999c8f12a087b320d06d23659e4d'}

def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def fixture(mode=4,request=0x1234,reply=2,context=0x9a,key=KEY,tail=b'\0'):
    return b'\x7a'+struct.pack('<HBBHHH16s',27+len(tail),mode,context,request,key,reply,bytes(16))+tail

class Native:
    def __init__(self,pe,strings):
        self.vm=Uc(UC_ARCH_X86,UC_MODE_32)
        mapped=pe.get_memory_mapped_image()
        self.vm.mem_map(BASE,(max(len(mapped),pe.OPTIONAL_HEADER.SizeOfImage)+4095)&~4095)
        self.vm.mem_write(BASE,mapped)
        for a,n in [(UI,0x240000),(RESOURCE,0x100000),(TABLE,0x10000),(STRINGS,0x10000),(PACKET,0x1000),(STACK,0x20000),(QUEUE,0x5000)]:self.vm.mem_map(a,n)
        self.write(UI+0xcff70,'I',RESOURCE);self.write(UI+0x86874,'I',QUEUE)
        self.write(UI+0x232dee,'h',0)
        self.write(RESOURCE+0xb2c50,'h',TABLE_COUNT);self.write(RESOURCE+0xb2c54,'I',TABLE)
        self.write(TABLE+(KEY-1)*8,'B',len(strings));self.write(TABLE+(KEY-1)*8+4,'I',STRINGS)
        ptr=STRINGS+0x100
        self.textptr=ptr
        for i,s in enumerate(strings):
            self.write(STRINGS+i*4,'I',ptr);self.vm.mem_write(ptr,s+b'\0');ptr+=len(s)+1
        # Modes1/2/3 test NPCMission namespace independently of MultiMessage.
        self.write(RESOURCE+0xb2c48,'h',KEY);self.write(RESOURCE+0xb2c4c,'I',TABLE+0x8000)
        self.write(TABLE+0x8000+(KEY-1)*4,'I',STRINGS+0xf000)
        self.vm.mem_write(STRINGS+0xf000,b'NPCMission sentinel\0')
        self.stops=set();self.packet_reads=[];self.calls=[];self.selected_text=None
        self.vm.hook_add(UC_HOOK_CODE,self.code)
        self.vm.hook_add(UC_HOOK_MEM_READ,self.readhook)
    def write(self,a,f,*v):self.vm.mem_write(a,struct.pack('<'+f,*v))
    def read(self,a,f):return struct.unpack('<'+f,self.vm.mem_read(a,struct.calcsize('<'+f)))[0]
    def reg(self,n):return self.vm.reg_read(getattr(R,'UC_X86_REG_'+n))
    def setreg(self,n,v):self.vm.reg_write(getattr(R,'UC_X86_REG_'+n),v)
    def code(self,vm,a,size,ctx):
        if a in self.stops:vm.emu_stop();return
        if a==0x4c81f0:self.selected_text=self.read(self.reg('ESP')+4,'I')
        if a==0x4132e0:
            sp=self.reg('ESP');op=self.read(sp+4,'I');p=self.read(sp+8,'I');n=self.read(sp+12,'I')
            self.calls.append(dict(opcode=op,payload=bytes(vm.mem_read(p,n)).hex()))
        require(BASE<=a<0x600000,'Escaped current executable: '+hex(a))
    def readhook(self,vm,access,a,size,value,ctx):
        if PACKET<=a<PACKET+4096:self.packet_reads.append((a,size))
    def run(self,entry,stops):
        self.stops=set(stops);self.vm.emu_start(entry,0,count=250000)
        require(self.reg('EIP') in self.stops,'instruction budget exceeded at '+hex(self.reg('EIP')))
        return self.reg('EIP')
    def setup(self,*args):
        self.vm.mem_write(STACK,b'\xa5'*0x1f000);self.write(SP,'I',RETURN)
        for i,arg in enumerate(args):self.write(SP+4+i*4,'I',arg)
        self.setreg('ESP',SP);self.setreg('ECX',UI)
    def ingest(self,packet):
        addr=PACKET+4096-len(packet);self.vm.mem_write(addr,packet);self.setup(addr+1)
        stop=self.run(0x4c7f10,[0x4c8234,0x402c70,RETURN])
        return dict(stop=hex(stop),mode=self.read(UI+0xccc1c,'H'),key=self.read(UI+0xccc1e,'H'),context=self.read(UI+0xccd36,'B'),request=self.read(0x5b7bfa,'H'),reply=self.read(0x5b7bf8,'H'),text_pointer=self.selected_text,packet_read_max=max((a+s-addr for a,s in self.packet_reads),default=0))
    def pages(self):
        self.setup(self.textptr);self.run(0x4c8780,[RETURN,0x402c70])
        return dict(page_count=self.read(0x5b7bf4,'i'),threshold=self.read(UI+0xccd32,'h'),bias=self.read(UI+0xccd34,'h'))
    def choose(self,choice,page):
        self.write(UI+0xccc20,'h',choice);self.write(0x5b7bf0,'i',page)
        self.write(QUEUE+0x36c4,'I',0);self.write(QUEUE+0x40d4,'I',0)
        self.calls=[];self.setup()
        stop=self.run(0x4c8500,[RETURN,0x4c8350,0x475d60,0x413370])
        n=self.read(QUEUE+0x36c4,'I')
        return dict(stop=hex(stop),queue_hex=bytes(self.vm.mem_read(QUEUE+0x36c8,n)).hex(),calls=self.calls.copy())

def audit(client,packet=None):
    raw=(client/'God2.exe').read_bytes();require(sha(raw)==SHA,'Current PE pin mismatch');pe=pefile.PE(data=raw)
    catalogs=[];all_keys=[]
    for filename,pin in SOURCE_PINS.items():
        data=(client/'Data2/Patch/Comm'/filename).read_bytes();require(sha(data)==pin,'MultiMessage pin changed: '+filename)
        decoded=decode_csvz(data);lines=decoded.splitlines();declared=int(lines[1].split(b',')[1]);keys=[int(line.split(b',',1)[0]) for line in lines[2:] if line.split(b',',1)[0].isdigit()]
        require(len(keys)==declared,'Source declared count mismatch');all_keys.extend(keys)
        catalogs.append(dict(file=filename,sha256=sha(data),decoded_sha256=sha(decoded),header_count=declared,record_count=len(keys),minimum=min(keys),maximum=max(keys)))
    require(all_keys==list(range(1,TABLE_COUNT+1)),'MultiMessage global keys changed')
    compressed=(client/'Data2/Patch/Comm/MultiMessage02.csvZ').read_bytes();require(sha(compressed)==SOURCE_SHA,'MultiMessage source pin mismatch')
    rows=decode_csvz(compressed).splitlines()[1528:1536]
    require(rows[0].startswith(b'1434,7,'),'Source row changed')
    require([r.split(b',',2)[1] for r in rows[1:]]==[str(i).encode() for i in range(1,8)],'Option ordinal mismatch')
    require(struct.unpack('<I',pe.get_data(0x1324+4*0x7a,4))[0]==0x401318 and pe.get_data(0x1318,6)==bytes.fromhex('b8feffffffc3'),'7A variable length table changed')
    strings=[r.split(b',',2)[2] for r in rows]
    require(all(b'%' not in s and b'\0' not in s for s in strings),'Only nonformatting resource qualified')
    packet=fixture() if packet is None else packet
    require(len(packet)==28 and packet[0]==0x7a and packet[1:4]==bytes([28,0,4]) and int.from_bytes(packet[7:9],'little')==KEY and packet[11:]==bytes(17),'Only exact28 mode4/key1434/noformat/count0 packet is qualified')
    scoped_hex=packet.hex()
    request=int.from_bytes(packet[5:7],'little');reply=int.from_bytes(packet[9:11],'little');context=packet[4]
    require(reply<0x8000,'Compiled candidate limited to reply0..32767; high-flag and FFFF separately probed')
    native=Native(pe,strings);ingest=native.ingest(packet);pages=native.pages()
    require(ingest['stop']=='0x4c8234' and ingest['key']==KEY and ingest['request']==request and ingest['reply']==reply and ingest['context']==context,'ingest mismatch')
    actions=[]
    for choice in range(-1,9):
        result=native.choose(choice,pages['page_count']-1)
        if 0<=choice<=7:
            require(result['queue_hex'][:12]==('85'+struct.pack('<HHB',request,choice,context).hex()) and len(result['queue_hex'])==14,'choice output mismatch')
        else:require(result['queue_hex']=='' and result['stop']=='0x475d60','invalid choice not rejected')
        actions.append(dict(choice=choice,**result))
    before=native.choose(0,pages['threshold']-1)
    require(before['queue_hex']=='' and before['stop']==hex(RETURN),'early page not blocked')
    modes=[]
    for mode in (1,2,3,4):
        n=Native(pe,strings);r=n.ingest(fixture(mode=mode));modes.append(r)
        require(r['stop']=='0x4c8234' and r['mode']==mode,'mode mismatch')
        require(r['text_pointer']==(n.textptr if mode==4 else STRINGS+0xf000),'Wrong text namespace')
    clicks=[]
    for page,first,count in [(0,2,3),(1,0,4)]:
        for row in range(first,first+count):
            native.setup();native.setreg('ESI',UI);native.setreg('EDI',row)
            native.write(0x5b7bf0,'i',page)
            native.run(0x4c8671,[0x4c86a7])
            choice=native.read(UI+0xccc20,'h')
            require(choice==len(clicks),'Native page/row choice mapping mismatch')
            clicks.append(dict(page=page,visible_row=row,choice=choice))
    replies=[]
    for reply in (0,2,0x7fff,0x8002,0xffff):
        n=Native(pe,strings);r=n.ingest(fixture(reply=reply));pg=n.pages();action=n.choose(0,pg['page_count']-1)
        require(r['reply']==(reply if reply==0xffff else reply&0x7fff),'Reply normalization changed')
        require(bool(action['queue_hex'])==(reply!=0xffff),'Signed reply gate changed')
        replies.append(dict(incoming_reply=reply,high_flag=n.read(0x5b7bec,'I'),ingest=r,action=action))
    invalid_keys=[]
    for key in (0,TABLE_COUNT+1,65535):
        n=Native(pe,strings);r=n.ingest(fixture(key=key));require(r['stop']=='0x402c70','Invalid key did not stop at native assertion');invalid_keys.append(dict(key=key,stop=r['stop']))
    copy_bounds=[]
    for length in (283,284):
        n=Native(pe,strings);n.write(UI+0xccd32,'H',0x1234)
        tail=bytes(length-28)+b'\xee';r=n.ingest(fixture(tail=tail))
        threshold=n.read(UI+0xccd32,'H')
        require(threshold==(0x1234 if length==283 else 0x12ee),'Copy boundary mismatch')
        copy_bounds.append(dict(length=length,threshold_after=hex(threshold),stop=r['stop']))
    receiver=[]
    for length in (0,1,2,3,27,28,283,284,2559,2560,2561,65535):
        n=Native(pe,strings);n.write(QUEUE+0x2cc5,'H',length);n.write(QUEUE+0x2cc0,'I',length);n.setup();n.setreg('ESI',QUEUE)
        stop=n.run(0x41351f,[0x413534,0x41359a,0x4135c9])
        require(stop==(0x413534 if length>2560 else 0x41359a if length==2560 else 0x4135c9),'Receiver length branch mismatch')
        receiver.append(dict(length=length,stop=hex(stop),edi=n.reg('EDI')))
    bounds=[]
    for length in (3,10,11,12,26,27,28,283,284):
        n=Native(pe,strings);packet=fixture(tail=bytes(max(0,length-27)))[:length]
        if length>=3:packet=packet[:1]+struct.pack('<H',length)+packet[3:]
        try:r=n.ingest(packet);bounds.append(dict(length=length,**r))
        except UcError as e:bounds.append(dict(length=length,fault=str(e),eip=hex(n.reg('EIP'))))
    require(all('fault' in x for x in bounds if x['length']<27),'expected truncated mode4 copy boundary')
    require(all(x.get('stop')=='0x4c8234' for x in bounds if x['length'] in (27,28)),'safe length failed')
    return dict(schema='current-mode4-bounded-20260926',current_exe_sha256=sha(raw),source_sha256=sha(compressed),catalogs=catalogs,table_count=TABLE_COUNT,source_rows=[dict(line=1529+i,sha256=sha(row),raw_hex=row.hex(),text=row.decode('cp950')) for i,row in enumerate(rows)],fixture_hex=scoped_hex,ingest=ingest,pages=pages,choices=actions,click_mapping=clicks,reply_gates=replies,invalid_keys=invalid_keys,copy_bounds=copy_bounds,receiver_bounds=receiver,early_page=before,modes=modes,bounds=bounds,spans=[dict(start=hex(a),end_exclusive=hex(b),sha256=sha(pe.get_data(a-BASE,b-a))) for a,b in [(0x4c7f10,0x4c8240),(0x4c8500,0x4c85a1),(0x4c8671,0x4c86ac),(0x41351f,0x413566),(0x4c8780,0x4c8920),(0x497dc0,0x497e00),(0x4ffdf0,0x500100)]],scope='Actual current x86 consumer to pre-render header boundary, actual text pagination, actual 85 queue producer. Synthetic loader-equivalent resource table and post-render choice state. No rendering/input hit test, native text loader execution, full close, wire network or gameplay acceptance.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--client',type=Path,default=ROOT.parent/'God2');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--packet-hex',help='Optional exact compiled 28-byte mode4/key1434 candidate');args=ap.parse_args()
    result=audit(args.client.resolve(),bytes.fromhex(args.packet_hex) if args.packet_hex else None);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS: current PE mode4 input, pagination, native85 and bounds; '+str(args.output))
if __name__=='__main__':main()
