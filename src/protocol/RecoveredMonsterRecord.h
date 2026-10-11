#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// S2C71, logical length21 (40127C). 46A3B4 -> 4CB120/4CB720.
// Preserve opaque bytes; a catalog key is NOT an instance or a map placement.
class RecoveredMonsterRecord {
public:
    static constexpr std::size_t wireSize=21;
    using Bytes=std::array<std::uint8_t,wireSize>;
    static std::optional<RecoveredMonsterRecord> parse(std::span<const std::uint8_t> input) {
        if(input.size()!=wireSize || input[0]!=0x71) return std::nullopt;
        Bytes bytes;std::copy(input.begin(),input.end(),bytes.begin());
        return RecoveredMonsterRecord(bytes);
    }
    Bytes encode() const noexcept {return bytes_;}
    std::uint16_t identity() const noexcept {return static_cast<std::uint16_t>(read32(1));}
    std::uint8_t facing() const noexcept {return static_cast<std::uint8_t>(read32(1)>>29);}
    std::uint8_t resourceOverride() const noexcept {return bytes_[3];}
    std::uint8_t catalogArea() const noexcept {return bytes_[5]&0x3f;}
    std::uint16_t catalogScene() const noexcept {return read16(5)>>6;}
    std::uint16_t catalogOrdinal() const noexcept {return read16(19)>>3;}
    std::uint16_t x() const noexcept {return static_cast<std::uint16_t>((read32(9)>>2)&0x7fff);}
    std::uint16_t y() const noexcept {return static_cast<std::uint16_t>(read32(9)>>17);}
    bool setPosition(std::uint64_t xValue,std::uint64_t yValue) noexcept {
        if(xValue>0x7fff || yValue>0x7fff) return false;
        write32(9,static_cast<std::uint32_t>((yValue<<17)|(xValue<<2))|(read32(9)&3));return true;
    }
    bool setFacing(std::uint64_t value) noexcept {
        if(value>7) return false;
        write32(1,(read32(1)&0x1fffffff)|(static_cast<std::uint32_t>(value)<<29));return true;
    }
    bool setIdentity(std::uint64_t value) noexcept {
        if(value>0xffff) return false;
        bytes_[1]=static_cast<std::uint8_t>(value);bytes_[2]=static_cast<std::uint8_t>(value>>8);return true;
    }
    bool setCatalog(std::uint64_t area,std::uint64_t scene,std::uint64_t ordinal) noexcept {
        if(area>=17 || scene>1023 || !ordinal || ordinal>8191) return false;
        const auto group=(scene<<6)|area;
        bytes_[5]=static_cast<std::uint8_t>(group);bytes_[6]=static_cast<std::uint8_t>(group>>8);
        const auto key=(ordinal<<3)|(read16(19)&7);
        bytes_[19]=static_cast<std::uint8_t>(key);bytes_[20]=static_cast<std::uint8_t>(key>>8);return true;
    }
private:
    explicit RecoveredMonsterRecord(Bytes bytes):bytes_(bytes){}
    std::uint16_t read16(std::size_t offset) const noexcept {
        return static_cast<std::uint16_t>(bytes_[offset]|(std::uint16_t{bytes_[offset+1]}<<8));
    }
    std::uint32_t read32(std::size_t offset) const noexcept {
        std::uint32_t value=0;for(unsigned i=0;i<4;++i)value|=std::uint32_t{bytes_[offset+i]}<<(8*i);return value;
    }
    void write32(std::size_t offset,std::uint32_t value) noexcept {
        for(unsigned i=0;i<4;++i)bytes_[offset+i]=static_cast<std::uint8_t>(value>>(8*i));
    }
    Bytes bytes_;
};
}
