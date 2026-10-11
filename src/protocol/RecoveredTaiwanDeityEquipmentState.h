#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Pinned149c:40127C returns21;46B2EA/5194C3 advance past D1 then49F510
// copies20 bytes to UI866A8. D2/49F540 copies20 to866BC instead.
// Owner-local received values; no selected-row key, formula or equip rights.
struct RecoveredTaiwanDeityEquipmentState {
    template<std::uint8_t Opcode> class Record final {
    public:
        using Bytes=std::array<std::uint8_t,21>;
        static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {
            if(raw.size()!=21 || raw[0]!=Opcode)return std::nullopt;
            Bytes bytes;std::copy(raw.begin(),raw.end(),bytes.begin());return Record(bytes);
        }
        const Bytes& logical() const noexcept{return bytes_;}
        bool operator==(const Record&) const=default;
    private:
        explicit Record(Bytes bytes):bytes_(bytes) {}
        Bytes bytes_;
    };
    using Base=Record<0xd1>;
    using Addition=Record<0xd2>;
    // A storage container, NOT recovered reply ordering or an atomic native
    // packet. Both full independent logical records must come from a real issuer.
    class Pair final {
    public:
        static constexpr std::size_t storage_bytes=42;
        static std::optional<Pair> parse_storage(std::span<const std::uint8_t> raw) noexcept {
            if(raw.size()!=storage_bytes)return std::nullopt;
            const auto base=Base::parse(raw.first(21));
            const auto addition=Addition::parse(raw.subspan(21));
            if(!base || !addition)return std::nullopt;
            return Pair(*base,*addition);
        }
        const Base& base() const noexcept{return base_;}
        const Addition& addition() const noexcept{return addition_;}
        // 49B5E0 reads body18, at logical19. Retain all other bits/bytes.
        std::uint8_t client_guard_state() const noexcept{return base_.logical()[19]&3;}
        // Only a client emission predicate; never a server equipment permission.
        bool client_guard_allows(std::uint16_t key) const noexcept {
            if(key<=7000 || key>=8000)return true;
            const auto state=client_guard_state();
            if(state==2)return !((key>=7101 && key<=7200)||(key>=7401 && key<=7500));
            if(state==1)return !((key>=7201 && key<=7300)||(key>=7501 && key<=7600));
            return true;
        }
        bool operator==(const Pair&) const=default;
    private:
        Pair(Base base,Addition addition):base_(base),addition_(addition) {}
        Base base_;
        Addition addition_;
    };
};
}
