#include "cn/assets/CnSharedSkillBookSourceCatalog.h"
#include "cn/assets/CnNativeSkillBookSourceImport.h"
#include <array>
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2::cn {
CnSharedSkillBookSourceCatalog::CnSharedSkillBookSourceCatalog(const Reader& reader,
    std::shared_ptr<const Books> books,std::shared_ptr<const void> lifetime,StoreCurrent current)
    :reader_(reader),books_(std::move(books)),lifetime_(std::move(lifetime)),store_current_(std::move(current)) {}
CnSharedSkillBookSourceCatalog::~CnSharedSkillBookSourceCatalog() {
    if(thread_!=std::this_thread::get_id())std::terminate();
}
void CnSharedSkillBookSourceCatalog::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN shared book source game owner mismatch");
}
struct CnSharedSkillBookSourceCatalog::Operation {
    const CnSharedSkillBookSourceCatalog& source;
    explicit Operation(const CnSharedSkillBookSourceCatalog& value):source(value) {
        source.owner();
        if(source.busy_) {
            source.terminal_=true;throw std::logic_error("CN shared book source reentry rejected");
        }
        source.busy_=true;
    }
    ~Operation(){source.busy_=false;}
};
bool CnSharedSkillBookSourceCatalog::uses_native_books(const Books& books) const {owner();return books_.get()==&books;}
bool CnSharedSkillBookSourceCatalog::uses_source_reader(const Reader& reader) const {owner();return &reader_==&reader;}
bool CnSharedSkillBookSourceCatalog::observe() const {
    // Do not borrow either catalog until the actual store owner first
    // qualifies its lifetime. Captured true reentry cannot reopen this source.
    if(terminal_ || !store_current_(reader_,lifetime_) || terminal_)return false;
    if(!books_->current() || terminal_)return false;
    return store_current_(reader_,lifetime_) && !terminal_;
}
bool CnSharedSkillBookSourceCatalog::current() const {
    Operation operation(*this);
    try {const bool valid=observe();if(!valid)terminal_=true;return valid;}
    catch(...) {terminal_=true;throw;}
}
std::optional<CnSharedSkillBookSourceCatalog::Binding> CnSharedSkillBookSourceCatalog::retained_lookup(
    std::uint16_t item) const {
    if(!observe()){terminal_=true;return std::nullopt;}
    const auto book=books_->lookup_item(item);
    if(!observe()){terminal_=true;return std::nullopt;}
    // No book in the qualified pinned source is a missing item fact, not an
    // implicit grant or a reason to synthesize a same-number TW book.
    if(!book)return std::nullopt;
    const auto expected_source=CnNativeSkillBookSourceImport::expected_source();
    const NativeSkillBookSourceRecord expected{expected_source,book->source_record_index,book->source_line,
        book->decoded_offset,book->item_id,book->record_sha256,book->raw_line};
    // Fence before EACH borrowed SQL read, not just before factory creation.
    if(!observe()){terminal_=true;return std::nullopt;}
    const auto by_item=reader_.lookup(expected_source.dataset_id,item);
    if(!observe()){terminal_=true;return std::nullopt;}
    const auto by_index=reader_.lookup_by_index(expected_source.dataset_id,book->source_record_index);
    if(!observe()){terminal_=true;return std::nullopt;}
    if(!by_item || !by_index || *by_item!=expected || *by_index!=expected) {
        terminal_=true;return std::nullopt;
    }
    // Values are independently owned; this source supplies no alias inversion,
    // parsed396 image, learned/custody rule or mutation evidence.
    return Binding{*book,*by_item};
}
std::optional<CnSharedSkillBookSourceCatalog::Binding> CnSharedSkillBookSourceCatalog::lookup_item(
    std::uint16_t item) const {
    Operation operation(*this);
    try {return retained_lookup(item);}catch(...) {terminal_=true;throw;}
}
std::shared_ptr<const CnSharedSkillBookSourceCatalog> CnSharedSkillBookSourceCatalog::bind_actual_shared_store(
    const Reader& reader,std::shared_ptr<const Books> books,std::shared_ptr<const void> lifetime,StoreCurrent current) {
    if(!books || !lifetime || !current)return {};
    auto result=std::shared_ptr<CnSharedSkillBookSourceCatalog>(new CnSharedSkillBookSourceCatalog(
        reader,std::move(books),std::move(lifetime),std::move(current)));
    Operation operation(*result);
    try {
        if(!result->observe())return {};
        std::array<bool,Books::book_count> seen{};
        std::optional<Books::Source> epoch;
        std::size_t count=0;
        for(std::uint16_t item=6501;item<=6900;++item) {
            const auto row=result->retained_lookup(item);
            if(!row) {if(result->terminal_)return {};continue;}
            const auto index=row->book.source_record_index;
            if(index>=seen.size() || seen[index] || (epoch && *epoch!=row->book.source))return {};
            if(!epoch)epoch=row->book.source;
            seen[index]=true;++count;
        }
        if(count!=Books::book_count || !result->observe())return {};
        return result;
    }catch(...) {result->terminal_=true;throw;}
}
}
