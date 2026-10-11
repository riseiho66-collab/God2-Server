#include "game/RecoveredKunlunNavigation.h"
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif
namespace god2 {
namespace {
void require(bool value) { if(!value)throw std::invalid_argument("Kunlun navigation source/structure mismatch"); }
bool pinned(std::string& bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0)))
        throw std::runtime_error("Kunlun navigation SHA256 unavailable");
    std::array<unsigned char,32> digest{};
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))throw std::runtime_error("Kunlun SHA256 failed");
    std::string hex;for(const auto byte:digest){hex.push_back("0123456789abcdef"[byte>>4]);hex.push_back("0123456789abcdef"[byte&15]);}
    return hex=="d429b1f94a9c1e2cf1bb8d0194213a25de22b9bb86c036a335d5c6952ddd95aa";
#else
    (void)bytes;throw std::runtime_error("Kunlun navigation requires qualified SHA256 backend");
#endif
}
}
RecoveredKunlunNavigation::RecoveredKunlunNavigation(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);if(!input)throw std::invalid_argument("Kunlun navigation unavailable");
    constexpr std::size_t limit=4*1024*1024;std::string bytes(limit+1,'\0');input.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!input.bad() && input.gcount()>0 && static_cast<std::size_t>(input.gcount())<=limit);
    bytes.resize(static_cast<std::size_t>(input.gcount()));require(pinned(bytes));const auto j=nlohmann::json::parse(bytes);
    require(j.at("schema")=="god2-recovered-kunlun-navigation-v1" && j.at("area")==4 && j.at("scene")==3 && j.at("kind")==0 &&
        j.at("side")==63 && j.at("block_width")==12 && j.at("block_height")==12 && j.at("unknown_marker")=="??" &&
        j.at("dynamic_occupancy_included")==false);
    const auto& windows=j.at("windows");require(windows.is_array() && windows.size()==144);
    const auto& present=j.at("block_present");require(present.is_array() && present.size()==144);
    for(const auto& value:present)require(value.is_boolean());
    for(std::size_t i=0;i<windows.size();++i) {
        const auto& window=windows[i];const int bx=static_cast<int>(i%12),by=static_cast<int>(i/12);
        const bool available=present[i].get<bool>();
        require(window.at("block_x")==bx && window.at("block_y")==by && window.at("origin_x")==bx*21-21 && window.at("origin_y")==by*21-21);
        const auto encoded=window.at("cells_hex").get<std::string>();require(encoded.size()==63*63*2);
        std::size_t known=0;
        for(int y=0;y<63;++y)for(int x=0;x<63;++x) {
            const auto offset=static_cast<std::size_t>((y*63+x)*2);std::uint8_t value=255;
            if(encoded[offset]=='?' && encoded[offset+1]=='?')continue;
            require(encoded[offset]=='0' && encoded[offset+1]>='0' && encoded[offset+1]<='2');value=static_cast<std::uint8_t>(encoded[offset+1]-'0');++known;
            if(!available)continue;
            const int world_x=bx*21-21+x,world_y=by*21-21+y;
            if(world_x<0 || world_y<0 || world_x>=252 || world_y>=252)continue;
            auto& previous=cells_[static_cast<std::size_t>(world_y*252+world_x)];
            if(previous==255)previous=value;else if(previous!=value)previous=254;
            auto& pass=walkable_[static_cast<std::size_t>(world_y*252+world_x)];
            if(pass==255)pass=value!=0?1:0;else if(value==0)pass=0;
        }
        require(window.at("known_cells")==known);
    }
}
std::optional<std::uint8_t> RecoveredKunlunNavigation::consistent_cell(int x,int y) const noexcept {
    if(x<0 || y<0 || x>=252 || y>=252)return std::nullopt;
    const auto value=cells_[static_cast<std::size_t>(y*252+x)];return value>2?std::nullopt:std::optional<std::uint8_t>{value};
}
bool RecoveredKunlunNavigation::consistently_walkable(int x,int y) const noexcept {
    return x>=0 && y>=0 && x<252 && y<252 && walkable_[static_cast<std::size_t>(y*252+x)]==1;
}
}
