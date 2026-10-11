#include "bull_effect.h"
#include "bull_frames.h"
#include <windows.h>
#include <ddraw.h>
#include <mmsystem.h>
#include <array>
#include <cmath>
#include <filesystem>
#include <memory>
#include <cstdio>
namespace bull_effect {
namespace {
using Byte=unsigned char;
template<class T>T read(const void* p,unsigned o){T v{};std::memcpy(&v,static_cast<const Byte*>(p)+o,sizeof(v));return v;}
std::uintptr_t image_base{};void* audio_owner{};void* drawing_renderer{};
unsigned recording_hit{};
void note(const char* s);
std::filesystem::path directory;
struct Audio {
 HWAVEOUT device{};WAVEHDR header{};std::vector<Byte> samples;
 void stop(){if(device){waveOutReset(device);waveOutUnprepareHeader(device,&header,sizeof(header));waveOutClose(device);}device=nullptr;header={};samples.clear();}
 void play(const std::filesystem::path& path){
  stop();if(!audio_owner||!read<Byte>(audio_owner,0x7f19)||!read<void*>(audio_owner,0)){note("BULL150 audio unavailable or muted\r\n");return;}
  std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file)return;const auto n=file.tellg();if(n<44||n>16*1024*1024)return;
  std::vector<Byte> bytes(static_cast<std::size_t>(n));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),n);
  if(!file||std::memcmp(bytes.data(),"RIFF",4)||std::memcmp(bytes.data()+8,"WAVE",4))return;
  WAVEFORMATEX format{};bool found_format=false,found_data=false;
  for(std::size_t p=12;p+8<=bytes.size();){const auto size=frames::u32(bytes.data()+p+4);if(size>bytes.size()-p-8)return;
   if(!std::memcmp(bytes.data()+p,"fmt ",4)){if(size<16)return;std::memcpy(&format,bytes.data()+p+8,16);found_format=true;}
   if(!std::memcmp(bytes.data()+p,"data",4)){samples.assign(bytes.begin()+p+8,bytes.begin()+p+8+size);found_data=true;}
   p+=8+size+(size&1);
  }
  if(!found_format||!found_data||format.wFormatTag!=WAVE_FORMAT_PCM||format.nChannels<1||format.nChannels>2||
     format.nSamplesPerSec<8000||format.nSamplesPerSec>48000||(format.wBitsPerSample!=8&&format.wBitsPerSample!=16)||
     format.nBlockAlign!=format.nChannels*(format.wBitsPerSample/8)||format.nAvgBytesPerSec!=format.nSamplesPerSec*format.nBlockAlign||
     samples.size()%format.nBlockAlign||samples.size()>std::size_t(format.nAvgBytesPerSec)*9){samples.clear();return;}
  // Native44E870 selects effect volume DWORD+7F14;44EBF0 clamps0..10
  // and reads DirectSound hundredth-dB table VA570C30. Scale only this owned
  // sample buffer, never the OS/global output device volume.
  const int level=std::clamp(read<int>(audio_owner,0x7f14),0,10);
  if(!level){samples.clear();return;}
  const int db=read<int>(reinterpret_cast<const void*>(image_base),0x170c30+unsigned(level)*4);
  const float gain=std::clamp(std::pow(10.0f,float(db)/2000.0f),0.0f,1.0f);
  // Keep the whistle unchanged; strengthen only the approved hoofbeat tail.
  // A20ms ramp avoids a gain discontinuity; soft limiting prevents clipping.
  const auto boosted=[&](float sample,std::size_t index,float maximum){
   const float seconds=float(index/format.nBlockAlign)/format.nSamplesPerSec;
   const float amount=std::clamp((seconds-0.8373923f)/0.02f,0.0f,1.0f);
   return (amount>0?maximum*std::tanh(sample*(1.0f+1.5f*amount)/maximum):sample)*gain;
  };
  if(format.wBitsPerSample==16){for(std::size_t i=0;i<samples.size();i+=2){std::int16_t v{};std::memcpy(&v,samples.data()+i,2);v=static_cast<std::int16_t>(std::lround(boosted(float(v),i,32767.0f)));std::memcpy(samples.data()+i,&v,2);}}
  else for(std::size_t i=0;i<samples.size();++i)samples[i]=Byte(std::clamp(int(std::lround(boosted(float(int(samples[i])-128),i,127.0f)))+128,0,255));
  if(waveOutOpen(&device,WAVE_MAPPER,&format,0,0,CALLBACK_NULL)!=MMSYSERR_NOERROR){device=nullptr;samples.clear();note("BULL150 audio device open failed\r\n");return;}
  header.lpData=reinterpret_cast<char*>(samples.data());header.dwBufferLength=static_cast<DWORD>(samples.size());
  if(waveOutPrepareHeader(device,&header,sizeof(header))!=MMSYSERR_NOERROR||waveOutWrite(device,&header,sizeof(header))!=MMSYSERR_NOERROR){note("BULL150 audio submit failed\r\n");stop();}
  else note("BULL150 audio buffer submitted\r\n");
 }
} audio;
struct Pending {void* war{};unsigned side{},slot{};};
std::array<Pending,28> queued{};unsigned queued_count{};
struct Cast {void* war{};void* display{};void* screen{};unsigned side{},slot{},start{},tick{};bool started{},ready{},reported{},shake_reported{};frames::Pack ground,foreground;std::array<float,480> shake{};} cast;
void clear(){audio.stop();cast.ground.close();cast.foreground.close();cast.war=nullptr;cast.display=nullptr;cast.screen=nullptr;cast.started=cast.ready=cast.reported=cast.shake_reported=false;cast.tick=0;}
void note(const char* s){HANDLE f=CreateFileA("shunying-clone.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);if(f!=INVALID_HANDLE_VALUE){DWORD n;WriteFile(f,s,DWORD(std::strlen(s)),&n,nullptr);CloseHandle(f);}}
IDirectDrawSurface7* surface(void* renderer){if(!renderer)return nullptr;void* cdx=read<void*>(renderer,0xa0);return cdx?read<IDirectDrawSurface7*>(cdx,0x80):nullptr;}
bool valid(const DDSURFACEDESC2& d){return d.lpSurface&&d.dwWidth&&d.dwHeight&&d.dwWidth<=4096&&d.dwHeight<=2160&&(d.ddpfPixelFormat.dwFlags&DDPF_RGB)&&
 (d.ddpfPixelFormat.dwRGBBitCount==16||d.ddpfPixelFormat.dwRGBBitCount==32)&&std::abs(std::int64_t(d.lPitch))>=std::int64_t(d.dwWidth*(d.ddpfPixelFormat.dwRGBBitCount/8));}
bool active(){return cast.war&&cast.started&&cast.ready&&DWORD(GetTickCount()-cast.start)<8000;}
struct Mapping {
 unsigned width{},height{},y0{},y1{};std::vector<unsigned> x,y;
 void configure(unsigned w,unsigned h){if(width==w&&height==h)return;x.resize(w);y.resize(h);
  // Draw the whole canvas. The original preview's UI crop slices running
  // bulls horizontally in the real client; native UI renders above us.
  y0=0;y1=h;
  for(unsigned n=0;n<w;++n)x[n]=std::min(1039u,unsigned(std::floor(double(n)*1024.0/w+8.0)));
  for(unsigned n=0;n<h;++n)y[n]=std::min(806u,unsigned(std::max(0.0,std::floor(double(n)*768.0/h-1.0))));
  width=w;height=h;
 }
} mapping;
frames::BlendTable colors;
void paint(frames::Pack& pack,void* display,unsigned viewport){
 if(!active()||!drawing_renderer||display!=cast.display||display!=read<void*>(drawing_renderer,0xa8)||viewport!=0)return;
 if(!pack.frame(cast.tick)){note("BULL150 invalid frame; disabling visual pack\r\n");cast.ready=false;return;}
 auto* target=surface(drawing_renderer);if(!target)return;DDSURFACEDESC2 d{};d.dwSize=sizeof(d);
 if(FAILED(target->Lock(nullptr,&d,DDLOCK_WAIT,nullptr)))return;
 if(valid(d)){
  const unsigned bytes=d.ddpfPixelFormat.dwRGBBitCount/8;
  // Allocation is only needed on a display-size change; never leave it locked
  // if that allocation fails. All steady-state coordinates/colors are cached.
  try{mapping.configure(d.dwWidth,d.dwHeight);}catch(...){target->Unlock(nullptr);return;}
  if(!colors.matches(d.ddpfPixelFormat.dwRBitMask,d.ddpfPixelFormat.dwGBitMask,d.ddpfPixelFormat.dwBBitMask))colors.configure(d.ddpfPixelFormat.dwRBitMask,d.ddpfPixelFormat.dwGBitMask,d.ddpfPixelFormat.dwBBitMask);
  if(!cast.reported){char line[192]{};std::snprintf(line,sizeof(line),"BULL150 native surface %lux%lu bits%lu fixed800x600 preview mapping x*1.28+8,y*1.28-1\r\n",d.dwWidth,d.dwHeight,d.ddpfPixelFormat.dwRGBBitCount);note(line);cast.reported=true;}
  const unsigned y0=mapping.y0,y1=mapping.y1;
  for(unsigned y=y0;y<y1;++y){Byte* row=static_cast<Byte*>(d.lpSurface)+std::ptrdiff_t(y)*d.lPitch;const unsigned sy=mapping.y[y];
   for(unsigned x=0;x<d.dwWidth;++x){const unsigned sx=mapping.x[x];const Byte* src=pack.rgba.data()+(std::size_t(sy)*pack.width+sx)*4;if(!src[3])continue;
    std::uint32_t dst=0;std::memcpy(&dst,row+x*bytes,bytes);dst=colors.valid?colors.apply(dst,src):frames::blend(dst,src,d.ddpfPixelFormat.dwRBitMask,d.ddpfPixelFormat.dwGBitMask,d.ddpfPixelFormat.dwBBitMask);std::memcpy(row+x*bytes,&dst,bytes);
   }
  }
 }
 target->Unlock(nullptr);
}
// Final-present temporary copy; restored after native present even if it fails.
struct Present {IDirectDrawSurface7* surface{};unsigned width{},height{},bytes{},depth{};std::vector<Byte> original;} present;
}
void initialize(std::uintptr_t base){image_base=base;recording_hit=0;wchar_t path[32768]{};const DWORD n=GetModuleFileNameW(nullptr,path,32768);if(n&&n<32768){
 const auto root=std::filesystem::path(path).parent_path();directory=root/L"Data2"/L"Fight"/L"Custom"/L"Bull150";
 unsigned value{};std::ifstream setting(root/L"recording-fixed-damage.txt");
 if(setting>>value && value==9999)recording_hit=value;
}}
unsigned recording_damage(){return recording_hit;}
void preload(void* battle){
 // 516AE0 receives the battle owner. Its +20 points to the UI owner;
 // CFF5C is a UI offset, not a battle offset.
 void* ui=battle?read<void*>(battle,0x20):nullptr;
 audio_owner=ui?read<void*>(ui,0xcff5c):nullptr;
}
void on_result(void* war,unsigned side,unsigned slot){
 if(!image_base||!war||side>1||slot>=14)return;
 if((cast.war&&cast.war!=war)||(queued_count&&queued[0].war!=war)){clear();queued_count=0;}
 for(unsigned i=0;i<queued_count;++i)if(queued[i].war==war&&queued[i].side==side&&queued[i].slot==slot)return;
 if(queued_count<queued.size())queued[queued_count++]={war,side,slot};
}
bool begin_actor(void* war,unsigned side,unsigned slot){
 if(!war||side>1||slot>=14)return false;
 if(cast.war)return cast.war==war&&cast.side==side&&cast.slot==slot;
 // Result arrival order is not native actor execution order. The actual
 // 524820 caller may claim any pending owner when no cast is active.
 bool pending=false;for(unsigned i=0;i<queued_count;++i)if(queued[i].war==war&&queued[i].side==side&&queued[i].slot==slot){pending=true;break;}
 if(!pending)return false;
 clear();cast.war=war;cast.side=side;cast.slot=slot;
 void* manager=read<void*>(war,0xc);cast.display=manager?read<void*>(manager,4):nullptr;
 const wchar_t* prefix=side?L"enemy":L"player";
 try {
 cast.ready=cast.ground.open((directory/(std::wstring(prefix)+L"-ground.bfx")).wstring())&&cast.foreground.open((directory/(std::wstring(prefix)+L"-foreground.bfx")).wstring());
 for(unsigned t=0;t<240;++t){const float amp=2.3f+((t>=40&&t<=155)?2.2f:0.0f)+1.1f*std::abs(std::sin(t*1.7f));cast.shake[t*2]=std::floor(std::sin(t*5.37f)*amp+0.5f);cast.shake[t*2+1]=std::floor(std::cos(t*4.11f)*amp*.68f+0.5f);}
 std::ifstream shake(directory/L"shake.f32",std::ios::binary);if(shake)shake.read(reinterpret_cast<char*>(cast.shake.data()),sizeof(cast.shake));
 for(float& v:cast.shake)if(!std::isfinite(v)||std::abs(v)>16)v=0;
 }catch(...){cast.ready=false;cast.ground.close();cast.foreground.close();}
 note(cast.ready?"BULL150 fixed 240-frame composition started\r\n":"BULL150 visual pack missing or invalid\r\n");
 cast.started=true;
 try{audio.play(directory/L"bull-stampede-native-voice.wav");}catch(...){audio.stop();}
 cast.start=GetTickCount();cast.tick=0;
 return true;
}
void finish_actor(void* war,unsigned side,unsigned slot){
 if(cast.war!=war||cast.side!=side||cast.slot!=slot)return;
 clear();
 for(unsigned i=0;i<queued_count;++i)if(queued[i].war==war&&queued[i].side==side&&queued[i].slot==slot){
  for(unsigned j=i+1;j<queued_count;++j)queued[j-1]=queued[j];--queued_count;break;}
}
void before_frame(void* war){if(cast.war!=war||!cast.started)return;void* manager=read<void*>(war,0xc);cast.display=manager?read<void*>(manager,4):nullptr;cast.tick=std::min<unsigned>(239u,DWORD(GetTickCount()-cast.start)*30/1000);if(audio.device&&audio_owner&&!read<Byte>(audio_owner,0x7f19))audio.stop();}
unsigned elapsed_ms(void* war){return cast.war==war&&cast.started?DWORD(GetTickCount()-cast.start):0;}
bool has_tail(void* war){return cast.war==war&&cast.started&&DWORD(GetTickCount()-cast.start)<8000;}
void reset(void* war){if(!war||cast.war==war)clear();unsigned kept=0;for(unsigned i=0;i<queued_count;++i)if(war&&queued[i].war!=war)queued[kept++]=queued[i];queued_count=kept;}
void reset_display(void* display){if(cast.display==display){cast.display=nullptr;cast.screen=nullptr;}}
void begin_battle_draw(void* renderer){drawing_renderer=renderer;if(renderer&&cast.display&&read<void*>(renderer,0xa8)==cast.display)cast.screen=read<void*>(renderer,0x9c);}
void end_battle_draw(){drawing_renderer=nullptr;}
const void* damage_source(void* display,unsigned viewport){
 if(!active()||!drawing_renderer||viewport!=0||display!=cast.display||display!=read<void*>(drawing_renderer,0xa8))return nullptr;
 return read<void*>(cast.war,0x38+((cast.side*14+cast.slot)*6)*4);
}
void draw_ground(void* display,unsigned viewport){try{paint(cast.ground,display,viewport);}catch(...){cast.ready=false;note("BULL150 ground resource allocation failed\r\n");}}
void draw_foreground(void* display,unsigned viewport){try{paint(cast.foreground,display,viewport);}catch(...){cast.ready=false;note("BULL150 foreground resource allocation failed\r\n");}}
void before_surface_present(IDirectDrawSurface7* target){
 // A nested repaint must reuse the outer shifted image, not overwrite its
 // restore snapshot or acquire an unpaired reference.
 if(present.depth++)return;
 present.surface=nullptr;if(!active()||!target)return;
 DDSURFACEDESC2 d{};d.dwSize=sizeof(d);if(FAILED(target->Lock(nullptr,&d,DDLOCK_WAIT,nullptr)))return;
 if(valid(d)){
  const int dx=int(std::lround(cast.shake[cast.tick*2]*d.dwWidth/1024.0f)),dy=int(std::lround(cast.shake[cast.tick*2+1]*d.dwHeight/768.0f));
  if(dx||dy){const unsigned bytes=d.ddpfPixelFormat.dwRGBBitCount/8,row=d.dwWidth*bytes;try{present.original.resize(std::size_t(row)*d.dwHeight);}catch(...){target->Unlock(nullptr);return;}
   for(unsigned y=0;y<d.dwHeight;++y)std::memcpy(present.original.data()+std::size_t(y)*row,static_cast<Byte*>(d.lpSurface)+std::ptrdiff_t(y)*d.lPitch,row);
   for(unsigned y=0;y<d.dwHeight;++y){Byte* dst=static_cast<Byte*>(d.lpSurface)+std::ptrdiff_t(y)*d.lPitch;const int sy=std::clamp(int(y)-dy,0,int(d.dwHeight)-1);
    for(unsigned x=0;x<d.dwWidth;++x){const int sx=std::clamp(int(x)-dx,0,int(d.dwWidth)-1);std::memcpy(dst+x*bytes,present.original.data()+std::size_t(sy)*row+sx*bytes,bytes);}}
   // Native presentation can trigger a focus/device rebuild. Hold the exact
   // COM surface alive across that call; a replaced pointer must not dangle.
   target->AddRef();present.surface=target;present.width=d.dwWidth;present.height=d.dwHeight;present.bytes=bytes;
   if(!cast.shake_reported){note("BULL150 final screen backbuffer shake applied\r\n");cast.shake_reported=true;}
  }
 }
 target->Unlock(nullptr);
}
void before_present(void* renderer){before_surface_present(renderer&&read<void*>(renderer,0xa8)==cast.display?surface(renderer):nullptr);}
void before_screen_present(void* screen){
 // 53CA50 is the common final screen presenter. Its +10 is the backbuffer
 // already containing the full frame; renderer+A0 has already been copied.
 void* cdx=screen&&screen==cast.screen?read<void*>(screen,0x10):nullptr;
 before_surface_present(cdx?read<IDirectDrawSurface7*>(cdx,0x80):nullptr);
}
void before_renderer_present(void* renderer){
 // 432A20 mode!=0 blits directly through COM and never calls53CA50.
 // Surround the entire renderer presenter to cover both native branches.
 const bool ours=renderer&&cast.display&&read<void*>(renderer,0xa8)==cast.display;
 if(ours)cast.screen=read<void*>(renderer,0x9c);
 before_screen_present(ours?cast.screen:nullptr);
}
void after_present(){
 if(!present.depth||--present.depth)return;
 auto* target=present.surface;present.surface=nullptr;if(!target)return;DDSURFACEDESC2 d{};d.dwSize=sizeof(d);if(FAILED(target->Lock(nullptr,&d,DDLOCK_WAIT|DDLOCK_WRITEONLY,nullptr))){target->Release();return;}
 if(valid(d)&&d.dwWidth==present.width&&d.dwHeight==present.height&&d.ddpfPixelFormat.dwRGBBitCount==present.bytes*8){const unsigned row=present.width*present.bytes;for(unsigned y=0;y<d.dwHeight;++y)std::memcpy(static_cast<Byte*>(d.lpSurface)+std::ptrdiff_t(y)*d.lPitch,present.original.data()+std::size_t(y)*row,row);}
 target->Unlock(nullptr);target->Release();
}
}
