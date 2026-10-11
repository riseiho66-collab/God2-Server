// Internal integration: actual tick, owner scheduler, file streams, compositing
// and presentation restoration. Native actor/DirectDraw APIs are bounded sinks.
#include <windows.h>
#include <mmsystem.h>
#include <cassert>
#include <vector>
static unsigned audio_opens{},audio_writes{},audio_closes{};
static std::vector<char> last_audio;
MMRESULT WINAPI pipeline_open(LPHWAVEOUT out,UINT device,LPCWAVEFORMATEX fmt,DWORD_PTR,DWORD_PTR,DWORD flags){
 assert(device==WAVE_MAPPER&&fmt->wFormatTag==WAVE_FORMAT_PCM&&flags==CALLBACK_NULL);
 *out=reinterpret_cast<HWAVEOUT>(123);++audio_opens;return MMSYSERR_NOERROR;
}
MMRESULT WINAPI pipeline_prepare(HWAVEOUT,LPWAVEHDR header,UINT){assert(header->dwBufferLength>10000);return MMSYSERR_NOERROR;}
MMRESULT WINAPI pipeline_write(HWAVEOUT,LPWAVEHDR header,UINT){
 bool nonzero=false;for(unsigned i=0;i<header->dwBufferLength;++i)nonzero|=header->lpData[i]!=0;
 assert(nonzero);last_audio.assign(header->lpData,header->lpData+header->dwBufferLength);++audio_writes;return MMSYSERR_NOERROR;
}
MMRESULT WINAPI pipeline_header(HWAVEOUT,LPWAVEHDR,UINT){return MMSYSERR_NOERROR;}
MMRESULT WINAPI pipeline_reset(HWAVEOUT){return MMSYSERR_NOERROR;}
MMRESULT WINAPI pipeline_close(HWAVEOUT){++audio_closes;return MMSYSERR_NOERROR;}
#define waveOutOpen pipeline_open
#define waveOutPrepareHeader pipeline_prepare
#define waveOutWrite pipeline_write
#define waveOutUnprepareHeader pipeline_header
#define waveOutReset pipeline_reset
#define waveOutClose pipeline_close
static DWORD simulated_ms=100;
DWORD pipeline_clock(){return simulated_ms;}
#define GetTickCount pipeline_clock
#include "bull_effect.cpp"
#undef GetTickCount
#define BULL_TICK_TEST
#include "bull_native_tick.cpp"
#include <iostream>
#include <stdexcept>

