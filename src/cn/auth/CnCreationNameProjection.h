#pragma once
#include "cn/protocol/CnCharacterCreate.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <array>
#include <optional>
#include <string>
#include <string_view>

namespace god2::cn {
// Bounded unchanged-original-name normal17 form, not a44-to40 profile map.
// Actual native rules supply ALL common fields and complete02/choices. No
// permission/default/unique/replay entitlement follows from this projection.
class CnCreationNameProjection {
public:
    using Candidate=SqliteRecoveredCharacterRepository::NewOwnedCharacter;
    static std::optional<CnCreationNameProjection> from_common_candidate(
        const god2cn::CnCharacterCreate&,Candidate);
    const Candidate& storage_candidate() const noexcept {return candidate_;}
    std::string_view original_utf8() const noexcept {return utf8_;}
    bool matches(const god2cn::CnCharacterCreate& request) const noexcept {
        return native_==request.record_bytes();
    }
    bool matches_created(const RecoveredCharacter& row) const noexcept {
        return row.slot==candidate_.slot && row.profile==candidate_.profile &&
            row.name_codepage==candidate_.name_codepage &&
            row.streamer_privilege==candidate_.streamer_privilege;
    }
private:
    CnCreationNameProjection(std::array<std::uint8_t,45>,Candidate,std::string);
    std::array<std::uint8_t,45> native_;
    Candidate candidate_;
    std::string utf8_;
};
}
