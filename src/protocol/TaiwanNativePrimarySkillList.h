#pragma once

#include "db/NativeSkillCatalog.h"
#include "protocol/TaiwanNativeSkillCommand.h"
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
// Same149c issued-list data projection, retaining the existing primary API:
// 51C520, 51C7F0/51C8E0, 51BA90 -> 51B8C0 -> 51B9A0; optional independent
// secondary51C6C6 -> 51B900 -> 51B760. Inputs are server-owned issued
// observations, never manufactured client addresses or memory attestation.
// The fixed16/100 and3/10 limits are owned safe geometry, NOT native writer
// guards. No learned/grant/MP/actor authority or native packet is generated.
class TaiwanNativePrimarySkillList final {
public:
    static constexpr std::size_t bank_capacity=16,entry_capacity=100;
    static constexpr std::size_t secondary_bank_capacity=3,secondary_entry_capacity=10;
    struct RosterSkillRow {
        std::uint16_t row_key;
        // Same actual source row, NOT the battle bank: unsigned BYTE+1F0,
        // all flags+1F1 and nullable pointers+258; independent BYTE+5C and
        // pointers+60. Keep all100 slots, including inactive tails/duplicates.
        // The helper itself has no100 guard. This is owned safe geometry;
        // native S34's append guard is separate from the helper's contract.
        std::uint8_t learned_count;
        std::array<std::uint8_t,entry_capacity> learned_flags;
        // Exactly100 owned slots, stored dynamically so the large complete
        // records do not inflate every by-value Snapshot beyond x86 stacks.
        std::vector<std::optional<NativeSkillRecord>> learned_definitions;
        std::uint8_t auxiliary_count;
        std::vector<std::optional<NativeSkillRecord>> auxiliary_definitions;
        bool operator==(const RosterSkillRow&) const=default;
    };
    struct Bank {
        std::uint32_t entry_count;
        std::array<std::uint16_t,entry_capacity> raw_words;
        std::array<std::uint8_t,entry_capacity> auxiliary;
        // Complete ordered definitions replace the original active pointers.
        // Inactive raw words/auxiliary are retained, never zero-initialized here.
        std::vector<NativeSkillRecord> definitions;
        // Independent source-row+5C count and row+60 pointer list. Null
        // pointers are retained explicitly; this is NOT the main ordinal.
        std::uint8_t auxiliary_count;
        std::vector<std::optional<NativeSkillRecord>> auxiliary_definitions;
        std::uint8_t state;
        std::uint16_t row_key;
        std::uint32_t page_count;
        // Raw bank+2C8, separate from page count+2CC. Initial prefix writes
        // 0%1; S87/38 and the enable-clear leaves preserve later raw values.
        std::uint32_t raw_page_index;
        bool operator==(const Bank&) const=default;
    };
    struct SecondaryBank {
        // Separate0x54 geometry: WORDs+0, nullable pointers+14, bytes+3C,
        // raw fields+46/+48/+4C and signed count+50. Preserve inactive tails
        // too; ten is our owned safe geometry, not a recovered writer guard.
        std::array<std::uint16_t,secondary_entry_capacity> raw_words;
        std::array<std::optional<NativeSkillRecord>,secondary_entry_capacity> definitions;
        std::array<std::uint8_t,secondary_entry_capacity> auxiliary;
        std::array<std::uint8_t,2> opaque46;
        std::uint32_t opaque48,opaque4c;
        std::int32_t entry_count;
        bool operator==(const SecondaryBank&) const=default;
    };
    struct SecondarySnapshot {
        std::array<SecondaryBank,secondary_bank_capacity> banks;
        std::uint8_t current_selector,opaque2d11;
        std::array<std::uint8_t,2> opaque2d12;
        bool operator==(const SecondarySnapshot&) const=default;
    };
    struct Snapshot {
        std::array<Bank,bank_capacity> banks;
        std::uint8_t bank_count;
        std::int8_t current_selector;
        std::uint32_t control_a,control_b;
        // Actual battle BYTE+51/+52, independent of a saved deity key or the
        // world local-actor pointer. Values15 or an inactive stale byte may be
        // retained; the command grammar separately qualifies actor positions.
        std::uint8_t primary_actor,secondary_actor;
        // Last supplied86/5 raw record only, not complete history, a native
        // grant incarnation, OS-clock observation or full consumer snapshot.
        std::optional<std::array<std::uint8_t,17>> last_control86;
        NativeSkillSource catalog_source;
        // Absence keeps existing primary-only suppliers qualified. It never
        // creates zero/empty secondary state or borrows primary membership.
        std::optional<SecondarySnapshot> secondary;
        // Present only for the actual roster-rebuild input route. It retains
        // full resulting learned/aux source rows, not just an active prefix.
        // Absence never borrows saved34 or fabricates learned flags.
        std::optional<std::array<RosterSkillRow,bank_capacity>> roster_rows;
        bool operator==(const Snapshot&) const=default;
    };
    struct LinkedRosterRow {
        std::uint16_t row_key;
        // Actual linked row+5C/+60 material, independent of S34 learned
        // row+1F0/+258. Include every one of the16 linked rows, not only
        // bank_count or the selected saved deity. Null entries retain order.
        std::uint8_t auxiliary_count;
        std::vector<std::optional<NativeSkillRecord>> auxiliary_definitions;
    };
    struct InitializationPrefix {
        std::array<LinkedRosterRow,bank_capacity> linked_rows;
        std::uint8_t roster_count;
        std::int8_t selected_row;
        // These fields are not written by51BB80..51BC2A. The real owner
        // supplies their actual observations; no grant/reset is inferred.
        std::uint32_t control_a,control_b;
        std::uint8_t primary_actor,secondary_actor;
        std::optional<std::array<std::uint8_t,17>> last_control86;
        NativeSkillSource catalog_source;
        std::optional<SecondarySnapshot> secondary;
    };
    struct RosterInitializationPrefix {
        // Actual stable full same-roster rows BEFORE the observed4A9750
        // rebuild. This represents a distinct source event, not a claim that
        // the51BB80 constructor itself rebuilds or that a wire ACK exists.
        std::array<RosterSkillRow,bank_capacity> source_rows;
        std::uint8_t roster_count;
        std::int8_t selected_row;
        std::uint32_t control_a,control_b;
        std::uint8_t primary_actor,secondary_actor;
        std::optional<std::array<std::uint8_t,17>> last_control86;
        NativeSkillSource catalog_source;
        std::optional<SecondarySnapshot> secondary;
    };
    enum class EnableClear {Primary,Secondary};
    struct Lookup {
        // C35 carries a definition key, NOT its native selected UI index.
        std::uint32_t issued_lookup_ordinal;
        std::uint16_t raw_word;
        NativeSkillRecord definition;
        std::uint8_t actor_position,side_flag;
        bool operator==(const Lookup&) const=default;
    };
    static std::optional<TaiwanNativePrimarySkillList> from_actual(Snapshot supplied) {
        if(!valid(supplied))return std::nullopt;
        return TaiwanNativePrimarySkillList(std::move(supplied));
    }
    // Complete pure data helper4A9750..4A97A0. The original re-reads the
    // learned count each iteration; our actual game-owned immutable input is
    // stable during this projection. No concurrent/native-memory observation
    // or single native read is claimed. Copy NULL/duplicates in physical order,
    // reset count only, and preserve EVERY inactive auxiliary pointer tail.
    static std::optional<RosterSkillRow> rebuild_roster_auxiliary(
        RosterSkillRow row,const NativeSkillSource& source) {
        if(!valid_source(source) || !valid_roster_row(row,source))return std::nullopt;
        row.auxiliary_count=0;
        for(std::size_t i=0;i<std::size_t(row.learned_count);++i) {
            if((row.learned_flags[i]&2u)==0)continue;
            row.auxiliary_definitions[row.auxiliary_count]=row.learned_definitions[i];
            ++row.auxiliary_count;
        }
        return row;
    }
    // Concrete full roster helper -> independent linked auxiliary list ->
    // existing primary data prefix. Main remains genuinely zero; membership
    // is later issued by87. Preserve full source rows for catalog freshness.
    static std::optional<TaiwanNativePrimarySkillList> from_roster_rebuild_initialization_prefix(
        RosterInitializationPrefix input) {
        InitializationPrefix projected{};
        projected.roster_count=input.roster_count;projected.selected_row=input.selected_row;
        projected.control_a=input.control_a;projected.control_b=input.control_b;
        projected.primary_actor=input.primary_actor;projected.secondary_actor=input.secondary_actor;
        projected.last_control86=std::move(input.last_control86);
        projected.catalog_source=std::move(input.catalog_source);
        projected.secondary=std::move(input.secondary);
        for(std::size_t i=0;i<bank_capacity;++i) {
            auto rebuilt=rebuild_roster_auxiliary(std::move(input.source_rows[i]),projected.catalog_source);
            if(!rebuilt)return std::nullopt;
            input.source_rows[i]=std::move(*rebuilt);
            const auto& row=input.source_rows[i];
            auto& linked=projected.linked_rows[i];
            linked.row_key=row.row_key;linked.auxiliary_count=row.auxiliary_count;
            linked.auxiliary_definitions.assign(row.auxiliary_definitions.begin(),
                row.auxiliary_definitions.begin()+row.auxiliary_count);
        }
        auto model=from_initialization_prefix(std::move(projected));
        if(!model)return std::nullopt;
        model->snapshot_.roster_rows=std::move(input.source_rows);
        return from_actual(std::move(model->snapshot_));
    }
    // Exact DATA-prefix result, not whole native initialization or ordinary
    // entry/receipt proof. The native REP really zeros each primary bank;
    // zero main entries here are writes, never an empty learned roster claim.
    // Linked row contents are separately supplied same-roster observations.
    static std::optional<TaiwanNativePrimarySkillList> from_initialization_prefix(InitializationPrefix input) {
        Snapshot next{};
        next.bank_count=input.roster_count;
        next.current_selector=input.selected_row;
        next.control_a=input.control_a;next.control_b=input.control_b;
        next.primary_actor=input.primary_actor;next.secondary_actor=input.secondary_actor;
        next.last_control86=std::move(input.last_control86);
        next.catalog_source=std::move(input.catalog_source);
        next.secondary=std::move(input.secondary);
        for(std::size_t i=0;i<bank_capacity;++i) {
            auto& bank=next.banks[i];
            // Complete0x2D0-bank REP clear; later stores link the row,
            // set page_count1, then write raw_page_index=0%1=0.
            bank.entry_count=0;bank.raw_words.fill(0);bank.auxiliary.fill(0);
            bank.definitions.clear();bank.state=0;bank.page_count=1;bank.raw_page_index=0;
            bank.row_key=input.linked_rows[i].row_key;
            bank.auxiliary_count=input.linked_rows[i].auxiliary_count;
            bank.auxiliary_definitions=std::move(input.linked_rows[i].auxiliary_definitions);
        }
        return from_actual(std::move(next));
    }
    const Snapshot& snapshot() const noexcept {return snapshot_;}

