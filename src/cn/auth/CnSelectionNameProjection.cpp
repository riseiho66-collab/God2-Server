#include "cn/auth/CnSelectionNameProjection.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <utility>

namespace god2::cn {
CnSelectionNameProjection::CnSelectionNameProjection(std::array<std::uint8_t,25> native,
    Candidate candidate,std::string utf8)
    :native_(native),candidate_(std::move(candidate)),utf8_(std::move(utf8)) {}
std::optional<CnSelectionNameProjection> CnSelectionNameProjection::from_common_candidate(
    const god2cn::CnSelectionNameSubmission& request,Candidate candidate) {
    if(!request.matches_observed_ui_shape())return std::nullopt;
    const auto wire=OwnedCharacterNameText::from_encoded(request.submitted_name_bytes(),936);
    const auto& field=candidate.common_name_bytes;
    const auto end=std::find(field.begin(),field.begin()+15,0);
    if(!wire || end==field.begin() || end==field.begin()+15)return std::nullopt;
    const std::string_view bytes(reinterpret_cast<const char*>(field.data()),static_cast<std::size_t>(end-field.begin()));
    const auto common=OwnedCharacterNameText::from_encoded(bytes,candidate.name_codepage);
    if(!common || common->original_utf8()!=wire->original_utf8())return std::nullopt;
    // Preserve ALL explicit common16 bytes, including supplied postNUL bytes;
    // only from generated encoding below is zero padding locally constructed.
    return CnSelectionNameProjection(request.record_bytes(),std::move(candidate),std::string(wire->original_utf8()));
}
std::optional<CnSelectionNameProjection> CnSelectionNameProjection::for_common_encoding(
    const god2cn::CnSelectionNameSubmission& request,std::uint16_t page) {
    if(!request.matches_observed_ui_shape())return std::nullopt;
    const auto wire=OwnedCharacterNameText::from_encoded(request.submitted_name_bytes(),936);
    if(!wire)return std::nullopt;
    const auto common=OwnedCharacterNameText::from_utf8(wire->original_utf8(),page);
    if(!common)return std::nullopt;
    Candidate candidate{{},page};
    const auto bytes=common->encoded_bytes();
    std::copy(bytes.begin(),bytes.end(),candidate.common_name_bytes.begin());
    return from_common_candidate(request,std::move(candidate));
}
}
