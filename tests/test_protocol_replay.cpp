#include "tools/ProtocolReplayTool.h"
#include "protocol/God2ProtocolSpec.h"
#include "protocol/RecoveredServerRoutes.h"
#include "protocol/RecoveredTaiwanServerAdvertisement.h"
#include <algorithm>
#include <array>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace {
void check(bool value) { if (!value) throw std::runtime_error("test_protocol_replay check failed"); }
void three_channel_advertisement_source() {
    using Routes=god2::RecoveredServerRoutes;
    using Advertisement=god2::RecoveredTaiwanServerAdvertisement;
    // Explicit CUSTOM-0159 source fixture, not three live worlds or switching.
    // Preserve the supplied mask as opaque data; its value is not a slot count.
    const std::array<std::uint8_t,4> group{5,0x92,0xa5,0xc3};
    const std::array<Routes::ChannelEndpoint,3> channels{{
        {{127,0,0,1},2593,0x71,{0x11,0xa1,0xb1,0xc1}},
        {{127,0,0,1},2594,0x82,{0x83,0xa2,0xb2,0xc2}},
        {{127,12,34,56},2595,0x93,{0xfe,0xa3,0xb3,0xc3}}
    }};
    const auto wire=Routes::wire_three_channels(group,channels);
    const auto parsed=Advertisement::parse(wire);
    check(wire.size()==68&&parsed&&parsed->rows[group[0]]&&parsed->rows[group[0]]->raw==group&&
        parsed->rows[group[0]]->mask()==0xc3a5);
    const auto available_wire=Routes::wire_three_available_channels(group[0],group[1],channels);
    const auto available=Advertisement::parse(available_wire);
    const std::array<std::uint8_t,4> available_group{group[0],group[1],7,0};
    check(available&&available->rows[group[0]]&&available->rows[group[0]]->raw==available_group&&
        available->rows[group[0]]->mask()==7);
    for(unsigned slot=0;slot<8;++slot)
        check(bool(available->rows[group[0]]->mask()&(1u<<slot))==(slot<3));
    // Only the04 mask/checksum changes. All05/06 wire bytes, including opaque
    // endpoint/route fields, remain the supplied generic producer's bytes.
    check(std::equal(wire.begin()+8,wire.end(),available_wire.begin()+8));
    for(std::size_t i=0;i<parsed->rows.size();++i)check(i==group[0]||!parsed->rows[i]);
    std::vector<std::uint8_t> expected{4,group[0],group[1],group[2],group[3]};
    for(std::uint8_t k=0;k<channels.size();++k) {
        const auto& channel=channels[k];
        const std::array<std::uint8_t,8> endpoint{k,channel.endpoint_reserved,
            channel.address[0],channel.address[1],channel.address[2],channel.address[3],
            static_cast<std::uint8_t>(channel.port),static_cast<std::uint8_t>(channel.port>>8)};
        expected.push_back(5);expected.insert(expected.end(),endpoint.begin(),endpoint.end());
        expected.push_back(6);expected.insert(expected.end(),channel.route_body.begin(),channel.route_body.end());
        // Synthetic complete 07 logical list: one row, explicit token/key.
        // No character creation rights, profile or live connection is inferred.
        std::array<std::uint8_t,75> list{};list[0]=7;list[1]=1;list[3+19]=5;list[3+32]=channel.route_body[0];
        const auto destination=parsed->primary_destination({group[0],k,3},5,list);
        check(destination&&destination->address()==channel.address&&destination->port()==channel.port&&
            destination->endpoint_body==endpoint&&destination->route_body==channel.route_body&&
            destination->character_row==0&&destination->endpoint_index==k&&destination->route_index==0);
        check(available->primary_destination({group[0],k,3},5,list)==destination);
        check(!parsed->primary_destination({group[0],k,3},4,list));
        list[3+32]=0;check(!parsed->primary_destination({group[0],k,3},5,list));
    }
    check(parsed->logical_records==expected);
    auto available_expected=expected;available_expected[3]=7;available_expected[4]=0;
    check(available->logical_records==available_expected);
    const auto rejects=[&](const auto& candidate_group,const auto& candidate_channels){
        bool refused=false;
        try{(void)Routes::wire_three_channels(candidate_group,candidate_channels);}catch(const std::invalid_argument&){refused=true;}
        check(refused);
    };
    auto invalid_group=group;invalid_group[0]=64;rejects(invalid_group,channels);
    const auto last_visible=Advertisement::parse(Routes::wire_three_available_channels(9,group[1],channels));
    check(last_visible&&last_visible->rows[9]&&last_visible->rows[9]->raw==std::array<std::uint8_t,4>{9,group[1],7,0});
    bool invisible_group_refused=false;
    try{(void)Routes::wire_three_available_channels(10,group[1],channels);}catch(const std::invalid_argument&){invisible_group_refused=true;}
    check(invisible_group_refused);
    auto maximum_group=group;maximum_group[0]=63;
    const auto last=Advertisement::parse(Routes::wire_three_channels(maximum_group,channels));
    check(last&&last->rows[63]&&last->rows[63]->raw==maximum_group);
    for(std::size_t k=0;k<channels.size();++k) {
        auto invalid=channels;invalid[k].port=0;rejects(group,invalid);
        invalid=channels;invalid[k].route_body[0]=0;rejects(group,invalid);
        invalid=channels;invalid[k].address={192,168,1,1};rejects(group,invalid);
        if(k){invalid=channels;invalid[k].address=channels[0].address;invalid[k].port=channels[0].port;rejects(group,invalid);}
    }
    // Existing one-route overload remains byte-exact, including all reserved
    // fields and frame boundaries; this fixture predates CUSTOM-0159.
    constexpr std::array<std::uint8_t,28> single{
        8,0,1,1,0xfd,0xfe,0xfe,0xae,
        12,0,2,2,0xfd,0x7c,0x7c,0xfd,0xfe,0x1f,0x28,0x57,
        8,0,3,4,0xfe,0xfd,0xfd,0xb0};
    check(Routes::wire({127,0,0,1},2593)==single);
    const auto separate=Routes::wire(2593,1,{127,0,0,1});
    check(std::equal(separate.group.begin(),separate.group.end(),single.begin())&&
        std::equal(separate.endpoint.begin(),separate.endpoint.end(),single.begin()+8)&&
        std::equal(separate.route.begin(),separate.route.end(),single.begin()+20));
}
}
void test_protocol_replay() {
    using namespace god2;
    God2ProtocolSpec spec;
    ProtocolReplayTool tool(spec);
    check(ProtocolReplayTool::parse_hex("\tAa00 ff\r\n") == std::vector<uint8_t>({0xAA,0,0xFF}));
    const auto result = tool.replay_hex("07 00 01 10 aa bb cc\n04000510");
    check(result.status.ok && result.packets.size() == 2 && result.remaining_bytes == 0);
    check(result.packets[0].opcode == 0x1001 && result.packets[0].payload == std::vector<uint8_t>({0xAA,0xBB,0xCC}));
    check(result.lengths == std::vector<size_t>({7,4}));
    std::ostringstream output;
    ProtocolReplayTool::print(result, output);
    check(output.str() == "length=7 opcode=0x1001 payload=aa bb cc\nlength=4 opcode=0x1005 payload=\n");
    for (auto invalid : {"0", "0g", "0x04", "0 4", "04,00", "04:00"}) {
        check(!tool.replay_hex(invalid).status.ok);
        bool threw = false;
        try { ProtocolReplayTool::parse_hex(invalid); } catch (const std::runtime_error&) { threw = true; }
        check(threw);
    }
    const auto truncated = tool.replay_hex("04000510 07000110aa");
    check(!truncated.status.ok && truncated.packets.size() == 1 && truncated.remaining_bytes == 5);
    check(truncated.status.error.find("Truncated") != std::string::npos);
    const auto malformed = tool.replay_hex("03000110");
    check(!malformed.status.ok && malformed.status.error.find("header") != std::string::npos);
    std::ostringstream error;
    ProtocolReplayTool::print(malformed, error);
    check(error.str().find("parse error:") == 0);
    check(tool.replay_hex("").status.ok && tool.replay_hex(" \n\t").packets.empty());
    check(tool.replay_hex("04000510").status.ok);
    three_channel_advertisement_source();
}