    // Actual issuer-observed LOCAL data leaves, not wire messages or native
    // server permission. Preserve every field outside the exact footprints.
    // Primary51C4B0 clears all16 banks'100 enable bits/aux and stateBYTE.
    // Secondary51C4F0 clears only3*10 WORD enable bits; its aux is retained.
    std::optional<TaiwanNativePrimarySkillList> clear_enable(EnableClear target) const {
        auto next=snapshot_;
        switch(target) {
        case EnableClear::Primary:
            for(auto& bank:next.banks) {
                for(auto& word:bank.raw_words)word=std::uint16_t(word&0x7fffu);
                bank.auxiliary.fill(0);bank.state=0;
            }
            break;
        case EnableClear::Secondary:
            if(!next.secondary)return std::nullopt;
            for(auto& bank:next.secondary->banks)
                for(auto& word:bank.raw_words)word=std::uint16_t(word&0x7fffu);
            break;
        default:return std::nullopt;
        }
        return from_actual(std::move(next));
    }

    // Direct86/5 control/actor writes at1175B2/11776E only. Missing bits
    // PRESERVE full DWORD controls and actor bytes; high flag bits do not clear
    // them. The real consumer also calls UI/rearm/time helpers, not projected
    // here. Other selectors and local post-builder consumption need an actual
    // complete replacement from their owner, never a guessed wire ACK.
    std::optional<TaiwanNativePrimarySkillList> apply86_control(
        std::span<const std::uint8_t> logical) const {
        if(logical.size()!=17 || logical[0]!=0x86 || logical[1]!=5)return std::nullopt;
        auto next=snapshot_;
        std::array<std::uint8_t,17> raw;
        std::copy(logical.begin(),logical.end(),raw.begin());
        next.last_control86=raw;
        if(raw[3]&1u) {
            next.control_a=1;
            next.primary_actor=std::uint8_t(raw[4]&15u);
        }
        if(raw[3]&2u) {
            next.control_b=1;
            next.secondary_actor=std::uint8_t(raw[4]>>4);
        }
        return from_actual(std::move(next));
    }

