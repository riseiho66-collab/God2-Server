#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
namespace god2 {
// Native114464/1144C8 ->1177C0: the handler receives logical+1.
// Its +1 position, +2 mode, +3..10 packed appearance and +C WORD therefore
// correspond to logical+2,+3,+4..11,+13. Current mapped149c1b.. only.
// Preserve all17 bytes; no world DA -> battle conversion or renderer success
// is inferred from parsing. Nonzero special WORD and other modes stay open.
struct RecoveredBattlePlayerAppearance {
    static constexpr std::size_t logical_size=17;
    using Bytes=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint8_t position()const noexcept{return bytes_[2];}
        std::uint8_t mode()const noexcept{return bytes_[3];}
        bool ordinary_mode1()const noexcept{return mode()==1&&!bytes_[13]&&!bytes_[14];}
        std::span<const std::uint8_t,8> packed_components()const noexcept{
            return std::span<const std::uint8_t,logical_size>(bytes_).subspan<4,8>();
        }
        bool operator==(const Record&)const=default;
    private:
        friend struct RecoveredBattlePlayerAppearance;
        explicit Record(Bytes bytes):bytes_(bytes){}
        Bytes bytes_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t>b){
        if(b.size()!=logical_size||b[0]!=0x86||b[1]!=4||b[2]>=28||b[3]!=1||b[13]||b[14])return {};
        Bytes bytes{};std::copy(b.begin(),b.end(),bytes.begin());return Record(bytes);
    }
    static Bytes encode(const Record&r){return r.bytes_;}
    static Record at_position(const Record&r,std::uint8_t position){
        if(position>=28)throw std::invalid_argument("Player appearance position out of range");
        auto bytes=r.bytes_;bytes[2]=position;return Record(bytes);
    }
};
}
