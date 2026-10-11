#include "text/NativePeerRoleTextCodec.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <stdexcept>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace god2 {
namespace {
#ifdef _WIN32
std::wstring wide(std::string_view bytes,unsigned page) {
    if(bytes.empty())return {};
    const auto n=MultiByteToWideChar(page,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(bytes.size()),nullptr,0);
    if(!n)throw std::invalid_argument("Peer role source encoding");
    std::wstring result(n,L'\0');
    if(MultiByteToWideChar(page,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(bytes.size()),result.data(),n)!=n)
        throw std::invalid_argument("Peer role source decoding");
    return result;
}
std::string narrow(std::wstring_view text,unsigned page) {
    if(text.empty())return {};
    BOOL substituted=FALSE;
    const auto n=WideCharToMultiByte(page,WC_NO_BEST_FIT_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0,nullptr,&substituted);
    if(!n || substituted)throw std::invalid_argument("Peer role intermediate substitution");
    std::string result(n,'\0');
    if(WideCharToMultiByte(page,WC_NO_BEST_FIT_CHARS,text.data(),static_cast<int>(text.size()),result.data(),n,nullptr,&substituted)!=n || substituted || wide(result,page)!=text)
        throw std::invalid_argument("Peer role intermediate loss");
    return result;
}
std::string map936(const std::string& input,DWORD flags,std::size_t native_capacity) {
    // Match native ANSI LCMap(0x804), then independently compare its Unicode
    // mapping encoded strictly in936, detecting default/best-fit ANSI losses.
    const auto count=LCMapStringA(0x804,flags,input.c_str(),-1,nullptr,0);
    if(count<=0 || static_cast<std::size_t>(count)>native_capacity)
        throw std::invalid_argument("Native peer role map capacity");
    std::string mapped(count,'\0');
    if(LCMapStringA(0x804,flags,input.c_str(),-1,mapped.data(),count)!=count || mapped.back()!=0)
        throw std::invalid_argument("Native peer role map failed");
    mapped.pop_back();
    const auto source=wide(input,936);
    const auto wide_count=LCMapStringW(0x804,flags,source.c_str(),-1,nullptr,0);
    if(wide_count<=0)throw std::invalid_argument("Peer role Unicode map failed");
    std::wstring expected(wide_count,L'\0');
    if(LCMapStringW(0x804,flags,source.c_str(),-1,expected.data(),wide_count)!=wide_count || expected.back()!=0)
        throw std::invalid_argument("Peer role Unicode map failed");
    expected.pop_back();
    if(narrow(expected,936)!=mapped)throw std::invalid_argument("Native peer role map substituted");
    return mapped;
}
#endif
}
std::optional<std::string> NativePeerRoleTextCodec::project(std::string_view source,
    std::uint16_t from,std::uint16_t to) {
    if((from!=936 && from!=950) || (to!=936 && to!=950) || source.size()>15 || source.find('\0')!=source.npos)return std::nullopt;
    try {
        const auto unicode=LegacyChineseCodec::decode(source,from==936);
        if(LegacyChineseCodec::encode(unicode,from==936)!=source)return std::nullopt;
        if(from==to)return std::string(source);
        if(source.empty())return std::string{};
#ifdef _WIN32
        std::string result;
        if(from==950) {
            const auto intermediate=narrow(wide(source,950),936);
            result=map936(intermediate,LCMAP_SIMPLIFIED_CHINESE,intermediate.size()+1);
        } else {
            const auto intermediate=map936(std::string(source),LCMAP_TRADITIONAL_CHINESE,2*(wide(source,936).size()+1));
            result=narrow(wide(intermediate,936),950);
        }
        if(result.size()>15 || result.find('\0')!=result.npos)return std::nullopt;
        return result;
#else
        // No substitute script converter on other hosts: only unchanged ASCII
        // is portable until the matching native OS conversion is qualified.
        if(std::all_of(source.begin(),source.end(),[](unsigned char c){return c<0x80;}))return std::string(source);
        return std::nullopt;
#endif
    } catch(const std::exception&) {return std::nullopt;}
}
}
