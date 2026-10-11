#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <variant>

namespace god2 {
// Current EXE 48B9B0 -> 458430 -> 4132E0. D8 is a daily-panel
// interaction, NOT proven quest acceptance/completion or reward authority.
struct RecoveredDailyQuestRequest {
    static constexpr std::uint8_t opcode=0xd8;
    static constexpr std::size_t logical_size=9;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct Selection {
        std::uint8_t index,branch,item_slot;
        std::uint16_t npc;
        std::uint8_t side,opaque_tail;
        bool operator==(const Selection&) const = default;
    };
    // Controls16/2D: mode2 followed by seven zero bytes. The current-native
    // control text is 每日領取. Eligibility, item identity and award rules are
    // server-owned and unresolved; the request carries no reward/item key.
    struct Auxiliary { bool operator==(const Auxiliary&) const = default; };
    using Request=std::variant<Selection,Auxiliary>;
    static std::optional<LogicalRecord> encode(const Selection& r) noexcept {
        if((r.item_slot>=30 && r.item_slot!=0xff) || (r.side!=1 && r.side!=2)) return std::nullopt;
        return LogicalRecord{opcode,1,r.index,r.branch,r.item_slot,
            static_cast<std::uint8_t>(r.npc),static_cast<std::uint8_t>(r.npc>>8),r.side,r.opaque_tail};
    }
    static constexpr LogicalRecord encode(Auxiliary) noexcept { return {opcode,2,0,0,0,0,0,0,0}; }
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode) return std::nullopt;
        if(bytes[1]==2) {
            for(std::size_t i=2;i<bytes.size();++i) if(bytes[i]) return std::nullopt;
            return Auxiliary{};
        }
        if(bytes[1]!=1) return std::nullopt;
        const Selection r{bytes[2],bytes[3],bytes[4],
            static_cast<std::uint16_t>(bytes[5] | (std::uint16_t{bytes[6]}<<8)),bytes[7],bytes[8]};
        if(!encode(r)) return std::nullopt;
        return r;
    }
    // Server-owned binding must come from an actually issued list. Pair+NPC
    // alone do not authorize a quest mutation. Item18CA ownership/count, world
    // state, position, replay protection and original rules belong to service.
    struct Binding { std::uint8_t index,branch; std::uint16_t start_npc,end_npc; std::uint8_t flags; };
    static bool matches(const Selection& r,const Binding& bound) noexcept {
        return encode(r).has_value() && (bound.flags&0x3f)!=0 && r.index==bound.index &&
            r.branch==bound.branch && r.npc==(r.side==1 ? bound.start_npc : bound.end_npc);
    }
    // FD total length = opcode1 + length2 + subtype1 + fixed payload168.
    // 48B710 copies payload[A0] DWORDs into capacity40, with no native clamp.
    // This read-only guard prevents malformed list generation/replay; it does
    // not synthesize availability, accept-count or reward fields.
    static constexpr std::size_t list_logical_size=172;
    static bool valid_list(std::span<const std::uint8_t> bytes) noexcept {
        return bytes.size()==list_logical_size && bytes[0]==0xfd &&
            bytes[1]==list_logical_size && bytes[2]==0 && bytes[3]==2 && bytes[164]<=40;
    }
};
}
