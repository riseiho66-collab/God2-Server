#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
namespace bull_effect::frames {
inline std::uint16_t u16(const unsigned char* p){return std::uint16_t(p[0])|std::uint16_t(p[1])<<8;}
inline std::uint32_t u32(const unsigned char* p){return std::uint32_t(u16(p))|std::uint32_t(u16(p+2))<<16;}
inline std::uint64_t u64(const unsigned char* p){return std::uint64_t(u32(p))|std::uint64_t(u32(p+4))<<32;}
struct Index {std::uint64_t offset{};std::uint32_t size{};};
// Strict bounds before any pixel write. Each frame is independently seekable;
// decoded memory is bounded rather than loading 480 whole-screen images.
inline bool decode(const std::vector<unsigned char>& payload,unsigned w,unsigned h,std::vector<unsigned char>& out) {
    if(!w||!h||w>2048||h>2048||payload.size()<4)return false;
    const unsigned count=u32(payload.data());if(count>w*h)return false;
    std::size_t p=4;std::uint64_t previous_end=0;
    for(unsigned n=0;n<count;++n){
        if(payload.size()-p<8)return false;
        const unsigned x=u16(payload.data()+p),y=u16(payload.data()+p+2),len=u16(payload.data()+p+4),reserved=u16(payload.data()+p+6);p+=8;
        const std::uint64_t linear=std::uint64_t(y)*w+x;
        if(reserved||!len||x>=w||y>=h||len>w-x||linear<previous_end||std::size_t(len)*4>payload.size()-p)return false;
        p+=std::size_t(len)*4;previous_end=linear+len;
    }
    if(p!=payload.size())return false;
    // Validate before touching output; reuse its allocation across frames.
    out.resize(std::size_t(w)*h*4);std::fill(out.begin(),out.end(),static_cast<unsigned char>(0));p=4;
    for(unsigned n=0;n<count;++n){const unsigned x=u16(payload.data()+p),y=u16(payload.data()+p+2),len=u16(payload.data()+p+4);p+=8;
        std::memcpy(out.data()+(std::size_t(y)*w+x)*4,payload.data()+p,std::size_t(len)*4);p+=std::size_t(len)*4;}
    return true;
}
class Pack {
    std::ifstream file;std::vector<Index> index;std::vector<unsigned char> payload;int loaded=-1;
public:
    unsigned width{},height{};std::vector<unsigned char> rgba;
    bool open(const std::wstring& path){
        close();file.open(path,std::ios::binary|std::ios::ate);if(!file)return false;
        const auto length=file.tellg();if(length<24||length>std::streamoff(2ull*1024*1024*1024)){close();return false;}
        file.seekg(0);unsigned char header[24]{};file.read(reinterpret_cast<char*>(header),24);
        if(std::memcmp(header,"BULLFX01",8)||u32(header+16)!=240||u32(header+20)!=30){close();return false;}
        width=u32(header+8);height=u32(header+12);if(width!=1040||height!=807){close();return false;}
        index.resize(240);std::uint64_t end=24+240*12;
        for(auto& i:index){unsigned char row[12]{};file.read(reinterpret_cast<char*>(row),12);i={u64(row),u32(row+8)};
            if(!file||i.offset<end||i.size<4||i.size>width*height*12+4||i.offset>std::uint64_t(length)||i.size>std::uint64_t(length)-i.offset){close();return false;}end=i.offset+i.size;}
        return true;
    }
    bool frame(unsigned tick){
        if(tick>=index.size())return false;if(loaded==int(tick))return true;
        const auto& i=index[tick];payload.resize(i.size);file.clear();file.seekg(std::streamoff(i.offset));file.read(reinterpret_cast<char*>(payload.data()),i.size);
        if(!file||!decode(payload,width,height,rgba))return false;loaded=int(tick);return true;
    }
    void close(){file.close();file.clear();index.clear();rgba.clear();payload.clear();width=height=0;loaded=-1;}
};
inline unsigned channel(std::uint32_t value,std::uint32_t mask){
    if(!mask)return 0;unsigned shift=0;while(!(mask&1)){mask>>=1;++shift;}return ((value>>shift)&mask)*255/mask;
}
inline std::uint32_t encode(unsigned value,std::uint32_t mask){
    if(!mask)return 0;unsigned shift=0;while(!(mask&1)){mask>>=1;++shift;}return ((value*mask+127)/255)<<shift;
}
inline std::uint32_t blend(std::uint32_t dst,const unsigned char* s,std::uint32_t r,std::uint32_t g,std::uint32_t b){
    const unsigned a=s[3],inv=255-a;
    return (dst&~(r|g|b))|encode((s[0]*a+channel(dst,r)*inv+127)/255,r)|encode((s[1]*a+channel(dst,g)*inv+127)/255,g)|encode((s[2]*a+channel(dst,b)*inv+127)/255,b);
}
}

namespace bull_effect::frames {
struct BlendTable {
    struct Channel {std::uint32_t mask{};unsigned shift{};std::array<unsigned,256> decode{};std::array<std::uint32_t,256> encode{};};
    std::array<Channel,3> channels{};std::uint32_t preserve{};bool valid{};
    bool matches(std::uint32_t r,std::uint32_t g,std::uint32_t b)const{return valid&&channels[0].mask==r&&channels[1].mask==g&&channels[2].mask==b;}
    void configure(std::uint32_t r,std::uint32_t g,std::uint32_t b){
        valid=false;const std::uint32_t masks[]{r,g,b};preserve=~(r|g|b);
        for(unsigned n=0;n<3;++n){auto& c=channels[n];c.mask=masks[n];c.shift=0;unsigned maximum=c.mask;if(!maximum)return;
            while(!(maximum&1)){maximum>>=1;++c.shift;}
            if(maximum>255||(maximum&(maximum+1)))return;
            for(unsigned i=0;i<256;++i){c.decode[i]=i*255/maximum;c.encode[i]=((i*maximum+127)/255)<<c.shift;}
        }valid=true;
    }
    std::uint32_t apply(std::uint32_t dst,const unsigned char* src)const{
        const unsigned a=src[3];if(!a)return dst;std::uint32_t result=dst&preserve;
        if(a==255){for(unsigned n=0;n<3;++n)result|=channels[n].encode[src[n]];return result;}
        const unsigned inv=255-a;
        for(unsigned n=0;n<3;++n){const auto& c=channels[n];const unsigned value=(src[n]*a+c.decode[(dst&c.mask)>>c.shift]*inv+127)/255;result|=c.encode[value];}
        return result;
    }
};
}
