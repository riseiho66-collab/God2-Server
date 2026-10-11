#pragma once
#include "cn/protocol/CnTransport.h"
#include <algorithm>
#include <array>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// Native-only evidence: artifacts/native/20261006-cn-native-login-02/.
// These are wire contracts, not authentication or completed account routes.
struct CnAccountWire {
    static constexpr std::size_t login_record_size=205;
    static constexpr std::uint16_t native_config_version=40;
    static constexpr std::uint16_t native_world_version=240;
    // 004468F0's raw-UI login metadata. Different from the transport roles'
    // version replies above; matching this field never proves product identity.
    static constexpr std::uint16_t native_ui_login_version=200;
    // 00444F1A and0044D777 write200 immediately before world C2S00.
    // This is distinct from the world transport's S2C01 version240.
    static constexpr std::uint16_t native_world_login_version=200;
    static constexpr std::string_view client_sha256=
        "582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";

    struct Login {
        // Keep bytes as supplied. No codepage conversion, case normalization,
        // logging, Lua exposure or language conversion of credentials.
        std::array<std::uint8_t,204> payload{};
        std::string_view account() const {return terminated(0,24);}
        std::string_view credential() const {return terminated(24,132);}
        // 1D overwrites this shared record at004802F9; S2CCF overwrites
        // the same204 bytes at00492768 before reauthentication can replace
        // them again. CF's additional selector is OUTSIDE this record.
        // Evidence: cn-account-tail-agent-01. Subsequent raw-UI
        // account04 and world00 preserve9C/A0 while recopying credentials.
        // Both values are claims, possibly from a previous login. Do not
        // require them to be zero, authorize by them, or echo them as a grant.
        // Evidence: cn-admission-contract-agent-01; server lease policy open.
        std::uint32_t account_id() const {return word32(0x9c);}
        std::uint32_t check_key() const {return word32(0xa0);}
        // 0044D625 (transfer) and00445BB4 (UI+58C path) write selected group
        // intoA9. These writes do not establish server1D serialization rules.
        // A claim only: the account catalog/session must authorize this group.
        std::uint8_t claimed_group_index() const {return payload[0xa9];}
        std::uint16_t game_serial_number() const {
            // 0048001C scans GameSN_God2.DAT, then unsigned-clamps to0..999.
            // Local client metadata only; never an identity or permission.
            return static_cast<std::uint16_t>(payload[0xa4]+256u*payload[0xa5]);
        }
        std::uint16_t client_version_field() const {
            return static_cast<std::uint16_t>(payload[0xa6]+256u*payload[0xa7]);
        }
    private:
        std::uint32_t word32(std::size_t offset) const {
            std::uint32_t value=0;
            for(unsigned i=0;i<4;++i)value|=std::uint32_t(payload[offset+i])<<(8*i);
            return value;
        }
        std::string_view terminated(std::size_t offset,std::size_t width) const {
            const auto first=payload.begin()+offset;
            const auto end=std::find(first,first+width,0);
            return {reinterpret_cast<const char*>(payload.data()+offset),static_cast<std::size_t>(end-first)};
        }
    };

    static std::optional<Login> parse_login(std::span<const std::uint8_t> record) {
        return parse_record(record,0x04);
    }
    static std::optional<Login> parse_world_login(std::span<const std::uint8_t> record) {
        // 00444EC0 / 0044D5F0 -> 004814D0(0, account), after world version 240.
        return parse_record(record,0x00);
    }
    // Read-only issued1D view. A complete native source supplies every byte;
    // this parser cannot turn the incoming04 into a success response.
    static std::optional<Login> parse_issued_login(std::span<const std::uint8_t> record) {
        return parse_record(record,0x1d);
    }
    struct SelectServer {std::uint8_t group;std::uint8_t server;};
    struct Disconnect {
        // This is a claimed name to compare with connection-owned identity.
        // It is never an authority to disconnect another account.
        std::array<std::uint8_t,16> payload;
        std::string_view claimed_account() const {
            const auto end=std::find(payload.begin(),payload.end(),0);
            return {reinterpret_cast<const char*>(payload.data()),static_cast<std::size_t>(end-payload.begin())};
        }
    };
    static std::optional<Disconnect> parse_disconnect(std::span<const std::uint8_t> record) {
        // C2S0A is NOT the S2C0A billing structure. 0047F310 copies an account
        // string into16 bytes; native bytes afterNUL are uninitialized.
        if(record.size()!=17 || record[0]!=0x0a)return std::nullopt;
        const auto payload=record.subspan(1);
        if(std::find(payload.begin(),payload.end(),0)==payload.end())return std::nullopt;
        Disconnect result;
        std::copy(payload.begin(),payload.end(),result.payload.begin());
        return result;
    }
    static std::optional<SelectServer> parse_select_server(std::span<const std::uint8_t> record) {
        // 00481640 writes group and server as two distinct u8 bytes, not a
        // u16 server identifier. 0047CBC0 permits 64 groups / 10 servers.
        // Application must also check authentication and actual catalog slots.
        if(record.size()!=3 || record[0]!=0xa6 || record[1]>=64 || record[2]>=10)return std::nullopt;
        return SelectServer{record[1],record[2]};
    }
    static Bytes account_version_reply() {return {0x01,static_cast<std::uint8_t>(native_config_version),0x00};}
    static Bytes world_version_reply() {return {0x01,static_cast<std::uint8_t>(native_world_version),0x00};}
private:
    static std::optional<Login> parse_record(std::span<const std::uint8_t> record,std::uint8_t opcode) {
        if(record.size()!=login_record_size || record[0]!=opcode)return std::nullopt;
        // 004468F0 copies 18h and 84h bytes and explicitly terminates at
        // payload+17h and +9Bh. Remaining metadata stays opaque until recovered.
        const auto payload=record.subspan(1);
        if(std::find(payload.begin(),payload.begin()+24,0)==payload.begin()+24 ||
           std::find(payload.begin()+24,payload.begin()+156,0)==payload.begin()+156)return std::nullopt;
        Login result;std::copy(payload.begin(),payload.end(),result.payload.begin());return result;
    }

    // Account version: compressed config*iniZ $296 -> u8 40 (0047CBC0).
    // World version: callers 00448F20 / 004490F0 / 00445B40 / 0044D5F0
    // pass F0h directly to 0047E6C0. Never send the account value to world.
    // Matching a version/challenge never proves account or product identity.
};
}
