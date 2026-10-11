#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string_view>
#include <vector>
namespace god2 {
// Build-matched 4F0470/4F05E0: member upsert and member removal. 92 is NOT
// an end-of-page marker. Local 4F0180 pagination sends no network record.
struct RecoveredGuildRoster {
    struct PanelReady { bool operator==(const PanelReady&) const=default; };
    static std::optional<PanelReady> panel_ready(std::span<const std::uint8_t> logical) {
        if(logical.size()!=2 || logical[0]!=0xb8 || logical[1]!=0)return {};
        return PanelReady{};
    }
    static std::vector<std::uint8_t> member(std::uint8_t slot,std::uint8_t role,
        std::uint8_t level,std::uint8_t profession,std::uint8_t status,std::string_view name) {
        // Client class table has9 entries, role icon table4 entries. Status
        // indexes8 icons using ((status>>1)&7)+(status&1), not a raw index.
        if(slot>=50 || role>3 || profession>8 || ((status>>1)&7)+(status&1)>7 ||
           name.empty() || name.size()>15 || name.find('\0')!=std::string_view::npos ||
           name.find('%')!=std::string_view::npos)
            throw std::invalid_argument("Native guild91 member bounds");
        std::vector<std::uint8_t> out(22,0);out[0]=0x91;out[1]=slot;out[2]=role;
        out[3]=level;out[4]=profession;out[5]=status;
        std::copy(name.begin(),name.end(),out.begin()+6);return out;
    }
    static std::vector<std::uint8_t> remove(std::uint8_t slot) {
        if(slot>=50)throw std::invalid_argument("Native guild92 slot bounds");
        return {0x92,slot};
    }
};
}
