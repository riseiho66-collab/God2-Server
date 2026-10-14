#include "game/TaiwanNativeActorResourceBank.h"
#include <algorithm>
#include <charconv>
#include <limits>
#include <set>
#include <stdexcept>
#include <utility>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
[[noreturn]] void invalid(){throw std::invalid_argument("Unqualified TW ordinary actor resource bank");}
std::string digest(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    struct Algorithm {
        BCRYPT_ALG_HANDLE value=nullptr;
        ~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}
    } algorithm;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)))invalid();
    DWORD size=0,returned=0;
    if(!BCRYPT_SUCCESS(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,
            reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0)) || returned!=sizeof(size) || !size)invalid();
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    // Destroy hash before its retained object buffer and algorithm, even when
    // allocation/formatting throws. No provider handle leaks on exceptions.
    struct Hash {BCRYPT_HASH_HANDLE value=nullptr;~Hash(){if(value)BCryptDestroyHash(value);}} hash;
    if(!BCRYPT_SUCCESS(BCryptCreateHash(algorithm.value,&hash.value,object.data(),size,nullptr,0,0)) ||
       bytes.size()>std::numeric_limits<ULONG>::max() ||
       !BCRYPT_SUCCESS(BCryptHashData(hash.value,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)) ||
       !BCRYPT_SUCCESS(BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)))invalid();
    std::string out;out.reserve(64);
    for(const auto b:result){out+="0123456789abcdef"[b>>4];out+="0123456789abcdef"[b&15];}return out;
#else
    (void)bytes;throw std::runtime_error("TW ordinary actor SHA256 backend unavailable");
#endif
}
using Bytes=std::vector<std::uint8_t>;
struct Line {std::size_t offset,size;};
std::vector<Line> lines(const Bytes& bytes,std::size_t expected) {
    if(std::find(bytes.begin(),bytes.end(),0)!=bytes.end() ||
       std::find(bytes.begin(),bytes.end(),'"')!=bytes.end())invalid();
    std::vector<Line> out;std::size_t begin=0;
    for(std::size_t i=0;i<bytes.size();++i)if(bytes[i]=='\n') {
        if(i==begin || bytes[i-1]!='\r')invalid();
        out.push_back({begin,i-begin+1});begin=i+1;
    } else if(bytes[i]=='\r' && (i+1==bytes.size() || bytes[i+1]!='\n'))invalid();
    if(begin!=bytes.size() || out.size()!=expected)invalid();return out;
}
std::vector<Bytes> fields(const Bytes& bytes,Line line) {
    std::vector<Bytes> out;const auto end=line.offset+line.size-2;std::size_t begin=line.offset;
    for(std::size_t i=begin;i<=end;++i)if(i==end || bytes[i]==',') {
        out.emplace_back(bytes.begin()+begin,bytes.begin()+i);begin=i+1;
    }
    return out;
}
std::string ascii(const Bytes& bytes) {
    if(!std::all_of(bytes.begin(),bytes.end(),[](auto c){return c>=0x20 && c<0x7f;}))invalid();
    return std::string(bytes.begin(),bytes.end());
}
std::uint8_t ascii_lower(std::uint8_t c) {return c>='A' && c<='Z'?c+('a'-'A'):c;}
std::int32_t number(const Bytes& bytes) {
    if(bytes.empty() || !std::all_of(bytes.begin(),bytes.end(),[](auto c){return c>='0' && c<='9';}))invalid();
    const auto* begin=reinterpret_cast<const char*>(bytes.data());std::int32_t value=0;
    const auto parsed=std::from_chars(begin,begin+bytes.size(),value);
    if(parsed.ec!=std::errc{} || parsed.ptr!=begin+bytes.size())invalid();return value;
}
TaiwanNativeActorResourceBank::SourceRow row(const Bytes& bytes,Line line,std::size_t ordinal,
        std::size_t source_line,std::vector<Bytes> columns) {
    return {ordinal,source_line,line.offset,Bytes(bytes.begin()+line.offset,bytes.begin()+line.offset+line.size),
        std::move(columns)};
}
}
TaiwanNativeActorResourceBank::TaiwanNativeActorResourceBank(std::filesystem::path drv_origin,
        Bytes drv_plain,std::vector<Drv> drv,std::filesystem::path hero_origin,Bytes hero_plain,std::vector<Hero> hero)
    :drv_origin_(std::move(drv_origin)),hero_origin_(std::move(hero_origin)),drv_plain_(std::move(drv_plain)),
     hero_plain_(std::move(hero_plain)),drv_(std::move(drv)),hero_(std::move(hero)) {}
