#include "clone_particles.h"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <fstream>
#include <string>
#include <limits>
#include <vector>
namespace {
using Byte=unsigned char;
std::vector<Byte> display(0xf6000);unsigned allocated{},released{};
template<class T> void put(void* p,unsigned o,T v){std::memcpy(static_cast<Byte*>(p)+o,&v,sizeof(v));}
template<class T> T get(const void* p,unsigned o){T v{};std::memcpy(&v,static_cast<const Byte*>(p)+o,sizeof(v));return v;}
Byte* entry(unsigned h){return display.data()+0x1258+h*200;}
unsigned __fastcall allocate(void*,void*) {for(unsigned h=0;h<5000;++h)if(!entry(h)[0]){entry(h)[0]=1;++allocated;return h;}return 0xffff;}
void __fastcall init(void*,void*,unsigned h,int x,int y,void* bitmap,unsigned flags,int z,void* palette,void* clip) {
    assert(x==0&&y==0&&flags==1&&z==29990&&!clip);auto p=entry(h);p[0]=2;
    put<void*>(p,0x8c,bitmap);put<void*>(p,0x94,palette);
    assert(get<unsigned short>(bitmap,0)==get<unsigned>(display.data(),0)&&get<unsigned short>(bitmap,2)==get<unsigned>(display.data(),4));
    assert(get<Byte>(bitmap,6)==3&&get<void*>(bitmap,16)==nullptr&&get<void*>(bitmap,20));
}
void __fastcall release(void*,void*,unsigned h){assert(entry(h)[0]==2);entry(h)[0]=0;++released;}
unsigned lit(unsigned h) {auto b=get<void*>(entry(h),0x8c);auto p=get<Byte*>(b,20);unsigned n=0;for(unsigned i=0;i<unsigned(get<unsigned short>(b,0))*get<unsigned short>(b,2);++i)n+=p[i]!=0;return n;}
void dump(unsigned handle,const std::string& filename) {
    auto b=get<void*>(entry(handle),0x8c);const unsigned w=get<unsigned short>(b,0),h=get<unsigned short>(b,2);
    auto pixels=get<Byte*>(b,20);auto palette=get<unsigned short*>(entry(handle),0x94);
    std::ofstream f(filename,std::ios::binary);f<<"P6\n"<<w<<" "<<h<<"\n255\n";
    for(unsigned i=0;i<w*h;++i){const unsigned color=palette[pixels[i]];const char rgb[]{char(std::min(255u,40+((color>>11)&31)*255/31)),char(std::min(255u,40+((color>>5)&63)*255/63)),char(std::min(255u,40+(color&31)*255/31))};f.write(rgb,3);}
}
}
std::uintptr_t particle_test_native(unsigned rva) {
    switch(rva){case 0x25b60:return reinterpret_cast<std::uintptr_t>(&allocate);case 0x25dc0:return reinterpret_cast<std::uintptr_t>(&init);case 0x26a30:return reinterpret_cast<std::uintptr_t>(&release);default:assert(false);return 0;}
}
int main(int argc,char** argv) {
    static_assert(sizeof(void*)==4);using namespace shunying_clone::particles;
    put<unsigned>(display.data(),0,800);put<unsigned>(display.data(),4,600);put<unsigned short>(display.data(),0x1210,0xf800);put<unsigned short>(display.data(),0x1212,0x07e0);put<unsigned short>(display.data(),0x1214,0x001f);
    initialize(0x400000);begin_frame(display.data(),0);burst(0,300,350,-1);end_frame(0);assert(allocated==0);
    begin_frame(display.data(),0,2);burst(0,300,350,7,14);end_frame(0);assert(allocated==1&&entry(0)[3]==2&&lit(0)>1000);
    if(argc>1)dump(0,std::string(argv[1])+"/burst.ppm");
    auto bitmap=get<void*>(entry(0),0x8c);auto pixels=get<Byte*>(bitmap,20);const auto snapshot=std::vector<Byte>(pixels,pixels+800*600);
    begin_frame(display.data(),1);burst(1,500,300,7,14);end_frame(1);assert(allocated==2&&get<void*>(entry(1),0x8c)!=bitmap);
    assert(std::equal(snapshot.begin(),snapshot.end(),pixels)); // independent lifetime
    begin_frame(display.data(),0);return_stream(0,250,230,520,390,.5f,-1);end_frame(0);assert(allocated==2&&get<void*>(entry(0),0x8c)==bitmap&&lit(0)>100);
    if(argc>1)dump(0,std::string(argv[1])+"/return-stream.ppm");
    begin_frame(display.data(),0);burst(0,0,0,14,14);return_stream(0,250,230,520,390,1,-1);end_frame(0);assert(released==1);
    begin_frame(display.data(),0);burst(0,std::numeric_limits<float>::quiet_NaN(),0,7);end_frame(0);assert(allocated==2);
    reset_display(reinterpret_cast<void*>(1));assert(released==1);reset_display(display.data());assert(released==2);reset_display(display.data());assert(released==2);
    put<unsigned>(display.data(),0,1024);put<unsigned>(display.data(),4,768);
    begin_frame(display.data(),0);burst(0,930,710,7,14);end_frame(0);assert(lit(0)>1000);if(argc>1)dump(0,std::string(argv[1])+"/native-1024-corner.ppm");release_cast(0);
    std::array<Byte,24> shape{};std::array<Byte,24*60> shape_pixels{};
    for(unsigned yy=5;yy<55;++yy)for(unsigned xx=7;xx<17;++xx)shape_pixels[yy*24+xx]=1;
    put<unsigned short>(shape.data(),0,24);put<unsigned short>(shape.data(),2,60);put<Byte*>(shape.data(),20,shape_pixels.data());
    begin_frame(display.data(),0);silhouette(0,shape.data(),380,300,1,.42f);end_frame(0);assert(lit(0)>50);if(argc>1)dump(0,std::string(argv[1])+"/silhouette.ppm");release_cast(0);
    std::cout<<"PASS: particle native bitmap ABI, fade endpoints, independent lifetime, clipped raster, curved stream, reset and nonfinite guard\n";
}
