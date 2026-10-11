#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// Bounded1A subset of upstream CnCharacterRequests; native004813C0.
// No create/delete rules imported. Credentials are byte identities, never Lua,
// display text or authority for another account. Tail34..36 is not initialized
// by the native producer and must not be treated as zero or a permission.
class CnCharacterEnter {
public:
    static constexpr std::size_t record_size=38;
    ~CnCharacterEnter(){volatile std::uint8_t* p=payload_.data();for(std::size_t i=0;i<payload_.size();++i)p[i]=0;}
    std::string_view account() const {return field(0);}
    std::string_view credential() const {return field(16);}
    std::uint8_t slot() const {return payload_[32];}
    static std::optional<CnCharacterEnter> read(std::span<const std::uint8_t> bytes) {
        if(bytes.size()!=record_size || bytes[0]!=0x1a)return std::nullopt;
        const auto payload=bytes.subspan(1);
        if(payload[32]>=4 || payload[33]!=4)return std::nullopt;
        for(const auto offset:{0u,16u})
            if(std::find(payload.begin()+offset,payload.begin()+offset+16,0)==payload.begin()+offset+16)
                return std::nullopt;
        CnCharacterEnter value;
        std::copy(payload.begin(),payload.end(),value.payload_.begin());return value;
    }
private:
    CnCharacterEnter()=default;
    std::string_view field(std::size_t offset) const {
        const auto begin=payload_.begin()+offset;
        const auto end=std::find(begin,begin+16,0);
        return {reinterpret_cast<const char*>(payload_.data()+offset),static_cast<std::size_t>(end-begin)};
    }
    std::array<std::uint8_t,37> payload_{};
};
}
