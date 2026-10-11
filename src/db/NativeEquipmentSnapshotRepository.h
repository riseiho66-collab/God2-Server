#pragma once
#include "db/AccountRepository.h"
#include "protocol/RecoveredTaiwanPlayerAppearanceUpdate.h"
#include "db/RecoveredCharacterRepository.h"
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// Version-keyed equipment delivery witness, NOT canonical items or equip rules.
// Same149c native inventory has50 actual24B cache rows; retain every byte,
// including unknown prefix1..3, followed by complete actual DA15. This1215B
// owned structure is not a packet or a snapshot inferred from additive3B/41.
struct NativeEquipmentSnapshot {
    RecoveredCharacter root;
    RecoveredPosition position;
    std::string client_sha256,record_kind,source_sha256,source_record;
    std::vector<std::uint8_t> record;
    std::uint64_t revision{};
    std::uint16_t actor_handle{}; // Actual scene handle; NEVER common64 characterID.
    static constexpr std::size_t inventory_bytes=50*24,record_bytes=inventory_bytes+15;
    static constexpr const char* client_pin="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr const char* kind="tw149c-inventory24x50-da15";
    std::optional<RecoveredTaiwanPlayerAppearanceUpdate::Record> appearance() const noexcept {
        if(record.size()!=record_bytes)return std::nullopt;
        return RecoveredTaiwanPlayerAppearanceUpdate::parse_logical(
            std::span<const std::uint8_t>(record).subspan(inventory_bytes));
    }
    static bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
        return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
            a.profile==b.profile && a.created_at==b.created_at &&
            a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
    }
    bool operator==(const NativeEquipmentSnapshot& b) const {
        return same_root(root,b.root) && position==b.position && client_sha256==b.client_sha256 &&
            record_kind==b.record_kind && source_sha256==b.source_sha256 &&
            source_record==b.source_record && record==b.record && revision==b.revision && actor_handle==b.actor_handle;
    }
};
class NativeEquipmentSnapshotRepository {
public:
    virtual ~NativeEquipmentSnapshotRepository()=default;
    virtual bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept=0;
    virtual bool owns_characters(const RecoveredCharacterRepository&) const noexcept=0;
    // Single owned raw observation; stale witnesses remain replaceable by CAS.
    // Loading is not a claim that the witnessed root/position is still current.
    // Missing schema is an error, absent stored material is nullopt.
    virtual std::optional<NativeEquipmentSnapshot> load(std::uint64_t account,std::uint64_t character,
        std::string_view client_sha256,std::string_view record_kind)=0;
};
}
