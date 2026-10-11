#include "game/RecoveredParentNavigation.h"
#include <array>
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
void require(bool value) {if(!value)throw std::invalid_argument("Parent navigation source/structure mismatch");}
void verify(const std::string& bytes,std::uint16_t area) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    std::array<unsigned char,32> digest{};
    auto status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0);
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(bytes.data())),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;
    const auto closed=algorithm?BCryptCloseAlgorithmProvider(algorithm,0):0;
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))throw std::runtime_error("Parent navigation SHA256 failed");
    std::string actual;for(auto byte:digest){actual+="0123456789abcdef"[byte>>4];actual+="0123456789abcdef"[byte&15];}
    require(actual==(area==4?"64c42e064fab5196cb3c413b8d5c483e73de315407c529683683ef855a340841":"16a428a106eb2bc63f4996af51cf0cdbdb13ab02712d32664123832006920aa6"));
#else
    (void)bytes;(void)area;throw std::runtime_error("Parent navigation requires qualified SHA256 backend");
#endif
}
}
RecoveredParentNavigation::RecoveredParentNavigation(const std::filesystem::path& path,std::uint16_t area) {
    require(area==2||area==4);
    const int columns=area==4?20:35,rows=area==4?52:37;
    width=columns*21;height=rows*21;cells_.assign(static_cast<std::size_t>(width*height),255);
    std::ifstream file(path,std::ios::binary);if(!file)throw std::invalid_argument("Parent navigation unavailable");
    constexpr std::size_t limit=11*1024*1024;
    std::string bytes(limit+1,'\0');file.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!file.bad() && file.gcount()>0 && static_cast<std::size_t>(file.gcount())<=limit);
    bytes.resize(static_cast<std::size_t>(file.gcount()));verify(bytes,area);
    const auto j=nlohmann::json::parse(bytes);
    require(j.at("schema")=="god2-current-parent-full-navigation-v1" && j.at("area")==area && j.at("scene")==0 && j.at("kind")==1 &&
        j.at("block_width")==columns && j.at("block_height")==rows && j.at("dynamic_occupancy_included")==false &&
        j.at("source_mdl_pin").at("source_sha256")== (area==4?"66072bf1ba35166f9d76af79a7cb7cdd9d7af7f3748f2898c05cb440c88d384e":"cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d") &&
        j.at("mbd_sha256")== (area==4?"a4aa72fd851a2ecce3dd45ed3ef76c1c72a5bc50270f57ee733a8fe671b4caed":"b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80"));
    const auto& windows=j.at("windows");require(windows.is_array() && windows.size()==static_cast<std::size_t>(columns*rows));
    std::size_t available=0;
    for(std::size_t i=0;i<windows.size();++i) {
        const auto& row=windows[i];const int bx=static_cast<int>(i%columns),by=static_cast<int>(i/columns);
        require(row.at("block_x")==bx && row.at("block_y")==by && row.at("origin_x")==bx*21-21 && row.at("origin_y")==by*21-21 && row.at("block_present").is_boolean());
        const bool present=row.at("block_present").get<bool>();available+=present;
        const auto encoded=row.at("cells_hex").get<std::string>();require(encoded.size()==63*63*2);
        for(int y=0;y<63;++y)for(int x=0;x<63;++x) {
            const auto offset=static_cast<std::size_t>((y*63+x)*2);
            if(encoded[offset]=='?' && encoded[offset+1]=='?')continue;
            require(encoded[offset]=='0' && encoded[offset+1]>='0' && encoded[offset+1]<='2');
            if(!present)continue;
            const int wx=bx*21-21+x,wy=by*21-21+y;
            if(wx<0||wy<0||wx>=width||wy>=height)continue;
            const auto value=static_cast<std::uint8_t>(encoded[offset+1]-'0');
            auto& previous=cells_[static_cast<std::size_t>(wy*width+wx)];
            if(previous==255)previous=value;else if(previous!=value)previous=254;
        }
    }
    std::size_t covered=0,conflicts=0,walkable=0;
    for(const auto value:cells_){covered+=value!=255;conflicts+=value==254;walkable+=value==1||value==2;}
    require(available==(area==4?782u:859u) && covered==(area==4?344862u:378819u) &&
        conflicts==(area==4?87u:6196u) && walkable==(area==4?29589u:129792u));
    require(area==4?consistent_cell(318,363)==2:(consistent_cell(477,209)==2 && consistent_cell(476,209)==1));
}
std::optional<std::uint8_t> RecoveredParentNavigation::consistent_cell(int x,int y) const noexcept {
    if(x<0||y<0||x>=width||y>=height)return std::nullopt;
    const auto value=cells_[static_cast<std::size_t>(y*width+x)];
    return value>2?std::nullopt:std::optional<std::uint8_t>{value};
}
}