namespace fixture {
using Byte=unsigned char;
void check(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class T>T get(const void* p,unsigned offset){T value{};std::memcpy(&value,static_cast<const Byte*>(p)+offset,sizeof(value));return value;}
template<class T>void put(void* p,unsigned offset,T value){std::memcpy(static_cast<Byte*>(p)+offset,&value,sizeof(value));}
std::array<std::array<Byte,4096>,28> actors{};
std::array<Byte,110> definition{};
std::array<Byte,0x400> war{};
std::array<Byte,64> manager{};
std::array<Byte,192> renderer{},cdx{},screen{},screen_cdx{};
unsigned floating{},completed{},native_deaths{};
void* __fastcall lookup(void*,void*,unsigned side,unsigned slot,unsigned kind){check(side<2&&slot<14&&kind==0,"actor lookup");return actors[side*14+slot].data();}
void __fastcall pose(void*,void*,void* target,unsigned state,unsigned once){check(once==1,"pose mode");if(state==9){++native_deaths;put<Byte>(target,0x1ea,9);}}
void __fastcall text(void*,void*,unsigned side,unsigned slot,unsigned target_side,unsigned target_slot,int delta,unsigned zero,unsigned status,unsigned end){
 check(side<2&&slot<14&&target_side==1-side&&target_slot<14&&zero==0&&status==0&&end==28,"native text args");
 auto* source=actors[side*14+slot].data();auto index=get<Byte>(source,0x239);check(index<14,"text index");put<std::int16_t>(source,0x28a+index*2,static_cast<std::int16_t>(delta));
}
void __fastcall hp(void*,void*,void* target,int delta){put<int>(target,0xde8,std::max(0,get<int>(target,0xde8)+delta));}
void __fastcall bar(void*,void*,void*){}
void __fastcall show(void*,void*){++floating;}
unsigned __fastcall cleanup(void*,void*,void* source){check(get<Byte>(source,0x233)==7,"native cleanup phase");put<Byte>(source,0x239,0);put<Byte>(source,0x259,1);++completed;return 1;}
struct Surface {void** table{};unsigned refs{1};std::vector<Byte> pixels=std::vector<Byte>(800*600*2);};
HRESULT __stdcall lock(IDirectDrawSurface7* pointer,LPRECT,LPDDSURFACEDESC2 d,DWORD,HANDLE){
 auto& s=*reinterpret_cast<Surface*>(pointer);d->dwWidth=800;d->dwHeight=600;d->lPitch=1600;d->lpSurface=s.pixels.data();
 d->ddpfPixelFormat.dwFlags=DDPF_RGB;d->ddpfPixelFormat.dwRGBBitCount=16;d->ddpfPixelFormat.dwRBitMask=0xf800;d->ddpfPixelFormat.dwGBitMask=0x7e0;d->ddpfPixelFormat.dwBBitMask=31;return DD_OK;
}
HRESULT __stdcall unlock(IDirectDrawSurface7*,LPRECT){return DD_OK;}
ULONG __stdcall addref(IDirectDrawSurface7* p){return ++reinterpret_cast<Surface*>(p)->refs;}
ULONG __stdcall release(IDirectDrawSurface7* p){return --reinterpret_cast<Surface*>(p)->refs;}
std::array<void*,45> vtable{};Surface surface,backbuffer;
void* display=reinterpret_cast<void*>(1234);
void initialize(){
 bull_effect::reset(nullptr);bull_native_tick::initialize(0);actors={};definition={};definition[0]=150;
 floating=completed=native_deaths=0;simulated_ms+=100;
 put(war.data(),0xc,manager.data());put(manager.data(),4,display);
 put(renderer.data(),0xa0,cdx.data());put(renderer.data(),0xa8,display);put(cdx.data(),0x80,&surface);
 put(renderer.data(),0x9c,screen.data());put(screen.data(),0x10,screen_cdx.data());put(screen_cdx.data(),0x80,&backbuffer);
 for(unsigned i=0;i<28;++i){put<Byte>(actors[i].data(),0x234,static_cast<Byte>((i/14)*128+i%14));put(war.data(),0x38+i*6*4,actors[i].data());}
}
void prepare(unsigned source_slot,unsigned count,int damage,bool lethal){
 auto* source=actors[source_slot].data();const unsigned side=source_slot/14;
 put(source,0xec4,definition.data());put<Byte>(source,0x239,static_cast<Byte>(count));put<Byte>(source,0x259,0);
 for(unsigned i=0;i<count;++i){put<Byte>(source,0x23a+i,static_cast<Byte>((1-side)*128+i));
  put<std::int16_t>(source,0x28a+i*2,static_cast<std::int16_t>(-damage));put<Byte>(source,0x224+i,lethal?9:0);}
 bull_effect::on_result(war.data(),side,source_slot%14);
}
unsigned exercise(unsigned side,unsigned count,bool shared,bool reverse,const std::filesystem::path& packs){
 initialize();const unsigned first=side*14,second=shared?side*14+13:first,enemy=(1-side)*14;
 prepare(first,count,100,false);if(shared)prepare(second,count,100,true);
 for(unsigned i=0;i<count;++i){auto* target=actors[enemy+i].data();put<int>(target,0xde8,200);put<Byte>(target,0x232,shared?9:0);put<Byte>(target,0x277,shared?2:1);}
 const auto native=reinterpret_cast<bull_native_tick::Original>(&cleanup);
 const std::array<unsigned,2> order=reverse?std::array<unsigned,2>{second,first}:std::array<unsigned,2>{first,second};
 for(unsigned turn=0;turn<2;++turn){
  if(!shared&&turn){prepare(first,count,100,true);for(unsigned i=0;i<count;++i){put<Byte>(actors[enemy+i].data(),0x232,9);put<Byte>(actors[enemy+i].data(),0x277,1);}}
  auto* source=actors[order[turn]].data();const auto started=simulated_ms;
  check(bull_native_tick::step(war.data(),source,native)==0,"cast start");
  check(bull_effect::cast.side==side&&bull_effect::elapsed_ms(war.data())==0,"side or cast clock");
  for(unsigned ms:{2333u,2334u,3667u,5000u,6333u,6334u,7999u}){
   simulated_ms=started+ms;bull_effect::before_frame(war.data());check(bull_native_tick::step(war.data(),source,native)==0,"early completion");
   if(ms==5000&&shared&&turn==0){
    check(bull_native_tick::step(war.data(),actors[order[1]].data(),native)==0,"waiting owner");
    check(bull_effect::elapsed_ms(war.data())==5000&&bull_effect::cast.slot==order[0]%14,"waiting owner changed active clock");
   }
   if(ms==2334||ms==3667||ms==5000||ms==6334){
    std::fill(surface.pixels.begin(),surface.pixels.end(),Byte{0x6b});const auto blank=surface.pixels;
    check(!bull_effect::damage_source(display,0),"damage overlay outside battle pass");
    bull_effect::begin_battle_draw(renderer.data());
    check(bull_effect::damage_source(display,0)==source,"damage overlay wrong casting owner");
    check(!bull_effect::damage_source(display,1)&&!bull_effect::damage_source(nullptr,0),"damage overlay escaped battle viewport");
    bull_effect::draw_ground(display,0);bull_effect::draw_foreground(display,0);bull_effect::end_battle_draw();
    check(bull_effect::cast.ready&&surface.pixels!=blank,"actual frame layers not rendered");
    const auto frame=ms*30/1000;
    bull_effect::frames::Pack expected;check(expected.open((packs/(side?L"enemy-ground.bfx":L"player-ground.bfx")).wstring())&&expected.frame(frame),"expected side pack");
    check(expected.rgba==bull_effect::cast.ground.rgba,"wrong casting-side frame pack");
    // Independently compare every destination pixel, including above/below
    // the former preview crop. Native viewport1/UI is composited afterward.
    unsigned upper=0;
    for(unsigned y=0;y<600;++y)for(unsigned x=0;x<800;++x){
     const unsigned sx=unsigned(std::floor(double(x)*1024/800+8)),sy=unsigned(std::max(0.0,std::floor(double(y)*768/600-1)));
     const auto offset=(std::size_t(sy)*1040+sx)*4;
     const auto* ground=bull_effect::cast.ground.rgba.data()+offset;
     const auto* front=bull_effect::cast.foreground.rgba.data()+offset;
     auto pixel=bull_effect::frames::blend(0x6b6b,ground,0xf800,0x7e0,31);
     pixel=bull_effect::frames::blend(pixel,front,0xf800,0x7e0,31);
     check(get<std::uint16_t>(surface.pixels.data(),(y*800+x)*2)==pixel,"full canvas composition mismatch");
     if(sy<99&&front[3])++upper;
    }
    if(ms==2334)check(upper>100,"pack still clips upper edge");
    const auto composed=surface.pixels;backbuffer.pixels=composed;
    bull_effect::before_renderer_present(renderer.data());
    check(backbuffer.pixels!=composed&&surface.pixels==composed&&backbuffer.refs==2,"final screen shake absent or wrong buffer");
    if(turn==0){
     const auto shifted=backbuffer.pixels;bull_effect::before_screen_present(screen.data());
     check(backbuffer.pixels==shifted&&backbuffer.refs==2,"nested screen presenter double shake");
     bull_effect::after_present();check(backbuffer.pixels==shifted&&backbuffer.refs==2,"nested screen presenter early restore");
    }
    bull_effect::after_present();check(backbuffer.pixels==composed&&backbuffer.refs==1,"presentation restore");
    bull_effect::reset_display(display);bull_effect::before_frame(war.data());check(bull_effect::elapsed_ms(war.data())==ms&&bull_effect::cast.display==display,"focus restart");
   }
   const unsigned percent=ms<2334?0:ms<3667?20:ms<5000?45:ms<6334?75:100;
   for(unsigned i=0;i<count;++i){auto* target=actors[enemy+i].data();check(get<int>(target,0xde8)==200-int(turn)*100-int(percent),"four-phase HP mismatch");
    if(ms<6334)check(get<Byte>(target,0x1ea)!=9,"premature death");
    if(shared)check(get<Byte>(target,0x277)==(ms<6334?2-turn:1-turn),"shared pending count");
    if(ms>=6334&&turn)check(get<Byte>(target,0x1ea)==9&&get<Byte>(target,0x277)==0,"lethal target not finalized");}
  }
  simulated_ms=started+8000;check(bull_native_tick::step(war.data(),source,native)==1,"8s completion");
  check(!bull_effect::cast.war&&!bull_effect::has_tail(war.data()),"effect owner not released");
 }
 check(floating==8*count&&completed==2&&native_deaths==count&&!bull_effect::queued_count,"result conservation or pending owner leak");
 return 2;
}
}
std::uintptr_t bull_tick_test_native(unsigned rva){using namespace fixture;switch(rva){
 case 0x11e6e0:return reinterpret_cast<std::uintptr_t>(&lookup);case 0x129870:return reinterpret_cast<std::uintptr_t>(&pose);
 case 0x12b060:return reinterpret_cast<std::uintptr_t>(&text);case 0x128a70:return reinterpret_cast<std::uintptr_t>(&hp);
 case 0x12d9f0:return reinterpret_cast<std::uintptr_t>(&bar);case 0x11dcc0:return reinterpret_cast<std::uintptr_t>(&show);
 default:throw std::runtime_error("Unexpected native API");}}
int main(int argc,char** argv){try{using namespace fixture;check(argc==2,"pack directory required");
 vtable[1]=reinterpret_cast<void*>(&addref);vtable[2]=reinterpret_cast<void*>(&release);vtable[25]=reinterpret_cast<void*>(&lock);vtable[32]=reinterpret_cast<void*>(&unlock);surface.table=backbuffer.table=vtable.data();
 std::vector<Byte> image(0x180000),ui(0xd0000),sound(0x8000),battle(0xd0000);
 put(battle.data(),0x20,ui.data());put(ui.data(),0xcff5c,sound.data());put(sound.data(),0,reinterpret_cast<void*>(123));
 put<Byte>(sound.data(),0x7f19,1);put<int>(sound.data(),0x7f14,10);
 bull_effect::image_base=reinterpret_cast<std::uintptr_t>(image.data());bull_effect::directory=std::filesystem::path(argv[1]);
 bull_effect::preload(battle.data());check(bull_effect::audio_owner==sound.data(),"battle to UI audio owner chain");
 unsigned cases=0,casts=0;
 for(unsigned side:{0u,1u})for(unsigned targets:{1u,2u,14u}){
  casts+=exercise(side,targets,false,false,bull_effect::directory);++cases;
  for(bool reverse:{false,true}){casts+=exercise(side,targets,true,reverse,bull_effect::directory);++cases;}}
 check(audio_opens==36&&audio_writes==36&&audio_closes==36,"every cast must submit and release audio");
 {std::ofstream pcm("audio-submitted.pcm",std::ios::binary);pcm.write(last_audio.data(),last_audio.size());}
 put<Byte>(sound.data(),0x7f19,0);bull_effect::audio.play(bull_effect::directory/L"bull-stampede-native-voice.wav");check(audio_opens==36,"muted audio played");
 put<Byte>(sound.data(),0x7f19,1);put<int>(sound.data(),0x7f14,0);bull_effect::audio.play(bull_effect::directory/L"bull-stampede-native-voice.wav");check(audio_opens==36,"zero volume audio played");
 std::cout<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"casts\":"<<casts<<",\"player_cases\":9,\"enemy_cases\":9,\"audio_submissions\":"<<audio_writes<<"}\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
