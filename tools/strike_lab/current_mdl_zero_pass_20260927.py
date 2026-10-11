"""Current native Pass loop proof and bounded current MDL source audit.

Runs44CC84..44CD56 with complete441880/441730. Only CRT fscanf/strcmp/new
are adapted; no game callee stubs, runtime processes, DB, or desktop access.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import x86_const as x
from .omega_assets import decode_csvz
from .current_monster_binary_producer import parse_mdl

ROOT=Path(__file__).resolve().parents[2];CLIENT=ROOT.parent/'God2'
PIN='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
BASE,STACK,OBJ,HEAP,VER=0x400000,0x2000000,0x3000000,0x3100000,0x3200000


def require(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


class PassLoop:
    def __init__(self,image,data,frames,zero_null=False):
        self.data=data;self.cursor=0;self.allocs=[];self.reads=[];self.setters=0;self.writes=[]
        self.frames=frames;self.zero_null=zero_null;self.heap=HEAP;self.steps=0
        self.vm=v=Uc(UC_ARCH_X86,UC_MODE_32)
        for at,size in ((BASE,(len(image)+4095)&~4095),(STACK,0x10000),(OBJ,0x1000),(HEAP,0x10000),(VER,0x1000)):
            v.mem_map(at,size)
        v.mem_write(BASE,image);v.mem_write(VER,b'v1.6\0');self.sp=STACK+0x8000
        v.mem_write(self.sp+0x1c,struct.pack('<I',frames));v.mem_write(self.sp+0x170,struct.pack('<II',0x11223344,VER))
        v.reg_write(x.UC_X86_REG_ESP,self.sp);v.reg_write(x.UC_X86_REG_ESI,OBJ);v.reg_write(x.UC_X86_REG_EBP,0x11223344)
        v.hook_add(UC_HOOK_CODE,self.code)
        v.hook_add(UC_HOOK_MEM_WRITE,lambda v,access,at,size,value,ctx:self.writes.append((at,size,value)))

    def word(self,at):return struct.unpack('<I',self.vm.mem_read(at,4))[0]
    def string(self,at):
        result=bytearray()
        for i in range(100):
            b=self.vm.mem_read(at+i,1)[0]
            if not b:return bytes(result)
            result.append(b)
        raise ValueError('CRT string bounds')

    def ret(self,value):
        v=self.vm;sp=v.reg_read(x.UC_X86_REG_ESP)
        v.reg_write(x.UC_X86_REG_EAX,value&0xffffffff);v.reg_write(x.UC_X86_REG_EIP,self.word(sp));v.reg_write(x.UC_X86_REG_ESP,sp+4)

    def code(self,v,at,size,_):
        self.steps+=1
        if at==0x549a00:
            sp=v.reg_read(x.UC_X86_REG_ESP);a=self.string(self.word(sp+4));b=self.string(self.word(sp+8))
            require(a==b'v1.6' and b==b'v1.6','Unexpected CRT version comparison')
            self.ret((a>b)-(a<b));return
        if at==0x5490ad:
            sp=v.reg_read(x.UC_X86_REG_ESP);require(self.word(sp+4)==0x11223344,'Unexpected stream')
            fmt=self.string(self.word(sp+8));require(fmt in (b'%d %d',b'%d'),'Unexpected fscanf format')
            begin=self.cursor;values=[]
            for i in range(fmt.count(b'%d')):
                m=re.match(rb'\s*([+-]?\d+)',self.data[self.cursor:]);require(m is not None,'Native fscanf input missing')
                value=int(m[1]);require(-0x80000000<=value<=0x7fffffff,'CRT decimal overflow')
                self.cursor+=m.end();v.mem_write(self.word(sp+12+i*4),struct.pack('<i',value));values.append(value)
            self.reads.append({'caller':hex(self.word(sp)),'format':fmt.decode(),'begin':begin,'end':self.cursor,'values':values})
            self.ret(len(values));return
        if at==0x55b406:
            size=self.word(v.reg_read(x.UC_X86_REG_ESP)+4);require(size<=4096,'Allocation bounds')
            pointer=0 if size==0 and self.zero_null else self.heap
            if pointer:self.heap+=max(size,16);v.mem_write(pointer,bytes([0xa5])*max(size,16))
            self.allocs.append({'bytes':size,'pointer':pointer});self.ret(pointer);return
        if at==0x441730:self.setters+=1
        require(any(a<=at<b for a,b in ((0x44cc84,0x44cd56),(0x441880,0x4419c5),(0x441730,0x4417b2))),
                'Unexpected game boundary '+hex(at))

    def run(self,expected):
        self.vm.emu_start(0x44cc84,0x44cd56,count=100000)
        require(self.vm.reg_read(x.UC_X86_REG_EIP)==0x44cd56 and self.vm.reg_read(x.UC_X86_REG_ESP)==self.sp,'Native loop/budget/stack boundary')
        require(self.setters==sum(w*h for w,h,cells in expected),'Wrong original setter count')
        outputs=[]
        for i,(w,h,cells) in enumerate(expected):
            pointer,width,height,count=struct.unpack('<4I',self.vm.mem_read(OBJ+0x4c+i*0x24,16))
            require((width,height,count)==(w,h,w*h),'Original allocator dimensions')
            actual=bytes(self.vm.mem_read(pointer,count)) if count else b''
            require(actual==bytes(cells),'Original setter output')
            outputs.append({'width':width,'height':height,'bytes':count,'pointer':pointer,'cells_hex':actual.hex()})
        heap_cell_writes=[(at,s) for at,s,val in self.writes if HEAP<=at<HEAP+0x10000]
        return {'frames':outputs,'fscanf_reads':self.reads,'allocations':self.allocs,'setters':self.setters,
                'stream_bytes_consumed':self.cursor,'remaining_hex':self.data[self.cursor:].hex(),
                'zero_new_adapter_returns_null':self.zero_null,'steps':self.steps,
                'scope':'Original44C980 Pass loop through44CD56, full441880/441730; CRT I/O/allocator adapters. Not full44C980 return.'}


def verify_native(image):
    result=[]
    for zero_null in (False,True):
        for dims in ((0,2),(2,0),(0,0),(2,2)):
            w,h=dims;cells=list(range(w*h));data=f'{w} {h}\r\n'.encode()
            data+=b''.join((' '.join(map(str,cells[row*w:(row+1)*w]))+'\r\n').encode() for row in range(h))
            data+=b'246 0 0\r\n'
            oracle=PassLoop(image,data,1,zero_null);r=oracle.run([(w,h,cells)])
            require(re.match(rb'\s*246 0 0',data[oracle.cursor:]),'Next model token consumed')
            require(len(r['fscanf_reads'])==1+w*h,'Unexpected data read for zero grid')
            result.append(r)
    # Real CityI2 bytes include two explicit blank source rows after0x2.
    raw=(CLIENT/'Data2/map/island03/cityi2/cityi2.mdlZ').read_bytes()
    require(sha(raw)=='cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc','CityI2 pin')
    plain=decode_csvz(raw);require(sha(plain)=='bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f','CityI2 decoded pin')
    lines=plain.splitlines(keepends=True);data=b''.join(lines[5011:5015]);require(data==b'0 2\r\n\r\n\r\n246 0 0\r\n','Real zero grid source')
    oracle=PassLoop(image,data,1);r=oracle.run([(0,2,[])])
    require(oracle.cursor==3 and oracle.setters==0,'Real source zero grid consumption')
    result.append(dict(r,source_line=5012,source_raw_hex=data.hex()))
    # Two-frame boundary: the second fscanf itself skips blank source rows.
    data=b'0 2\r\n\r\n\r\n2 1\r\n7 9\r\n246 0 0\r\n'
    oracle=PassLoop(image,data,2);r=oracle.run([(0,2,[]),(2,1,[7,9])])
    require(re.match(rb'\s*246 0 0',data[oracle.cursor:]),'Second frame consumed next model')
    result.append(r)
    return result


def audit_files():
    files=sorted(p for p in (CLIENT/'Data2/map').rglob('*') if p.is_file() and p.suffix.lower() in ('.mdl','.mdlz'))
    rows=[];failures=[];zero=[];npc=[];strict=[]
    for path in files:
        raw=path.read_bytes();plain=decode_csvz(raw) if path.suffix.lower()=='.mdlz' else raw
        source={'file':path.relative_to(CLIENT).as_posix(),'source_sha256':sha(raw),'decoded_sha256':sha(plain),'decoded_bytes':len(plain)}
        try:strict_model=parse_mdl(plain)
        except ValueError as error:strict.append(dict(source,status='REJECTED',error=str(error)))
        else:
            require(strict_model['unaccounted_bytes']==0,'Strict unconsumed bytes')
            strict.append(dict(source,status='PARSED'))
        try:model=parse_mdl(plain,allow_parent_rom=True)
        except ValueError as error:
            # Preserve the rejected ROM grammar evidence; do not open paths or
            # normalize source bytes to force the existing parser to accept.
            lines=plain.splitlines();refs=[]
            if len(lines)>1 and lines[1].startswith(b'ROMFILE '):
                count=int(lines[1].split()[1]);require(0<=count<=128,'ROM count audit bounds')
                refs=[{'line':i+3,'raw_hex':r.hex()} for i,r in enumerate(lines[2:2+count])
                      if not re.fullmatch(rb'(?:\.\.\\)?[A-Za-z0-9_]+\.[Rr][Oo][Mm]',r)]
            failures.append(dict(source,error=str(error),unsupported_rom_rows=refs));continue
        require(model['unaccounted_bytes']==0,'Unconsumed MDL bytes')
        rows.append(dict(source,models=len(model['models']),placements=len(model['placements']),rom_references=model['rom_references']))
        for i,m in enumerate(model['models']):
            for j,g in enumerate(m['grids']):
                if g['width']==0 or g['height']==0:
                    linked=[dict(p,index=k) for k,p in enumerate(model['placements']) if p['fields'][0]==i]
                    tiles=[dict(model['tiles'][layer[0]],index=layer[0]) for layer in m['layers'] if layer[0]>=0]
                    zero.append(dict(source,model=i,frame=j,grid=g,model_fields=m,tiles=tiles,placements=linked,
                                     raw_rows_hex=plain[g['start']:g['end_exclusive']].hex()))
        for i,t in enumerate(model['tiles']):
            rom=model['rom_references'][t['fields'][3]]
            if 'npc' not in rom.lower():continue
            indices=[j for j,m in enumerate(model['models']) if any(layer[0]==i for layer in m['layers'])]
            placements=[dict(p,index=j) for j,p in enumerate(model['placements']) if p['fields'][0] in indices]
            npc.append(dict(source,tile=i,name=bytes.fromhex(t['name_hex']).decode('cp950'),raw_tile=t,rom=rom,models=indices,placements=placements))
    return {'files_attempted':len(files),'strict_default':strict,'explicit_parent_option':True,
            'parsed':rows,'rejected':failures,'zero_grids':zero,
            'npc_named_resource_chains':npc,'qualified_npc_spawns':0}


def verify_rom_string_copy(image):
    #44D520 reads a%s token and44D5A5 calls55AFCA, whose55B00C call reaches
    #55AF26. Execute that complete native concatenate/allocation/memcpy path.
    #The prefix is synthetic. No ROM open or game resource loader is called.
    references=set()
    for path in sorted((CLIENT/'Data2/map').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in ('.mdl','.mdlz'):continue
        raw=path.read_bytes();plain=decode_csvz(raw) if path.suffix.lower()=='.mdlz' else raw
        lines=plain.splitlines();require(lines[1].startswith(b'ROMFILE '),'ROMFILE header')
        count=int(lines[1].split()[1]);require(1<=count<=128,'ROMFILE count')
        references.update(lines[2:2+count])
    v=Uc(UC_ARCH_X86,UC_MODE_32)
    for at,size in ((BASE,(len(image)+4095)&~4095),(STACK,0x10000),(OBJ,0x1000),(HEAP,0x10000),(VER,0x1000)):
        v.mem_map(at,size)
    v.mem_write(BASE,image);prefix=b'Data2/map/test/'
    def hook(vm,at,size,ctx):
        if at==0x546326:
            require(vm.reg_read(x.UC_X86_REG_ECX)==0x6f4d70,'Unexpected CString pool bucket')
            sp=vm.reg_read(x.UC_X86_REG_ESP);ret=struct.unpack('<I',vm.mem_read(sp,4))[0]
            vm.reg_write(x.UC_X86_REG_EAX,HEAP);vm.reg_write(x.UC_X86_REG_EIP,ret);vm.reg_write(x.UC_X86_REG_ESP,sp+4);return
        require(any(a<=at<b for a,b in ((0x55af26,0x55af64),(0x55aba2,0x55ac24),(0x54a8c0,0x54ac00))),
                'Unexpected native string-copy PC '+hex(at))
    v.hook_add(UC_HOOK_CODE,hook);outputs=[]
    for token in sorted(references):
        require(0<len(token)<260 and not re.search(rb'\s',token),'Native%s token bounds')
        require(len(prefix)+len(token)<=64,'Qualified native pool size')
        v.mem_write(VER,prefix+b'\0');v.mem_write(VER+0x100,token+b'\0')
        sp=STACK+0x8000;stop=VER+0x800
        v.mem_write(sp,struct.pack('<5I',stop,len(prefix),VER,len(token),VER+0x100))
        v.reg_write(x.UC_X86_REG_ESP,sp);v.reg_write(x.UC_X86_REG_ECX,OBJ)
        v.emu_start(0x55af26,stop,count=10000)
        require(v.reg_read(x.UC_X86_REG_EIP)==stop and v.reg_read(x.UC_X86_REG_ESP)==sp+20,'Native string-copy return/budget')
        pointer=struct.unpack('<I',v.mem_read(OBJ,4))[0]
        length=struct.unpack('<I',v.mem_read(pointer-8,4))[0]
        actual=bytes(v.mem_read(pointer,length+1))
        require(actual==prefix+token+b'\0','ROM reference not preserved')
        outputs.append({'raw_token_hex':token.hex(),'result_hex':actual.hex(),'native_return':True})
    #Pin the actual caller edges/%s before relying on this library subpath.
    for at,target in ((0x4d57f,0x1490ad),(0x4d5a5,0x15afca),(0x15b00c,0x15af26)):
        require(image[at]==0xe8 and at+5+struct.unpack_from('<i',image,at+1)[0]==target,'ROM reader call edge')
    require(image[0x184954:0x184957]==b'%s\0','ROM reader token format')
    require(image[0x4d579]==0x68 and struct.unpack_from('<I',image,0x4d57a)[0]==0x584954,'ROM%s argument')
    return {'unique_tokens':len(outputs),'tokens':outputs,
            'scope':'Native55AF26->55ABA2->54A8C0 complete return; MFC pool allocator adapter.44D520 token-read/55AFCA caller machine edges verified, full ROM reader/file loader not executed.'}


def run():
    raw=(CLIENT/'God2.exe').read_bytes();require(sha(raw)==PIN,'Current PE pin')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    native=verify_native(image);rom_strings=verify_rom_string_copy(image);sources=audit_files()
    raw=decode_csvz((CLIENT/'Data2/map/island03/cityi2/cityi2.mdlZ').read_bytes())
    old=b'0 2\r\n\r\n\r\n246 0 0\r\n';require(raw.count(old)==1,'Mutation anchor uniqueness')
    rejected=[]
    for name,new in (('negative_width',b'-1 2\r\n\r\n\r\n246 0 0\r\n'),
                     ('negative_height',b'0 -1\r\n\r\n\r\n246 0 0\r\n'),
                     ('excess_width',b'513 2\r\n\r\n\r\n246 0 0\r\n'),
                     ('excess_height',b'0 513\r\n\r\n\r\n246 0 0\r\n'),
                     ('nonempty_zero_row',b'0 2\r\n1\r\n\r\n246 0 0\r\n'),
                     ('missing_zero_row',b'0 2\r\n\r\n246 0 0\r\n')):
        try:parse_mdl(raw.replace(old,new),allow_parent_rom=True)
        except ValueError as error:rejected.append({'case':name,'error':str(error)})
        else:raise ValueError('Parser accepted invalid zero case '+name)
    lines=raw.splitlines(keepends=True);n=int(lines[1].split()[1])
    baseline=b''.join(lines[:2]+[b'safe.ROM\r\n']*n+lines[2+n:])
    require(parse_mdl(baseline)['unaccounted_bytes']==0,'Synthetic simple-path baseline')
    path_rejects=[]
    for value in (b'\\absolute.ROM',b'C:\\drive.ROM',b'\\\\host\\share.ROM',
                  b'..\\..\\..\\escape.ROM',b'dir\\..\\escape.ROM',b'a\\b\\c\\d\\e\\deep.ROM',b'x'*260+b'.ROM'):
        candidate=baseline.replace(b'safe.ROM',value,1)
        try:parse_mdl(candidate,allow_parent_rom=True)
        except ValueError as error:path_rejects.append({'raw_token_hex':value.hex(),'error':str(error)})
        else:raise ValueError('Unsafe/unbounded ROM grammar admitted')
    parent=baseline.replace(b'safe.ROM',b'..\\..\\Array\\Array01\\S31D.ROM',1)
    require(parse_mdl(parent,allow_parent_rom=True)['unaccounted_bytes']==0,'Explicit source path rejected')
    try:parse_mdl(parent)
    except ValueError:pass
    else:raise ValueError('Default ROM grammar broadened')
    return {'status':'PASS','current_pe_sha256':PIN,'native':native,'rom_strings':rom_strings,'sources':sources,
            'parser_negative_cases':rejected,'rom_path_negative_cases':path_rejects,'default_path_mode_unchanged':True,
            'counts':{'native_cases':len(native),'native_rom_string_copies':rom_strings['unique_tokens'],'mdl_attempted':sources['files_attempted'],
                      'strict_default_parsed':sum(r['status']=='PARSED' for r in sources['strict_default']),
                      'explicit_parent_parsed':len(sources['parsed']),
                      'mdl_rejected':len(sources['rejected']),'zero_grids':len(sources['zero_grids']),
                      'parser_rejections':len(rejected),'path_rejections':len(path_rejects),'qualified_npc_spawns':0},
            'code_spans':[{'start_rva':hex(a),'end_rva':hex(b),'sha256':sha(image[a:b])} for a,b in ((0x4c980,0x4ce6b),(0x41880,0x419c5),(0x41730,0x417b2))]}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(args.output.resolve().is_relative_to((ROOT/'artifacts/research/mdl-zero-pass-20260927').resolve()),'Output scope')
    result=run();args.output.parent.mkdir(parents=True,exist_ok=True);temp=args.output.with_suffix('.pending')
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(args.output)
    print(json.dumps(result['counts']))
