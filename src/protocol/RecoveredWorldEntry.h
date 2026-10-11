#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <span>
#include <stdexcept>

namespace god2 {
struct RecoveredWorldEntry {
    using Body=std::array<std::uint8_t,36>;
    using Frame=std::array<std::uint8_t,40>;
    // Historical decoded record, qualified against the current 68160 consumer.
    // This is an opt-in bootstrap candidate, not a complete profile projection.
    // Provenance: tests/fixtures/recovered-world-entry.json. Preserve opaque bits.
    static constexpr Body historical_body{
        0xd9,0x00,0x80,0x00,0x05,0x10,0x1b,0x02,0x00,0x00,0x00,0x00,
        0x01,0x80,0x01,0x60,0x01,0x60,0x31,0x00,0x60,0x00,0x31,0x0c,
        0xc2,0x03,0x00,0x00,0x46,0x00,0x1a,0x00,0x00,0x00,0x00,0x00};

    static Frame decoded(std::uint64_t local_id) {
        // Current 68629 masks to 14 bits. Never silently alias a larger DB ID.
        if(local_id==0 || local_id>0x3fff)
            throw std::invalid_argument("World candidate identity exceeds recovered 14-bit range");
        Frame frame{};frame[0]=40;frame[2]=0x2a;
        std::copy(historical_body.begin(),historical_body.end(),frame.begin()+3);
        frame[3]=static_cast<std::uint8_t>(local_id);
        frame[4]=static_cast<std::uint8_t>((frame[4]&0xc0)|(local_id>>8));
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        return frame;
    }
    static Frame decoded(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile) {
        if(profile[32]>6 || (profile[36]>>5)>6)
            throw std::invalid_argument("World component variant exceeds current profile bounds");
        static_assert(historical_body[32]==0 && historical_body[33]==0,
                      "Profile variants require the normal component branch");
        auto frame=decoded(local_id);
        // Current create preview and world path share FFA20 variant setters.
        // Preserve binary/resource selectors; their correspondence is unqualified.
        frame[16]=static_cast<std::uint8_t>((frame[16]&0x1f)|(profile[32]<<5));
        frame[18]=static_cast<std::uint8_t>((frame[18]&0x1f)|(profile[36]&0xe0));
        // Native 68370 copies body[20..23] to actor+458C. HUD ABCED
        // passes that block to ABE80: hairstyle/color, accessory, sex/face.
        // Match selection W20/W22/W23/W24 (8076..8106), including its zero accessory.
        // Selection 7FBD..800D reduces the low-five-bit hairstyle modulo 8.
        frame[23]=static_cast<std::uint8_t>(profile[36]&0xe7);
        frame[24]=0;
        frame[25]=profile[38];
        frame[26]=profile[39];
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        return frame;
    }
    static Frame wire(std::uint64_t local_id) { return encode(decoded(local_id)); }
    static Frame decoded(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile,
                         std::uint16_t x,std::uint16_t y) {
        if(x>0x7fff || y>0x7fff) throw std::invalid_argument("World coordinate exceeds 15-bit field");
        auto frame=decoded(local_id,profile);
        // Current 68636..68659 reads body+28: kind:2, x:15, y:15.
        const auto packed=static_cast<std::uint32_t>(frame[31]&3)|
            (static_cast<std::uint32_t>(x)<<2)|(static_cast<std::uint32_t>(y)<<17);
        for(unsigned i=0;i<4;++i) frame[31+i]=static_cast<std::uint8_t>(packed>>(8*i));
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        return frame;
    }
    static Frame wire(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile,
                      std::uint16_t x,std::uint16_t y) { return encode(decoded(local_id,profile,x,y)); }
    static Frame decoded(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile,
                         std::uint16_t x,std::uint16_t y,std::uint16_t area,std::uint16_t scene,
                         std::uint16_t kind=2) {
        // Current 681CF..68310 reads body+24: area:6, scene:10.
        // Field bounds do not establish map existence or navigation validity.
        if(area<1 || area>16 || scene>1023 || kind>3)
            throw std::invalid_argument("World map exceeds current consumer bounds");
        auto frame=decoded(local_id,profile,x,y);
        const auto packed=static_cast<std::uint16_t>(area|(scene<<6));
        frame[27]=static_cast<std::uint8_t>(packed);
        frame[28]=static_cast<std::uint8_t>(packed>>8);
        frame[31]=static_cast<std::uint8_t>((frame[31]&0xfc)|kind);
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        return frame;
    }
    static Frame wire(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile,
                      std::uint16_t x,std::uint16_t y,std::uint16_t area,std::uint16_t scene,
                      std::uint16_t kind=2) {
        return encode(decoded(local_id,profile,x,y,area,scene,kind));
    }
    static Frame wire(std::uint64_t local_id,const std::array<std::uint8_t,40>& profile) {
        return encode(decoded(local_id,profile));
    }
private:
    static Frame encode(Frame frame) {
        std::uint8_t previous=0;
        for(std::size_t i=2;i<frame.size();++i) {
            const auto plain=frame[i];
            frame[i]=static_cast<std::uint8_t>((plain^recovered_zero_seed_key[i-2])+previous-3);
            previous=plain;
        }
        return frame;
    }
};
}
