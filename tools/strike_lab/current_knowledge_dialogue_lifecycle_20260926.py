"""Current-PE tutorial text candidates and dialogue lifecycle, isolated native vectors."""
import argparse,hashlib,json,struct
from pathlib import Path
from .current_dialogue_mode4_native_20260926 import Native,fixture,require,sha,ROOT,UI,RESOURCE,TABLE,STRINGS,PACKET,QUEUE,SP,RETURN,pefile,SHA
from .omega_assets import decode_csvz
SOURCE_PINS={'NPCMission04.csvZ': 'd173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f', 'NPCMission09.csvZ': '0f00d56b93808a933e6bee811c79d477651b8c6aac002b271a79e002e5dfc812'}
BACKING,INPUT=0x60000000,0x61000000
MAPPING={0:[8779],1:[3016],2:[3017],3:[3018,3019],4:[3020],5:[3021],6:[8786]}

class Lifecycle(Native):
    def __init__(self,pe,menu):
        super().__init__(pe,menu)
        self.vm.mem_map(TABLE+0x10000,0x10000)
        self.vm.mem_map(BACKING,4096);self.vm.mem_map(INPUT,0x13000)
        self.write(UI+0xcc9d4,'I',INPUT);self.write(UI+0xcc9d4+4,'I',BACKING)
        self.write(BACKING+0x1e,'H',65535)
        self.write(UI+0x8688c,'I',BACKING+0x800);self.write(BACKING+0x800,'I',0xdeadbeef)
        self.write(UI+0x232ec8,'I',1);self.write(0x593e68,'H',65535)
        self.write(UI+0xccc18,'i',-1)
        self.write(RESOURCE+0xb2c48,'h',14600)
    def teach(self,key,raw,reply=2,request=0x2468,context=0x5b):
        pointer=STRINGS+0x5000;self.vm.mem_write(pointer,raw+b'\0')
        self.write(TABLE+0x8000+(key-1)*4,'I',pointer)
        result=self.ingest(fixture(mode=1,key=key,reply=reply,request=request,context=context,tail=b''))
        require(result['text_pointer']==pointer,'wrong NPCMission pointer')
        self.textptr=pointer
        return result
    def visible(self,mode,choice=0,page=0,count=1):
        self.write(UI+0xaff00,'I',1);self.write(UI+0xaff04,'I',0)
        self.write(UI+0xccc1c,'H',mode);self.write(UI+0xccc20,'h',choice)
        self.write(0x5b7bf0,'i',page);self.write(0x5b7bf4,'i',count)
    def execute(self,entry,*args):
        self.setup(*args);self.calls=[]
        stop=self.run(entry,[RETURN,0x402c70,0x413370,0x475d60])
        require(stop==RETURN,'unexpected lifecycle stop '+hex(stop))
        return self.snapshot()
    def snapshot(self):
        count=self.read(QUEUE+0x36c4,'I')
        return dict(queue_hex=bytes(self.vm.mem_read(QUEUE+0x36c8,count)).hex(),calls=self.calls.copy(),open=self.read(UI+0xaff00,'I'),action=self.read(UI+0xaff04,'I'),high_flag=self.read(0x5b7bec,'I'),request=self.read(0x5b7bfa,'H'),reply=self.read(0x5b7bf8,'H'),context=self.read(UI+0xccd36,'B'))
    def click(self,page,row):
        self.write(0x5b7bf0,'i',page)
        rendered=self.execute(0x4c8920);require(not rendered['calls'],'Rendering emitted packet')
        self.write(UI+0xcc9d4+0x224,'h',-1)
        for i in range(50):
            self.write(UI+0xcc9d4+0x1c+2*i,'h',i if i<5 else -1)
            if i<5:require(self.read(UI+0xcc9d4+0x148+4*i,'I')==int((page==0 and 2<=i<=4) or (page==1 and i<4)),'Native option availability mismatch')
            if i<5:self.write(INPUT+i*24,'6i',1,10,20+i*20,110,39+i*20,0)
        self.setup(0x201,0,(25+row*20)<<16|40);self.setreg('ECX',INPUT)
        self.run(0x418950,[RETURN])
        hit=self.read(INPUT+row*24+20,'I');require(hit==1,'actual hit test failed')
        result=self.execute(0x4c85b0,65535,1)
        result.update(page=page,row=row,hit=hit)
        return result

