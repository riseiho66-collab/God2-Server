#include "cn/auth/CnCreationNameProjection.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <utility>

namespace god2::cn {
CnCreationNameProjection::CnCreationNameProjection(std::array<std::uint8_t,45> native,
    Candidate candidate,std::string utf8)
    :native_(native),candidate_(std::move(candidate)),utf8_(std::move(utf8)) {}
std::optional<CnCreationNameProjection> CnCreationNameProjection::from_common_candidate(
    const god2cn::CnCharacterCreate& request,Candidate candidate) {
    const auto name=request.ui_name();
    if(!name)return std::nullopt;
    const auto wire=OwnedCharacterNameText::from_encoded(*name,936);
    const auto& profile=candidate.profile;
    const auto end=std::find(profile.begin(),profile.begin()+15,0);
    if(!wire || end==profile.begin() || end==profile.begin()+15)return std::nullopt;
    const std::string_view bytes(reinterpret_cast<const char*>(profile.data()),
        static_cast<std::size_t>(end-profile.begin()));
    const auto common=OwnedCharacterNameText::from_encoded(bytes,candidate.name_codepage);
    if(!common || common->original_utf8()!=wire->original_utf8())return std::nullopt;
    // Keep the entire explicit common40-byte profile (including postNUL and
    // all non-name bytes), slot/codepage/style. Never synthesize defaults or
    // copy unknown native offsets into common gameplay/level fields.
    return CnCreationNameProjection(request.record_bytes(),std::move(candidate),
        std::string(wire->original_utf8()));
}
}
