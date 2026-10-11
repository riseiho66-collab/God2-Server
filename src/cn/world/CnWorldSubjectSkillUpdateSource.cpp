#include "cn/world/CnWorldSubjectSkillUpdateSource.h"
#include <algorithm>
#include <exception>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
namespace {
std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) {
    return std::uint16_t(bytes[at])|(std::uint16_t(bytes[at+1])<<8);
}
std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t at) {
    return std::uint32_t(bytes[at])|(std::uint32_t(bytes[at+1])<<8)|
        (std::uint32_t(bytes[at+2])<<16)|(std::uint32_t(bytes[at+3])<<24);
}
void put_dword(CnWorldSubjectSkillUpdateSource::Row& row,std::size_t at,std::uint32_t value) {
    for(unsigned n=0;n<4;++n)row[at+n]=static_cast<std::uint8_t>(value>>(8*n));
}
void rebuild_actual_auxiliary(CnWorldSubjectSkillUpdateSource::Row& row) {
    // Pure4D5830: clear ONLY count, then copy flag-bit2 pointers. The unused
    // stale auxiliary tail stays intact, never zero-fabricated or deduplicated.
    row[0x5c]=0;
    for(std::size_t n=0;n<row[0x1f0];++n)if(row[0x1f1+n]&2) {
        put_dword(row,0x60+4*row[0x5c],dword(row,0x258+4*n));++row[0x5c];
    }
}
}
CnWorldSubjectSkillUpdateSource::CnWorldSubjectSkillUpdateSource(Scope scope,
    std::vector<std::uint8_t> object,std::vector<std::uint8_t> bank,
    std::shared_ptr<const Catalog> catalog,Current current)
    :scope_(std::move(scope)),object_(std::move(object)),bank_(std::move(bank)),
     catalog_(std::move(catalog)),current_(std::move(current)) {}
