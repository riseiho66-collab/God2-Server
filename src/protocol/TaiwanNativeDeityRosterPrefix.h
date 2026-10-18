#pragma once

#include "protocol/TaiwanNativePrimarySkillList.h"
#include "protocol/RecoveredInventory.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace god2 {
// Expected DATA-PREFIX replay for the qualified normal468120 reset and actual
// ordered restoration records. The caller supplies that real source epoch;
// this pure API cannot prove remote execution, issuance, ownership or a grant.
// S30 resource/name and refresh helpers, S31 pre/post selection helpers and
// S34 diagnostic/page/refresh helpers remain opaque. Their transitive effects
// are NOT projected here. Complete input bytes remain owned separately below.
class TaiwanNativeDeityRosterPrefix final {
public:
    using Row=TaiwanNativePrimarySkillList::RosterSkillRow;
    static constexpr std::size_t row_capacity=16,skill_capacity=100;
    static constexpr char historical_catalog_sha256[]=
        "7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51";

    static std::optional<TaiwanNativeDeityRosterPrefix> from_reset_and_records(
            std::span<const std::vector<std::uint8_t>> actual_batches,
            std::span<const NativeSkillRecord> owned_definitions,
            bool issued_activation_records=false,
            NativeTaiwanSkillProfile profile=NativeTaiwanSkillProfile::Historical448) {
        if(!native_taiwan_skill_dataset_id(profile))return std::nullopt;
        TaiwanNativeDeityRosterPrefix next;next.profile_=profile;
        for(const auto& definition:owned_definitions) {
            if(!valid_definition(definition,profile))return std::nullopt;
            if(!next.catalog_records_.empty() && definition.source!=next.catalog_records_.front().source)
                return std::nullopt;
            const auto old=std::find_if(next.catalog_records_.begin(),next.catalog_records_.end(),
                [&](const auto& r){return same_identity(r,definition);});
            if(old!=next.catalog_records_.end()) {
                if(*old!=definition)return std::nullopt;
            } else next.catalog_records_.push_back(definition);
        }
        // This is a projection of actual468120 writes, not constructor-default
        // evidence. Native pointers are represented by full owned nullable rows.
        for(auto& row:next.rows_) {
            row.row_key=0;row.learned_count=0;row.learned_flags.fill(0);
            row.learned_definitions.resize(skill_capacity);
            row.auxiliary_count=0;row.auxiliary_definitions.resize(skill_capacity);
        }
        next.actual_batches_.assign(actual_batches.begin(),actual_batches.end());
        for(const auto& batch:next.actual_batches_) {
            // Existing restoration emits whole records in native frame-sized
            // logical batches. A record crossing a boundary is unsupported.
            if(batch.size()>2560)return std::nullopt;
            for(std::size_t at=0;at<batch.size();) {
                // S35 is opt-in only for an actual separately qualified issued source.
                const auto size=(issued_activation_records && batch[at]==0x35)?
                    std::optional<std::size_t>{4}:record_size(batch[at]);
                if(!size || *size>batch.size()-at)return std::nullopt;
                const auto record=std::span<const std::uint8_t>(batch).subspan(at,*size);
                switch(record[0]) {
                case 0x30:if(!next.apply30(record))return std::nullopt;break;
                case 0x31:next.apply31(record);break;
                case 0x34:if(!next.apply34(record))return std::nullopt;break;
                case 0x35:if(!issued_activation_records || !next.apply35(record))return std::nullopt;break;
                default:break; // Known pet records: exact full bytes retained.
                }
                at+=*size;
            }
        }
        return next;
    }

