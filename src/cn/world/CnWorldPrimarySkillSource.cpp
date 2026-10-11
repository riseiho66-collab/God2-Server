#include "cn/world/CnWorldPrimarySkillSource.h"
#include <algorithm>
#include <exception>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
CnWorldPrimarySkillSource::CnWorldPrimarySkillSource(Subject subject,Scope scope,std::vector<std::uint8_t> bank,
    std::shared_ptr<const Catalog> catalog,Current current)
    :subject_(std::move(subject)),scope_(std::move(scope)),bank_(std::move(bank)),
     catalog_(std::move(catalog)),current_(std::move(current)) {}
CnWorldPrimarySkillSource::~CnWorldPrimarySkillSource(){if(thread_!=std::this_thread::get_id())std::terminate();}
void CnWorldPrimarySkillSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN world primary skill source game owner mismatch");
}
struct CnWorldPrimarySkillSource::Operation {
    const CnWorldPrimarySkillSource& source;
    const int exceptions=std::uncaught_exceptions();
    explicit Operation(const CnWorldPrimarySkillSource& value):source(value) {
        source.owner();
        if(source.operating_){source.terminal_=true;throw std::logic_error("CN world primary source reentry rejected");}
        source.operating_=true;
    }
    ~Operation(){if(std::uncaught_exceptions()>exceptions)source.terminal_=true;source.operating_=false;}
};
bool CnWorldPrimarySkillSource::observe() const {
    if(terminal_ || !current_(scope_) || terminal_ || !subject_.current() || terminal_)return false;
    if(!catalog_->current() || terminal_ || catalog_->source()!=scope_.definitions)return false;
    return current_(scope_) && !terminal_ && subject_.current() && !terminal_;
}
bool CnWorldPrimarySkillSource::current() const {
    Operation operation(*this);const bool valid=observe();if(!valid)terminal_=true;return valid;
}
std::optional<CnWorldPrimarySkillSource::PrimaryOrdinal>
CnWorldPrimarySkillSource::find_actual_primary_ordinal(std::uint32_t kind,std::uint32_t id) const {
    Operation operation(*this);
    if(!observe()){terminal_=true;return std::nullopt;}
    auto result=retained_first_ordinal(kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}
    return result;
}
CnWorldPrimarySkillSource::PrimaryOrdinal
CnWorldPrimarySkillSource::retained_first_ordinal(std::uint32_t kind,std::uint32_t id) const {
    PrimaryOrdinal result{kind,id,std::nullopt};
    // The complete captured row/bank already owns the native count and every
    // pointer's raw110-byte definition. Iterate its original physical order;
    // no flags filtering, deduplication or catalog-wide membership substitute.
    for(std::size_t n=0;n<entries_.size();++n) {
        const auto& bytes=entries_[n].definition.raw;
        if(std::uint32_t(bytes[1])==kind && std::uint32_t(bytes[0])==id) {
            result.first_ordinal=static_cast<std::uint8_t>(n);break;
        }
    }
    return result;
}
std::optional<CnWorldPrimarySkillSource::PrimaryGate>
CnWorldPrimarySkillSource::project_actual_first_primary_gate(std::uint32_t kind,std::uint32_t id) const {
    Operation operation(*this);
    if(!observe()){terminal_=true;return std::nullopt;}
    PrimaryGate result{retained_first_ordinal(kind,id),std::nullopt,false};
    if(result.lookup.first_ordinal) {
        const auto& entry=entries_[*result.lookup.first_ordinal];
        const auto& bytes=entry.definition.raw;
        result.first_definition=PrimaryGate::Operands{
            entry.reference.actual_native_pointer_word,bytes[0x67],
            static_cast<std::uint16_t>(std::uint16_t(bytes[0x42])|(std::uint16_t(bytes[0x43])<<8)),
            subject_.retained_inline_role_unsigned_counters()[1]};
        const auto& operands=*result.first_definition;
        result.native_predicate=operands.native_byte67!=0 &&
            std::uint32_t(operands.native_unsigned_word42)<=operands.native_inline_unsigned_counter64;
    }
    if(!observe()){terminal_=true;return std::nullopt;}
    return result;
}
bool CnWorldPrimarySkillSource::matches_subject(const Subject& supplied) const {
    owner();const auto& first=subject_.retained_selection();const auto& second=supplied.retained_selection();
    return first && second && supplied.scope()==subject_.scope() &&
        supplied.retained_subject_identifier()==subject_.retained_subject_identifier() &&
        supplied.retained_inline_role_word()==subject_.retained_inline_role_word() &&
        supplied.retained_inline_role_unsigned_counters()==subject_.retained_inline_role_unsigned_counters() &&
        supplied.retained_list_count()==subject_.retained_list_count() &&
        supplied.retained_selected_index()==subject_.retained_selected_index() &&
        supplied.retained_selected_pointer()==subject_.retained_selected_pointer() &&
        supplied.retained_skill_bank_pointer()==subject_.retained_skill_bank_pointer() &&
        first->actual_native_row==second->actual_native_row;
}
std::shared_ptr<const CnWorldPrimarySkillSource> CnWorldPrimarySkillSource::read_actual_source(
    const Subject& supplied,Bank input,std::shared_ptr<const Catalog> catalog,Current current) {
    constexpr auto size=Catalog::resource_bytes-4;
    if(!catalog || !current || input.bytes.size()!=size || !input.address ||
       std::uint64_t(input.address)+size>std::uint64_t(std::numeric_limits<std::uint32_t>::max())+1)return {};
    // Own the same actual source BEFORE any external callback; spans and
    // caller-held snapshots cannot be replaced by a caught observing callback.
    const Subject subject=supplied;
    std::vector<std::uint8_t> bank(input.bytes.begin(),input.bytes.end());
    if(!subject.retained_selection() || subject.retained_skill_bank_pointer()!=input.address ||
       catalog->source().actual_client_sha256!=Catalog::client_sha256)return {};
    Scope scope{subject.scope(),catalog->source(),subject.retained_selected_pointer(),input.address};
    auto result=std::shared_ptr<CnWorldPrimarySkillSource>(new CnWorldPrimarySkillSource(
        subject,std::move(scope),std::move(bank),std::move(catalog),std::move(current)));
    Operation operation(*result);
    if(!result->observe())return {};
    const auto payload=result->catalog_->retained_payload_bytes();
    if(payload.size()!=result->bank_.size() || !std::equal(payload.begin(),payload.end(),result->bank_.begin()))return {};
    const auto address=result->scope_.actual_bank_address;
    const auto& references=result->subject_.retained_selection()->skills;
    result->entries_.reserve(references.size());
    for(const auto reference:references) {
        const auto pointer=reference.actual_native_pointer_word;
        if(pointer<std::uint64_t(address)+4)return {};
        const auto delta=std::uint64_t(pointer)-address-4;
        const auto kind=delta/Catalog::group_bytes,within=delta%Catalog::group_bytes;
        if(kind>=Catalog::declared_counts.size() || within%Catalog::record_bytes)return {};
        const auto id=within/Catalog::record_bytes+1;
        if(id>Catalog::declared_counts[kind] || !result->observe())return {};
        const auto record=result->catalog_->lookup(static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(id));
        if(!record || !result->observe() || record->source!=result->scope_.definitions || record->file_offset<4)return {};
        const auto at=std::size_t(record->file_offset-4);
        if(std::uint64_t(address)+at!=pointer || at>result->bank_.size() ||
           record->raw.size()>result->bank_.size()-at ||
           !std::equal(record->raw.begin(),record->raw.end(),result->bank_.begin()+at))return {};
        result->entries_.push_back({reference,*record}); //Exact flags, order and duplicates.
    }
    if(!result->observe())return {};return result;
}
}
