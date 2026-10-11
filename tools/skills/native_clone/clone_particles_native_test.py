"""Execute original additive blitter on the adapter's uncompressed8-bit bitmap ABI.

Only Win32 SetRect/IntersectRect are adapted. No native renderer routine is stubbed.
"""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
IMAGE=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'

def run():
    image=IMAGE.read_bytes()
    assert hashlib.sha256(image).hexdigest()=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    v=Uc(UC_ARCH_X86,UC_MODE_32);v.mem_map(0x400000,(len(image)+4095)&~4095);v.mem_write(0x400000,image)
    ctx,fb,stack,bmp=0x20000000,0x21000000,0x22000000,0x23000000
    for p in (ctx,fb,stack,bmp):v.mem_map(p,0x10000)
    def put(p,fmt,*values):v.mem_write(p,struct.pack('<'+fmt,*values))
    def read(p,fmt):return struct.unpack('<'+fmt,v.mem_read(p,struct.calcsize('<'+fmt)))
    apis={read(0x5706e4,'I')[0]:'SetRect',read(0x570668,'I')[0]:'IntersectRect'}
    for page in {a&~4095 for a in apis}:v.mem_map(page,4096)
    stop=stack+0xf000;calls=[]
    def hook(vm,pc,size,_):
        if pc==stop:vm.emu_stop();return
        if pc not in apis:return
        sp=vm.reg_read(UC_X86_REG_ESP);ret=read(sp,'I')[0];kind=apis[pc]
        if kind=='SetRect':
            p,l,t,r,b=read(sp+4,'5I');put(p,'4I',l,t,r,b);count=5;result=1
        else:
            p,a,b=read(sp+4,'3I');aa=read(a,'4i');bb=read(b,'4i')
            rect=[max(aa[0],bb[0]),max(aa[1],bb[1]),min(aa[2],bb[2]),min(aa[3],bb[3])]
            result=int(rect[0]<rect[2] and rect[1]<rect[3]);put(p,'4i',*(rect if result else [0]*4));count=3
        calls.append(kind);vm.reg_write(UC_X86_REG_EAX,result);vm.reg_write(UC_X86_REG_ESP,sp+4*(count+1));vm.reg_write(UC_X86_REG_EIP,ret)
    v.hook_add(UC_HOOK_CODE,hook)
    put(ctx,'6I',8,8,0,0,8,8);put(ctx+0x1208,'I',fb)
    put(ctx+0x1210,'3H',0xf800,0x07e0,0x001f)
    pal,pixels=bmp+0x100,bmp+0x400
    put(bmp,'HHHBBIIII',2,2,256,3,0,pal,0,0,pixels)
    palette=[0]*256;palette[1]=0xf800;palette[2]=0x07e0;palette[3]=0x001f
    put(pal,'256H',*palette);v.mem_write(pixels,bytes([1,2,3,0]))
    cases=[]
    for x,y in [(2,2),(-1,-1),(7,7)]:
        backdrop=0x4208;put(fb,'64H',*([backdrop]*64));sp=stack+0x8000
        put(sp,'8I',stop,0,x&0xffffffff,y&0xffffffff,bmp,1,pal,0)
        v.reg_write(UC_X86_REG_ESP,sp);v.reg_write(UC_X86_REG_ECX,ctx)
        v.emu_start(0x424880,0,count=100000)
        assert v.reg_read(UC_X86_REG_EIP)==stop and v.reg_read(UC_X86_REG_ESP)==sp+32
        expected=[backdrop]*64
        for py in range(2):
            for px in range(2):
                if 0<=x+px<8 and 0<=y+py<8:
                    add=palette[[1,2,3,0][py*2+px]]
                    expected[(y+py)*8+x+px]=sum(min(mask,(backdrop&mask)+(add&mask)) for mask in (0xf800,0x07e0,0x1f))
        assert list(read(fb,'64H'))==expected
        cases.append(dict(x=x,y=y,original_blitter_exact=True,stack_balanced=True))
    result=dict(status='PASS',bitmap_header_bytes=24,format=3,palette_words=256,pixels='8bit-uncompressed',original_function='00424880',dispatcher='00425700 case3 routes to00424880 when row_table pointer+16 is null',adapted_only=sorted(set(calls)),cases=cases,live_acceptance=False)
    Path(__file__).with_name('clone_particles_native_evidence.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
if __name__=='__main__':run()
