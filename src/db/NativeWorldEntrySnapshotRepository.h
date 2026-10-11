#pragma once
#include "db/AccountRepository.h"
#include "db/RecoveredCharacterRepository.h"
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// A version-keyed delivery witness, not a second authoritative character.
// The complete raw record and its common-root/position observation stay owned.
struct NativeWorldEntrySnapshot {
    RecoveredCharacter root;
    RecoveredPosition position;
    std::string client_sha256,record_kind,source_sha256,source_record;
    std::vector<std::uint8_t> record;
    std::uint64_t revision{};
    static bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
        return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
            a.profile==b.profile && a.created_at==b.created_at &&
            a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
    }
    bool operator==(const NativeWorldEntrySnapshot& b) const {
        return same_root(root,b.root) && position==b.position && client_sha256==b.client_sha256 &&
            record_kind==b.record_kind && source_sha256==b.source_sha256 &&
            source_record==b.source_record && record==b.record && revision==b.revision;
    }
};
class NativeWorldEntrySnapshotRepository {
public:
    virtual ~NativeWorldEntrySnapshotRepository()=default;
    virtual bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept=0;
    virtual bool owns_characters(const RecoveredCharacterRepository&) const noexcept=0;
    // Single owned raw observation; stale witnesses remain replaceable by CAS.
    // Loading is not a claim that the witnessed root/position is still current.
    // Missing schema is an error, absent stored material is nullopt.
    virtual std::optional<NativeWorldEntrySnapshot> load(std::uint64_t account,std::uint64_t character,
        std::string_view client_sha256,std::string_view record_kind)=0;
};
}
