#pragma once
#include "cn/assets/CnNpcNameCatalog.h"

namespace god2cn {
// Current encoded8A72/decoded16F7 NPCAppearData source, statically recovered
// without native loader execution. Historical names stay in their own catalog.
// Source names are not common IDs, monster stats or native acceptance evidence.
class CnCurrentNpcNameCatalog {
public:
    using Resource=CnNpcNameCatalog::Resource;
    using Row=CnNpcNameCatalog::Row;
    static constexpr std::size_t source_rows=4466,unique_selectors=4464;
    static constexpr std::int16_t resource_max_selector=6553;
    static const Row* lookup(std::uint16_t key) {
        const auto found=std::lower_bound(rows_.begin(),rows_.end(),key,
            [](const Row& row,std::uint16_t wanted){return row.selector<wanted;});
        return found!=rows_.end() && found->selector==key?&*found:nullptr;
    }
    static bool matches(const Resource& source) {
        return source.revision && source.actual_native_max_selector==resource_max_selector &&
            source.client_sha256=="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8" &&
            source.encoded_sha256=="8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a" &&
            source.decoded_sha256=="16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3";
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
        return result; // Real owner must still qualify the actual loaded resource/revision/maximum and gameplay issuance.
    }
private:
    inline static constexpr std::array<Row,unique_selectors> rows_={{
#include "cn/assets/CnCurrentNpcNameRows.inc"
    }};
};
}
