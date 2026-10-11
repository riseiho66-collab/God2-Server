#include "text/LegacyChineseCodec.h"
#include "text/ChineseText.h"
#include <stdexcept>
#include <string>
#ifdef _WIN32
#include <windows.h>
#else
#include <iconv.h>
#include <cerrno>
#endif

namespace god2 {
namespace {
#ifdef _WIN32
std::wstring wide(std::string_view input,unsigned codepage) {
    if(input.empty()) return {};
    const auto size=MultiByteToWideChar(codepage,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),nullptr,0);
    if(!size) throw std::invalid_argument("Invalid Chinese client text encoding");
    std::wstring result(size,L'\0');
    if(MultiByteToWideChar(codepage,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),result.data(),size)!=size)
        throw std::runtime_error("Chinese client decoding failed");
    return result;
}
std::string narrow(std::wstring_view input,unsigned codepage) {
    if(input.empty()) return {};
    BOOL substituted=FALSE;
    const auto flags=codepage==CP_UTF8?WC_ERR_INVALID_CHARS:WC_NO_BEST_FIT_CHARS;
    const auto size=WideCharToMultiByte(codepage,flags,input.data(),
        static_cast<int>(input.size()),nullptr,0,nullptr,
        codepage==CP_UTF8?nullptr:&substituted);
    if(!size || substituted) throw std::invalid_argument("Chinese client cannot represent text");
    std::string result(size,'\0');
    if(WideCharToMultiByte(codepage,flags,input.data(),static_cast<int>(input.size()),
        result.data(),size,nullptr,codepage==CP_UTF8?nullptr:&substituted)!=size || substituted)
        throw std::invalid_argument("Chinese client cannot represent text");
    return result;
}
#else
std::string convert(std::string_view input,const char* from,const char* to) {
    iconv_t converter=iconv_open(to,from);
    if(converter==(iconv_t)-1) throw std::runtime_error("Chinese codec unavailable");
    std::string output(input.size()*4+8,'\0');
    auto* source=const_cast<char*>(input.data());auto remaining=input.size();
    auto* target=output.data();auto capacity=output.size();
    const auto result=iconv(converter,&source,&remaining,&target,&capacity);
    iconv_close(converter);
    if(result==static_cast<std::size_t>(-1) || remaining)
        throw std::invalid_argument("Invalid or unrepresentable Chinese client text");
    output.resize(output.size()-capacity);
    return output;
}
#endif
}
std::string LegacyChineseCodec::decode(std::string_view bytes,bool simplified) {
#ifdef _WIN32
    return narrow(wide(bytes,simplified?936:950),CP_UTF8);
#else
    return convert(bytes,simplified?"CP936":"CP950","UTF-8");
#endif
}
std::string LegacyChineseCodec::encode(std::string_view utf8,bool simplified) {
#ifdef _WIN32
    return narrow(wide(utf8,CP_UTF8),simplified?936:950);
#else
    return convert(utf8,"UTF-8",simplified?"CP936":"CP950");
#endif
}
LegacyChineseCodec::DisplayText LegacyChineseCodec::encode_display(
    std::string_view utf8,bool simplified,std::size_t max_bytes) {
    if(utf8.empty() || utf8.find('\0')!=std::string_view::npos ||
       !ChineseText::valid_utf8(utf8))
        throw std::invalid_argument("Invalid client display text");
    DisplayText result;
    for(std::size_t at=0;at<utf8.size();) {
        const auto lead=static_cast<unsigned char>(utf8[at]);
        const auto width=lead<0x80?1u:lead<0xe0?2u:lead<0xf0?3u:4u;
        std::string encoded;
        bool substituted=false;
        try { encoded=encode(utf8.substr(at,width),simplified); }
        catch(const std::invalid_argument&) {
            encoded="?";
            substituted=true;
        }
        if(result.bytes.size()+encoded.size()>max_bytes) {
            result.truncated=true;
            break;
        }
        result.bytes+=encoded;
        if(substituted) ++result.replacements;
        at+=width;
    }
    if(result.bytes.empty()) throw std::invalid_argument("Empty client display text");
    return result;
}
}
