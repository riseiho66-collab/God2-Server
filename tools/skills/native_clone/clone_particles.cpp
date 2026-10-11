#include "clone_particles.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <vector>

#if !defined(_M_IX86) && !defined(SHUNYING_PARTICLE_TEST)
#error Particle adapter requires the verified 32-bit God2 client.
#endif
#if defined(SHUNYING_PARTICLE_TEST)
extern std::uintptr_t particle_test_native(unsigned rva);
#endif

namespace shunying_clone::particles {
namespace {
using Byte = unsigned char;
constexpr unsigned kCasts=28, kNone=0xffff;
constexpr float preview_scale=1.0f/1.28f;
constexpr float pi=3.14159265358979323846f;
std::uintptr_t base{};
template<class T> T get(const void* p,unsigned o) {T v{};std::memcpy(&v,static_cast<const Byte*>(p)+o,sizeof(v));return v;}
template<class T> void put(void* p,unsigned o,T v) {std::memcpy(static_cast<Byte*>(p)+o,&v,sizeof(v));}
template<class T> T native(unsigned rva) {
#if defined(SHUNYING_PARTICLE_TEST)
    return reinterpret_cast<T>(particle_test_native(rva));
#else
    return reinterpret_cast<T>(base+rva);
#endif
}
struct RGB {float r{},g{},b{};};
struct Cast {
    void* display{};unsigned handle{kNone},viewport{},width{},height{};bool drawing{},painted{};
    std::array<Byte,32> bitmap{};
    std::array<std::uint16_t,256> palette{};
    std::vector<Byte> pixels;
};
std::array<Cast,kCasts> casts;
// Calls are sequential on the native render thread. No scratch is referenced
// by native display entries; each cast keeps its OWN indexed bitmap alive.
std::vector<RGB> scratch;
unsigned scratch_width{};
int dirty_left{},dirty_top{},dirty_right{-1},dirty_bottom{-1};
unsigned active=kNone;
constexpr std::array<RGB,8> hues{{
    {255,40,55},{255,63,71},{255,85,97},{255,104,111},
    {255,135,122},{255,166,143},{255,196,163},{255,209,173}}};
RGB rgb(unsigned hex) {return {float((hex>>16)&255),float((hex>>8)&255),float(hex&255)};}
RGB mix(RGB a,RGB b,float p) {return {a.r+(b.r-a.r)*p,a.g+(b.g-a.g)*p,a.b+(b.b-a.b)*p};}
void clear_handle(Cast& c) {
    if(c.display&&c.handle<5000)native<void(__thiscall*)(void*,unsigned)>(0x26a30)(c.display,c.handle);
    c.handle=kNone;
}
std::uint16_t channel(float value,std::uint16_t mask) {
    if(!mask)return 0;unsigned shift=0;while(((mask>>shift)&1)==0&&shift<16)++shift;
    const auto maximum=unsigned(mask)>>shift;
    return std::uint16_t((unsigned(std::lround(std::clamp(value,0.0f,255.0f)*float(maximum)/255.0f))<<shift)&mask);
}
void palette(Cast& c) {
    // 427270 stores DDPIXELFORMAT R/G/B masks here. Support both 555 and565.
    const auto r=get<std::uint16_t>(c.display,0x1210),g=get<std::uint16_t>(c.display,0x1212),b=get<std::uint16_t>(c.display,0x1214);
    for(unsigned h=0;h<8;++h)for(unsigned l=0;l<32;++l) {
        const float p=float(l)/31.0f;
        c.palette[h*32+l]=channel(hues[h].r*p,r)|channel(hues[h].g*p,g)|channel(hues[h].b*p,b);
    }
}
Cast* current(unsigned key) {return key<kCasts&&active==key&&casts[key].drawing?&casts[key]:nullptr;}
bool coordinate(float value) {return std::isfinite(value)&&std::fabs(value)<4096;}
void pixel(Cast& c,int x,int y,RGB color,float alpha) {
    if(x<0||y<0||x>=int(c.width)||y>=int(c.height)||alpha<=0)return;
    RGB& d=scratch[unsigned(y)*c.width+unsigned(x)];
    d.r=std::min(255.0f,d.r+color.r*alpha);d.g=std::min(255.0f,d.g+color.g*alpha);d.b=std::min(255.0f,d.b+color.b*alpha);
    dirty_left=std::min(dirty_left,x);dirty_right=std::max(dirty_right,x);dirty_top=std::min(dirty_top,y);dirty_bottom=std::max(dirty_bottom,y);
    c.painted=true;
}
void glow(Cast& c,float x,float y,float radius,RGB inner,float inner_a,RGB middle,float middle_a,float fade) {
    for(int py=std::max(0,int(std::floor(y-radius)));py<=std::min(int(c.height)-1,int(std::ceil(y+radius)));++py)
        for(int px=std::max(0,int(std::floor(x-radius)));px<=std::min(int(c.width)-1,int(std::ceil(x+radius)));++px) {
            const float dx=px+.5f-x,dy=py+.5f-y,p=std::sqrt(dx*dx+dy*dy)/radius;
            if(p>=1)continue;
            const bool first=p<.35f;const float t=first?p/.35f:(p-.35f)/.65f;
            pixel(c,px,py,first?mix(inner,middle,t):middle,fade*(first?inner_a+(middle_a-inner_a)*t:middle_a*(1-t)));
        }
}
void line(Cast& c,float ax,float ay,float bx,float by,float width,RGB color,float alpha) {
    const float vx=bx-ax,vy=by-ay,length=vx*vx+vy*vy,rad=width*.5f;
    const int x0=std::max(0,int(std::floor(std::min(ax,bx)-rad-1))),x1=std::min(int(c.width)-1,int(std::ceil(std::max(ax,bx)+rad+1)));
    const int y0=std::max(0,int(std::floor(std::min(ay,by)-rad-1))),y1=std::min(int(c.height)-1,int(std::ceil(std::max(ay,by)+rad+1)));
    for(int y=y0;y<=y1;++y)for(int x=x0;x<=x1;++x) {
        const float px=x+.5f-ax,py=y+.5f-ay,t=length>0?std::clamp((px*vx+py*vy)/length,0.0f,1.0f):0;
        const float dx=px-t*vx,dy=py-t*vy;
        pixel(c,x,y,color,alpha*std::clamp(rad+.5f-std::sqrt(dx*dx+dy*dy),0.0f,1.0f));
    }
}
void ellipse(Cast& c,float x,float y,float rx,float ry,float width,RGB color,float alpha) {
    // Signed ellipse-distance approximation gives one smooth stroke; no bright
    // seams from accumulating overlapping segment endpoints.
    for(int py=std::max(0,int(y-ry-width));py<=std::min(int(c.height)-1,int(y+ry+width));++py)
        for(int px=std::max(0,int(x-rx-width));px<=std::min(int(c.width)-1,int(x+rx+width));++px) {
            const float dx=(px+.5f-x)/rx,dy=(py+.5f-y)/ry,q=std::sqrt(dx*dx+dy*dy);
            const float denominator=std::sqrt(dx*dx/(rx*rx)+dy*dy/(ry*ry));
            const float distance=denominator>.00001f?std::fabs(q*(q-1)/denominator):ry;
            pixel(c,px,py,color,alpha*std::clamp(width*.5f+.5f-distance,0.0f,1.0f));
        }
}
void point(float fx,float fy,float tx,float ty,float p,float side,float& x,float& y) {
    const float wave=std::sin(pi*p);x=fx+(tx-fx)*p+wave*side*45*preview_scale;y=fy+(ty-fy)*p-wave*75*preview_scale;
}
}

void initialize(std::uintptr_t image_base) {base=image_base;}
void begin_frame(void* display,unsigned key,unsigned viewport) {
    if(!base||!display||key>=kCasts)return;
    // Original22540 clips against these same native renderer dimensions.
    // The OS window/client size is not used as a coordinate-space guess.
    const unsigned width=get<unsigned>(display,0),height=get<unsigned>(display,4);
    if(!width||!height||width>4096||height>4096||width*height>4096u*2160u){release_cast(key);return;}
    if(active!=kNone&&active!=key)end_frame(active);
    Cast& c=casts[key];if(c.display&&c.display!=display)release_cast(key);
    if(c.width!=width||c.height!=height) {clear_handle(c);c.width=width;c.height=height;c.pixels.resize(width*height);}
    c.display=display;c.viewport=viewport&255;c.drawing=true;c.painted=false;active=key;
    if(scratch.size()!=width*height||scratch_width!=width) scratch.assign(width*height,RGB{});
    else for(int y=dirty_top;y<=dirty_bottom;++y)
        std::fill(scratch.begin()+y*width+dirty_left,scratch.begin()+y*width+dirty_right+1,RGB{});
    scratch_width=width;dirty_left=int(width);dirty_top=int(height);dirty_right=dirty_bottom=-1;
}
void burst(unsigned key,float x,float y,float age,float span) {
    Cast* c=current(key);if(!c||!coordinate(x)||!coordinate(y)||!std::isfinite(age)||!std::isfinite(span)||span<=0||age<0||age>=span)return;
    const float p=age/span,fade=std::sin(pi*p),radius=(18+30*p)*preview_scale;
    glow(*c,x,y-40*preview_scale,75*preview_scale,rgb(0xffb19b),136.0f/255,rgb(0xa91524),102.0f/255,fade);
    ellipse(*c,x,y+7*preview_scale,radius,radius*.35f,2.5f*preview_scale,rgb(0xd75151),fade);
    ellipse(*c,x,y+7*preview_scale,radius+9*preview_scale,(radius+9*preview_scale)*.35f,preview_scale,rgb(0x8a1628),fade);
    for(unsigned i=0;i<18;++i) {
        const float angle=float(i)*pi*2/18+p*2.5f,spread=(15+35*p)*preview_scale;
        const float px=x+std::cos(angle)*spread,py=y-(10+float(i%6)*12+35*p)*preview_scale,half=1.5f*preview_scale;
        const RGB color=rgb(i%3?0xdf373e:0xffd0ad);
        for(int yy=int(std::floor(py-half));yy<int(std::ceil(py+half));++yy)
            for(int xx=int(std::floor(px-half));xx<int(std::ceil(px+half));++xx) {
                const float coverage=std::max(0.0f,std::min(float(xx+1),px+half)-std::max(float(xx),px-half))*std::max(0.0f,std::min(float(yy+1),py+half)-std::max(float(yy),py-half));
                pixel(*c,xx,yy,color,fade*coverage);
            }
    }
}
void silhouette(unsigned key,const void* bitmap,float x,float y,unsigned flags,float opacity) {
    Cast* c=current(key);
    if(!c||!bitmap||!coordinate(x)||!coordinate(y)||!std::isfinite(opacity)||opacity<=0||get<Byte>(bitmap,6)!=0)return;
    const unsigned w=get<std::uint16_t>(bitmap,0),h=get<std::uint16_t>(bitmap,2);
    const Byte* source=get<const Byte*>(bitmap,20);
    if(!source||!w||!h||w>2048||h>2048)return;
    constexpr int radius=7; // round(preview shadowBlur9 /1.28)
    const unsigned bw=w+radius*2,bh=h+radius*2;
    std::vector<float> mask(bw*bh),horizontal(bw*bh);
    for(unsigned yy=0;yy<h;++yy)for(unsigned xx=0;xx<w;++xx) {
        const unsigned sx=flags&2?w-1-xx:xx,sy=flags&4?h-1-yy:yy;
        mask[(yy+radius)*bw+xx+radius]=source[sy*w+sx]?1.0f:0.0f;
    }
    std::array<float,radius*2+1> kernel{};float total=0;
    const float sigma=9*preview_scale*.5f;
    for(int n=-radius;n<=radius;++n){kernel[n+radius]=std::exp(-float(n*n)/(2*sigma*sigma));total+=kernel[n+radius];}
    for(float& value:kernel)value/=total;
    for(unsigned yy=0;yy<bh;++yy)for(unsigned xx=0;xx<bw;++xx) {
        float sum=0;for(int n=-radius;n<=radius;++n){const int sx=int(xx)+n;if(sx>=0&&sx<int(bw))sum+=mask[yy*bw+unsigned(sx)]*kernel[n+radius];}
        horizontal[yy*bw+xx]=sum;
    }
    for(unsigned yy=0;yy<bh;++yy)for(unsigned xx=0;xx<bw;++xx) {
        if(mask[yy*bw+xx]>0)continue; // outer glow, never red-fill clone's body
        float sum=0;for(int n=-radius;n<=radius;++n){const int sy=int(yy)+n;if(sy>=0&&sy<int(bh))sum+=horizontal[unsigned(sy)*bw+xx]*kernel[n+radius];}
        pixel(*c,int(std::lround(x))+int(xx)-radius,int(std::lround(y))+int(yy)-radius,rgb(0xe63039),sum*std::min(1.0f,opacity));
    }
}
void return_stream(unsigned key,float fx,float fy,float tx,float ty,float p,float side) {
    Cast* c=current(key);if(!c||!coordinate(fx)||!coordinate(fy)||!coordinate(tx)||!coordinate(ty)||!std::isfinite(side)||std::fabs(side)>1||!std::isfinite(p)||p<=0||p>=1)return;
    for(unsigned i=0;i<12;++i) {
        const float lo=std::max(0.0f,p-.32f+float(i)*.027f),hi=std::min(p,lo+.027f);
        float ax,ay,bx,by;point(fx,fy,tx,ty,lo,side,ax,ay);point(fx,fy,tx,ty,hi,side,bx,by);
        line(*c,ax,ay-44*preview_scale,bx,by-44*preview_scale,(1+float(i)*.22f)*preview_scale,rgb(i%2?0xd62b3b:0xffd1ad),float(i+1)/12*.7f);
    }
    float x,y;point(fx,fy,tx,ty,p,side,x,y);
    glow(*c,x,y-44*preview_scale,21*preview_scale,rgb(0xffc4a3),187.0f/255,rgb(0xae192e),136.0f/255,1);
}
void end_frame(unsigned key) {
    Cast* cp=current(key);if(!cp)return;Cast& c=*cp;c.drawing=false;active=kNone;
    if(!c.painted){clear_handle(c);return;}
    palette(c);
    std::fill(c.pixels.begin(),c.pixels.end(),Byte{});
    for(int y=dirty_top;y<=dirty_bottom;++y)for(int x=dirty_left;x<=dirty_right;++x) {
        const unsigned i=unsigned(y)*c.width+unsigned(x);
        const RGB v=scratch[i];if(v.r<1){c.pixels[i]=0;continue;}
        const float ng=v.g/v.r,nb=v.b/v.r;float best=1000;unsigned hue=0;
        for(unsigned h=0;h<8;++h) {const float dg=ng-hues[h].g/255,db=nb-hues[h].b/255,d=dg*dg+db*db;if(d<best){best=d;hue=h;}}
        const unsigned level=std::min(31u,unsigned(std::lround(v.r*31/255)));
        c.pixels[i]=level?Byte(hue*32+level):0;
    }
    if(c.handle==kNone) {
        c.handle=native<unsigned(__thiscall*)(void*)>(0x25b60)(c.display)&0xffff;
        if(c.handle>=5000){c.handle=kNone;return;}
        c.bitmap.fill(0);put<std::uint16_t>(c.bitmap.data(),0,std::uint16_t(c.width));put<std::uint16_t>(c.bitmap.data(),2,std::uint16_t(c.height));
        put<std::uint16_t>(c.bitmap.data(),4,256);c.bitmap[6]=3;
        put<void*>(c.bitmap.data(),8,c.palette.data());put<void*>(c.bitmap.data(),20,c.pixels.data());
        native<void(__thiscall*)(void*,unsigned,int,int,void*,unsigned,int,void*,void*)>(0x25dc0)(c.display,c.handle,0,0,c.bitmap.data(),1,29990,c.palette.data(),nullptr);
    }
    Byte* entry=static_cast<Byte*>(c.display)+0x1258+c.handle*200;
    entry[3]=Byte(c.viewport);
}
void release_cast(unsigned key) {
    if(key>=kCasts)return;clear_handle(casts[key]);casts[key]=Cast{};if(active==key)active=kNone;
}
void reset_display(void* display) {
    for(unsigned key=0;key<kCasts;++key)if(casts[key].display==display)release_cast(key);
}
}
