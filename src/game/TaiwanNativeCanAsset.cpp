#include "game/TaiwanNativeCanAsset.h"
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <utility>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
struct TaiwanNativeCanAsset::Storage {
    std::filesystem::path source;
    std::vector<std::uint8_t> bytes;
    std::vector<File> files;
    std::vector<std::uint16_t> indices;
};
TaiwanNativeCanAsset::TaiwanNativeCanAsset(std::shared_ptr<const Storage> value):storage_(std::move(value)){}
const TaiwanNativeCanAsset::Storage& TaiwanNativeCanAsset::storage()const {
    if(!storage_)throw std::logic_error("CAN source moved or unavailable");return *storage_;
}
bool TaiwanNativeCanAsset::matches_sha256(std::span<const std::uint8_t> bytes,std::string_view expected) {
    if(expected.size()!=64||expected.find_first_not_of("0123456789abcdef")!=std::string_view::npos)return false;
#ifdef _WIN32
    struct Algorithm {BCRYPT_ALG_HANDLE handle=nullptr;~Algorithm(){if(handle)BCryptCloseAlgorithmProvider(handle,0);}} algorithm;
    struct Hash {BCRYPT_HASH_HANDLE handle=nullptr;~Hash(){if(handle)BCryptDestroyHash(handle);}};
    if(BCryptOpenAlgorithmProvider(&algorithm.handle,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
    DWORD size=0,returned=0;
    if(BCryptGetProperty(algorithm.handle,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0)<0||
       returned!=sizeof(size)||!size)return false;
    std::vector<std::uint8_t> object(size);Hash hash;
    if(BCryptCreateHash(algorithm.handle,&hash.handle,object.data(),size,nullptr,0,0)<0)return false;
    while(!bytes.empty()){
        const auto count=static_cast<ULONG>(std::min<std::size_t>(bytes.size(),65536));
        if(BCryptHashData(hash.handle,const_cast<PUCHAR>(bytes.data()),count,0)<0)return false;
        bytes=bytes.subspan(count);
    }
    std::array<std::uint8_t,32> digest{};
    if(BCryptFinishHash(hash.handle,digest.data(),static_cast<ULONG>(digest.size()),0)<0)return false;
    constexpr char hex[]="0123456789abcdef";
    for(std::size_t i=0;i<digest.size();++i)
        if(expected[2*i]!=hex[digest[i]>>4]||expected[2*i+1]!=hex[digest[i]&15])return false;
    return true;
#else
    (void)bytes;return false;
#endif
}
std::optional<TaiwanNativeCanAsset> TaiwanNativeCanAsset::from_bytes(
        std::filesystem::path path,std::span<const std::uint8_t> bytes,std::string_view digest) {
    constexpr std::array<std::uint8_t,8> magic{'C','A','N',' ','v','1','.','0'};
    if(!path.is_absolute()||bytes.size()<16||bytes.size()>max_bytes||
       !std::equal(magic.begin(),magic.end(),bytes.begin())||!matches_sha256(bytes,digest))return {};
    const auto u32=[&](std::size_t at){return static_cast<std::uint32_t>(bytes[at])|
        (static_cast<std::uint32_t>(bytes[at+1])<<8)|(static_cast<std::uint32_t>(bytes[at+2])<<16)|
        (static_cast<std::uint32_t>(bytes[at+3])<<24);};
    const auto count=u32(8);if(count>max_files)return {};
    const std::size_t count_at=12+count*record_size;if(count_at+4>bytes.size())return {};
    const auto scenes=u32(count_at);const auto table=count_at+4;
    if(scenes>max_scenes||bytes.size()!=table+scenes*2)return {};
    auto out=std::make_shared<Storage>();out->source=std::move(path);
    out->bytes.assign(bytes.begin(),bytes.end());out->files.reserve(count);out->indices.reserve(scenes);
    for(std::size_t i=0;i<count;++i){
        const auto at=12+i*record_size;const auto row=bytes.subspan(at,record_size);
        const auto end=std::find(row.begin()+1,row.end(),0);if(end==row.end()||end==row.begin()+1)return {};
        File file{i,at,{},row[0],{}};std::copy(row.begin(),row.end(),file.raw.begin());
        file.reference.assign(row.begin()+1,end);out->files.push_back(std::move(file));
    }
    for(std::size_t i=0;i<scenes;++i){
        const auto value=static_cast<std::uint16_t>(bytes[table+2*i]|(static_cast<unsigned>(bytes[table+2*i+1])<<8));
        if(value>=count)return {};out->indices.push_back(value);
    }
    return TaiwanNativeCanAsset(std::move(out));
}
std::optional<TaiwanNativeCanAsset> TaiwanNativeCanAsset::load_file(const std::filesystem::path& path,std::string_view digest) {
    if(!path.is_absolute())return {};std::ifstream stream(path,std::ios::binary);if(!stream.is_open())return {};
    std::vector<std::uint8_t> bytes(max_bytes+1);
    stream.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    const auto count=stream.gcount();if(stream.bad()||count<0||static_cast<std::uint64_t>(count)>max_bytes)return {};
    bytes.resize(static_cast<std::size_t>(count));return from_bytes(path,bytes,digest);
}
const std::filesystem::path& TaiwanNativeCanAsset::source()const{return storage().source;}
const std::vector<std::uint8_t>& TaiwanNativeCanAsset::bytes()const{return storage().bytes;}
const std::vector<TaiwanNativeCanAsset::File>& TaiwanNativeCanAsset::files()const{return storage().files;}
const std::vector<std::uint16_t>& TaiwanNativeCanAsset::scene_indices()const{return storage().indices;}
const TaiwanNativeCanAsset::File* TaiwanNativeCanAsset::scene(std::size_t index)const {
    const auto& s=storage();return index<s.indices.size()?&s.files[s.indices[index]]:nullptr;
}
}
