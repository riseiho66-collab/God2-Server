#include "game/TaiwanNativeClientGroupConfiguration.h"
#include <algorithm>
#include <array>
#include <stdexcept>

namespace god2 {
namespace {
[[noreturn]] void unqualified() {throw std::invalid_argument("TW group configuration source/form unqualified");}
bool horizontal(char c) {return c==' ' || c=='\t';}
bool token_space(char c) {return c==' ' || (c>='\t' && c<='\r');}
std::string_view left_trim(std::string_view s) {
    while(!s.empty() && horizontal(s.front()))s.remove_prefix(1);
    return s;
}
std::string_view filename(const TaiwanNativeClientGroupConfiguration::Selection& source) {
    if(source.initial_host.size()>255 || source.initial_host.find('\0')!=std::string::npos)unqualified();
    const bool gb=source.word_59dfd8==4 && source.word_59dfda==2;
    if(source.initial_host.starts_with("192.168."))return gb?"config2_gb.ini":"config2.ini";
    return gb?"config_gb.ini":"config.ini";
}
std::vector<std::uint8_t> decode(std::span<const std::uint8_t> source,std::size_t budget) {
    // Independent TW00401D20: 0516/u32-size/extraBYTE, 4096-byte ring,
    // Selected-0516 failure rejects this source. Native temporary FILE/reopen
    // failure/fallback side effects are deliberately outside the owned subset.
    if(!budget || source.empty())unqualified();
    if(source.size()<2 || source[0]!=5 || source[1]!=0x16) {
        if(source.size()>budget)unqualified();
        return {source.begin(),source.end()};
    }
    if(source.size()<7)unqualified();
    const auto size=std::uint32_t(source[2])|(std::uint32_t(source[3])<<8)|
        (std::uint32_t(source[4])<<16)|(std::uint32_t(source[5])<<24);
    if(!size || size>budget)unqualified();
    std::array<std::uint8_t,4096> ring{};std::fill_n(ring.begin(),0xFEE,' ');
    std::array<bool,4096> initialized{};std::fill_n(initialized.begin(),0xFEE,true);
    std::size_t cursor=0xFEE,position=7;unsigned flags=0;
    std::vector<std::uint8_t> result;result.reserve(size);
    const auto append=[&](std::uint8_t value) {
        if(result.size()>=size)unqualified();
        result.push_back(value);ring[cursor]=value;initialized[cursor]=true;cursor=(cursor+1)&4095;
    };
    while(position<source.size()) {
        flags>>=1;
        if(!(flags&0x100))flags=source[position++]|0xFF00;
        if(flags&1) {
            if(position==source.size())break;
            append(source[position++]);
        } else {
            if(source.size()-position<2)unqualified();
            const auto low=source[position++],high=source[position++];
            const auto offset=std::size_t(low)|((std::size_t(high)&0xF0)<<4);
            for(std::size_t i=0;i<std::size_t(high&15)+3;++i) {
                const auto address=(offset+i)&4095;
                if(!initialized[address])unqualified();
                append(ring[address]);
            }
        }
    }
    if(result.size()!=size)unqualified();
    return result;
}
std::int32_t version_integer(std::string_view line) {
    while(!line.empty() && token_space(line.front()))line.remove_prefix(1);
    const bool negative=!line.empty() && line.front()=='-';
    if(!line.empty() && (line.front()=='-' || line.front()=='+'))line.remove_prefix(1);
    if(line.empty() || line.front()<'0' || line.front()>'9')unqualified();
    std::int64_t magnitude=0;const std::int64_t limit=negative?2147483648LL:2147483647LL;
    while(!line.empty() && line.front()>='0' && line.front()<='9') {
        const auto digit=line.front()-'0';if(magnitude>(limit-digit)/10)unqualified();
        magnitude=magnitude*10+digit;line.remove_prefix(1);
    }
    // Own subset excludes failed/partial %d. TW failed scan leaves the old
    if(!std::all_of(line.begin(),line.end(),token_space))unqualified();
    return static_cast<std::int32_t>(negative?-magnitude:magnitude);
}
struct Parsed {
    std::vector<TaiwanNativeClientGroupConfiguration::Group> groups;
    std::optional<std::int32_t> version;
};
Parsed parse(std::span<const std::uint8_t> plain) {
    std::string text;text.reserve(plain.size());
    for(std::size_t i=0;i<plain.size();++i) {
        if(!plain[i] || plain[i]==0x1A)unqualified();
        // Native rt FILE translates CRLF before fgets. Retain raw plain bytes.
        if(plain[i]=='\r') {
            if(i+1==plain.size() || plain[i+1]!='\n')unqualified();
            continue;
        }
        text.push_back(static_cast<char>(plain[i]));
    }
    Parsed result;bool rows=false;std::size_t at=0;
    while(at<text.size()) {
        const auto end=text.find('\n',at);
        // Complete LF-terminated lines only; do not imitate unsafe/chunk scans.
        if(end==std::string::npos || end-at+1>127)unqualified();
        auto line=left_trim(std::string_view(text).substr(at,end-at));at=end+1;
        if(line.empty()){rows=false;continue;}
        if(line.front()==';' || line.front()=='#')continue;
        if(!rows && line.front()=='$'){result.version=version_integer(line.substr(1));continue;}
        if(line.front()=='[') {
            if(result.groups.size()>=64)unqualified();
            const auto close=line.find(']',1);
            if(close==std::string_view::npos || close-1>=64)unqualified();
            // Duplicate labels and empty groups retain independent ordinals.
            result.groups.push_back({std::string(line.substr(1,close-1)),{}});rows=true;continue;
        }
        if(!rows)continue;
        TaiwanNativeClientGroupConfiguration::Slot slot;
        const auto equals=line.find('=');
        if(equals!=std::string_view::npos) {
            auto name=line.substr(0,equals);
            while(!name.empty() && horizontal(name.back()))name.remove_suffix(1);
            if(name.empty() || name.size()>=64)unqualified();
            slot.name_bytes=std::string(name);
            auto value=line.substr(equals+1);
            while(!value.empty() && token_space(value.front()))value.remove_prefix(1);
            const auto finish=std::find_if(value.begin(),value.end(),token_space);
            value=value.substr(0,static_cast<std::size_t>(finish-value.begin()));
            if(value.size()>=64)unqualified();
            slot.value_bytes=std::string(value);
        }
        // No '=': native helpers write two empty strings, then still ++T+40.
        result.groups.back().slots.push_back(std::move(slot));
        if(result.groups.back().slots.size()==10)rows=false;
    }
    return result;
}
}
TaiwanNativeClientGroupConfiguration::TaiwanNativeClientGroupConfiguration(Selection selection,
    TaiwanNativeResourceSelection selected,std::vector<std::uint8_t> plain,std::vector<Group> groups,
    std::optional<std::int32_t> version)
    :selection_(std::move(selection)),selected_(std::move(selected)),plain_(std::move(plain)),
     groups_(std::move(groups)),version_(version) {}
std::shared_ptr<const TaiwanNativeClientGroupConfiguration> TaiwanNativeClientGroupConfiguration::read(
    const std::filesystem::path& root,Selection selection,std::size_t encoded_budget,std::size_t plain_budget) {
    if(!root.is_absolute() || !encoded_budget || !plain_budget)unqualified();
    // Already resolved actual root, not native formatter emulation. Preserve
    // this exact relative source request and all candidate/original file bytes.
    const std::string reference="Data3/"+std::string(filename(selection));
    TaiwanNativeResourceSelection::Request request{TaiwanNativeResourceSelection::Kind::TextFile,
        {reference.begin(),reference.end()},{},root,0};
    auto selected=TaiwanNativeResourceSelection::select(request,encoded_budget);
    if(!selected)unqualified();
    std::vector<std::uint8_t> plain;
    if(selected->branch()==TaiwanNativeResourceSelection::Branch::Candidate0516)
        plain=decode(selected->encoded_bytes(),plain_budget);
    else {
        // OriginalAfter* is a native rt reopen, even when the original starts
        // with0516. Do not re-probe that file and invent a second decode branch.
        const auto& original=selected->encoded_bytes();
        if(original.size()>plain_budget)unqualified();
        plain.assign(original.begin(),original.end());
    }
    auto parsed=parse(plain);
    return std::shared_ptr<const TaiwanNativeClientGroupConfiguration>(new TaiwanNativeClientGroupConfiguration(
        std::move(selection),std::move(*selected),std::move(plain),std::move(parsed.groups),parsed.version));
}
std::optional<std::uint8_t> TaiwanNativeClientGroupConfiguration::configured_slots(std::uint8_t ordinal) const noexcept {
    if(ordinal>=groups_.size())return std::nullopt;
    return static_cast<std::uint8_t>(groups_[ordinal].slots.size());
}
}
