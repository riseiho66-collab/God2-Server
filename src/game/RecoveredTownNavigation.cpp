#include "game/RecoveredTownNavigation.h"
#include <array>
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
void require(bool condition) {
    if(!condition) throw std::invalid_argument("Town navigation identity or structure mismatch");
}
bool matches_pin(std::string& bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0)))
        throw std::runtime_error("Town navigation SHA256 unavailable");
    std::array<unsigned char,32> digest{};
    BCRYPT_HASH_HANDLE hash=nullptr;
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status)) status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(bytes.data()),
        static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status)) status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;
    const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))
        throw std::runtime_error("Town navigation SHA256 failed");
    std::string hex;
    constexpr char digits[]="0123456789abcdef";
    for(auto b:digest) { hex+=digits[b>>4];hex+=digits[b&15]; }
    return hex=="536bf3d370b256ae38d175c665aabab595ddc9843704699f03d5c9529645684c";
#else
    (void)bytes;
    throw std::runtime_error("Town navigation requires qualified SHA256 backend");
#endif
}
}
RecoveredTownNavigation::RecoveredTownNavigation(const std::filesystem::path& path) {
    std::ifstream file(path,std::ios::binary);
    if(!file) throw std::invalid_argument("Town navigation file unavailable");
    constexpr std::size_t limit=2*1024*1024;
    std::string bytes(limit+1,'\0');
    file.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!file.bad() && file.gcount()>0 && static_cast<std::size_t>(file.gcount())<=limit);
    bytes.resize(static_cast<std::size_t>(file.gcount()));
    require(matches_pin(bytes));
    const auto data=nlohmann::json::parse(bytes);
    require(data.at("schema")=="god2-recovered-town-navigation-v2" && data.at("area")==area &&
            data.at("scene")==scene && data.at("kind")==kind && data.at("side")==63 &&
            data.at("unknown_marker")=="??" && data.at("dynamic_occupancy_included")==false &&
            data.at("runtime_validated")==false);
    require(data.at("block_width")==9 && data.at("block_height")==9);
    const auto& presence=data.at("block_present");
    require(presence.is_array() && presence.size()==block_present_.size());
    for(std::size_t i=0;i<block_present_.size();++i) {
        require(presence[i].is_boolean());
        block_present_[i]=presence[i].get<bool>();
    }
    const auto& windows=data.at("windows");
    require(windows.is_array() && windows.size()==81);
    cells_.reserve(81*3969);
    for(std::size_t i=0;i<81;++i) {
        const auto& w=windows[i];
        const auto cx=static_cast<int>(i%9),cy=static_cast<int>(i/9);
        require(w.at("block_x")==cx && w.at("block_y")==cy &&
                w.at("origin_x")==cx*21-21 && w.at("origin_y")==cy*21-21);
        const auto hex=w.at("cells_hex").get<std::string>();
        require(hex.size()==7938);
        std::size_t known=0;
        for(std::size_t offset=0;offset<hex.size();offset+=2) {
            if(hex[offset]=='?' && hex[offset+1]=='?') cells_.push_back(255);
            else {
                require(hex[offset]=='0' && hex[offset+1]>='0' && hex[offset+1]<='2');
                cells_.push_back(static_cast<std::uint8_t>(hex[offset+1]-'0'));
                ++known;
            }
        }
        require(w.at("known_cells")==known);
    }
    consistent_.fill(255);
    for(int cy=0;cy<9;++cy) for(int cx=0;cx<9;++cx) {
        if(!available_center(cx,cy)) continue;
        for(int ly=0;ly<63;++ly) for(int lx=0;lx<63;++lx) {
            const int x=cx*21-21+lx,y=cy*21-21+ly;
            const auto value=cell(cx,cy,x,y);
            if(!value) continue;
            auto& previous=consistent_[static_cast<std::size_t>(y*189+x)];
            if(previous==255) previous=*value;
            else if(previous!=*value) previous=254;
        }
    }
}
std::optional<std::uint8_t> RecoveredTownNavigation::consistent_cell(int x,int y) const noexcept {
    if(x<0 || y<0 || x>=189 || y>=189) return std::nullopt;
    const auto value=consistent_[static_cast<std::size_t>(y*189+x)];
    return value>2?std::nullopt:std::optional<std::uint8_t>(value);
}
bool RecoveredTownNavigation::consistently_walkable(int x,int y) const noexcept {
    if(x<0 || y<0 || x>=189 || y>=189)return false;
    bool observed=false;
    for(int cy=1;cy<=7;++cy)for(int cx=1;cx<=7;++cx) {
        if(!available_center(cx,cy))continue;
        const auto local_x=x-cx*21+21,local_y=y-cy*21+21;
        if(local_x<0 || local_y<0 || local_x>=63 || local_y>=63)continue;
        const auto value=cell(cx,cy,x,y);
        if(!value || (*value!=1 && *value!=2))return false;
        observed=true;
    }
    return observed;
}
bool RecoveredTownNavigation::available_center(int x,int y) const noexcept {
    if(x<1 || y<1 || x>7 || y>7) return false;
    for(int by=y-1;by<=y+1;++by) for(int bx=x-1;bx<=x+1;++bx)
        if(!block_present_[static_cast<std::size_t>(by*9+bx)]) return false;
    return true;
}
std::optional<RecoveredTownNavigation::Center> RecoveredTownNavigation::select_center(int x,int y) const noexcept {
    const int cx=x/21,cy=y/21;
    if(available_center(cx,cy)) return Center{cx,cy};
    for(int by=cy-1;by<=cy+1;++by) for(int bx=cx-1;bx<=cx+1;++bx)
        if(available_center(bx,by)) return Center{bx,by};
    return std::nullopt;
}
std::optional<std::uint8_t> RecoveredTownNavigation::cell(int center_x,int center_y,int x,int y) const noexcept {
    if(center_x<0 || center_y<0 || center_x>=9 || center_y>=9 || x<0 || y<0 || x>=189 || y>=189)
        return std::nullopt;
    const auto local_x=x-center_x*21+21,local_y=y-center_y*21+21;
    if(local_x<0 || local_y<0 || local_x>=63 || local_y>=63) return std::nullopt;
    const auto value=cells_[static_cast<std::size_t>((center_y*9+center_x)*3969+local_y*63+local_x)];
    return value==255?std::nullopt:std::optional<std::uint8_t>(value);
}
}
