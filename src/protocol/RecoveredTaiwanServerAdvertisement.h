#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <optional>
#include <span>
#include <algorithm>
#include <vector>

namespace god2 {
// Account-phase known-profile advertisement facts only. Native14242 copies
// the full04 body DWORD to ordinal<64; Main+8E WORD is its received mask.
// Neither the mask nor observed bytes grant a realm/route/game permission.
struct RecoveredTaiwanServerAdvertisement {
    struct Row {
        std::array<std::uint8_t,4> raw;
        std::uint16_t mask() const noexcept {return static_cast<std::uint16_t>(raw[2]+256u*raw[3]);}
        bool operator==(const Row&) const=default;
    };
    std::array<std::optional<Row>,64> rows{};
    // Complete decoded04/05/06 stream in receive order. Original outer bytes
    // remain in Session's actual successful-write advertisement observation.
    std::vector<std::uint8_t> logical_records;
    struct Table {
        std::uint8_t group,subgroup,configured_subgroups;
        bool operator==(const Table&) const=default;
    };
    struct Destination {
        std::array<std::uint8_t,8> endpoint_body;
        std::array<std::uint8_t,4> route_body;
        std::uint8_t character_row,endpoint_index,route_index;
        std::array<std::uint8_t,4> address() const noexcept {
            return {endpoint_body[2],endpoint_body[3],endpoint_body[4],endpoint_body[5]};
        }
        std::uint16_t port() const noexcept {
            return static_cast<std::uint16_t>(endpoint_body[6]+256u*endpoint_body[7]);
        }
        bool operator==(const Destination&) const=default;
    };
    // Actual configured table/count comes from the caller's mandatory source,
    // never inferred from A6 bytes or mask. Own bounded primary-only subset:
    // native writers lack these bounds. Fallback12250 is intentionally OPEN.
    std::optional<Destination> primary_destination(Table table,std::uint8_t token,
            std::span<const std::uint8_t> list) const {
        if(table.group>=rows.size() || !rows[table.group] || !table.configured_subgroups ||
           table.configured_subgroups>10 || table.subgroup>=table.configured_subgroups ||
           list.size()!=75 || list[0]!=7 || !list[1] || list[1]>2)return std::nullopt;
        std::optional<std::uint8_t> selected;
        for(std::uint8_t i=0;i<list[1];++i)
            if((list[3+36u*i+19]&7)==token){selected=i;break;}
        if(!selected)return std::nullopt;
        const auto key=list[3+36u * *selected+32];
        if(!key)return std::nullopt;
        // 13FE3..1403B initially clears each configured endpoint area; repeated
        // 04 does NOT clear it. Model physical byte offsets, not independent
        // (k,j,r) maps: 0x260/0x30 strides can overlap adjacent subgroup areas.
        // Every qualified k's read/write range lies in its native cleared480B.
        std::array<std::uint8_t,0x260*10+0xc4+480> bytes{};
        std::optional<std::uint8_t> group,subgroup;
        int endpoint=-1,route=-1;
        for(std::size_t at=0;at<logical_records.size();) {
            const auto op=logical_records[at];
            const auto size=op==4?5u:op==5?9u:op==6?5u:0u;
            if(!size || size>logical_records.size()-at)return std::nullopt;
            if(op==4) {
                if(logical_records[at+1]>=rows.size())return std::nullopt;
                group=logical_records[at+1];endpoint=-1;subgroup.reset();route=-1;
            } else if(op==5) {
                if(!group || ++endpoint>=10)return std::nullopt;
                subgroup=logical_records[at+1];route=-1;
                if(*group==table.group) {
                    if(*subgroup>=table.configured_subgroups)return std::nullopt;
                    const auto offset=0x260u * *subgroup+0x30u*endpoint+0xc4;
                    std::copy_n(logical_records.begin()+at+1,8,bytes.begin()+offset);
                }
            } else {
                if(!group || !subgroup || endpoint<0 || ++route>=10)return std::nullopt;
                if(*group==table.group) {
                    const auto offset=0x260u * *subgroup+0x30u*endpoint+0xcc+4u*route;
                    std::copy_n(logical_records.begin()+at+1,4,bytes.begin()+offset);
                }
            }
            at+=size;
        }
        for(std::uint8_t j=0;j<10;++j)for(std::uint8_t r=0;r<10;++r) {
            const auto base=0x260u*table.subgroup+0x30u*j;
            if(bytes[base+0xcc+4u*r]!=key)continue;
            Destination result{{},{},*selected,j,r};
            std::copy_n(bytes.begin()+base+0xc4,8,result.endpoint_body.begin());
            std::copy_n(bytes.begin()+base+0xcc+4u*r,4,result.route_body.begin());
            return result; // First physical nonzero lowBYTE match, not latest.
        }
        return std::nullopt;
    }
    // Existing transport memory budget, not an advertisement/native capacity.
    static constexpr std::size_t max_wire_bytes=1024*1024;
    static std::optional<RecoveredTaiwanServerAdvertisement> parse(std::span<const std::uint8_t> wire) {
        if(wire.empty() || wire.size()>max_wire_bytes)return std::nullopt;
        RecoveredTaiwanServerAdvertisement result;
        bool found=false;
        std::size_t at=0;
        while(at<wire.size()) {
            if(wire.size()-at<2)return std::nullopt;
            const auto length=static_cast<std::size_t>(wire[at])+256u*wire[at+1];
            if(length<4 || length>wire.size()-at)return std::nullopt;
            const auto logical=RecoveredWorldFrame::decode(wire.subspan(at,length));
            if(!logical)return std::nullopt;
            result.logical_records.insert(result.logical_records.end(),logical->begin(),logical->end());
            std::size_t item=0;
            while(item<logical->size()) {
                const auto opcode=(*logical)[item];
                const auto size=opcode==4?5u:opcode==5?9u:opcode==6?5u:0u;
                if(!size || size>logical->size()-item)return std::nullopt;
                if(opcode==4) {
                    const auto index=(*logical)[item+1];
                    if(index>=result.rows.size())return std::nullopt;
                    result.rows[index]=Row{{(*logical)[item+1],(*logical)[item+2],(*logical)[item+3],(*logical)[item+4]}};
                    found=true; // Native receiver overwrites repeated ordinals in source order.
                }
                // 05/06 raw endpoint/route data remain in the immutable original
                // advertisement; no default destination or resource ID inferred.
                item+=size;
            }
            at+=length;
        }
        return found?std::optional{result}:std::nullopt;
    }
    bool operator==(const RecoveredTaiwanServerAdvertisement&) const=default;
};
}