std::shared_ptr<const TaiwanNativeActorResourceBank> TaiwanNativeActorResourceBank::from_pinned_decoded(
        std::filesystem::path drv_origin,std::span<const std::uint8_t> drv_bytes,
        std::filesystem::path hero_origin,std::span<const std::uint8_t> hero_bytes) {
    if(!drv_origin.is_absolute() || !hero_origin.is_absolute() || drv_bytes.size()!=3899 || hero_bytes.size()!=37189)invalid();
    Bytes drv_plain(drv_bytes.begin(),drv_bytes.end()),hero_plain(hero_bytes.begin(),hero_bytes.end());
    if(digest(drv_plain)!=drv_decoded_sha256 || digest(hero_plain)!=hero_decoded_sha256)invalid();
    const auto dl=lines(drv_plain,101),hl=lines(hero_plain,943);
    const auto dh=fields(drv_plain,dl[0]),hh=fields(hero_plain,hl[0]);
    if(dh.size()!=5 || ascii(dh[0])!="Drv" || ascii(dh[1])!="1.03" || number(dh[2])!=10 ||
       hh.size()!=5 || ascii(hh[1])!="1.01" || number(hh[2])!=26 || number(hh[4])!=918)invalid();
    std::vector<Drv> drv;drv.reserve(92);
    for(std::size_t index=0;index<92;++index) {
        auto columns=fields(drv_plain,dl[index+9]);
        // Native consumes first8; source comments contain real extra commas.
        if(columns.size()!=9 && columns.size()!=10)invalid();
        if(number(columns[0])!=static_cast<std::int32_t>(index) || columns[1].size()>=16)invalid();
        (void)ascii(columns[1]);
        std::array<std::uint16_t,6> values{};
        for(std::size_t i=0;i<values.size();++i) {
            const auto value=number(columns[i+2]);if(value>0xffff)invalid();values[i]=static_cast<std::uint16_t>(value);
        }
        Drv record{static_cast<std::uint16_t>(index),values[0],values[1],
            {values[2],values[3],values[4],values[5]},columns[1],
            row(drv_plain,dl[index+9],index,index+10,std::move(columns))};
        drv.push_back(std::move(record));
    }
    std::vector<Hero> hero;hero.reserve(918);std::set<std::string> keys;
    for(std::size_t index=0;index<918;++index) {
        auto columns=fields(hero_plain,hl[index+25]);
        if(columns.size()!=6 && columns.size()!=7)invalid();
        auto key=ascii(columns[0])+ascii(columns[1]);
        for(auto& c:key)c=static_cast<char>(ascii_lower(static_cast<std::uint8_t>(c)));
        if(key.empty() || !keys.insert(key).second || columns[3].size()>=30)invalid();
        (void)ascii(columns[3]);
        auto filename=columns[3];for(auto& c:filename)c=ascii_lower(c);
        const std::array<std::int32_t,3> numeric={number(columns[2]),number(columns[4]),number(columns[5])};
        Hero record{index,std::move(key),std::move(filename),numeric,static_cast<std::uint8_t>(numeric[2]&0xff),
            row(hero_plain,hl[index+25],index,index+26,std::move(columns))};
        hero.push_back(std::move(record));
    }
    return std::shared_ptr<const TaiwanNativeActorResourceBank>(new TaiwanNativeActorResourceBank(
        std::move(drv_origin),std::move(drv_plain),std::move(drv),
        std::move(hero_origin),std::move(hero_plain),std::move(hero)));
}
const TaiwanNativeActorResourceBank::Drv* TaiwanNativeActorResourceBank::find_drv(std::uint32_t ordinal) const noexcept {
    // Native463780 sign-extends WORD and lacks a general negative guard.
    // Refuse aliases/negative operands; never silently truncate a larger ID.
    if(ordinal>0x7fff || ordinal>=drv_.size())return nullptr;return &drv_[ordinal];
}
const TaiwanNativeActorResourceBank::Hero* TaiwanNativeActorResourceBank::find_hero(std::string_view key) const noexcept {
    for(const auto& record:hero_)if(record.key==key)return &record;return nullptr;
}
TaiwanNativeActorResourceBank::ResolvedRom::ResolvedRom(std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        Family family,std::size_t ordinal,TaiwanNativeResourceSelection selected,
        std::shared_ptr<const TaiwanNativeRomAsset> rom,std::uint32_t action)
    :bank_(std::move(bank)),family_(family),ordinal_(ordinal),selected_(std::move(selected)),
     rom_(std::move(rom)),action_operand_(action) {}
