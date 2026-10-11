// Actual renderer/lifecycle implementation with deterministic clock and DD
// memory surfaces. These are internal black-box-style contract tests, NOT UI.
#include <windows.h>
static DWORD now_ms=100;
DWORD lifecycle_clock(){return now_ms;}
#define GetTickCount lifecycle_clock
#include "bull_effect.cpp"
#undef GetTickCount
#include <cassert>
#include <iostream>
using namespace bull_effect;
template<class T,std::size_t N>void put(std::array<Byte,N>& a,unsigned offset,T v){std::memcpy(a.data()+offset,&v,sizeof(v));}
struct Fake {void** table{};unsigned width{},height{},bytes{},stride{},refs{1},locks{},unlocks{};bool negative{},failed{};std::vector<Byte> pixels;
 void configure(unsigned w,unsigned h,unsigned b,bool neg){width=w;height=h;bytes=b;stride=w*b+8;negative=neg;pixels.assign(std::size_t(stride)*h,0xa5);for(unsigned y=0;y<h;++y)for(unsigned x=0;x<w*b;++x)pixels[std::size_t(y)*stride+x]=Byte(x*3+y*11);}
};
HRESULT __stdcall lock_fake(IDirectDrawSurface7* p,LPRECT,LPDDSURFACEDESC2 d,DWORD,HANDLE){auto& f=*reinterpret_cast<Fake*>(p);++f.locks;if(f.failed)return DDERR_SURFACELOST;
 d->dwWidth=f.width;d->dwHeight=f.height;d->lPitch=f.negative?-LONG(f.stride):LONG(f.stride);d->lpSurface=f.pixels.data()+(f.negative?std::size_t(f.height-1)*f.stride:0);
 d->ddpfPixelFormat.dwFlags=DDPF_RGB;d->ddpfPixelFormat.dwRGBBitCount=f.bytes*8;
 d->ddpfPixelFormat.dwRBitMask=f.bytes==2?0xf800:0xff0000;d->ddpfPixelFormat.dwGBitMask=f.bytes==2?0x7e0:0xff00;d->ddpfPixelFormat.dwBBitMask=f.bytes==2?31:255;return DD_OK;
}
HRESULT __stdcall unlock_fake(IDirectDrawSurface7* p,LPRECT){++reinterpret_cast<Fake*>(p)->unlocks;return DD_OK;}
ULONG __stdcall addref_fake(IDirectDrawSurface7* p){return ++reinterpret_cast<Fake*>(p)->refs;}
ULONG __stdcall release_fake(IDirectDrawSurface7* p){return --reinterpret_cast<Fake*>(p)->refs;}
int main(int argc,char** argv){
 assert(argc==2);std::array<void*,45> table{};table[1]=reinterpret_cast<void*>(addref_fake);table[2]=reinterpret_cast<void*>(release_fake);table[25]=reinterpret_cast<void*>(lock_fake);table[32]=reinterpret_cast<void*>(unlock_fake);
 std::array<Byte,0xc0> renderer{},cdx{};std::array<Byte,0x20> war{},manager{};void* display=reinterpret_cast<void*>(1234);put(war,0xc,manager.data());put(manager,4,display);put(renderer,0xa0,cdx.data());put(renderer,0xa8,display);
 Fake f{};f.table=table.data();put(cdx,0x80,&f);image_base=0x400000;directory=std::filesystem::path(argv[1]);
 // Repeated per-target receipts cannot rewind a cast. A true completion reset
 // permits the same caster to launch a fresh independent eight-second cast.
 on_result(war.data(),0,0);before_frame(war.data());assert(!cast.started&&!has_tail(war.data()));assert(begin_actor(war.data(),0,0));before_frame(war.data());assert(cast.started&&cast.ready);auto first=cast.start;
 now_ms+=1500;on_result(war.data(),0,0);before_frame(war.data());assert(cast.start==first&&elapsed_ms(war.data())==1500);
 reset_display(display);assert(!cast.display&&cast.started);now_ms+=500;before_frame(war.data());assert(cast.display==display&&elapsed_ms(war.data())==2000);
 now_ms=first+8000;assert(!has_tail(war.data()));finish_actor(war.data(),0,0);assert(!queued_count);on_result(war.data(),0,0);assert(begin_actor(war.data(),0,0));before_frame(war.data());assert(cast.start==now_ms&&elapsed_ms(war.data())==0);
 // UI, field, and bottom chat pixels shift as one image; original buffer and
 // padding restore byte-for-byte for both current and expanded dimensions.
 for(auto size:std::array<std::array<unsigned,2>,2>{{{800,600},{1024,768}}})for(unsigned bytes:{2u,4u})for(bool neg:{false,true}){
  f.configure(size[0],size[1],bytes,neg);cast.tick=70;cast.shake[140]=5;cast.shake[141]=-3;const auto original=f.pixels;
  before_present(renderer.data());assert(present.surface&&f.pixels!=original&&f.refs==2);
  auto shifted=f.pixels;after_present();assert(f.pixels==original&&f.refs==1);
  // Guard bytes on every padded row were never touched.
  for(unsigned y=0;y<f.height;++y)for(unsigned x=f.width*bytes;x<f.stride;++x)assert(shifted[std::size_t(y)*f.stride+x]==0xa5);
 }
 // Reentrant presentation does not double-translate, overwrite the outer
 // snapshot, or acquire an unpaired surface reference.
 f.configure(800,600,2,false);const auto nested_original=f.pixels;before_present(renderer.data());const auto nested_shifted=f.pixels;
 before_present(renderer.data());assert(f.refs==2&&f.pixels==nested_shifted);after_present();assert(f.refs==2&&f.pixels==nested_shifted);
 after_present();assert(f.refs==1&&f.pixels==nested_original&&present.depth==0);after_present();assert(f.refs==1);
 // A screen reset inside native presentation can replace the COM pointer.
 // The retained old surface remains valid until restoration/release completes.
 f.configure(800,600,2,false);const auto old_pixels=f.pixels;before_present(renderer.data());assert(f.refs==2);
 Fake replacement{};replacement.table=table.data();replacement.configure(800,600,2,false);replacement.pixels.assign(replacement.pixels.size(),0x5c);const auto replacement_pixels=replacement.pixels;
 put(cdx,0x80,&replacement);release_fake(reinterpret_cast<IDirectDrawSurface7*>(&f));assert(f.refs==1);reset_display(display);
 after_present();assert(f.refs==0&&f.pixels==old_pixels&&replacement.pixels==replacement_pixels);f.refs=1;put(cdx,0x80,&f);before_frame(war.data());assert(cast.display==display);
 // Missing assets still terminate at eight seconds instead of waiting forever.
 reset(war.data());directory/=L"missing-directory";now_ms+=10;on_result(war.data(),0,0);assert(begin_actor(war.data(),0,0));before_frame(war.data());assert(!cast.ready&&has_tail(war.data()));now_ms+=8000;assert(!has_tail(war.data()));reset(war.data());
 // Valid pack headers with corrupt frame payloads must stop drawing while
 // preserving finite timeline completion. No stale decoded image may appear.
 const auto bad=std::filesystem::current_path()/L"corrupt-frame-pack";std::filesystem::create_directories(bad);
 std::vector<Byte> malformed(24+240*12+240*4,0);std::memcpy(malformed.data(),"BULLFX01",8);
 auto word=[&](unsigned off,std::uint32_t value){std::memcpy(malformed.data()+off,&value,4);};word(8,1040);word(12,807);word(16,240);word(20,30);
 for(unsigned tick=0;tick<240;++tick){std::uint64_t offset=24+240*12+tick*4;std::memcpy(malformed.data()+24+tick*12,&offset,8);word(32+tick*12,4);}word(24+240*12,1);
 for(const wchar_t* name:{L"player-ground.bfx",L"player-foreground.bfx"}){std::ofstream file(bad/name,std::ios::binary);file.write(reinterpret_cast<const char*>(malformed.data()),malformed.size());}
 directory=bad;now_ms+=10;on_result(war.data(),0,0);assert(begin_actor(war.data(),0,0)&&cast.ready);before_frame(war.data());begin_battle_draw(renderer.data());
 const auto corrupt_before=f.pixels;draw_ground(display,0);draw_foreground(display,0);end_battle_draw();assert(!cast.ready&&f.pixels==corrupt_before&&has_tail(war.data()));now_ms+=8000;assert(!has_tail(war.data()));finish_actor(war.data(),0,0);
 // Full battle reset cancels queued visuals even before their first frame.
 on_result(war.data(),1,2);assert(queued_count==1&&!cast.war);reset(war.data());assert(!cast.war&&!has_tail(war.data())&&!queued_count);
 // Two native owners may arrive in the same packet batch. Their fixed8s
 // timelines follow native actor selection, not packet arrival order.
 directory=std::filesystem::path(argv[1]);on_result(war.data(),0,0);on_result(war.data(),1,2);on_result(war.data(),0,0);assert(queued_count==2);
 // Enqueue A then B, but native selects B first: it must start immediately.
 assert(begin_actor(war.data(),1,2));first=cast.start;assert(cast.side==1);
 now_ms+=2000;before_frame(war.data());assert(!begin_actor(war.data(),0,0)&&cast.side==1&&elapsed_ms(war.data())==2000);
 finish_actor(war.data(),0,0);assert(cast.side==1&&queued_count==2);
 now_ms=first+8000;finish_actor(war.data(),1,2);assert(queued_count==1&&!cast.war);assert(begin_actor(war.data(),0,0));assert(cast.side==0&&elapsed_ms(war.data())==0);
 now_ms+=7999;assert(has_tail(war.data()));now_ms+=1;assert(!has_tail(war.data()));finish_actor(war.data(),0,0);assert(!queued_count&&!cast.war);
 // Invalid owner coordinates never enter the queue; cancellation removes all.
 on_result(war.data(),2,0);on_result(war.data(),0,14);assert(!queued_count);
 for(unsigned side=0;side<2;++side)for(unsigned slot=0;slot<14;++slot)on_result(war.data(),side,slot);assert(queued_count==28);reset(nullptr);assert(!queued_count);
 // Direction gate: actual begin_actor must open that caster side's pack for
 // both layers on every frame, including switching back after an enemy cast.
 unsigned direction_frames=0;
 for(unsigned side:{0u,1u,0u}){
  frames::Pack expected_ground,expected_foreground,opposite;
  const std::wstring prefix=side?L"enemy":L"player",other=side?L"player":L"enemy";
  assert(expected_ground.open((directory/(prefix+L"-ground.bfx")).wstring()));
  assert(expected_foreground.open((directory/(prefix+L"-foreground.bfx")).wstring()));
  assert(opposite.open((directory/(other+L"-foreground.bfx")).wstring()));
  on_result(war.data(),side,0);assert(begin_actor(war.data(),side,0)&&cast.ready);
  bool different_direction=false;
  for(unsigned tick=0;tick<240;++tick){
   assert(cast.ground.frame(tick)&&cast.foreground.frame(tick));
   assert(expected_ground.frame(tick)&&expected_foreground.frame(tick)&&opposite.frame(tick));
   assert(cast.ground.rgba==expected_ground.rgba&&cast.foreground.rgba==expected_foreground.rgba);
   different_direction|=cast.foreground.rgba!=opposite.rgba;direction_frames+=2;
  }
  assert(different_direction);finish_actor(war.data(),side,0);
 }
 std::cout<<"bull direction layer-frame comparisons="<<direction_frames<<" passed\n";
 std::cout<<"bull lifecycle: same-caster repeat, focus reset,800/1024 UI restore16/32bit padded +/-pitch, missing-pack completion and cancellation passed\n";
}
