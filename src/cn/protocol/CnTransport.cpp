#include "cn/protocol/CnTransport.h"
#include "cn/protocol/CnNativeTables.h"
#include <algorithm>
#include <stdexcept>

namespace god2cn {
// Evidence: pinned CN 00479650 key/challenge, 0047A760 encode,
// 0047A590 decode, 0047A800 seed intake, 0047A3C0 challenge emission.
// Static reconstruction. Comprehensive execution verification is deferred.
CnTransport::CnTransport(const std::array<std::uint8_t,16>& seed):seed_(seed) {
    std::copy(seed.begin(),seed.end(),key_.begin());
    for(unsigned i=16;i<256;++i) {
        const auto selector=seed[i&15];
        const auto value=seed[selector&15];
        auto accumulator=static_cast<std::uint8_t>(i+selector);
        for(unsigned bit=0;bit<4;++bit) {
            accumulator=static_cast<std::uint8_t>(accumulator+
                ((selector&(0x80u>>bit))?static_cast<int>(value>>bit):-static_cast<int>(value<<bit)));
        }
        key_[i]=static_cast<std::uint8_t>(cn_key_table[i]+accumulator);
    }
    for(unsigned i=0;i<16;++i) {
        const auto index=static_cast<std::uint8_t>(cn_key_table[i]+cn_key_table[i+1]);
        challenge_[i]=static_cast<std::uint8_t>(key_[index]+cn_key_table[i]);
    }
    for(auto value:key_)initial_previous_=static_cast<std::uint8_t>(initial_previous_-value);
}
Bytes CnTransport::frame(std::span<const std::uint8_t> logical,bool encrypted) const {
    if(logical.empty() || logical.size()>max_logical)throw std::invalid_argument("CN logical envelope bounds");
    const auto size=logical.size()+3;
    Bytes output{static_cast<std::uint8_t>(size),static_cast<std::uint8_t>(size>>8)};
    output.reserve(size);
    auto checksum=static_cast<std::uint8_t>(output[0]+output[1]+2*0x3c);
    auto previous=initial_previous_;
    for(std::size_t i=0;i<=logical.size();++i) {
        const auto plain=i==logical.size()?checksum:logical[i];
        output.push_back(encrypted?static_cast<std::uint8_t>((plain^key_[i&255])+previous-3):plain);
        previous=plain;
        if(i<logical.size())checksum=static_cast<std::uint8_t>(checksum+plain+0x3c);
    }
    return output;
}
Bytes CnTransport::seed_frame() const {return frame(seed_,false);}
Bytes CnTransport::encode_server_frame(std::span<const std::uint8_t> logical) const {return frame(logical,true);}
Bytes CnTransport::decode_client_frame(std::span<const std::uint8_t> wire) const {
    if(wire.size()<4 || wire.size()>max_wire || (wire[1]&0x80) ||
       (static_cast<std::size_t>(wire[0])+(static_cast<std::size_t>(wire[1])<<8))!=wire.size())
        throw std::invalid_argument("CN frame length/flags invalid");
    // CN C2S encoder 0047A760 emits uncompressed frames. The compression flag
    // in 0047A590 belongs to client S2C reception, not inferred C2S support.
    Bytes result;result.reserve(wire.size()-3);
    auto checksum=static_cast<std::uint8_t>(wire[0]+wire[1]+2*0x3c);
    auto previous=initial_previous_;
    for(std::size_t i=2;i<wire.size();++i) {
        const auto plain=static_cast<std::uint8_t>(static_cast<std::uint8_t>(wire[i]+3-previous)^key_[(i-2)&255]);
        previous=plain;
        if(i+1==wire.size()) {
            if(plain!=checksum)throw std::invalid_argument("CN frame checksum invalid");
        } else {result.push_back(plain);checksum=static_cast<std::uint8_t>(checksum+plain+0x3c);}
    }
    return result;
}
bool CnTransport::accepts_challenge(std::span<const std::uint8_t> wire) const {
    if(wire.size()!=19)return false;
    const auto plain=decode_client_frame(wire);
    unsigned difference=0;
    for(std::size_t i=0;i<challenge_.size();++i)difference|=plain[i]^challenge_[i];
    return difference==0;
}
}
