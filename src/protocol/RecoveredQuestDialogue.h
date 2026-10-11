#pragma once
#include <array>
#include <cstdint>
#include <optional>

namespace god2 {
// Current mode1 consumer C7F10/C81F0; variable-length receiver 13420.
// Candidate construction only: no world gate, NPC ownership or quest rules.
struct RecoveredQuestDialogue {
    using Mode1Candidate=std::array<std::uint8_t,27>;
    using KnowledgeMenu=std::array<std::uint8_t,28>;
    // Current MultiMessage key1434: seven knowledge topics. This qualified
    // mode4 branch has no name substitutions, formatting parameters or reward
    // semantics. It requires the matching complete2995-entry client table.
    static constexpr std::optional<KnowledgeMenu> kunlun_knowledge_menu(
        std::uint32_t request,std::uint32_t context,std::uint32_t table_count) {
        if(request>0xffff || context>0xff || table_count!=2995)return std::nullopt;
        KnowledgeMenu result{};
        result[0]=0x7a;result[1]=28;result[3]=4;result[4]=static_cast<std::uint8_t>(context);
        result[5]=static_cast<std::uint8_t>(request);result[6]=static_cast<std::uint8_t>(request>>8);
        result[7]=0x9a;result[8]=0x05; //1434, original MultiMessage namespace.
        // reply0, name16 zero bytes, trailing parameter count0.
        return result;
    }
    // Keep the previously executed 27-byte fixture shape, not a universal 7A size.
    // Caller supplies the count from the matching loaded NPCMissionMessage table.
    static constexpr std::optional<Mode1Candidate> mode1(
        std::uint32_t request,std::uint32_t reply,std::uint32_t context,
        std::uint32_t text_key,std::uint32_t text_count) {
        if(request>0xffff || reply>0xffff || context>0xff || !text_key ||
           !text_count || text_count>0x7fff || text_key>text_count) return std::nullopt;
        Mode1Candidate result{};
        result[0]=0x7a;result[1]=static_cast<std::uint8_t>(result.size());
        result[3]=1;result[4]=static_cast<std::uint8_t>(context);
        const auto word=[&](unsigned offset,std::uint32_t value) {
            result[offset]=static_cast<std::uint8_t>(value);
            result[offset+1]=static_cast<std::uint8_t>(value>>8);
        };
        word(5,request);word(7,text_key);word(9,reply);
        // Offset11 selects non-formatting text. Remaining fixture bytes are zero.
        return result;
    }
};
}