    // Exact original87 route bit14 and actual full catalog row.
    // Existing first kind/id match replaces bit15 ONLY; append retains the
    // whole incoming WORD. Primary's separate source-row auxiliary pointer
    // list uses its OWN first matching ordinal; secondary uses the matched
    // main ordinal directly. Neither auxiliary byte is a server grant.
    std::optional<TaiwanNativePrimarySkillList> apply87(
        std::span<const std::uint8_t> logical,const NativeSkillRecord& definition) const {
        if(logical.size()!=3 || logical[0]!=0x87 ||
           !valid_definition(definition,snapshot_.catalog_source))return std::nullopt;
        const auto incoming=std::uint16_t(std::uint16_t(logical[1])|
            (std::uint16_t(logical[2])<<8));
        if((incoming&0x3fffu)!=key(definition))return std::nullopt;
        if(incoming&0x4000u) {
            if(!snapshot_.secondary)return std::nullopt;
            auto next=snapshot_;
            auto& secondary=*next.secondary;
            // Unsigned secondary selector is independent of primary count
            // and signed selector. Native invalid selector is a no-op.
            if(secondary.current_selector>=secondary_bank_capacity)return from_actual(std::move(next));
            auto& bank=secondary.banks[secondary.current_selector];
            for(std::size_t i=0;i<std::size_t(bank.entry_count);++i) {
                const auto& old=bank.definitions[i];
                if(!old || old->kind!=definition.kind || old->definition_id!=definition.definition_id)continue;
                if(*old!=definition)return std::nullopt;
                bank.raw_words[i]=std::uint16_t((bank.raw_words[i]&0x7fffu)|(incoming&0x8000u));
                // Unlike primary, this is the SAME ordinal, including any
                // skipped null pointer rows. No independent auxiliary search.
                bank.auxiliary[i]=std::uint8_t(incoming>>15);
                return from_actual(std::move(next));
            }
            if(std::size_t(bank.entry_count)>=secondary_entry_capacity)return std::nullopt;
            const auto i=std::size_t(bank.entry_count);
            bank.raw_words[i]=incoming;
            bank.definitions[i]=definition;
            bank.auxiliary[i]=std::uint8_t(incoming>>15);
            ++bank.entry_count;
            return from_actual(std::move(next));
        }
        // Native primary writer ignores an invalid signed selector. This is
        // a qualified no-op, distinct from unavailable/bad source material.
        if(!primary_selector(snapshot_))return from_actual(snapshot_);
        auto next=snapshot_;
        auto& bank=next.banks[std::size_t(next.current_selector)];
        bool matched=false;
        for(std::size_t i=0;i<bank.definitions.size();++i) {
            const auto& old=bank.definitions[i];
            if(old.kind!=definition.kind || old.definition_id!=definition.definition_id)continue;
            if(old!=definition)return std::nullopt;
            bank.raw_words[i]=std::uint16_t((bank.raw_words[i]&0x7fffu)|(incoming&0x8000u));
            matched=true;
            break;
        }
        if(!matched) {
            if(bank.entry_count>=entry_capacity)return std::nullopt;
            bank.raw_words[bank.entry_count]=incoming;
            bank.definitions.push_back(definition);
            ++bank.entry_count;
            bank.page_count=(bank.entry_count+14u)/15u;
        }
        for(std::size_t j=0;j<bank.auxiliary_definitions.size();++j) {
            const auto& auxiliary=bank.auxiliary_definitions[j];
            if(!auxiliary || auxiliary->kind!=definition.kind ||
               auxiliary->definition_id!=definition.definition_id)continue;
            if(*auxiliary!=definition)return std::nullopt;
            bank.auxiliary[j]=std::uint8_t(incoming>>15);
            break;
        }
        return from_actual(std::move(next));
    }

