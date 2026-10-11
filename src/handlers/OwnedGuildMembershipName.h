#pragma once
#include "protocol/RecoveredGuildMembership.h"
#include "text/LegacyChineseCodec.h"
#include <string>
#include <string_view>
#include <stdexcept>
namespace god2 {
// CUSTOM-0078: identity fields never use display replacement/OpenCC/truncation.
struct OwnedGuildMembershipName {
    static std::string decode(const RecoveredGuildMembership::Name& field,std::uint16_t codepage) {
        if(codepage!=950 && codepage!=936)throw std::invalid_argument("Guild name codepage unavailable");
        const auto nul=std::find(field.begin(),field.end(),0);
        if(nul==field.begin() || nul==field.end())throw std::invalid_argument("Guild name termination invalid");
        const std::string bytes(reinterpret_cast<const char*>(field.data()),static_cast<std::size_t>(nul-field.begin()));
        const auto name=LegacyChineseCodec::decode(bytes,codepage==936);
        // Controls and printf metacharacters are rejected as Unicode identity,
        // not raw MBC trail bytes. Native names may be passed to format routines.
        for(const auto c:name)if(static_cast<unsigned char>(c)<0x20 || c==0x7f || c=='%')
            throw std::invalid_argument("Guild name contains a control or format character");
        for(std::size_t at=0;at+1<name.size();++at)
            if(static_cast<unsigned char>(name[at])==0xc2 &&
               static_cast<unsigned char>(name[at+1])>=0x80 && static_cast<unsigned char>(name[at+1])<=0x9f)
                throw std::invalid_argument("Guild name contains control");
        for(const bool simplified:{false,true}) {
            const auto encoded=LegacyChineseCodec::encode(name,simplified);
            if(encoded.empty() || encoded.size()>15 || LegacyChineseCodec::decode(encoded,simplified)!=name)
                throw std::invalid_argument("Guild name lacks a lossless bounded bilingual identity");
        }
        if(LegacyChineseCodec::encode(name,codepage==936)!=bytes)
            throw std::invalid_argument("Guild name encoding is not canonical");
        return name;
    }
    static bool valid(const RecoveredGuildMembership::Name& field,std::uint16_t codepage) {
        try {(void)decode(field,codepage);return true;}catch(const std::exception&){return false;}
    }
};
}
