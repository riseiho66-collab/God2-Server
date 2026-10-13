#include "cn/assets/CnSharedSkillCatalog.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2::cn {
NativeSkillSource CnSharedSkillCatalog::expected_source() {
    return NativeSkillSource{Native::dataset_id,Native::resource_path,Native::resource_sha256,
        Native::resource_sha256,Native::client_sha256,"CN preborn cbspec2 version1.03",
        "0x161bb0","0x133300",453};
}
CnSharedSkillCatalog::CnSharedSkillCatalog(const NativeSkillCatalog& shared,std::shared_ptr<const Native> native,
    std::shared_ptr<const void> lifetime,StoreCurrent current)
    :shared_(shared),native_(std::move(native)),actual_store_lifetime_(std::move(lifetime)),store_current_(std::move(current)) {}
CnSharedSkillCatalog::~CnSharedSkillCatalog() {if(thread_!=std::this_thread::get_id())std::terminate();}
void CnSharedSkillCatalog::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN shared skill catalog game owner mismatch");
}
struct CnSharedSkillCatalog::Operation {
    const CnSharedSkillCatalog& source;
    const int exceptions=std::uncaught_exceptions();
    explicit Operation(const CnSharedSkillCatalog& value):source(value) {
        source.owner();
        if(source.operating_) {source.terminal_=true;throw std::logic_error("CN shared skill catalog reentry rejected");}
        source.operating_=true;
    }
    ~Operation() {if(std::uncaught_exceptions()>exceptions)source.terminal_=true;source.operating_=false;}
};
bool CnSharedSkillCatalog::observe() const {
    if(terminal_ || !store_current_(shared_,*native_,actual_store_lifetime_) || terminal_)return false;
    if(!native_->current() || terminal_)return false;
    return store_current_(shared_,*native_,actual_store_lifetime_) && !terminal_;
}
bool CnSharedSkillCatalog::current() const {
    Operation operation(*this);const bool valid=observe();if(!valid)terminal_=true;return valid;
}
std::shared_ptr<const CnSharedSkillCatalog> CnSharedSkillCatalog::bind_actual_shared_store(
    const NativeSkillCatalog& shared,std::shared_ptr<const Native> native,
    std::shared_ptr<const void> lifetime,StoreCurrent current) {
    if(!native || !lifetime || !current)return {};
    const auto result=std::shared_ptr<const CnSharedSkillCatalog>(new CnSharedSkillCatalog(
        shared,std::move(native),std::move(lifetime),std::move(current)));
    // Qualify actual populated rows; a provider object or format-only schema
    // is insufficient. Missing/changed CN rows never alias the TW dataset.
    for(std::size_t kind=0;kind<Native::declared_counts.size();++kind)
        for(std::uint32_t id=1;id<=Native::declared_counts[kind];++id)
            if(!result->lookup(static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(id)))return {};
    if(!result->current())return {};return result;
}
std::optional<CnSharedSkillCatalog::Record> CnSharedSkillCatalog::retained_lookup(
    std::uint8_t kind,std::uint8_t id) const {
    if(!observe()){terminal_=true;return std::nullopt;}
    const auto expected=native_->lookup(kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}
    if(!expected)return std::nullopt;
    auto actual=shared_.lookup(Native::dataset_id,kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}
    if(!actual){terminal_=true;return std::nullopt;}
    std::int64_t ordinal=id-1;
    for(unsigned k=0;k<kind;++k)ordinal+=Native::declared_counts[k];
    if(actual->source!=expected_source() || actual->source_record_index!=ordinal ||
       actual->kind!=kind || actual->definition_id!=id || actual->source_offset!=expected->file_offset ||
       actual->record_sha256!=expected->record_sha256 || actual->raw_record.size()!=Native::record_bytes ||
       !std::equal(actual->raw_record.begin(),actual->raw_record.end(),expected->raw.begin())) {
        terminal_=true;return std::nullopt;
    }
    return actual;
}
std::optional<CnSharedSkillCatalog::Record> CnSharedSkillCatalog::lookup(
    std::uint8_t kind,std::uint8_t id) const {
    Operation operation(*this);
    auto result=retained_lookup(kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}return result;
}
std::optional<SharedSkillLookup> CnSharedSkillCatalog::lookup_shared(
    std::uint8_t kind,std::uint8_t id) const {
    Operation operation(*this);
    auto actual=retained_lookup(kind,id);
    if(!actual)return std::nullopt;
    if(!observe()){terminal_=true;return std::nullopt;}
    auto common=shared_.lookup_shared_definition_main(kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}
    if(!common){terminal_=true;return std::nullopt;}
    const auto found=std::find_if(common->definition.profiles.begin(),common->definition.profiles.end(),
        [](const auto& b){return b.region==SharedSkillRegion::China;});
    if(found==common->definition.profiles.end() || found->source!=actual->source ||
       found->source_record_index!=actual->source_record_index || found->source_offset!=actual->source_offset ||
       found->record_sha256!=actual->record_sha256 ||
       !std::equal(found->raw.begin(),found->raw.end(),actual->raw_record.begin(),actual->raw_record.end())) {
        terminal_=true;return std::nullopt;
    }
    // Requested native remains the exact qualified CN original, never the
    // selected common TW parameter profile or an invented TW source row.
    common->requested_native=std::move(actual);
    if(!observe()){terminal_=true;return std::nullopt;}return common;
}
std::optional<std::vector<CnSharedSkillCatalog::Record>> CnSharedSkillCatalog::lookup_words(
    std::span<const std::uint16_t> words) const {
    Operation operation(*this);
    if(!observe()){terminal_=true;return std::nullopt;}
    std::vector<Record> result;result.reserve(words.size());
    for(const auto word:words) {
        auto record=retained_lookup(static_cast<std::uint8_t>(word>>8),static_cast<std::uint8_t>(word&255));
        if(!record)return std::nullopt;result.push_back(std::move(*record));
    }
    if(!observe()){terminal_=true;return std::nullopt;}return result;
}
}