def audit(client):
    raw=(client/'God2.exe').read_bytes();require(sha(raw)==SHA,'PE pin changed');pe=pefile.PE(data=raw)
    from .current_dialogue_mode4_native_20260926 import SOURCE_SHA
    require(sha((client/'Data2/Patch/Comm/MultiMessage02.csvZ').read_bytes())==SOURCE_SHA,'Menu source pin changed')
    menurows=decode_csvz((client/'Data2/Patch/Comm/MultiMessage02.csvZ').read_bytes()).splitlines()[1528:1536]
    menu=[row.split(b',',2)[2] for row in menurows]
    sources=[];texts={}
    for fn,keys in [('NPCMission04.csvZ',range(3016,3023)),('NPCMission09.csvZ',[8779,8780,8786])]:
        data=(client/'Data2/Patch/Comm'/fn).read_bytes();require(sha(data)==SOURCE_PINS[fn],'Source pin changed: '+fn);decoded=decode_csvz(data)
        for line,row in enumerate(decoded.splitlines(),1):
            first,_,text=row.partition(b',')
            if first.isdigit() and int(first) in keys:
                require(b'%' not in text and b'\0' not in text,'formatting resource excluded')
                texts[int(first)]=text;sources.append(dict(file=fn,source_sha256=sha(data),decoded_sha256=sha(decoded),line=line,key=int(first),raw_hex=row.hex(),row_sha256=sha(row),text=row.decode('cp950')))
    teaching=[]
    for key in sorted(texts):
        n=Lifecycle(pe,menu);r=n.teach(key,texts[key]);pages=n.pages()
        require(not n.calls,'ingest unexpectedly emitted request')
        n.visible(1,page=pages['page_count']-1,count=pages['page_count'])
        action=n.execute(0x4c8500)
        require([c['opcode'] for c in action['calls']]==[0x85],'mode1 full action must emit only85')
        require(action['queue_hex'].startswith('85682402005b'),'request/context not retained')
        teaching.append(dict(key=key,ingest=r,pages=pages,action=action))
    sequences=[]
    for mode in (1,4):
        for reply in (2,0x8002,0xffff):
            for entry in ('action','close'):
                n=Lifecycle(pe,menu)
                if mode==1:n.teach(3016,texts[3016],reply=reply,request=0x1234,context=0x9a)
                else:n.ingest(fixture(reply=reply))
                pg=n.pages();n.visible(mode,choice=3,page=pg['page_count']-1,count=pg['page_count'])
                r=n.execute(0x4c8500 if entry=='action' else 0x4c8350)
                expected=([0x86] if reply==0xffff else [0x85] if mode==1 or reply==2 else [0x85,0x85]) if entry=='action' else ([0x86,0x85] if reply==0x8002 else [0x86])
                require([c['opcode'] for c in r['calls']]==expected,'close ordering mismatch')
                sequences.append(dict(mode=mode,incoming_reply=reply,entry=entry,**r))
    clicks=[]
    for page,rows in [(0,range(2,5)),(1,range(4))]:
        for row in rows:
            n=Lifecycle(pe,menu);n.ingest(fixture());pg=n.pages();n.visible(4,page=page,count=pg['page_count'])
            r=n.click(page,row);choice=len(clicks)
            require(len(r['calls'])==1 and r['calls'][0]['opcode']==0x85 and bytes.fromhex(r['calls'][0]['payload'])[2:4]==struct.pack('<H',choice),'full click85 mismatch')
            require(r['open']==0,'dialog did not close')
            r['choice']=choice;clicks.append(r)
    navigation=[]
    n=Lifecycle(pe,menu);n.ingest(fixture());pg=n.pages();n.visible(4,page=0,count=pg['page_count'])
    for control,expected_page in [(3,1),(3,1),(2,0),(2,0)]:
        r=n.execute(0x4c85b0,control,1);page=n.read(0x5b7bf0,'i');enabled=[n.read(UI+0xcc9d4+0x148+i*4,'I') for i in range(5)]
        require(page==expected_page and not r['calls'],'Page navigation emitted data or wrong page')
        require(enabled==([1,1,1,1,0] if page==1 else [0,0,1,1,1]),'Native rendered option availability wrong')
        navigation.append(dict(control=control,page=page,row_enabled=enabled,**r))
    roundtrip=[]
    n=Lifecycle(pe,menu);n.ingest(fixture());pg=n.pages();n.visible(4,page=0,count=pg['page_count']);first=n.click(0,3);roundtrip.append(dict(stage='menu_choice1',**first))
    before=n.read(QUEUE+0x36c4,'I');n.teach(3016,texts[3016]);require(n.read(QUEUE+0x36c4,'I')==before,'Opening mode1 emitted data')
    pg=n.pages();n.visible(1,page=pg['page_count']-1,count=pg['page_count']);roundtrip.append(dict(stage='teaching_action',**n.execute(0x4c8500)))
    before=n.read(QUEUE+0x36c4,'I');n.ingest(fixture(request=0x3579,context=0x6c));require(n.read(QUEUE+0x36c4,'I')==before,'Reopening menu emitted data');n.textptr=n.selected_text;pg=n.pages();n.visible(4,page=0,count=pg['page_count']);last=n.click(0,4)
    require(bytes.fromhex(last['calls'][0]['payload'])[:5]==bytes.fromhex('793502006c'),'New header request/context not retained');roundtrip.append(dict(stage='reopened_menu_choice2',**last))
    high_flush=[]
    n=Lifecycle(pe,menu);n.ingest(fixture(reply=0x8002))
    high_flush.append(n.execute(0x4c84a0));require([c['opcode'] for c in high_flush[-1]['calls']]==[0x85],'high flush missing85')
    high_flush.append(n.execute(0x4c84a0));require(not high_flush[-1]['calls'],'high flush repeated85')
    noops=[]
    for opcode in (0x11,0x17):
        n=Lifecycle(pe,menu);n.ingest(fixture());n.visible(4)
        before=n.snapshot();n.vm.mem_write(PACKET,bytes([opcode]));n.setup();n.setreg('EBX',PACKET);n.setreg('EBP',UI-0xa7f2f6c)
        stop=n.run(0x468b4e,[0x46b517]);after=n.snapshot()
        require(before==after,'opcode unexpectedly changed dialogue')
        noops.append(dict(opcode=opcode,dispatch=hex(struct.unpack('<I',pe.get_data(0x6b5d4+opcode*4,4))[0]),stop=hex(stop),dialog_unchanged=True))
    return dict(schema='current-knowledge-dialogue-lifecycle-v1',exe_sha256=sha(raw),mapping_authority='CONTENT_MATCH_CANDIDATE_NOT_ORIGINAL_SERVER_EVENT_JOIN',mapping=MAPPING,source_rows=sources,teaching=teaching,lifecycle=sequences,mouse_clicks=clicks,page_navigation=navigation,roundtrip=roundtrip,high_flag_flush=high_flush,world_opcode_noops=noops,scope='Actual current native header/parser/close and mouse message hit-testing -> mode4 event ->85, with synthetic resource tables, empty graphics and synthetic rectangles. Not populated current-client GUI acceptance.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--client',type=Path,default=ROOT.parent/'God2');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();result=audit(a.client);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS: current native tutorial/close/mouse-hit vectors '+str(a.output))
if __name__=='__main__':main()

