#pragma once
#include "cn/protocol/CnWorldEntry.h"
#include "db/NativeMapCatalog.h"
#include "game/RecoveredPosition.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace god2::cn {
// Pinned TW/CN144-row native identity join. Uses the existing common map table,
// not a CN gameplay database. Does not prepare actors, validate walkability,
// infer spawns, match asset geometry or issue the actor's native scene mode.
// shared-scene-identity-01 retains both raw resources and exact row provenance.
class SharedSceneIdentity {
public:
    struct Reference {
        std::uint16_t area,scene;
        std::uint8_t declared_kind;
        std::string_view tw_row_sha256,native_mdt_path;
    };
    static const Reference* find(std::uint16_t area,std::uint16_t scene) noexcept {
        for(const auto& row:references_)if(row.area==area && row.scene==scene)return &row;
        return nullptr;
    }
    // The selection controller fetches this NativeMapRecord from its shared
    // NativeMapCatalog; the preparation owner supplies the reserved position. This
    // adapter never loads/transfers a character based on packet coordinates.
    static bool matches(const NativeMapRecord& record,const RecoveredPosition& position,
                        const god2cn::CnWorldEntry::BeginPlay& entry,
                        const std::optional<RecoveredPosition>& previous) {
        const auto* ref=find(position.area,position.scene);
        if(!ref || record.area!=ref->area || record.scene!=ref->scene || record.kind!=ref->declared_kind ||
           record.source_record_index<0 || record.source_record_index>=144)return false;
        const auto index=static_cast<std::size_t>(ref-references_);
        const auto raw=expected_rows_[index];
        const auto& source=record.source;
        if(record.source_record_index!=static_cast<std::int64_t>(index) || record.record_sha256!=ref->tw_row_sha256 ||
           record.raw_record.size()!=raw.size() || !std::equal(raw.begin(),raw.end(),record.raw_record.begin(),
               [](char a,std::uint8_t b){return static_cast<unsigned char>(a)==b;}) ||
           source.dataset_id!=NativeMapCatalog::current_dataset_id || source.row_count!=144 ||
           source.source_path!="Data2/Patch/Comm/gamedata.csvZ" || source.source_section!="Map_City_Coordniate" ||
           source.source_sha256!="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731" ||
           source.decoded_sha256!="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815" ||
           source.native_image_sha256!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
           source.loader_rva!="0x59a80" || source.lookup_rva!="0x59d80")return false;
        // Catalogue kind and2A actor scene mode are different native fields.
        // Actual preparation must qualify that mode with its resource owner.
        if(!entry.initial_consumer_accepts_map_family() || entry.map_family()!=position.area ||
           entry.map_index()!=position.scene)return false;
        if(previous) {
            if(!find(previous->area,previous->scene))return false;
            const auto effective=entry.transfer_location(previous->area,previous->scene);
            return effective.x==position.x && effective.y==position.y;
        }
        return entry.x()==position.x && entry.y()==position.y;
    }
private:
    inline static constexpr Reference references_[]={
#include "cn/world/SharedSceneIdentity.inc"
    };
    inline static constexpr std::string_view expected_rows_[]={
#include "cn/world/SharedSceneRows.inc"
    };
};
}