    NativeTaiwanSkillProfile profile() const noexcept {return profile_;}
    const std::array<Row,row_capacity>& rows() const noexcept {return rows_;}
    std::uint8_t roster_count() const noexcept {return roster_count_;}
    std::int8_t selected_row() const noexcept {return selected_row_;}
    const std::vector<NativeSkillRecord>& catalog_records() const noexcept {return catalog_records_;}
    const std::vector<std::vector<std::uint8_t>>& actual_batches() const noexcept {return actual_batches_;}
private:
    friend class OwnedTaiwanPkCompanionSource;
    // Same original reset/roster, followed by actual Written S31 records.
    // This models only the already-qualified direct selector data prefix;
    // opaque refresh helpers, constructor events and grants are not inferred.
    static std::optional<TaiwanNativeDeityRosterPrefix> advance_written_selection(
            const TaiwanNativeDeityRosterPrefix& before,
            std::span<const std::vector<std::uint8_t>> records) {
        if(records.empty())return {};
        auto next=before;
        for(const auto& raw:records) {
            if(raw.size()!=29 || raw[0]!=0x31 ||
               std::none_of(next.rows_.begin(),next.rows_.begin()+next.roster_count_,
                   [&](const auto& row){return int(row.row_key)==signed_byte(raw[1]);}))return {};
            next.apply31(raw);next.actual_batches_.push_back(raw);
        }
        return next;
    }
    // Restricted actual S34/S35/S41 successor. Retain every old physical row,
    // selector and inactive tail; never execute a new normal-entry reset.
    static std::optional<TaiwanNativeDeityRosterPrefix> advance_written_learning(
            const TaiwanNativeDeityRosterPrefix& before,std::span<const std::uint8_t> delta,
            const NativeSkillRecord& definition) {
        if(delta.size()!=13 || delta[0]!=0x34 || delta[4]!=0x35 || delta[8]!=0x41 ||
           !std::equal(delta.begin()+1,delta.begin()+4,delta.begin()+5) ||
           !RecoveredInventory::decode_slot_update(delta.subspan(8,5)) ||
           definition.kind!=delta[2] || definition.definition_id!=delta[3] ||
           !valid_definition(definition,before.profile_))return {};
        auto next=before;
        if(!next.catalog_records_.empty() && definition.source!=next.catalog_records_.front().source)return {};
        const auto old=std::find_if(next.catalog_records_.begin(),next.catalog_records_.end(),
            [&](const auto& value){return same_identity(value,definition);});
        if(old!=next.catalog_records_.end()) {if(*old!=definition)return {};}
        else next.catalog_records_.push_back(definition);
        bool subject=false;
        for(std::size_t i=0;i<before.roster_count_;++i) {
            const auto& row=before.rows_[i];if(row.row_key!=delta[1])continue;
            subject=true;if(row.learned_count>=skill_capacity)return {};
            for(std::size_t j=0;j<row.learned_count;++j)
                if(!row.learned_definitions[j] || same_identity(*row.learned_definitions[j],definition))return {};
        }
        if(!subject || !next.apply34(delta.first(4)) || !next.apply35(delta.subspan(4,4)))return {};
        // S41 bytes are genuine history; this prefix models no inventory/UI or
        // opaque S35 page/shortcut effects. Those remain independent evidence.
        next.actual_batches_.emplace_back(delta.begin(),delta.end());
        return next;
    }
    TaiwanNativeDeityRosterPrefix()=default;
    NativeTaiwanSkillProfile profile_=NativeTaiwanSkillProfile::Historical448;
    std::array<Row,row_capacity> rows_;
    std::uint8_t roster_count_=0;
    std::int8_t selected_row_=-1;
    std::vector<NativeSkillRecord> catalog_records_;
    std::vector<std::vector<std::uint8_t>> actual_batches_;

