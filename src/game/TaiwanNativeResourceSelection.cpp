#include "game/TaiwanNativeResourceSelection.h"
#include <algorithm>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace god2 {
namespace {
struct Unqualified {};
bool ascii_name(const std::vector<std::uint8_t>& name) {
    return std::all_of(name.begin(),name.end(),[](std::uint8_t value) {
        return value>=0x20 && value<0x7F;
    });
}
std::filesystem::path resolved(const std::vector<std::uint8_t>& bytes,
    const std::filesystem::path& actual_cwd) {
    // Widen only exactly proven ASCII, without ACP/locale or UTF8 substitution.
    std::wstring name;name.reserve(bytes.size());
    for(const auto byte:bytes) name.push_back(static_cast<wchar_t>(byte));
    const std::filesystem::path native(name);
    // Drive-relative (C:foo) and rooted-without-drive (\foo) names depend on
    // additional native process drive context. Exclude them, never guess it.
    if(native.has_root_name() && !native.has_root_directory()) throw Unqualified{};
    if(native.has_root_directory() && !native.has_root_name()) throw Unqualified{};
    return native.is_absolute()?native:actual_cwd/native;
}
std::optional<std::vector<std::uint8_t>> opened(const std::filesystem::path& path,std::size_t limit) {
    std::ifstream stream(path,std::ios::binary);
    if(!stream.is_open()) return std::nullopt;
    std::vector<std::uint8_t> bytes(limit+1);
    stream.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    const auto count=stream.gcount();
    // Read errors / allocation limits are not evidence of native fopen failure.
    // They abort the selection instead of silently choosing the other file.
    if(stream.bad() || count<0 || static_cast<std::uint64_t>(count)>limit) throw Unqualified{};
    bytes.resize(static_cast<std::size_t>(count));return bytes;
}
}
struct TaiwanNativeResourceSelection::Storage {
    const Request request;
    const std::vector<std::uint8_t> requested,candidate,encoded;
    const std::filesystem::path candidate_path,selected_path;
    const std::optional<std::vector<std::uint8_t>> candidate_original;
    const Probe probe;
    const Branch branch;
    Storage(Request context,std::vector<std::uint8_t> name,std::vector<std::uint8_t> attempted,
        std::filesystem::path attempted_path,std::filesystem::path selected,
        std::vector<std::uint8_t> original,std::optional<std::vector<std::uint8_t>> candidate_data,
        Probe outcome,Branch selected_branch):request(std::move(context)),requested(std::move(name)),
        candidate(std::move(attempted)),encoded(std::move(original)),candidate_path(std::move(attempted_path)),
        selected_path(std::move(selected)),candidate_original(std::move(candidate_data)),probe(outcome),branch(selected_branch) {}
};
TaiwanNativeResourceSelection::TaiwanNativeResourceSelection(std::shared_ptr<const Storage> value):storage_(std::move(value)) {}
const TaiwanNativeResourceSelection::Storage& TaiwanNativeResourceSelection::storage() const {
    if(!storage_) throw std::logic_error("TW selected resource has no retained original");
    return *storage_;
}
std::optional<TaiwanNativeResourceSelection> TaiwanNativeResourceSelection::select(
    const Request& request,std::size_t limit) {
    if(request.kind!=Kind::RomBinary && request.kind!=Kind::TextFile) return std::nullopt;
    if(request.original_reference.empty() || !ascii_name(request.original_reference) ||
        !ascii_name(request.native_prefix) || !request.actual_working_directory.is_absolute() ||
        limit==0 || limit>=static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max())) return std::nullopt;
    // Actual00429843 compares low WORD unsigned with512. Keep the full DWORD
    // for the real caller's ordinal binding; do not rewrite it to ACTINDEX.
    if(request.kind==Kind::RomBinary && (request.full_bank_operand&0xFFFF)>=512) return std::nullopt;
    // Qualified safe domain: at most255 pathname bytes plus terminating NUL,
    // including the optional suffix. Native unbounded strcpy/strcat beyond
    // its local buffer is not silently reproduced as memory corruption.
    const std::size_t capacity=256;
    if(request.native_prefix.size()>=capacity ||
        request.original_reference.size()>=capacity-request.native_prefix.size()) return std::nullopt;
    std::vector<std::uint8_t> name(request.native_prefix.begin(),request.native_prefix.end());
    name.insert(name.end(),request.original_reference.begin(),request.original_reference.end());
    std::vector<std::uint8_t> candidate(name);
    const bool suffix=request.kind==Kind::TextFile || (name.size()>=4 && name[name.size()-4]=='.');
    // Native binary len<4 dereferences before its name buffer; excluded here.
    if(request.kind==Kind::RomBinary && name.size()<4) return std::nullopt;
    if(suffix) {
        if(candidate.size()+1>=capacity) return std::nullopt;
        candidate.push_back('Z');
    }
    try {
        const auto candidate_path=resolved(candidate,request.actual_working_directory);
        auto candidate_data=opened(candidate_path,limit);
        const auto outcome=!candidate_data?Probe::OpenFailed:
            (candidate_data->size()>=2 && (*candidate_data)[0]==5 && (*candidate_data)[1]==0x16?
                Probe::Marker0516:Probe::Non0516);
        if(outcome==Probe::Marker0516) {
            // A marker selects the compressed-reader branch. Decoder/parser
            // failure does NOT qualify original-file fallback in00429820.
            // Text native temporary-file/reopen side effects are not recreated.
            auto selected_original=*candidate_data;
            return TaiwanNativeResourceSelection(std::make_shared<const Storage>(request,std::move(name),
                std::move(candidate),candidate_path,candidate_path,std::move(selected_original),std::move(candidate_data),
                outcome,Branch::Candidate0516));
        }
        const auto selected_path=resolved(name,request.actual_working_directory);
        auto selected=opened(selected_path,limit); // Native reopens, even same pathname.
        if(!selected || selected->empty()) return std::nullopt;
        return TaiwanNativeResourceSelection(std::make_shared<const Storage>(request,std::move(name),
            std::move(candidate),candidate_path,selected_path,std::move(*selected),std::move(candidate_data),outcome,
            outcome==Probe::OpenFailed?Branch::OriginalAfterOpenFailed:Branch::OriginalAfterNon0516));
    } catch(const Unqualified&) {return std::nullopt;}
}
const TaiwanNativeResourceSelection::Request& TaiwanNativeResourceSelection::request() const {return storage().request;}
const std::vector<std::uint8_t>& TaiwanNativeResourceSelection::request_bytes() const {return storage().requested;}
const std::vector<std::uint8_t>& TaiwanNativeResourceSelection::candidate_bytes() const {return storage().candidate;}
const std::filesystem::path& TaiwanNativeResourceSelection::candidate_source() const {return storage().candidate_path;}
const std::filesystem::path& TaiwanNativeResourceSelection::actual_source() const {return storage().selected_path;}
const std::vector<std::uint8_t>& TaiwanNativeResourceSelection::encoded_bytes() const {return storage().encoded;}
const std::optional<std::vector<std::uint8_t>>& TaiwanNativeResourceSelection::candidate_original() const {return storage().candidate_original;}
TaiwanNativeResourceSelection::Probe TaiwanNativeResourceSelection::probe() const {return storage().probe;}
TaiwanNativeResourceSelection::Branch TaiwanNativeResourceSelection::branch() const {return storage().branch;}
}
