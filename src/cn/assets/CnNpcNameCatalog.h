#pragma once
#include "cn/protocol/CnSpecialDirectoryWire.h"
#include <array>
#include <string>

namespace god2cn {
// Retained same-EXE historical NPCAppearData name source. The currently
// installed encoded resource has a DIFFERENT hash and cannot use this catalog.
// Names/appearance keys are not monster combat attributes or common actor IDs.
class CnNpcNameCatalog {
public:
    struct Resource {
        std::string client_sha256,encoded_sha256,decoded_sha256;
        std::uint64_t revision;
        std::int16_t actual_native_max_selector;
    };
    struct Row {
        std::uint16_t selector;
        std::uint32_t source_line;
        std::uint8_t written_prefix_size;
        // Through firstNUL only. Remaining local zeros are unread padding in
        // this evidence view, NOT recovered native memory or outgoing bytes.
        std::array<std::uint8_t,16> consumed_name_prefix;
    };
    static constexpr std::size_t source_rows=4461,unique_selectors=4459;
    static constexpr std::int16_t resource_max_selector=6548;
    static const Row* lookup(std::uint16_t key) {
        const auto found=std::lower_bound(rows_.begin(),rows_.end(),key,
            [](const Row& row,std::uint16_t wanted){return row.selector<wanted;});
        return found!=rows_.end() && found->selector==key?&*found:nullptr;
    }
    static bool matches(const Resource& source) {
        return source.revision && source.actual_native_max_selector==resource_max_selector &&
            source.client_sha256=="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8" &&
            source.encoded_sha256=="f8b0762f111c532f1cbb38d66f06b6a4c6c685c278a5dcc98fbaead780e2376f" &&
            source.decoded_sha256=="1a818c454df37c58f1565b244a1030668cac52bf7ee75bb9a7db3e0bee263b44";
    }
    static std::optional<CnSpecialDirectoryWire::NpcNameEvidence> evidence(
        const CnSpecialDirectoryWire::Page& page,const Resource& source) {
        if(page.selector()!=CnSpecialDirectoryWire::Selector::Display25 || !matches(source))return std::nullopt;
        CnSpecialDirectoryWire::NpcNameEvidence result{source.revision,source.actual_native_max_selector,{}};
        for(unsigned n=0;n<page.consumed_rows();++n) {
            const auto key=*page.npc_name_selector(n);const auto* row=lookup(key);if(!row)return std::nullopt;
            if(std::any_of(result.slots.begin(),result.slots.end(),[key](const auto& slot){return slot.selector==key;}))continue;
            result.slots.push_back({key,row->consumed_name_prefix});
        }
        return result; // Actual owner's build/resource snapshot and issuance qualification remain mandatory.
    }
private:
    inline static constexpr std::array<Row,unique_selectors> rows_={{
#include "cn/assets/CnNpcNameRows.inc"
    }};
};
}