namespace {
bool selected_row(const std::vector<std::uint8_t>& filename,const TaiwanNativeResourceSelection& selected,
        const std::shared_ptr<const TaiwanNativeRomAsset>& rom,std::uint32_t action) {
    // Empty filenames are observed absence, not cache0/load success. Shared
    // filenames never merge the bank's distinct source occurrences.
    if(filename.empty() || !rom)return false;
    const auto& request=selected.request();
    return request.kind==TaiwanNativeResourceSelection::Kind::RomBinary &&
        request.original_reference==filename && rom->source()==selected.actual_source() &&
        rom->encoded_bytes()==selected.encoded_bytes() && rom->find_action(action);
}
}
std::shared_ptr<const TaiwanNativeActorResourceBank::ResolvedRom> TaiwanNativeActorResourceBank::bind_drv_rom(
        std::shared_ptr<const TaiwanNativeActorResourceBank> bank,std::uint32_t ordinal,
        const TaiwanNativeResourceSelection& selected,std::shared_ptr<const TaiwanNativeRomAsset> rom,
        std::uint32_t action) {
    if(!bank)return {};const auto* source=bank->find_drv(ordinal);
    if(!source || !selected_row(source->filename,selected,rom,action))return {};
    // Column2 is ActType for452260's Hero key transform, not a ROM action ID.
    // Retain a private VALUE copy: the caller may have a mutable alias to the
    // asset object even when this parameter is shared_ptr<const>. Its immutable
    // Storage can be shared; reassignment of the caller's object cannot change
    // this validated ROM or invalidate action().
    auto owned_rom=std::make_shared<const TaiwanNativeRomAsset>(*rom);
    return std::shared_ptr<const ResolvedRom>(new ResolvedRom(std::move(bank),ResolvedRom::Family::Drv,
        source->ordinal,selected,std::move(owned_rom),action));
}
std::shared_ptr<const TaiwanNativeActorResourceBank::ResolvedRom> TaiwanNativeActorResourceBank::bind_hero_rom(
        std::shared_ptr<const TaiwanNativeActorResourceBank> bank,std::string_view key,
        const TaiwanNativeResourceSelection& selected,std::shared_ptr<const TaiwanNativeRomAsset> rom,
        std::uint32_t action) {
    if(!bank)return {};const auto* source=bank->find_hero(key);
    if(!source || !selected_row(source->filename,selected,rom,action))return {};
    // Neither Hero column2 nor column4 is substituted for the full operand.
    auto owned_rom=std::make_shared<const TaiwanNativeRomAsset>(*rom);
    return std::shared_ptr<const ResolvedRom>(new ResolvedRom(std::move(bank),ResolvedRom::Family::Hero,
        source->ordinal,selected,std::move(owned_rom),action));
}
}
