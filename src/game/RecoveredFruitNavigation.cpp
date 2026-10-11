#include "game/RecoveredFruitNavigation.h"
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
void require(bool valid) {
    if(!valid) throw std::invalid_argument("Fruit navigation source/structure mismatch");
}
bool source_matches(std::string& bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;
    BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0)))
        throw std::runtime_error("Fruit navigation SHA256 unavailable");
    std::array<unsigned char,32> digest{};
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;
    const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))
        throw std::runtime_error("Fruit navigation SHA256 failed");
    std::string hex;
    for(const auto byte:digest) {
        hex.push_back("0123456789abcdef"[byte>>4]);
        hex.push_back("0123456789abcdef"[byte&15]);
    }
    return hex==RecoveredFruitNavigation::source_sha256;
#else
    (void)bytes;
    throw std::runtime_error("Fruit navigation requires qualified SHA256 backend");
#endif
}
int nibble(char c) {
    if(c>='0' && c<='9')return c-'0';
    if(c>='a' && c<='f')return c-'a'+10;
    throw std::invalid_argument("Fruit navigation hex rejected");
}
}
RecoveredFruitNavigation RecoveredFruitNavigation::load(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);
    if(!input)throw std::invalid_argument("Fruit navigation unavailable");
    constexpr std::size_t limit=1024*1024;
    std::string bytes(limit+1,'\0');
    input.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!input.bad() && input.gcount()>0 && static_cast<std::size_t>(input.gcount())<=limit);
    bytes.resize(static_cast<std::size_t>(input.gcount()));
    require(source_matches(bytes));
    const auto j=nlohmann::json::parse(bytes);
    require(j.at("schema")=="god2-recovered-fruit-navigation-v1" && j.at("area")==13 &&
        j.at("scene")==12 && j.at("kind")==0 && j.at("width")==width && j.at("height")==height &&
        j.at("dynamic_occupancy_included")==false);
    const auto encoded=j.at("cells_hex").get<std::string>();
    require(encoded.size()==static_cast<std::size_t>(width*height*2));
    RecoveredFruitNavigation result;
    std::array<std::size_t,5> counts{};
    for(std::size_t i=0;i<result.cells_.size();++i) {
        const auto raw=static_cast<std::uint8_t>((nibble(encoded[2*i])<<4)|nibble(encoded[2*i+1]));
        require(raw<=2 || raw==254 || raw==255);
        ++counts[raw<=2?raw:raw==254?3:4];
        result.cells_[i]=raw<=2?raw:0;
    }
    require(counts==std::array<std::size_t,5>{20955,7768,26,357,6615});
    return result;
}
std::uint8_t RecoveredFruitNavigation::consistent_cell(int x,int y) const noexcept {
    if(x<0 || y<0 || x>=width || y>=height)return 0;
    return cells_[static_cast<std::size_t>(y*width+x)];
}
}
