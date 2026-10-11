#pragma once
#include "cn/protocol/CnSelectionNameSubmission.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace god2::cn {
// Bound raw-D3 ->same exact Unicode identity->explicit common name encoding.
// No name lookup, native permission, server rule or display/script conversion.
// CN wire profile is explicitly936, independent of OS/display preference.
class CnSelectionNameProjection {
public:
    using Candidate=SqliteRecoveredCharacterRepository::OwnedNameCandidate;
    static std::optional<CnSelectionNameProjection> from_common_candidate(
        const god2cn::CnSelectionNameSubmission&,Candidate);
    // The actual rule owner selects common codepage. No automatic950/936
    // fallback or copying unknown0 high bytes; unrepresentable remains absent.
    static std::optional<CnSelectionNameProjection> for_common_encoding(
        const god2cn::CnSelectionNameSubmission&,std::uint16_t common_codepage);
    const Candidate& storage_candidate() const noexcept {return candidate_;}
    std::string_view original_utf8() const noexcept {return utf8_;}
    bool matches(const god2cn::CnSelectionNameSubmission& request) const noexcept {
        return native_==request.record_bytes();
    }
private:
    CnSelectionNameProjection(std::array<std::uint8_t,25>,Candidate,std::string);
    std::array<std::uint8_t,25> native_;
    Candidate candidate_;
    std::string utf8_;
};
}
