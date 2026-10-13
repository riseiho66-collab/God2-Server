#include "cn/world/CnPrebornSkillChoiceSource.h"
#include "cn/world/CnPrebornSkillReferences.h"
#include <algorithm>
#include <utility>

namespace god2::cn {
namespace {
int signed_word(std::uint16_t value) {
    return value<0x8000?int(value):int(value)-0x10000;
}
bool excluded_item(std::uint16_t item) {
    // Native532B20 insertion and native533850/532B20 label checks. Last
    // interval is the exact unsigned16(item+E51C)<3 form, not signed wrapping.
    return (item>=0x19a8 && item<=0x19af) || (item>=0x1a09 && item<=0x1a0d) ||
        (item>=0x1a6b && item<=0x1a6d) || static_cast<std::uint16_t>(unsigned(item)+0xe51c)<3;
}
std::optional<std::uint8_t> pinned_native_12c(const CnNativeSkillBookBindings::Book& book) {
    // All386 qualified raw27 tokens are exactly one digit0..4. Native42CFB0
    // stores this token reader's AL at+12C. No general tokenizer/MP formula.
    const auto& raw=book.opaque_tail_fields[0];
    if(raw.size()!=1 || raw[0]<'0' || raw[0]>'4')return std::nullopt;
    return static_cast<std::uint8_t>(raw[0]-'0');
}
}
std::optional<CnPrebornSkillChoiceSource::Resolved> CnPrebornSkillChoiceSource::resolve_actual_selection(
    std::span<const std::uint16_t> words,const std::optional<Subject>& subject,
    const CnSharedSkillCatalog& catalog,const CnNativeSkillBookBindings* books,
    const god2cn::CnWorldPrimarySkillSource* primary) {
    if(primary && (!subject || !primary->matches_subject(*subject) || !primary->current()))return std::nullopt;
    if(!catalog.current() || (books && (!books->uses_shared_catalog(catalog) || !books->current())))return std::nullopt;
    Resolved result;
    if(books) {
        result.books=books->lookup_words(words);if(!result.books)return std::nullopt;
        result.definitions.reserve(result.books->size());
        for(const auto& binding:*result.books)result.definitions.push_back(binding.definition);
    } else {
        auto actual=catalog.lookup_words(words);if(!actual)return std::nullopt;
        result.definitions=std::move(*actual);
    }
    result.facts.common_definitions.reserve(result.definitions.size());
    for(const auto& original:result.definitions) {
        auto common=catalog.lookup_shared(static_cast<std::uint8_t>(original.kind),
            static_cast<std::uint8_t>(original.definition_id));
        if(!common || !common->requested_native || *common->requested_native!=original)return std::nullopt;
        result.facts.common_definitions.push_back(std::move(common->definition));
    }
    if(subject) {
        if(!subject->current() || !subject->retained_selection())return std::nullopt;
        const auto references=primary?CnPrebornSkillReferences::resolve_actual_primary_source(*primary,catalog):
            CnPrebornSkillReferences::resolve_actual_snapshot(*subject,catalog);
        if(!references)return std::nullopt;
        if(primary) {
            result.facts.native_primary_bank_scope=primary->retained_scope();
            result.facts.native_primary_bank_entries=primary->retained_entries();
        }
        const auto role_word=subject->retained_inline_role_word();
        const auto family=static_cast<std::uint8_t>(signed_word(role_word)/2);
        const auto& selected=*subject->retained_selection();
        result.facts.native_scope=subject->scope();
        result.facts.native_inline_role_word=role_word;
        result.facts.native_family_byte=family;
        result.facts.native_filtered_offer_words.emplace();
        for(const auto& reference:references->entries) {
            const auto& definition=reference.definition;
            if((reference.native_reference.actual_native_flags&1) &&
               (definition.raw_record[1]==family || signed_word(selected.actual_native_identifier)>100 || selected.native_5b_operand))
                result.facts.native_filtered_offer_words->push_back(static_cast<std::uint16_t>(
                    unsigned(definition.raw_record[0])|(unsigned(definition.raw_record[1])<<8)));
        }
    }
    result.facts.entries.reserve(words.size());
    for(std::size_t n=0;n<words.size();++n) {
        Entry entry{words[n],std::nullopt,std::nullopt,std::nullopt,std::nullopt,std::nullopt,std::nullopt};
        for(std::size_t previous=0;previous<n;++previous)
            if(words[previous]==words[n]){entry.earlier_request_duplicate=previous;break;}
        if(result.books && (*result.books)[n].matching_book) {
            const auto& book=*(*result.books)[n].matching_book;
            entry.matched_book_native_12c=pinned_native_12c(book);
            if(!entry.matched_book_native_12c)return std::nullopt;
            entry.matched_item_in_native_exclusion_ranges=excluded_item(book.item_id);
        }
        if(result.facts.native_filtered_offer_words) {
            const auto& offer=*result.facts.native_filtered_offer_words;
            entry.in_supplied_native_filtered_offer=std::find(offer.begin(),offer.end(),words[n])!=offer.end();
        }
        if(primary) {
            entry.supplied_primary_gate=primary->project_actual_first_primary_gate(
                std::uint32_t(words[n]>>8),std::uint32_t(words[n]&0xff));
            if(!entry.supplied_primary_gate)return std::nullopt;
            entry.supplied_primary_ordinal=entry.supplied_primary_gate->lookup;
        }
        result.facts.entries.push_back(std::move(entry));
    }
    if(!catalog.current() || (books && !books->current()) || (subject && !subject->current()) ||
       (primary && (!primary->current() || !primary->matches_subject(*subject))))return std::nullopt;
    return result;
}
}
