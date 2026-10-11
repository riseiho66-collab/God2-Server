#include "game/TaiwanNativeNpcSceneGroups.h"
#include <algorithm>
#include <charconv>
#include <iterator>
#include <optional>
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
[[noreturn]] void invalid(){throw std::invalid_argument("Unqualified TW NPCList source");}
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
    (void)bytes;throw std::runtime_error("Qualified TW NPCList SHA256 backend unavailable");
#endif
}
struct Line {std::size_t offset,size;bool lf;};
std::string_view text(const std::vector<std::uint8_t>& data,Line line) {
    auto out=std::string_view(reinterpret_cast<const char*>(data.data()+line.offset),line.size);
    while(!out.empty()&&out.back()=='\r')out.remove_suffix(1);
    return out;
}
bool boundary(std::string_view s) {
    const auto letter=[](char c){return (c>='A'&&c<='Z')||(c>='a'&&c<='z');};
    if(s.empty()||!letter(s.front()))return false;
    std::size_t i=1;while(i<s.size()&&(letter(s[i])||(s[i]>='0'&&s[i]<='9')||s[i]=='_'))++i;
    if(i==s.size()||s[i++]!=',')return false;
    const auto start=i;while(i<s.size()&&s[i]>='0'&&s[i]<='9')++i;
    return i>start&&(i==s.size()||s[i]==',');
}
bool whitespace(char c){return c==' '||c=='\t'||c=='\r'||c=='\n'||c=='\v'||c=='\f';}
std::int32_t number(std::string_view field) {
    while(!field.empty()&&whitespace(field.front()))field.remove_prefix(1);
    while(!field.empty()&&whitespace(field.back()))field.remove_suffix(1);
    if(field.empty())invalid();
    if(field.front()=='+'){field.remove_prefix(1);if(field.empty()||field.front()=='-'||field.front()=='+')invalid();}
    std::int32_t value{};const auto parsed=std::from_chars(field.data(),field.data()+field.size(),value);
    if(parsed.ec!=std::errc{}||parsed.ptr!=field.data()+field.size())invalid();return value;
}
// Strict ASCII CSV integer subset used by the qualified original row source.
// Accept quoted numbers and CSV escaped quotes; numeric parsing rejects an
// embedded quote. Native sscanf's trailing-junk acceptance is not reproduced.
std::vector<std::int32_t> fields(std::string_view line) {
    std::vector<std::int32_t> out;std::size_t p=0;
    do {
        std::string field;
        if(p<line.size()&&line[p]=='"') {
            ++p;bool closed=false;
            while(p<line.size()) {
                const char c=line[p++];
                if(c!='"'){field+=c;continue;}
                if(p<line.size()&&line[p]=='"'){field+='"';++p;continue;}
                closed=true;break;
            }
            if(!closed||(p<line.size()&&line[p]!=','))invalid();
        } else {while(p<line.size()&&line[p]!=',')field+=line[p++];}
        if(out.size()==7)invalid();out.push_back(number(field));
        if(p==line.size())break;
        ++p;if(p==line.size())invalid();
    } while(true);
    if(out.size()<2)invalid();return out;
}
TaiwanNativeNpcSceneGroups::SourceRow source_row(
    const std::vector<std::uint8_t>& plain,Line line,std::size_t line_index,std::size_t record_index) {
    const auto end=line.offset+line.size+(line.lf?1:0);
    return {record_index,line_index+1,line.offset,{plain.begin()+line.offset,plain.begin()+end}};
}
}

TaiwanNativeNpcSceneGroups::TaiwanNativeNpcSceneGroups(std::filesystem::path origin,
    std::vector<std::uint8_t> plain,SourceRow header,std::vector<SourceRow> rows,
    std::array<std::vector<Group>,17> groups):origin_(std::move(origin)),plain_(std::move(plain)),
    header_(std::move(header)),rows_(std::move(rows)),groups_(std::move(groups)) {}

