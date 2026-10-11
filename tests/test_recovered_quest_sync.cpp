#include "protocol/RecoveredQuestSync.h"
#include "protocol/RecoveredQuestDialogue.h"
#include "protocol/DiagnosticQuestNpc.h"
#include "protocol/RecoveredNpcRecord.h"
#include "handlers/DiagnosticQuestConversation.h"
#ifdef NDEBUG
#undef NDEBUG // Standalone regression checks must also run in Release builds.
#endif
#include <cassert>
#include <charconv>
#include <cstdio>
#include <iostream>
#include <string_view>
#include <vector>

int main(int argc, char** argv) {
    using Codec = god2::RecoveredQuestSync;
    using Dialogue=god2::RecoveredQuestDialogue;
    {
        god2::DiagnosticQuestConversation service;
        assert(!service.leave_scene(1,2,3));
        assert(service.bind(1,2,3));assert(service.spawn(1,2,3));
        for(unsigned cycle=0;cycle<4;++cycle) {
            assert(service.open_town_npc(1,2,3,1606,{2,4,110,70,0}));
            const auto word=static_cast<std::uint16_t>(0x1234+cycle);
            assert(!service.leave_scene(1,4,3));assert(!service.leave_scene(1,2,4));
            if(cycle%2) assert(service.consume(1,2,3,{word,2,0x9a,0}));
            assert(service.leave_scene(1,2,3));
            assert(!service.consume(1,2,3,{word,2,0x9a,0}));
            assert(!service.open_town_npc(1,2,3,1606,{2,4,110,70,0}));
            assert(service.next_request_word(1,2,3)==word+1);
            assert(service.spawn(1,2,3));assert(!service.spawn(1,2,3));
            assert(!service.consume(1,2,3,{word,2,0x9a,0}));
        }
    }
    {
        god2::DiagnosticQuestConversation service;
        assert(!service.allow_followup(1,2,3));
        assert(service.bind(1,2,3));assert(service.spawn(1,2,3));
        assert(!service.allow_followup(1,2,3));
        assert(service.open_town_npc(1,2,3,1606,{2,4,110,70,0}));
        assert(!service.allow_followup(1,2,3));
        assert(service.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(!service.allow_followup(1,4,3));assert(!service.allow_followup(1,2,4));
        assert(service.allow_followup(1,2,3));assert(!service.allow_followup(1,2,3));
        assert(!service.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(service.open_town_npc(1,2,3,1607,{2,4,110,70,0}));
        assert(!service.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(service.consume(1,2,3,{0x1235,2,0x9a,0}));
        assert(service.allow_followup(1,2,3));
        assert(service.open_town_npc(1,2,3,1607,{2,4,110,70,0}));
        assert(service.cancel(1,2,3));
        assert(!service.allow_followup(1,2,3));
        assert(service.next_request_word(1,2,3)==0x1237);
    }
    for(const auto& npc:god2::DiagnosticTownNpc::guides) {
        god2::DiagnosticQuestConversation service;
        const god2::RecoveredPosition position{2,4,110,70,53};
        assert(service.bind(1,2,3));
        assert(!service.open_town_npc(1,2,3,npc.selector,position));
        assert(service.spawn(1,2,3));
        assert(!service.open_town_npc(2,2,3,npc.selector,position));
        assert(!service.open_town_npc(1,4,3,npc.selector,position));
        assert(!service.open_town_npc(1,2,4,npc.selector,position));
        assert(!service.open_town_npc(1,2,3,0x10000+npc.selector,position));
        assert(!service.open_town_npc(1,2,3,531,position));
        assert(!service.open_town_npc(1,2,3,npc.selector,{2,15,110,70,53}));
        assert(!service.open_town_npc(1,2,3,npc.selector,{3,4,110,70,53}));
        for(int dx=-4;dx<=4;++dx) for(int dy=-4;dy<=4;++dy) {
            god2::DiagnosticQuestConversation check;
            assert(check.bind(1,2,3));assert(check.spawn(1,2,3));
            const auto x=static_cast<std::uint16_t>(static_cast<int>(npc.x)+dx);
            const auto y=static_cast<std::uint16_t>(static_cast<int>(npc.y)+dy);
            assert(check.open_town_npc(1,2,3,npc.selector,{2,4,x,y,53})==
                   (dx>=-3 && dx<=3 && dy>=-3 && dy<=3));
        }
        assert(service.open_town_npc(1,2,3,npc.selector,position));
        assert(!service.open_town_npc(1,2,3,npc.selector,position));
        assert(service.cancel(1,2,3));
        assert(service.open_town_npc(1,2,3,npc.selector,position));
        assert(!service.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(service.consume(1,2,3,{0x1235,2,0x9a,0}));
        assert(!service.consume(1,2,3,{0x1235,2,0x9a,0}));
        service.remove(1);
        assert(!service.open_town_npc(1,2,3,npc.selector,position));
    }
    {
        god2::DiagnosticQuestConversation conversation;
        assert(!conversation.can_cancel(1,2,3));assert(!conversation.cancel(1,2,3));
        assert(conversation.bind(1,2,3));assert(!conversation.can_cancel(1,2,3));assert(!conversation.cancel(1,2,3));
        assert(conversation.open(1,2,3));
        assert(conversation.can_cancel(1,2,3));assert(!conversation.can_cancel(1,4,3));
        assert(!conversation.cancel(1,4,3));assert(!conversation.cancel(1,2,4));
        assert(conversation.cancel(1,2,3));assert(!conversation.can_cancel(1,2,3));assert(!conversation.cancel(1,2,3));
        assert(!conversation.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(conversation.next_request_word(1,2,3)==0x1235);
        assert(!conversation.next_request_word(1,4,3));
        assert(conversation.open(1,2,3));
        assert(!conversation.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(conversation.consume(1,2,3,{0x1235,2,0x9a,0}));
        assert(!conversation.open(1,2,3));
        conversation.remove(1);assert(!conversation.cancel(1,2,3));
    }
    {
        god2::DiagnosticQuestConversation conversation;
        assert(conversation.bind(1,2,3));assert(conversation.spawn(1,2,3));
        for(std::uint32_t word=0x1234;word<=0xffff;++word) {
            assert(conversation.next_request_word(1,2,3)==word);
            assert(!conversation.open_npc(1,2,3,531,{2,15,0,0,0}));
            assert(conversation.next_request_word(1,2,3)==word);
            assert(conversation.open_npc(1,2,3,531,{2,15,18,12,0}));
            assert(conversation.cancel(1,2,3));
        }
        assert(!conversation.next_request_word(1,2,3));
        assert(!conversation.open_npc(1,2,3,531,{2,15,18,12,0}));
    }
    const auto npc=god2::RecoveredNpcRecord::parse(god2::DiagnosticQuestNpc::logical());
    assert(npc && npc->primarySelector()==531 && npc->secondarySelector()==0 && npc->x()==17 && npc->y()==12);
    {
        god2::DiagnosticQuestConversation service;
        god2::RecoveredQuestAction::Request request{0x1234,2,0x9a,0x18};
        assert(!service.consume(1,2,3,request));
        assert(!service.bind(0,2,3));assert(!service.bind(1,0,3));assert(!service.bind(1,2,0));
        assert(service.bind(1,2,3));assert(!service.bind(1,2,3));
        assert(!service.consume(1,2,3,request));
        assert(!service.open(1,4,3));assert(!service.open(1,2,4));
        assert(service.open(1,2,3));assert(!service.open(1,2,3));
        assert(!service.consume(2,2,3,request));assert(!service.consume(1,4,3,request));
        assert(!service.consume(1,2,4,request));
        assert(!service.consume(1,2,3,{0x1235,2,0x9a,0x18}));
        assert(!service.consume(1,2,3,{0x1234,3,0x9a,0x18}));
        assert(!service.consume(1,2,3,{0x1234,2,0x9b,0x18}));
        assert(service.consume(1,2,3,request));assert(!service.consume(1,2,3,request));
        service.remove(1);assert(!service.consume(1,2,3,request));
        assert(service.bind(1,2,3));assert(service.open(1,2,3));
        request.opaque_tail=0xff;assert(service.consume(1,2,3,request));
    }
    {
        using Conversation=god2::DiagnosticQuestConversation;
        const god2::RecoveredPosition position{2,15,18,12,3};
        Conversation service;assert(service.bind(1,2,3));
        assert(!service.open_npc(1,2,3,531,position));
        assert(!service.spawn(1,4,3));assert(!service.spawn(1,2,4));
        assert(service.spawn(1,2,3));assert(!service.spawn(1,2,3));
        assert(!service.open_npc(1,4,3,531,position));
        assert(!service.open_npc(1,2,4,531,position));
        assert(!service.open_npc(1,2,3,532,position));
        assert(!service.open_npc(1,2,3,0x10000213,position));
        for(const auto invalid:std::array{
                god2::RecoveredPosition{3,15,18,12,3},god2::RecoveredPosition{2,16,18,12,3},
                god2::RecoveredPosition{2,15,13,12,3},god2::RecoveredPosition{2,15,21,12,3},
                god2::RecoveredPosition{2,15,17,8,3},god2::RecoveredPosition{2,15,17,16,3}})
            assert(!service.open_npc(1,2,3,531,invalid));
        assert(service.open_npc(1,2,3,531,position));
        assert(!service.open_npc(1,2,3,531,position));
        assert(service.consume(1,2,3,{0x1234,2,0x9a,0}));
        assert(!service.open_npc(1,2,3,531,position));
        for(const auto x:{14,20}) for(const auto y:{9,15}) {
            Conversation corner;assert(corner.bind(1,2,3));assert(corner.spawn(1,2,3));
            assert(corner.open_npc(1,2,3,531,{2,15,static_cast<std::uint16_t>(x),static_cast<std::uint16_t>(y),3}));
        }
    }
    static_assert(Dialogue::mode1(0x1234,2,0x9a,1,1).value()==Dialogue::Mode1Candidate{
        0x7a,27,0,1,0x9a,0x34,0x12,1,0,2,0});
    static_assert(!Dialogue::mode1(65536,0,0,1,1));
    static_assert(!Dialogue::mode1(0,65536,0,1,1));
    static_assert(!Dialogue::mode1(0,0,256,1,1));
    static_assert(!Dialogue::mode1(0,0,0,0,1));
    static_assert(!Dialogue::mode1(0,0,0,2,1));
    static_assert(!Dialogue::mode1(0,0,0,1,32768));
    static_assert(!Dialogue::mode1(0,0,0,1,0));
    static_assert(Dialogue::mode1(65535,65535,255,32767,32767).has_value());
    if(argc==7 && std::string_view(argv[1])=="--dialogue-mode1") {
        std::uint32_t values[5]{};
        for(unsigned i=0;i<5;++i) {
            const std::string_view input(argv[i+2]);
            const auto parsed=std::from_chars(input.data(),input.data()+input.size(),values[i]);
            if(parsed.ec!=std::errc{} || parsed.ptr!=input.data()+input.size()) return 2;
        }
        const auto record=Dialogue::mode1(values[0],values[1],values[2],values[3],values[4]);
        if(!record) return 1;
        for(const auto byte:*record) std::printf("%02x",static_cast<unsigned>(byte));
        std::puts("");return 0;
    }
    constexpr auto journal = Codec::emptyJournalLogical();
    static_assert(journal.size() == 195);
    static_assert(Codec::clearSlotLogical(14, 5).value()[5] == 14);
    static_assert(!Codec::clearSlotLogical(15, 4));
    static_assert(!Codec::clearSlotLogical(0, 0x104));
    static_assert(!Codec::clearSlotLogical(14, 0x105));
    static_assert(Codec::encodeSlotLogical(14, 5, 0x123401a2).value() ==
                  Codec::Record{0xdb, 5, 0, 0, 0, 14, 0, 0, 0, 0xa2, 1, 0x34, 0x12});
    static_assert(!Codec::encodeSlotLogical(15, 4, 0xffffffff));
    static_assert(!Codec::encodeSlotLogical(0, 0x105, 0xffffffff));
    constexpr std::array<std::uint16_t, 2> descriptionCounts{2, 7};
    static_assert(Codec::encodeJournalLogical({}, descriptionCounts).value() == journal);
    {
        Codec::JournalValues values{};
        for (std::size_t slot=0;slot<values.size();++slot) {
            values[slot]=slot%3==0 ? 0 : slot%3==1 ? 0x20001 : 0x70002;
        }
        const auto batch=Codec::encodeJournalLogical(values,descriptionCounts);
        assert(batch);
        for (std::size_t slot=0;slot<values.size();++slot) {
            const auto decoded=Codec::decode(std::span(*batch).subspan(slot*Codec::recordSize,Codec::recordSize));
            assert(decoded && decoded->subtype==4 && decoded->slot==slot && decoded->packedValue==values[slot]);
        }
        for (std::size_t slot=0;slot<values.size();++slot) {
            for (const auto invalid:{3u,0x30001u,0x80002u,0x10000u,0xffffffffu}) {
                auto corrupt=values;corrupt[slot]=invalid;
                assert(!Codec::encodeJournalLogical(corrupt,descriptionCounts));
            }
        }
        assert(!Codec::encodeJournalLogical(values,{}));
    }
    if (argc==2 && std::string_view(argv[1])=="--journal") {
        std::uint32_t length{};
        if (!(std::cin>>length) || length>32767) return 2;
        std::vector<std::uint16_t> counts(length);
        for(auto& count:counts) {
            std::uint32_t value{};
            if(!(std::cin>>value) || value>65535) return 2;
            count=static_cast<std::uint16_t>(value);
        }
        Codec::JournalValues values{};
        for(auto& value:values) if(!(std::cin>>value)) return 2;
        const auto batch=Codec::encodeJournalLogical(values,counts);
        if(!batch) return 1;
        for(const auto byte:*batch) std::printf("%02x",static_cast<unsigned>(byte));
        std::puts("");return 0;
    }
    static_assert(Codec::descriptionReference(1, descriptionCounts)->descriptionIndex == 0);
    static_assert(Codec::descriptionReference(0x10001, descriptionCounts)->descriptionIndex == 0);
    static_assert(Codec::descriptionReference(0x20001, descriptionCounts)->descriptionIndex == 1);
    static_assert(!Codec::descriptionReference(0x30001, descriptionCounts));
    static_assert(!Codec::descriptionReference(0x10000, descriptionCounts));
    if (argc == 2 && std::string_view(argv[1]) == "--descriptions") {
        // Batch input: catalog length, its u16 counts, then packed u32 values.
        // Each output retains the raw value in a DB4 record even if unresolved.
        std::uint32_t length{};
        if (!(std::cin >> length) || length > 65536) return 2;
        std::vector<std::uint16_t> counts(length);
        for (auto& count : counts) {
            std::uint32_t value{};
            if (!(std::cin >> value) || value > 65535) return 2;
            count = static_cast<std::uint16_t>(value);
        }
        std::uint32_t packed{};
        while (std::cin >> packed) {
            const auto reference = Codec::descriptionReference(packed, counts);
            if (reference) std::printf("%u %u ", static_cast<unsigned>(reference->missionIndex),
                                       static_cast<unsigned>(reference->descriptionIndex));
            else std::printf("- - ");
            const auto record = Codec::encodeSlotLogical(14, 4, packed).value();
            for (const auto byte : record) std::printf("%02x", static_cast<unsigned>(byte));
            std::puts("");
        }
        return std::cin.eof() ? 0 : 2;
    }
    if (argc == 5 && std::string_view(argv[1]) == "--encode") {
        std::uint32_t values[3]{};
        for (unsigned i = 0; i < 3; ++i) {
            const std::string_view input(argv[2 + i]);
            const auto parsed = std::from_chars(input.data(), input.data() + input.size(), values[i]);
            if (parsed.ec != std::errc{} || parsed.ptr != input.data() + input.size()) return 2;
        }
        const auto record = Codec::encodeSlotLogical(values[0], values[1], values[2]);
        if (!record) return 1;
        for (const auto byte : *record) std::printf("%02x", static_cast<unsigned>(byte));
        std::puts("");
        return 0;
    }
    if (argc == 4 && std::string_view(argv[1]) == "--clear") {
        std::uint32_t values[2]{};
        for (unsigned i = 0; i < 2; ++i) {
            const std::string_view input(argv[2 + i]);
            const auto parsed = std::from_chars(input.data(), input.data() + input.size(), values[i]);
            if (parsed.ec != std::errc{} || parsed.ptr != input.data() + input.size()) return 2;
        }
        const auto record = Codec::clearSlotLogical(values[0], values[1]);
        if (!record) return 1;
        for (const auto byte : *record) std::printf("%02x", static_cast<unsigned>(byte));
        std::puts("");
        return 0;
    }
    if (argc == 2 && std::string_view(argv[1]) == "--dump-clears") {
        for (const auto subtype : {4, 5}) {
            for (std::uint32_t slot = 0; slot < Codec::slotCount; ++slot) {
                const auto record = Codec::clearSlotLogical(slot, subtype);
                assert(record);
                for (const auto byte : *record) std::printf("%02x", static_cast<unsigned>(byte));
                std::puts("");
            }
        }
        return 0;
    }
    if (argc == 2 && std::string_view(argv[1]) == "--dump") {
        for (const auto byte : journal) std::printf("%02x", static_cast<unsigned>(byte));
        std::puts("");
        return 0;
    }
    for (const auto subtype : {4u, 5u}) {
        for (const auto slot : {0u, 14u}) {
            for (const auto value : {0u, 1u, 418u, 419u, 0x123401a2u,
                                     0xffff0000u, 0x80000001u, 0xffffffffu}) {
                const auto encoded = Codec::encodeSlotLogical(slot, subtype, value);
                assert(encoded);
                const auto decoded = Codec::decode(*encoded);
                assert(decoded && decoded->slot == slot && decoded->subtype == subtype &&
                       decoded->packedValue == value);
                if (value == 0) assert(encoded == Codec::clearSlotLogical(slot, subtype));
            }
        }
    }
    for (std::size_t slot = 0; slot < Codec::slotCount; ++slot) {
        const auto record = std::span(journal).subspan(slot * Codec::recordSize, Codec::recordSize);
        const auto update = Codec::decode(record);
        assert(update && update->subtype == 4 && update->slot == slot && update->packedValue == 0);
        for (std::size_t length = 0; length < record.size(); ++length)
            assert(!Codec::decode(record.first(length)));
    }
    assert(!Codec::decode(journal));
    for (unsigned subtype = 0; subtype < 256; ++subtype) {
        for (std::uint32_t slot = 0; slot <= Codec::slotCount; ++slot) {
            const auto record = Codec::clearSlotLogical(slot, subtype);
            const bool valid = slot < Codec::slotCount && (subtype == 4 || subtype == 5);
            assert(record.has_value() == valid);
            if (!record) continue;
            const auto update = Codec::decode(*record);
            assert(update && update->subtype == subtype && update->slot == slot && update->packedValue == 0);
            assert((*record)[2] == 0 && (*record)[3] == 0 && (*record)[4] == 0);
            for (std::size_t length = 0; length < record->size(); ++length)
                assert(!Codec::decode(std::span(*record).first(length)));
        }
    }
    for (const auto slot : {255u, 0x80000000u, 0xffffffffu}) {
        assert(!Codec::clearSlotLogical(slot, 4));
        assert(!Codec::clearSlotLogical(slot, 5));
    }
    for (const auto subtype : {0x104u, 0x105u, 0x204u, 0x205u, 0x10004u, 0x10005u,
                               0xffffff04u, 0xffffff05u, 0xffffffffu}) {
        for (std::uint32_t slot = 0; slot < Codec::slotCount; ++slot)
            assert(!Codec::clearSlotLogical(slot, subtype));
    }
    std::array<std::uint8_t, 14> oversized{};
    oversized[0] = 0xdb;
    oversized[1] = 4;
    assert(!Codec::decode(oversized));
    std::array<std::uint8_t, 13> record{0xdb, 5, 0xa5, 0x5a, 0xff, 14, 0, 0, 0,
                                        0x78, 0x56, 0x34, 0x12};
    auto update = Codec::decode(record);
    assert(update && update->subtype == 5 && update->slot == 14 && update->packedValue == 0x12345678);
    for (unsigned subtype = 0; subtype < 256; ++subtype) {
        record[1] = static_cast<std::uint8_t>(subtype);
        assert(Codec::decode(record).has_value() == (subtype == 4 || subtype == 5));
    }
    record[1] = 4;
    record[5] = 15;
    assert(!Codec::decode(record));
    record[5] = 0;
    record[8] = 0x80;
    assert(!Codec::decode(record));
    record[8] = 0;
    record[0] = 0xdf;
    assert(!Codec::decode(record));
    for (const auto subtype : {4, 5}) {
        for (const auto slot : {15u, 255u, 0x80000000u, 0xffffffffu}) {
            Codec::Record invalid{0xdb, static_cast<std::uint8_t>(subtype)};
            for (unsigned byte = 0; byte < 4; ++byte)
                invalid[5 + byte] = static_cast<std::uint8_t>(slot >> (8 * byte));
            assert(!Codec::decode(invalid));
        }
    }
}