    static std::optional<std::size_t> record_size(std::uint8_t opcode) noexcept {
        switch(opcode) {
        case 0x30:return 19;case 0x31:return 29;case 0x34:return 4;
        case 0x41:return 5;case 0x3b:return 25;case 0xfb:return 73;case 0xe3:return 53;
        default:return std::nullopt;
        }
    }
    static int signed_byte(std::uint8_t value) noexcept {
        return value<128?int(value):int(value)-256;
    }
    static bool text(const std::string& value) noexcept {
        return !value.empty() && value.find('\0')==std::string::npos;
    }
    static bool sha(const std::string& value) noexcept {
        return value.size()==64 && std::all_of(value.begin(),value.end(),[](unsigned char c){
            return (c>='0' && c<='9') || (c>='a' && c<='f');});
    }
    static bool same_identity(const NativeSkillRecord& a,const NativeSkillRecord& b) noexcept {
        return a.kind==b.kind && a.definition_id==b.definition_id;
    }
    static bool valid_definition(const NativeSkillRecord& r,NativeTaiwanSkillProfile profile) noexcept {
        const auto& s=r.source;
        const auto counts=native_taiwan_skill_bank_counts(profile);
        // Explicit pinned material epoch; raw digest/full-row Current remain
        // the actual caller's responsibility. A profile never grants a skill.
        if(!native_taiwan_skill_source_matches(s,profile) || r.kind<0 || r.kind>=4 ||
           r.definition_id<1 || r.definition_id>counts[std::size_t(r.kind)])return false;
        std::int64_t ordinal=r.definition_id-1;
        for(std::size_t i=0;i<std::size_t(r.kind);++i)ordinal+=counts[i];
        return r.source_record_index==ordinal && sha(r.record_sha256) && r.raw_record.size()==110 &&
            r.raw_record[0]==r.definition_id && r.raw_record[1]==r.kind &&
            r.source_offset==8+r.kind*0x6e04+(r.definition_id-1)*110;
    }
    bool apply30(std::span<const std::uint8_t> record) {
        const int raw=signed_byte(record[1]);
        const auto key=std::uint16_t(raw<0?-raw:raw);
        // Native skips the whole record before staging/duplicate reset at16.
        if(!key || roster_count_>=row_capacity)return true;
        auto& staged=rows_[roster_count_];staged.row_key=key;
        if(key>=100) {
            // Owned safe name subset: do not follow the native NUL scan past
            // the16 supplied name bytes into the flag/another logical record.
            if(std::find(record.begin()+2,record.begin()+18,0)==record.begin()+18)return false;
            if(record[18]==1) {
                for(std::size_t i=0;i<roster_count_;++i) {
                    if(rows_[i].row_key!=key)continue;
                    rows_[i].learned_count=0;
                    return true; // Staged inactive key and all tails persist.
                }
            }
        }
        ++roster_count_;
        if(raw<0)selected_row_=std::int8_t(roster_count_-1);
        return true;
    }
    void apply31(std::span<const std::uint8_t> record) noexcept {
        const auto key=signed_byte(record[1]);
        for(std::size_t i=0;i<roster_count_;++i) {
            if(int(rows_[i].row_key)!=key)continue;
            //4AA2BB/C7 write this actual first physical row and index, with
            // opaque helpers before/after. Status bytes remain in batches;
            // this model exposes only the expected row/skill data prefix.
            selected_row_=std::int8_t(i);break;
        }
    }
    // Actual4AA830 direct data prefix only: existing same catalog pointer,
    // whole flag3 overwrite then flags&2 auxiliary rebuild. Opaque UI omitted.
    bool apply35(std::span<const std::uint8_t> record) {
        const auto definition=std::find_if(catalog_records_.begin(),catalog_records_.end(),
            [&](const auto& value){return value.kind==record[2] && value.definition_id==record[3];});
        if(definition==catalog_records_.end())return false;
        for(std::size_t i=0;i<roster_count_;++i) {
            auto& row=rows_[i];if(row.row_key!=record[1])continue;
            for(std::size_t j=0;j<row.learned_count;++j) {
                const auto& owned=row.learned_definitions[j];
                if(!owned || *owned!=*definition)continue;
                row.learned_flags[j]=3;
                auto rebuilt=TaiwanNativePrimarySkillList::rebuild_roster_auxiliary(row,definition->source);
                if(!rebuilt)return false;
                row=std::move(*rebuilt);break;
            }
        }
        return true;
    }
    bool apply34(std::span<const std::uint8_t> record) {
        const auto definition=std::find_if(catalog_records_.begin(),catalog_records_.end(),
            [&](const auto& r){return r.kind==record[2] && r.definition_id==record[3];});
        // Explicit owned source subset even for an ignored/missing subject;
        // unknown definitions never become guessed native pointers.
        if(definition==catalog_records_.end())return false;
        for(std::size_t i=0;i<roster_count_;++i) {
            auto& row=rows_[i];
            if(row.row_key!=record[1] || row.learned_count>=skill_capacity)continue;
            bool duplicate=false;
            for(std::size_t j=0;j<row.learned_count;++j) {
                const auto& old=row.learned_definitions[j];
                if(!old)return false; // Native would dereference this pointer.
                if(!same_identity(*old,*definition))continue;
                if(*old!=*definition)return false;
                duplicate=true;break;
            }
            if(duplicate)continue; // Diagnostic boundary; no invented append.
            const auto at=std::size_t(row.learned_count);
            row.learned_flags[at]=0;row.learned_definitions[at]=*definition;
            ++row.learned_count;
            // Only append reaches4A9750. Preserve inactive auxiliary tails;
            // copy flags&2 in physical order, retaining nulls/duplicates.
            auto rebuilt=TaiwanNativePrimarySkillList::rebuild_roster_auxiliary(row,definition->source);
            if(!rebuilt)return false;
            row=std::move(*rebuilt);
        }
        return true;
    }
};
}
