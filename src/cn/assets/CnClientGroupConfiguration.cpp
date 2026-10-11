#include "cn/assets/CnClientGroupConfiguration.h"
#include <algorithm>
#include <stdexcept>

namespace god2cn {
namespace {
bool horizontal(char c) {return c==' ' || c=='\t';}
bool token_space(char c) {return c==' ' || (c>='\t' && c<='\r');}
std::string_view left_trim(std::string_view s) {
    while(!s.empty() && horizontal(s.front()))s.remove_prefix(1);
    return s;
}
std::int32_t version_integer(std::string_view s) {
    while(!s.empty() && token_space(s.front()))s.remove_prefix(1);
    const bool negative=!s.empty() && s.front()=='-';
    if(!s.empty() && (s.front()=='+' || s.front()=='-'))s.remove_prefix(1);
    std::int64_t magnitude=0;
    const std::int64_t limit=negative?2147483648LL:2147483647LL;
    while(!s.empty() && s.front()>='0' && s.front()<='9') {
        const auto digit=s.front()-'0';
        if(magnitude>(limit-digit)/10)
            throw std::invalid_argument("CN config integer overflow form unqualified");
        magnitude=magnitude*10+digit;s.remove_prefix(1);
    }
    // Native local integer is reset0 before%d scanning, even if no conversion
    // succeeds. Missing$ is DIFFERENT: no recorded version source is available.
    return static_cast<std::int32_t>(negative?-magnitude:magnitude);
}
struct Parsed {
    std::vector<CnClientGroupConfiguration::Group> groups;
    std::optional<std::int32_t> version;
};
Parsed parse(std::span<const std::uint8_t> input) {
    // fopen("r") translates CRLF. Reject unsupported malformed/oversized
    // forms instead of reproducing native buffer overwrite/chunk side effects.
    std::string text;
    text.reserve(input.size());
    for(std::size_t i=0;i<input.size();++i) {
        if(input[i]==0)throw std::invalid_argument("CN config embedded NUL unqualified");
        if(input[i]==0x1a)throw std::invalid_argument("CN config text EOF marker form unqualified");
        if(input[i]=='\r') {
            if(i+1>=input.size() || input[i+1]!='\n')
                throw std::invalid_argument("CN config lone CR unqualified");
            continue;
        }
        text.push_back(static_cast<char>(input[i]));
    }
    std::vector<CnClientGroupConfiguration::Group> groups;
    std::optional<std::int32_t> version;
    bool rows=false;
    std::size_t at=0;
    while(at<text.size()) {
        const auto end=text.find('\n',at);
        const auto stop=end==std::string::npos?text.size():end;
        const auto fgets_bytes=stop-at+(end!=std::string::npos?1:0);
        if(fgets_bytes>127)throw std::invalid_argument("CN config fgets chunk form unqualified");
        auto line=left_trim(std::string_view(text).substr(at,stop-at));
        at=end==std::string::npos?text.size():end+1;
        if(line.empty()){rows=false;continue;}
        if(line.front()==';' || line.front()=='#')continue;
        if(!rows && line.front()=='$') {version=version_integer(line.substr(1));continue;}
        if(line.front()=='[') {
            if(groups.size()>=64)throw std::invalid_argument("CN config group capacity exceeded");
            const auto close=line.find(']',1);
            if(close==std::string_view::npos || close-1>=64)
                throw std::invalid_argument("CN config group label unqualified");
            // Duplicate labels remain DIFFERENT ordinal groups, like native.
            groups.push_back({std::string(line.substr(1,close-1)),{}});
            rows=true;continue;
        }
        // Outside a group, native handles$ @ ^ - as local setup operands.
        // Their bytes remain in plain_, but are not gameplay rights/billing.
        if(!rows)continue;
        CnClientGroupConfiguration::Slot slot;
        const auto equals=line.find('=');
        if(equals!=std::string_view::npos) {
            auto name=line.substr(0,equals);
            while(!name.empty() && horizontal(name.back()))name.remove_suffix(1);
            if(name.empty() || name.size()>=64)
                throw std::invalid_argument("CN config row label unqualified");
            slot.name_bytes=std::string(name);
            auto value=line.substr(equals+1);
            while(!value.empty() && token_space(value.front()))value.remove_prefix(1);
            const auto token=std::find_if(value.begin(),value.end(),token_space);
            value=value.substr(0,static_cast<std::size_t>(token-value.begin()));
            if(value.size()>=64)throw std::invalid_argument("CN config row token unqualified");
            slot.value_bytes=std::string(value);
        }
        // A non-comment row WITHOUT'=' still consumes a native slot with
        // zeroed name/value. Do not infer the slot count from address validity.
        groups.back().slots.push_back(std::move(slot));
        if(groups.back().slots.size()==10)rows=false;
    }
    if(groups.empty())throw std::invalid_argument("CN group configuration unavailable");
    return {std::move(groups),version};
}
std::string_view filename(const CnClientGroupConfiguration::Selection& source) {
    if(source.initial_host.find('\0')!=std::string::npos || source.address_operand.find('\0')!=std::string::npos)
        throw std::invalid_argument("CN config selection operands contain embedded NUL");
    // The pinned helper00405A30 is xor eax,eax;ret. Its GB paths are not
    // selected by this build. Keep Hant/Hans and Windows locale independent.
    if(source.initial_host.starts_with("192.168."))
        return source.address_operand=="101.133.196.125"?"config2_2.ini":"config2.ini";
    return source.address_operand=="49.235.177.12"?"config_2.ini":"config.ini";
}
}
CnClientGroupConfiguration::CnClientGroupConfiguration(Selection selection,CnSelectedResource selected,
    std::vector<std::uint8_t> plain,std::vector<Group> groups,std::optional<std::int32_t> version)
    :selection_(std::move(selection)),selected_(std::move(selected)),plain_(std::move(plain)),
     groups_(std::move(groups)),version_(version) {}
std::shared_ptr<const CnClientGroupConfiguration> CnClientGroupConfiguration::read(
    const std::filesystem::path& root,Selection selection,std::size_t encoded_budget,std::size_t plain_budget) {
    const auto file=filename(selection);
    auto selected=read_cn_preferred_resource(root/"Data3"/std::string(file),encoded_budget);
    auto plain=decode_cn_resource(selected.encoded_bytes,plain_budget);
    auto parsed=parse(plain);
    return std::shared_ptr<const CnClientGroupConfiguration>(new CnClientGroupConfiguration(
        std::move(selection),std::move(selected),std::move(plain),std::move(parsed.groups),parsed.version));
}
std::optional<std::uint8_t> CnClientGroupConfiguration::configured_slots(std::uint8_t ordinal) const noexcept {
    if(ordinal>=groups_.size())return std::nullopt;
    return static_cast<std::uint8_t>(groups_[ordinal].slots.size());
}
std::shared_ptr<const CnClientGroupConfiguration> CnClientGroupConfiguration::read_from_startup_argument(
    const std::filesystem::path& root,std::span<const std::uint8_t> first_argument,
    std::size_t encoded_budget,std::size_t plain_budget) {
    //00404CE0 uses native vsnprintf_s and literal"%s" with a256-byte
    // destination: this COPIES the complete parsed argument, not scanf/token
    // splitting. Long/error paths remain unqualified, never truncated here.
    if(first_argument.size()>255 || std::find(first_argument.begin(),first_argument.end(),0)!=first_argument.end())
        throw std::invalid_argument("CN startup argument copy form unqualified");
    std::string address;
    if(!first_argument.empty())
        address.assign(reinterpret_cast<const char*>(first_argument.data()),first_argument.size());
    // Same local buffer is copied to008AEEC0 and supplied to00449F50 ->
    // main+240 -> both0047FA20 controllers ->0047C990 in normal startup.
    return read(root,Selection(address,address),encoded_budget,plain_budget);
}
}
