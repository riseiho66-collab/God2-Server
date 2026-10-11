#include "game/RecoveredIslandEntryNavigation.h"
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <array>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
int integer(const nlohmann::json& j,int low,int high) {
    if(!j.is_number_integer()) throw std::invalid_argument("Island navigation integer required");
    const auto n=j.get<std::int64_t>();
    if(n<low || n>high) throw std::invalid_argument("Island navigation integer out of range");
    return static_cast<int>(n);
}
int hex(char c) {
    if(c>='0' && c<='9') return c-'0';
    if(c>='a' && c<='f') return c-'a'+10;
    throw std::invalid_argument("Island navigation hex rejected");
}
std::uint64_t key(int x,int y) {
    return (static_cast<std::uint64_t>(x)<<32)|static_cast<std::uint32_t>(y);
}
}
RecoveredIslandEntryNavigation::RecoveredIslandEntryNavigation(const std::filesystem::path& path) {
    if(std::filesystem::file_size(path)>512*1024)
        throw std::invalid_argument("Island navigation input too large");
    std::ifstream file(path,std::ios::binary);
    if(!file)throw std::invalid_argument("Island navigation unavailable");
    std::string bytes(std::istreambuf_iterator<char>{file},{});
    const auto j=nlohmann::json::parse(bytes);
    const bool extended=j.at("schema")=="god2-recovered-island01-all-boundaries-navigation-v1";
    if(extended) {
        // CUSTOM-0036: this larger source export is separately pinned. Existing
        // nine-window fixtures retain their original contract and coverage.
#ifdef _WIN32
        BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
        std::array<unsigned char,32> digest{};
        auto status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0);
        if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
        if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
        if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
        const auto destroyed=hash?BCryptDestroyHash(hash):0;
        const auto closed=algorithm?BCryptCloseAlgorithmProvider(algorithm,0):0;
        if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))
            throw std::runtime_error("Island boundaries SHA256 failed");
        std::string actual;
        for(auto byte:digest){actual+="0123456789abcdef"[byte>>4];actual+="0123456789abcdef"[byte&15];}
        if(actual!="475faae6162c5fb8c6dc8f2ca6d7b63dfa0e9bc27725d24d7e75eef2bcf43eb9")
            throw std::invalid_argument("Island boundaries source changed");
#else
        throw std::runtime_error("Island boundaries require qualified SHA256 backend");
#endif
    }
    if((!extended && j.at("schema")!="god2-recovered-island01-entry-navigation-v1") ||
       integer(j.at("area"),0,63)!=2 || integer(j.at("scene"),0,1023)!=0 ||
       integer(j.at("kind"),0,3)!=1 ||
       j.at("sources").at("mbd_sha256")!="b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80")
        throw std::invalid_argument("Island navigation source mismatch");
    const auto& windows=j.at("windows");
    if(!windows.is_array() || windows.size()!=(extended?24u:9u))
        throw std::invalid_argument("Island navigation window count rejected");
    for(const auto& window:windows) {
        const auto origin_x=integer(window.at("origin_x"),0,32767);
        const auto origin_y=integer(window.at("origin_y"),0,32767);
        const auto& encoded=window.at("cells_hex");
        if(!encoded.is_string()) throw std::invalid_argument("Island navigation cells rejected");
        const auto cells=encoded.get<std::string>();
        if(cells.size()!=63*63*2 || integer(window.at("known_cells"),0,63*63)!=63*63)
            throw std::invalid_argument("Island navigation window size rejected");
        for(int y=0;y<63;++y) for(int x=0;x<63;++x) {
            const auto index=static_cast<std::size_t>((y*63+x)*2);
            const auto value=static_cast<std::uint16_t>((hex(cells[index])<<4)|hex(cells[index+1]));
            auto [it,inserted]=cells_.try_emplace(key(origin_x+x,origin_y+y),value);
            if(!inserted && it->second!=value) it->second=256;
        }
    }
    for(const auto& [coordinate,value]:cells_) {
        (void)coordinate;
        if(value==256) ++conflicts_;
    }
    if(cells_.size()!=(extended?21168u:11025u) || conflicts_!=(extended?454u:212u) ||
       consistent_cell(477,209)!=2 || consistent_cell(476,209)!=1)
        throw std::invalid_argument("Island navigation consensus mismatch");
}
std::optional<std::uint8_t> RecoveredIslandEntryNavigation::consistent_cell(int x,int y) const noexcept {
    if(x<0 || y<0) return std::nullopt;
    const auto it=cells_.find(key(x,y));
    if(it==cells_.end() || it->second==256) return std::nullopt;
    return static_cast<std::uint8_t>(it->second);
}
}