    // 38 body low5=index, high3=state. Leaving state2 clears all100 enable
    // bits and all100 aux bytes, including inactive tails. State2 switches
    // to FIRST same row_key bank other than signed current, NOT directly i.
    std::optional<TaiwanNativePrimarySkillList> apply38(
        std::span<const std::uint8_t> logical) const {
        if(logical.size()!=2 || logical[0]!=0x38)return std::nullopt;
        const auto i=std::size_t(logical[1]&31u);
        const auto state=std::uint8_t(logical[1]>>5);
        // Native ignores an out-of-count index without changing any bank.
        if(i>=snapshot_.bank_count)return from_actual(snapshot_);
        auto next=snapshot_;
        auto& bank=next.banks[i];
        if(bank.state==2 && state!=2) {
            for(auto& word:bank.raw_words)word=std::uint16_t(word&0x7fffu);
            bank.auxiliary.fill(0);
        }
        bank.state=state;
        if(state==2) {
            for(std::size_t j=0;j<next.bank_count;++j) {
                if(std::int32_t(j)!=std::int32_t(next.current_selector) &&
                   next.banks[j].row_key==bank.row_key) {
                    next.current_selector=std::int8_t(j);
                    break;
                }
            }
        }
        return from_actual(std::move(next));
    }

    // First physical full definition kind/id lookup, then nonnull owned row,
    // then enable bit. A disabled first duplicate never retries a later one.
    // Primary key-search is recovered51BA90. Secondary key-to-ordinal is an
    // explicit deterministic owned projection of the issued list, NOT a
    // recovered native key-search or observation of the client's UI ordinal.
    // The secondary ordinal compound gate515443 does prove51B900 nonnull
    // before51B760 rawWORD bit15 (not auxiliary BYTE). Ambiguous disabled
    // first duplicates remain outside this supported projection.
    // Bit15 only mirrors a client enable condition; it is NOT a turn grant.
    std::optional<Lookup> issued_lookup(std::uint32_t full_operand) const {
        if(full_operand>0xffffu || (!snapshot_.control_a && !snapshot_.control_b))return std::nullopt;
        if(!snapshot_.control_a && snapshot_.control_b) {
            if(!snapshot_.secondary || snapshot_.secondary->current_selector>=secondary_bank_capacity)return std::nullopt;
            const auto& bank=snapshot_.secondary->banks[snapshot_.secondary->current_selector];
            for(std::size_t i=0;i<std::size_t(bank.entry_count);++i) {
                const auto& definition=bank.definitions[i];
                if(!definition || key(*definition)!=full_operand)continue;
                if((bank.raw_words[i]&0x8000u)==0)return std::nullopt;
                return Lookup{std::uint32_t(i),bank.raw_words[i],*definition,snapshot_.secondary_actor,1};
            }
            return std::nullopt;
        }
        if(!primary_selector(snapshot_))return std::nullopt;
        const auto& bank=snapshot_.banks[std::size_t(snapshot_.current_selector)];
        for(std::size_t i=0;i<bank.definitions.size();++i) {
            const auto& definition=bank.definitions[i];
            if(key(definition)!=full_operand)continue;
            if((bank.raw_words[i]&0x8000u)==0)return std::nullopt;
            //5156E0 uses the same A==0/B!=0 predicate as5156A0's list.
            // A!=0 selects actual BYTE+51/side0 even when B is also nonzero.
            // Do not use an observed UI index or selected deity key.
            return Lookup{std::uint32_t(i),bank.raw_words[i],definition,snapshot_.primary_actor,0};
        }
        return std::nullopt;
    }
private:
    explicit TaiwanNativePrimarySkillList(Snapshot supplied):snapshot_(std::move(supplied)) {}
    Snapshot snapshot_;
    static bool primary_selector(const Snapshot& s) noexcept {
        // Native primary87/getter use signed0..15 independently of countBYTE5.
        return s.current_selector>=0 && std::size_t(s.current_selector)<bank_capacity;
    }
    static std::uint16_t key(const NativeSkillRecord& r) noexcept {
        return std::uint16_t(std::uint16_t(r.definition_id)|(std::uint16_t(r.kind)<<8));
    }
    static bool hex_sha(const std::string& s) noexcept {
        return s.size()==64 && std::all_of(s.begin(),s.end(),[](unsigned char c){
            return (c>='0' && c<='9') || (c>='a' && c<='f');});
    }
    static bool valid_source(const NativeSkillSource& s) noexcept {
        return native_taiwan_skill_source_matches(s,NativeTaiwanSkillProfile::Historical448) ||
            native_taiwan_skill_source_matches(s,NativeTaiwanSkillProfile::Installed453);
    }
    static bool valid_definition(const NativeSkillRecord& r,const NativeSkillSource& source) noexcept {
        // Exact explicit profile and full source equality; no catalog promotion
        // or learned/turn authority is inferred from these geometry checks.
        if(r.source!=source || !valid_source(source) || r.kind<0 || r.kind>=4)return false;
        const auto profile=native_taiwan_skill_source_matches(source,NativeTaiwanSkillProfile::Historical448)?
            NativeTaiwanSkillProfile::Historical448:NativeTaiwanSkillProfile::Installed453;
        const auto counts=native_taiwan_skill_bank_counts(profile);
        if(r.definition_id<1 || r.definition_id>counts[std::size_t(r.kind)])return false;
        std::int64_t ordinal=r.definition_id-1;
        for(std::size_t i=0;i<std::size_t(r.kind);++i)ordinal+=counts[i];
        return r.raw_record.size()==110 && r.raw_record[0]==r.definition_id && r.raw_record[1]==r.kind &&
            r.source_record_index==ordinal && hex_sha(r.record_sha256) &&
            r.source_offset==8+r.kind*0x6e04+(r.definition_id-1)*110;
    }
    static bool valid_roster_row(const RosterSkillRow& row,const NativeSkillSource& source) noexcept {
        if(row.learned_count>entry_capacity || row.auxiliary_count>entry_capacity ||
           row.learned_definitions.size()!=entry_capacity || row.auxiliary_definitions.size()!=entry_capacity)return false;
        for(const auto& definition:row.learned_definitions)
            if(definition && !valid_definition(*definition,source))return false;
        for(const auto& definition:row.auxiliary_definitions)
            if(definition && !valid_definition(*definition,source))return false;
        return true;
    }
    static bool valid(const Snapshot& s) noexcept {
        if(s.bank_count>bank_capacity || !valid_source(s.catalog_source))return false;
        if(s.last_control86 && ((*s.last_control86)[0]!=0x86 || (*s.last_control86)[1]!=5))return false;
        for(const auto& bank:s.banks) {
            if(bank.entry_count>entry_capacity || bank.definitions.size()!=bank.entry_count ||
               bank.auxiliary_count>entry_capacity ||
               bank.auxiliary_definitions.size()!=bank.auxiliary_count)return false;
            for(std::size_t i=0;i<bank.definitions.size();++i) {
                const auto& r=bank.definitions[i];
                if(!valid_definition(r,s.catalog_source) || (bank.raw_words[i]&0x4000u)!=0 ||
                   (bank.raw_words[i]&0x3fffu)!=key(r))return false;
            }
            for(const auto& r:bank.auxiliary_definitions)
                if(r && !valid_definition(*r,s.catalog_source))return false;
        }
        if(s.secondary) {
            for(const auto& bank:s.secondary->banks) {
                if(bank.entry_count<0 || std::size_t(bank.entry_count)>secondary_entry_capacity)return false;
                for(std::size_t i=0;i<secondary_entry_capacity;++i) {
                    const auto& r=bank.definitions[i];
                    if(r && (!valid_definition(*r,s.catalog_source) ||
                       (i<std::size_t(bank.entry_count) && (bank.raw_words[i]&0x3fffu)!=key(*r))))return false;
                }
            }
        }
        if(s.roster_rows) {
            for(std::size_t i=0;i<bank_capacity;++i) {
                const auto& row=(*s.roster_rows)[i];const auto& bank=s.banks[i];
                if(!valid_roster_row(row,s.catalog_source) || row.row_key!=bank.row_key ||
                   row.auxiliary_count!=bank.auxiliary_count ||
                   !std::equal(bank.auxiliary_definitions.begin(),bank.auxiliary_definitions.end(),
                       row.auxiliary_definitions.begin()))return false;
            }
        }
        return true;
    }
};
}
