#pragma once
#include "db/AccountRepository.h"
#include "db/RecoveredCharacterRepository.h"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace god2 {
// CUSTOM-0092 internal shared custody identity. None of these IDs is a native item WORD,
// slot selector, raw20 field, grant, stat or recovered acquisition rule.
struct OwnedItemNativeAlias {
    std::string client_sha256,profile,source_sha256,source_record;
    std::uint16_t native_key{};
    std::uint8_t native_slot{};
    std::uint64_t revision{};
    std::vector<std::uint8_t> record;
    bool operator==(const OwnedItemNativeAlias&) const=default;
};
struct OwnedInventoryInstance {
    std::uint64_t id{},definition_key{},quantity{},revision{};
    bool stackable{};
    // One genuine server acquisition receipt per instance. Immutable for this
    // identity; globally unique even after retirement. Never supplied by C28.
    std::string acquisition_sha256,acquisition_record;
    std::vector<OwnedItemNativeAlias> aliases;
    bool operator==(const OwnedInventoryInstance&) const=default;
};
struct OwnedInventoryCell {
    std::string location_kind;
    std::uint32_t location_index{};
    // Explicit empty cell differs from an absent/unqualified location.
    std::optional<OwnedInventoryInstance> instance;
    bool operator==(const OwnedInventoryCell&) const=default;
};
struct OwnedInventorySnapshot {
    RecoveredCharacter root;
    std::uint64_t revision{};
    std::string source_sha256,source_record;
    // Complete qualified population in strict (kind,index) order, with all
    // aliases in strict (client SHA,profile) order. No implicit free capacity.
    std::vector<OwnedInventoryCell> cells;
    static bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
        return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
            a.created_at==b.created_at && a.name_codepage==b.name_codepage &&
            a.streamer_privilege==b.streamer_privilege;
    }
    bool operator==(const OwnedInventorySnapshot& b) const {
        return same_root(root,b.root) && revision==b.revision && source_sha256==b.source_sha256 &&
            source_record==b.source_record && cells==b.cells;
    }
};
class OwnedInventoryRepository {
public:
    virtual ~OwnedInventoryRepository()=default;
    virtual bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept=0;
    // Stored full observation, not current entitlement. No default slots,
    // acquisitions, instance ID derivation or promotion of legacy CUSTOM rows.
    virtual std::optional<OwnedInventorySnapshot> load(std::uint64_t account,std::uint64_t character)=0;
};
}