std::shared_ptr<const TaiwanNativeNpcSceneGroups> TaiwanNativeNpcSceneGroups::from_pinned_decoded(
    std::filesystem::path origin,std::span<const std::uint8_t> bytes) {
    if(origin.empty()||!origin.is_absolute()||bytes.empty()||bytes.size()>4*1024*1024)invalid();
    // Own before hashing/parsing, so the caller's span is never retained.
    std::vector<std::uint8_t> plain(bytes.begin(),bytes.end());
    if(digest(plain)!=decoded_sha256)invalid();
    std::vector<Line> lines;std::size_t begin=0;
    for(std::size_t i=0;i<plain.size();++i)if(plain[i]=='\n'){lines.push_back({begin,i-begin,true});begin=i+1;}
    lines.push_back({begin,plain.size()-begin,false});
    std::optional<std::size_t> start;
    for(std::size_t i=0;i<lines.size();++i)if(text(plain,lines[i]).starts_with("NPCList,")) {
        if(start)invalid();start=i;
    }
    if(!start)invalid();
    const auto header=text(plain,lines[*start]);const auto count_text=header.substr(8);
    if(count_text.empty()||count_text.size()>5||!std::all_of(count_text.begin(),count_text.end(),[](char c){return c>='0'&&c<='9';})||number(count_text)!=451)invalid();
    if(*start+451>=lines.size())invalid();
    const auto end=*start+452;
    if(end<lines.size()){const auto following=text(plain,lines[end]);if(!following.empty()&&!boundary(following))invalid();}
    std::vector<SourceRow> rows;std::array<std::vector<Group>,17> groups;
    std::size_t total_groups=0,total_codes=0;
    for(std::size_t index=0;index<451;++index) {
        const auto line_index=*start+1+index;const auto line=lines[line_index];
        const auto row=text(plain,line);
        if(row.empty()||boundary(row)||row.find('\0')!=std::string_view::npos||row.size()>=2048||
           !std::all_of(row.begin(),row.end(),[](unsigned char c){return c<128;}))invalid();
        const auto values=fields(row);const auto area=values[0],scene=values[1];
        // These safety bounds belong to this qualified owned subset. Native
        //45A8F0 does not reject negative area or guard newly-created scene70.
        if(area<0||area>=17||scene<0||scene>255)invalid();
        auto& bank=groups[static_cast<std::size_t>(area)];
        auto group=std::find_if(bank.begin(),bank.end(),[scene](const Group& g){return g.scene==scene;});
        if(group==bank.end()) {
            if(bank.size()>=70)invalid();bank.push_back({static_cast<std::uint8_t>(scene),{}, {}});group=std::prev(bank.end());++total_groups;
        }
        group->source_record_indices.push_back(index);
        for(std::size_t field=2;field<values.size();++field) {
            const auto code=values[field];if(code<=0||group->resources.size()>=70)invalid();
            group->resources.push_back({code,index,field,static_cast<std::uint8_t>(code/1000),static_cast<std::uint8_t>(code%1000)});++total_codes;
        }
        rows.push_back(source_row(plain,line,line_index,index));
    }
    if(total_groups!=251||total_codes!=1509)invalid();
    auto header_row=source_row(plain,lines[*start],*start,0);
    return std::shared_ptr<const TaiwanNativeNpcSceneGroups>(new TaiwanNativeNpcSceneGroups(
        std::move(origin),std::move(plain),std::move(header_row),std::move(rows),std::move(groups)));
}

std::span<const TaiwanNativeNpcSceneGroups::Group> TaiwanNativeNpcSceneGroups::area_groups(std::uint8_t area) const {
    if(area>=groups_.size())throw std::out_of_range("TW NPCList area");return groups_[area];
}
const TaiwanNativeNpcSceneGroups::Group* TaiwanNativeNpcSceneGroups::find(std::uint8_t area,std::uint16_t scene) const {
    const auto groups=area_groups(area);const auto found=std::find_if(groups.begin(),groups.end(),[scene](const Group& g){return g.scene==scene;});
    return found==groups.end()?nullptr:&*found;
}
}