CnWorldSubjectSkillUpdateSource::~CnWorldSubjectSkillUpdateSource(){if(thread_!=std::this_thread::get_id())std::terminate();}
void CnWorldSubjectSkillUpdateSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN native skill roster source game owner mismatch");
}
struct CnWorldSubjectSkillUpdateSource::Operation {
    const std::shared_ptr<const CnWorldSubjectSkillUpdateSource> lifetime;
    const CnWorldSubjectSkillUpdateSource& source;
    const int exceptions=std::uncaught_exceptions();
    explicit Operation(const CnWorldSubjectSkillUpdateSource& value):lifetime(value.shared_from_this()),source(*lifetime) {
        source.owner();
        if(source.operating_){source.terminal_=true;throw std::logic_error("CN native skill roster source reentry rejected");}
        source.operating_=true;
    }
    ~Operation(){if(std::uncaught_exceptions()>exceptions)source.terminal_=true;source.operating_=false;}
};
bool CnWorldSubjectSkillUpdateSource::observe() const {
    if(terminal_)return false;
    if(!current_(scope_) || terminal_ || !catalog_->current() || terminal_ ||
       catalog_->source()!=scope_.definitions){terminal_=true;return false;}
    const bool valid=current_(scope_) && !terminal_;if(!valid)terminal_=true;return valid;
}
bool CnWorldSubjectSkillUpdateSource::current() const {
    Operation operation(*this);const bool valid=observe();if(!valid)terminal_=true;return valid;
}
std::shared_ptr<const CnWorldSubjectSkillUpdateSource> CnWorldSubjectSkillUpdateSource::read_actual_source(
    CnPrebornSubjectState::Scope identity,std::span<const std::uint8_t> supplied_members,
    std::span<const std::uint8_t> supplied_object,Bank input,std::shared_ptr<const Catalog> catalog,Current current) {
    constexpr auto bank_size=Catalog::resource_bytes-4;
    constexpr auto address_end=std::uint64_t(std::numeric_limits<std::uint32_t>::max())+1;
    if(!identity.actual_ui_owner_word || !identity.actual_object_word || !identity.actual_revision ||
       !catalog || !current || supplied_members.size()!=8 || supplied_object.size()<object_bytes ||
       !input.address || input.bytes.size()!=bank_size ||
       std::uint64_t(identity.actual_ui_owner_word)+0x430b0>address_end ||
       std::uint64_t(identity.actual_object_word)+object_bytes>address_end ||
       std::uint64_t(input.address)+bank_size>address_end)return {};
    // Copy every borrowed input before any observing callback.
    std::array<std::uint8_t,8> members;std::copy(supplied_members.begin(),supplied_members.end(),members.begin());
    std::vector<std::uint8_t> object(supplied_object.begin(),supplied_object.begin()+object_bytes);
    std::vector<std::uint8_t> bank(input.bytes.begin(),input.bytes.end());
    if(dword(members,0)!=identity.actual_object_word+0x90 || dword(members,4)!=identity.actual_object_word ||
       object[0x164]>row_slots || dword(object,0x4504)!=input.address ||
       catalog->source().actual_client_sha256!=Catalog::client_sha256)return {};
    Scope scope{identity,catalog->source(),input.address,dword(object,0x160),object[0x164]};
    auto result=std::shared_ptr<CnWorldSubjectSkillUpdateSource>(new CnWorldSubjectSkillUpdateSource(
        std::move(scope),std::move(object),std::move(bank),std::move(catalog),std::move(current)));
    Operation operation(*result);if(!result->observe())return {};
    const auto actual=result->catalog_->retained_payload_bytes();
    if(actual.size()!=result->bank_.size() || !std::equal(actual.begin(),actual.end(),result->bank_.begin()) ||
       !result->observe())return {};
    return result;
}
std::optional<std::size_t> CnWorldSubjectSkillUpdateSource::retained_definition_offset(std::uint32_t pointer) const {
    if(pointer<std::uint64_t(scope_.actual_bank_address)+4)return std::nullopt;
    const auto delta=std::uint64_t(pointer)-scope_.actual_bank_address-4;
    const auto kind=delta/Catalog::group_bytes,within=delta%Catalog::group_bytes;
    if(kind>=Catalog::declared_counts.size() || within%Catalog::record_bytes ||
       within/Catalog::record_bytes+1>Catalog::declared_counts[kind])return std::nullopt;
    const auto at=std::size_t(pointer-scope_.actual_bank_address);
    if(at>bank_.size() || Catalog::record_bytes>bank_.size()-at)return std::nullopt;
    return at;
}
std::optional<CnWorldSubjectSkillUpdateSource::Projection>
CnWorldSubjectSkillUpdateSource::project_updates(std::span<const Wire::Record> supplied) const {
    Operation operation(*this);
    if(supplied.empty() || supplied.size()>max_records_per_projection)return std::nullopt;
    const std::vector<Wire::Record> records(supplied.begin(),supplied.end());
    if(!observe()){terminal_=true;return std::nullopt;}
    Projection result{scope_,{},{},{}};
    for(std::size_t n=0;n<row_slots;++n)
        std::copy_n(object_.begin()+0x168+n*Row{}.size(),Row{}.size(),result.initial_rows[n].begin());
    result.staged_rows=result.initial_rows;
    for(const auto& record:records) {
        const auto parsed=Wire::read(record.raw);
        if(!parsed || parsed->form!=record.form || !observe())return std::nullopt;
        const auto definition=catalog_->lookup(record.kind(),record.definition_id());
        if(!definition || !observe() || definition->source!=scope_.definitions || definition->file_offset<4)return std::nullopt;
        const auto pointer64=std::uint64_t(scope_.actual_bank_address)+definition->file_offset-4;
        if(pointer64>=std::uint64_t(scope_.actual_bank_address)+bank_.size())return std::nullopt;
        const auto pointer=static_cast<std::uint32_t>(pointer64);
        const auto at=retained_definition_offset(pointer);
        if(!at || !std::equal(definition->raw.begin(),definition->raw.end(),bank_.begin()+*at))return std::nullopt;
        Step step{record,*definition,{}};
        for(std::size_t n=0;n<scope_.actual_roster_count;++n) {
            auto& row=result.staged_rows[n];
            // Native processes EVERY equal WORD row, not just the first or
            // current selection. Incoming subject BYTE is zeroextended.
            if(word(row,0)!=std::uint16_t(record.subject_identifier()))continue;
            const auto count=row[0x1f0];
            const bool selected=scope_.actual_selected_row==scope_.subject.actual_object_word+0x168+n*Row{}.size();
            Delta delta{static_cast<std::uint8_t>(n),Action::MissingPointer,row,row,std::nullopt,false,false,false,false};
            if(record.form==Wire::Form::Native34) {
                if(count>=100){delta.action=Action::CapacityReturn;step.rows.push_back(std::move(delta));continue;}
                for(std::size_t i=0;i<count;++i) {
                    const auto existing=retained_definition_offset(dword(row,0x258+4*i));
                    if(!existing)return std::nullopt; //Native dereference is not safely qualified.
                    if(bank_[*existing+1]==record.kind() && bank_[*existing]==record.definition_id()) {
                        delta.action=Action::DuplicateDiagnostic;delta.primary_ordinal=static_cast<std::uint8_t>(i);
                        result.requires_unchanged_unmodeled_call_roster=true;break;
                    }
                }
                if(!delta.primary_ordinal) {
                    delta.action=Action::AppendPrimary;delta.primary_ordinal=count;
                    row[0x1f1+count]=0;put_dword(row,0x258+4*count,pointer);
                    row[0x1f0]=static_cast<std::uint8_t>(count+1);row[0x3e8]=0;
                    row[0x3e9]=static_cast<std::uint8_t>((unsigned(row[0x1f0])+24)/25);
                    rebuild_actual_auxiliary(row);delta.auxiliary_rebuilt=true;
                    delta.selected_refresh_required=selected;delta.menu_refresh_required=true;
                    result.requires_unchanged_unmodeled_call_roster=true;
                }
            } else {
                if(count>100)return std::nullopt; //Own prefix bound, NOT a native35 guard or clipped count.
                for(std::size_t i=0;i<count;++i)if(dword(row,0x258+4*i)==pointer) {
                    delta.action=Action::SetFirstPointerFlag;delta.primary_ordinal=static_cast<std::uint8_t>(i);
                    row[0x1f1+i]=3;rebuild_actual_auxiliary(row);delta.auxiliary_rebuilt=true;
                    delta.selected_refresh_required=selected;delta.selected_pending_table_required=selected;break;
                }
            }
            if(delta.selected_refresh_required)result.requires_unchanged_unmodeled_call_roster=true;
            delta.after_primary_aux_stage=row;step.rows.push_back(std::move(delta));
        }
        result.steps.push_back(std::move(step));
    }
    if(!observe()){terminal_=true;return std::nullopt;}
    return result;
}
}
