#include <windows.h>
static DWORD now_ms=100;
DWORD test_clock(){return now_ms;}
#define GetTickCount test_clock
#include "bull_effect.cpp"
#undef GetTickCount
#include <cassert>
#include <iostream>
using namespace bull_effect;
struct Fake {void** table{};std::array<Byte,64> pixels{};bool negative{},fail{};unsigned locks{},unlocks{};};
HRESULT __stdcall lock_fake(IDirectDrawSurface7* p,LPRECT,LPDDSURFACEDESC2 d,DWORD,HANDLE){auto& f=*reinterpret_cast<Fake*>(p);++f.locks;if(f.fail)return DDERR_SURFACELOST;d->dwWidth=5;d->dwHeight=3;d->lPitch=f.negative?-16:16;d->lpSurface=f.pixels.data()+(f.negative?32:0);d->ddpfPixelFormat.dwFlags=DDPF_RGB;d->ddpfPixelFormat.dwRGBBitCount=16;d->ddpfPixelFormat.dwRBitMask=0xf800;d->ddpfPixelFormat.dwGBitMask=0x7e0;d->ddpfPixelFormat.dwBBitMask=31;return DD_OK;}
ULONG __stdcall ref_fake(IDirectDrawSurface7*){return 1;}
HRESULT __stdcall unlock_fake(IDirectDrawSurface7* p,LPRECT){++reinterpret_cast<Fake*>(p)->unlocks;return DD_OK;}
template<class T,std::size_t N>void put(std::array<Byte,N>& a,unsigned offset,T v){std::memcpy(a.data()+offset,&v,sizeof(v));}
int main(int argc,char** argv){
 std::vector<Byte> p{1,0,0,0,1,0,1,0,2,0,0,0,255,0,0,128,0,255,0,255},out;
 assert(frames::decode(p,5,3,out)&&out.size()==60&&out[(5+1)*4]==255&&out[(5+2)*4+1]==255);
 auto broken=p;broken[8]=5;assert(!frames::decode(broken,5,3,out));broken=p;broken.pop_back();assert(!frames::decode(broken,5,3,out));broken=p;broken[10]=1;assert(!frames::decode(broken,5,3,out));
 const Byte red[]={255,0,0,128},transparent[]={200,100,255,0},solid[]={255,0,0,255};
 assert(frames::blend(31,solid,0xf800,0x7e0,31)==0xf800);assert(frames::blend(31,transparent,0xf800,0x7e0,31)==31);
 const auto half=frames::blend(31,red,0xf800,0x7e0,31);assert(frames::channel(half,0xf800)>120&&frames::channel(half,31)>110);
 assert(frames::blend(0xff0000ff,solid,0xff0000,0xff00,0xff)==0xffff0000);
 frames::BlendTable table_blend;unsigned rng=0x919afe;
 for(const auto masks:std::array<std::array<unsigned,3>,3>{{{0xf800,0x7e0,31},{0x7c00,0x3e0,31},{0xff0000,0xff00,0xff}}}){
  table_blend.configure(masks[0],masks[1],masks[2]);assert(table_blend.valid);
  for(unsigned alpha=0;alpha<256;++alpha)for(unsigned n=0;n<1000;++n){rng=rng*1664525+1013904223;const unsigned dst=rng;
   Byte src[]{Byte(rng>>3),Byte(rng>>11),Byte(rng>>19),Byte(alpha)};
   assert(table_blend.apply(dst,src)==frames::blend(dst,src,masks[0],masks[1],masks[2]));
  }
 }
 mapping.configure(800,600);for(unsigned x=0;x<800;++x)assert(mapping.x[x]==std::min(1039u,unsigned(std::floor(double(x)*1024.0/800+8))));
 for(unsigned y=0;y<600;++y)assert(mapping.y[y]==std::min(806u,unsigned(std::max(0.0,std::floor(double(y)*768.0/600-1)))));
 std::array<void*,45> table{};table[1]=reinterpret_cast<void*>(ref_fake);table[2]=reinterpret_cast<void*>(ref_fake);table[25]=reinterpret_cast<void*>(lock_fake);table[32]=reinterpret_cast<void*>(unlock_fake);Fake f{};f.table=table.data();
 std::array<Byte,0xc0> renderer{},cdx{};void* display=reinterpret_cast<void*>(123);put(renderer,0xa0,cdx.data());put(renderer,0xa8,display);put(cdx,0x80,&f);
 cast.war=reinterpret_cast<void*>(234);cast.display=display;cast.started=cast.ready=true;cast.start=100;cast.tick=70;cast.shake[140]=210;cast.shake[141]=270;
 for(unsigned i=0;i<f.pixels.size();++i)f.pixels[i]=Byte(i+1);const auto before=f.pixels;
 before_present(renderer.data());assert(f.pixels!=before&&present.surface);after_present();assert(f.pixels==before&&!present.surface);
 f.negative=true;before_present(renderer.data());assert(f.pixels!=before);after_present();assert(f.pixels==before);
 f.fail=true;const auto unlocks=f.unlocks;before_present(renderer.data());after_present();assert(f.unlocks==unlocks);
 assert(has_tail(cast.war));now_ms=8099;assert(has_tail(cast.war)&&elapsed_ms(cast.war)==7999);now_ms=8100;assert(!has_tail(cast.war));
 void* war=cast.war;reset(reinterpret_cast<void*>(999));assert(cast.war==war);reset(war);assert(!cast.war&&!cast.started&&!cast.ready);
 if(argc>1){for(const char* name:{"player-ground.bfx","player-foreground.bfx","enemy-ground.bfx","enemy-foreground.bfx"}){
  frames::Pack pack;assert(pack.open((std::filesystem::path(argv[1])/name).wstring()));
  assert(pack.frame(0)&&pack.frame(70));unsigned visible=0;for(std::size_t pixel=3;pixel<pack.rgba.size();pixel+=4)visible+=pack.rgba[pixel]!=0;assert(visible>1000);
  assert(pack.frame(239));for(Byte value:pack.rgba)assert(value==0);assert(!pack.frame(240));pack.close();
 }}
 std::cout<<"bull effects: bounded spans, RGBA blend, pitch, final UI shift restore, failed lock, eight-second lifecycle passed\n";
}
