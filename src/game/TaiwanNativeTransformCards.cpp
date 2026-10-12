#include "game/TaiwanNativeTransformCards.h"
#include <algorithm>
#include <charconv>
#include <stdexcept>
#include <string>
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
[[noreturn]] void invalid(){throw std::invalid_argument("Unqualified TW ChangeDollCard source");}
std::string digest(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))invalid();
    DWORD size=0,returned=0;
    auto status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))invalid();
    std::string out;for(const auto b:result){out+="0123456789abcdef"[b>>4];out+="0123456789abcdef"[b&15];}return out;
#else
    (void)bytes;throw std::runtime_error("Qualified TW ChangeDollCard SHA256 backend unavailable");
#endif
}
struct Line {std::size_t offset,size;bool lf;};
std::string_view text(const std::vector<std::uint8_t>& data,Line line) {
    auto out=std::string_view(reinterpret_cast<const char*>(data.data()+line.offset),line.size);
    while(!out.empty()&&out.back()=='\r')out.remove_suffix(1);return out;
}
bool whitespace(char c){return c==' '||c=='\t'||c=='\r'||c=='\n'||c=='\v'||c=='\f';}
std::int32_t number(std::span<const std::uint8_t> bytes) {
    if(bytes.empty())invalid();
    auto field=std::string_view(reinterpret_cast<const char*>(bytes.data()),bytes.size());
    while(!field.empty()&&whitespace(field.front()))field.remove_prefix(1);
    while(!field.empty()&&whitespace(field.back()))field.remove_suffix(1);
    if(field.empty())invalid();
    if(field.front()=='+'){field.remove_prefix(1);if(field.empty()||field.front()=='-'||field.front()=='+')invalid();}
    std::int32_t value{};const auto parsed=std::from_chars(field.data(),field.data()+field.size(),value);
    // Preserve declared%d signed32 then lowBYTE/WORD stores, while refusing
    // trailing junk/failed conversions rather than copying native unchecked data.
    if(parsed.ec!=std::errc{}||parsed.ptr!=field.data()+field.size())invalid();return value;
}
TaiwanNativeTransformCards::SourceRow row(const std::vector<std::uint8_t>& plain,Line line,std::size_t index) {
    TaiwanNativeTransformCards::SourceRow source;
    source.source_record_index=index;source.source_line=index+6;source.source_offset=line.offset;
    const auto end=line.offset+line.size+(line.lf?1:0);
    source.raw_record.assign(plain.begin()+line.offset,plain.begin()+end);
    const auto value=text(plain,line);
    if(value.empty()||value.size()>=2048||value.find('\0')!=std::string_view::npos)invalid();
    std::size_t field=0,begin=0;
    for(std::size_t i=0;i<=value.size();++i)if(i==value.size()||value[i]==',') {
        if(field>=source.fields.size()||i-begin>=380)invalid();
        const auto* data=reinterpret_cast<const std::uint8_t*>(value.data());
        source.fields[field++].assign(data+begin,data+i);begin=i+1;
    }
    if(field!=source.fields.size())invalid();
    for(const auto selected:{0,1,3,4,5})source.selected_numbers[selected]=number(source.fields[selected]);
    for(std::size_t selected=8;selected<=22;++selected)source.selected_numbers[selected]=number(source.fields[selected]);
    return source;
}
}

TaiwanNativeTransformCards::TaiwanNativeTransformCards(std::filesystem::path origin,
    std::vector<std::uint8_t> plain,std::vector<std::uint8_t> header,std::vector<Record> records)
    :origin_(std::move(origin)),plain_(std::move(plain)),header_(std::move(header)),records_(std::move(records)) {}
std::shared_ptr<const TaiwanNativeTransformCards> TaiwanNativeTransformCards::from_pinned_decoded(
        std::filesystem::path origin,std::span<const std::uint8_t> bytes) {
    if(origin.empty()||!origin.is_absolute()||bytes.empty()||bytes.size()>4*1024*1024)invalid();
    std::vector<std::uint8_t> plain(bytes.begin(),bytes.end());if(digest(plain)!=decoded_sha256)invalid();
    std::vector<Line> lines;std::size_t begin=0;
    for(std::size_t i=0;i<plain.size();++i)if(plain[i]=='\n'){lines.push_back({begin,i-begin,true});begin=i+1;}
    if(begin<plain.size())lines.push_back({begin,plain.size()-begin,false});
    // These envelope/sequence facts are the existing original decoded pin,
    // not a claim that a new decoded file has been recovered or loaded today.
    if(lines.size()!=106||text(plain,lines[4])!="ChangeDollCount,101")invalid();
    std::vector<Record> records;records.reserve(101);
    for(std::size_t index=0;index<101;++index) {
        auto source=row(plain,lines[index+5],index);
        if(*source.selected_numbers[0]!=static_cast<std::int32_t>(index))invalid();
        Record record;
        record.key=static_cast<std::uint16_t>(*source.selected_numbers[0]);
        record.source_word1=static_cast<std::uint16_t>(*source.selected_numbers[1]);
        record.target={static_cast<std::uint8_t>(*source.selected_numbers[3]),
            static_cast<std::uint16_t>(*source.selected_numbers[4]),static_cast<std::uint16_t>(*source.selected_numbers[5])};
        for(std::size_t i=0;i<record.selected_words.size();++i)
            record.selected_words[i]=static_cast<std::uint16_t>(*source.selected_numbers[i+8]);
        record.source=std::move(source);records.push_back(std::move(record));
    }
    const auto header=lines[4];const auto end=header.offset+header.size+(header.lf?1:0);
    std::vector<std::uint8_t> raw_header(plain.begin()+header.offset,plain.begin()+end);
    return std::shared_ptr<const TaiwanNativeTransformCards>(new TaiwanNativeTransformCards(
        std::move(origin),std::move(plain),std::move(raw_header),std::move(records)));
}
const TaiwanNativeTransformCards::Record* TaiwanNativeTransformCards::find(std::uint16_t key) const noexcept {
    if(key>=records_.size()||records_[key].key!=key)return nullptr;return &records_[key];
}
}
