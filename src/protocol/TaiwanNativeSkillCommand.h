#pragma once

#include "db/NativeSkillCatalog.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <iterator>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace god2 {

// Same149c native C35 skill grammar: 51EAD0/51E910/519075..5191EE,
// scope tables571658/571BB0 and formation table59BE78. This component does
// not authorize learned skills, battle grants, charge MP or settle combat.
// Source owners must qualify the full catalog row and every supplied current
// observation before and after use. It does not replace CUSTOM-0086 selectors.
class TaiwanNativeSkillCommand final {
public:
    static constexpr std::size_t logical_size=17;
    static constexpr char image_sha256[]=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";

    struct WireRecord {
        std::array<std::uint8_t,logical_size> logical;
        std::uint8_t actor_position() const noexcept {return logical[1];}
        bool continuation() const noexcept {return logical[2]==0x83;}
        std::uint8_t side_flag() const noexcept {return logical[3];}
        std::uint16_t first_word() const noexcept {return word(logical,5);}
        std::uint16_t second_word() const noexcept {return word(logical,7);}
        std::uint32_t context() const noexcept {return dword(logical,9);}
        std::uint32_t raw_operand() const noexcept {return dword(logical,13);}
        std::uint8_t kind() const noexcept {return logical[14];}
        std::uint8_t definition_id() const noexcept {return logical[13];}
        bool operator==(const WireRecord&) const=default;
    };

    // Network-thread shape only. Do not consult a catalog or invent actor
    // bounds here. Preserve opaque byte4 and the entire operand13..16.
    static std::optional<WireRecord> parse_wire(std::span<const std::uint8_t> r) noexcept {
        if(r.size()!=logical_size || r[0]!=0x35 ||
           (r[2]!=3 && r[2]!=0x83) || r[3]>1) return std::nullopt;
        WireRecord out;
        std::copy(r.begin(),r.end(),out.logical.begin());
        return out;
    }
    // A sequence key is structural, not a wire nonce or replay capability.
    // Opaque bytes and targets are preserved but are not semantic group identity.
    static bool same_sequence(const WireRecord& a,const WireRecord& b) noexcept {
        return a.actor_position()==b.actor_position() && a.side_flag()==b.side_flag() &&
            a.context()==b.context() && a.raw_operand()==b.raw_operand();
    }

    struct Qualification {
        // Mandatory actual controlled actor/selector/context and candidate
        // observations from the real owner. No default zero means qualified.
        std::optional<std::uint8_t> actor_position;
        std::optional<std::uint8_t> side_flag;
        std::optional<std::uint32_t> context;
        std::optional<std::array<std::uint16_t,2>> target_candidates;
        // Scope17 restores saved friendly occupancy, not a calculated range.
        std::optional<std::uint16_t> restored_friendly_occupancy;
        // Formation full emitted source order, including any retained source.
        // Identity-retained entries require a real native state supplier;
        // received HP==0 is not substituted for native actor state+1EA==9.
        std::optional<std::vector<std::uint16_t>> formation_sources;
        std::optional<std::vector<std::uint16_t>> formation_identity_sources;
    };
    enum class Form {Ordinary,Ordered,CombinedSelfFriendly,Formation};
    struct Assignment {
        std::uint16_t source,destination;
        bool operator==(const Assignment&) const=default;
    };
    class Command {
    public:
        Form form() const noexcept {return form_;}
        const NativeSkillRecord& definition() const noexcept {return definition_;}
        const std::vector<WireRecord>& records() const noexcept {return records_;}
        // Ordered preserves duplicate targets. Ordinary/combined enumerate
        // the wire mask; that mask cannot recover duplicate click history.
        const std::vector<std::uint8_t>& targets() const noexcept {return targets_;}
        const std::vector<std::uint8_t>& ordered_targets() const noexcept {return targets_;}
        const std::vector<Assignment>& assignments() const noexcept {return assignments_;}
    private:
        friend class TaiwanNativeSkillCommand;
        Command(NativeSkillRecord d,std::vector<WireRecord> r,Form f)
            :definition_(std::move(d)),records_(std::move(r)),form_(f){}
        NativeSkillRecord definition_;
        std::vector<WireRecord> records_;
        Form form_;
        std::vector<std::uint8_t> targets_;
        std::vector<Assignment> assignments_;
    };

    // Game-owner pure projection only; inputs must already be current-owned
    // snapshots. No external callbacks, database reads or mutation take place.
    // No incomplete continuation prefix becomes a complete Command.
    static std::optional<Command> parse_qualified(std::span<const WireRecord> input,
        const NativeSkillRecord& definition,const Qualification& q) {
        if(input.empty() || !valid_definition(definition) ||
           !q.actor_position || !q.side_flag || !q.context || !q.target_candidates ||
           *q.actor_position>=14 || *q.side_flag>1 ||
           (((*q.target_candidates)[0]|(*q.target_candidates)[1])&0xc000u))
            return std::nullopt;
        const auto& raw=definition.raw_record;
        const bool formation=raw[1]==2 && word(raw,0x3e)!=0x0ff5;
        const auto scope=raw[0x45];
        const auto expected=scope==13?2u:scope==14?7u:scope==16?3u:1u;
        // Bound allocation by the selected grammar. Nine is only the number
        // of distinct integer source slots5..13 in this supported subset,
        // not a recovered native batch-capacity or general packet limit.
        if(formation){
            if(!q.formation_sources || input.size()!=q.formation_sources->size() ||
               input.size()>14u-5u) return std::nullopt;
        }else if(input.size()!=expected) return std::nullopt;
        Command out(definition,std::vector<WireRecord>(input.begin(),input.end()),Form::Ordinary);
        const auto& first=out.records_.front();
        for(std::size_t i=0;i<out.records_.size();++i){
            const auto& r=out.records_[i];
            if(!parse_wire(r.logical) || !same_sequence(first,r) ||
               r.actor_position()!=*q.actor_position || r.side_flag()!=*q.side_flag ||
               r.context()!=*q.context || r.raw_operand()!=
                   (std::uint32_t(definition.definition_id)|(std::uint32_t(definition.kind)<<8)) ||
               r.continuation()!=(i+1<out.records_.size())) return std::nullopt;
        }
        if(formation) return parse_formation(std::move(out),q);
        if(expected>1){
            out.form_=Form::Ordered;
            int side=-1;
            for(const auto& r:out.records_){
                const auto a=r.first_word(),b=r.second_word();
                if(((a|b)&0xc000u) || std::popcount(a)+std::popcount(b)!=1)
                    return std::nullopt;
                const int this_side=a?0:1;
                const auto mask=a?a:b;
                if((side!=-1 && side!=this_side) ||
                   (mask&(*q.target_candidates)[this_side])!=mask) return std::nullopt;
                side=this_side;
                out.targets_.push_back(static_cast<std::uint8_t>(14*this_side+std::countr_zero(mask)));
            }
            return out;
        }
        const auto a=first.first_word(),b=first.second_word();
        if(((a|b)&0xc000u) || (!a && !b) || (a && b)) return std::nullopt;
        const auto self=static_cast<std::uint16_t>(1u<<*q.actor_position);
        if(scope==17){
            if(raw[1]!=0 || raw[0]!=107 || !q.restored_friendly_occupancy || b ||
               (*q.restored_friendly_occupancy&0xc000u) ||
               !(*q.restored_friendly_occupancy&self) || !(a&self) ||
               (a&*q.restored_friendly_occupancy)!=a || std::popcount(a)>2)
                return std::nullopt;
            out.form_=Form::CombinedSelfFriendly;
        }else{
            const auto side=a?0u:1u;
            const auto mask=a?a:b;
            const auto candidates=(*q.target_candidates)[side];
            if(scope==11){if(a!=self || b || !(candidates&self)) return std::nullopt;}
            else if(scope==1 || scope==12){
                if(std::popcount(mask)!=1 || (mask&candidates)!=mask || (scope==12 && side))
                    return std::nullopt;
            }else if(scope>=2 && scope<=4){
                // The combined wire OR cannot attest distinct click count.
                if(std::popcount(mask)>scope || (mask&candidates)!=mask) return std::nullopt;
            }else if(scope==5){
                // 51E9B5 writes full3FFF, including empty positions. Candidate
                // observations select a side; they never clip this wire mask.
                if(mask!=0x3fff || !candidates) return std::nullopt;
            }
            else if(!pattern(scope,mask,candidates)) return std::nullopt;
        }
        for(unsigned i=0;i<14;++i){
            if(a&(1u<<i)) out.targets_.push_back(static_cast<std::uint8_t>(i));
            if(b&(1u<<i)) out.targets_.push_back(static_cast<std::uint8_t>(14+i));
        }
        return out;
    }

private:
    static std::uint16_t word(std::span<const std::uint8_t> r,std::size_t at) noexcept {
        return static_cast<std::uint16_t>(r[at]|(std::uint16_t{r[at+1]}<<8));
    }
    static std::uint32_t dword(std::span<const std::uint8_t> r,std::size_t at) noexcept {
        return std::uint32_t{word(r,at)}|(std::uint32_t{word(r,at+2)}<<16);
    }
    static bool hex_sha(const std::string& s) noexcept {
        return s.size()==64 && std::all_of(s.begin(),s.end(),[](unsigned char c){
            return (c>='0' && c<='9') || (c>='a' && c<='f');});
    }
    static bool valid_definition(const NativeSkillRecord& r) noexcept {
        const auto& s=r.source;
        const bool historical=native_taiwan_skill_source_matches(s,NativeTaiwanSkillProfile::Historical448);
        if(!historical && !native_taiwan_skill_source_matches(s,NativeTaiwanSkillProfile::Installed453))return false;
        const auto counts=native_taiwan_skill_bank_counts(historical?
            NativeTaiwanSkillProfile::Historical448:NativeTaiwanSkillProfile::Installed453);
        if(r.kind<0 || r.kind>=4 || r.definition_id<1 || r.definition_id>counts[std::size_t(r.kind)])return false;
        std::int64_t ordinal=r.definition_id-1;
        for(std::size_t i=0;i<std::size_t(r.kind);++i)ordinal+=counts[i];
        return r.raw_record.size()==110 && r.raw_record[0]==r.definition_id && r.raw_record[1]==r.kind &&
            r.source_record_index==ordinal && r.source_offset==8+r.kind*0x6e04+(r.definition_id-1)*110 &&
            hex_sha(r.record_sha256);
    }
    static bool pattern(std::uint8_t scope,std::uint16_t mask,std::uint16_t candidates) noexcept {
        struct Row {std::uint8_t scope,anchor;std::uint16_t mask;};
        static constexpr Row rows[]={
            {6,0,0x1f},{6,5,0x1e0},{6,9,0xe00},{6,12,0x3000},
            {7,1,0x62},{7,2,0xc4},{7,3,0x188},{7,6,0x640},{7,7,0xc80},{7,10,0x3400},
            {8,0,0x1221},{8,1,0x2442},{8,3,0x1488},{8,4,0x2910},
            {9,10,0x34c0},{10,10,0x3ec0},
            {15,5,0x23},{15,6,0x46},{15,7,0x8c},{15,8,0x118},{15,9,0x260},
            {15,10,0x4c0},{15,11,0x980},{15,12,0x1600},{15,13,0x2c00}};
        return std::any_of(std::begin(rows),std::end(rows),[&](const Row& r){
            return r.scope==scope && r.mask==mask && (candidates&(1u<<r.anchor));});
    }
    static std::optional<Command> parse_formation(Command out,const Qualification& q) {
        if(*q.side_flag || !q.formation_sources || !q.formation_identity_sources ||
           q.formation_sources->size()!=out.records_.size()) return std::nullopt;
        const auto id=out.definition_.definition_id;
        // Accepted native wire grammar, not a complete assignment policy or
        // proof that any actor may move. Exact mode0 rows at571338..5713BC;
        // later aliases are pointer-table aliases. Mode1 requires an
        // unavailable actual DB4 category supplier.
        const int row=id>=1 && id<=18?static_cast<int>((id-1)/3):
            id>=19 && id<=38?6+static_cast<int>((id-19)/4):
            id>=72 && id<=76?6+static_cast<int>(id-72):
            id>=77 && id<=82?static_cast<int>(id-77):
            id>=83 && id<=87?6+static_cast<int>(id-83):-1;
        if(row<0) return std::nullopt;
        static constexpr std::uint16_t destinations[11][5]={
            {6,7,9,10,11},{6,7,10,12,13},{5,8,10,12,13},{5,8,9,10,11},
            {5,6,7,8,10},{9,10,11,12,13},{6,7,8,11,13},{7,9,10,11,12},
            {6,7,9,12,13},{7,8,9,10,12},{6,7,8,10,11}};
        std::uint16_t seen_source=0,seen_destination=0,identity=0;
        for(const auto source:*q.formation_identity_sources){
            if(source<5 || source>=14 || (identity&(1u<<source))) return std::nullopt;
            identity=static_cast<std::uint16_t>(identity|(1u<<source));
        }
        out.form_=Form::Formation;
        for(std::size_t i=0;i<out.records_.size();++i){
            const auto source=out.records_[i].first_word(),destination=out.records_[i].second_word();
            if(source<5 || source>=14 || destination<5 || destination>=14 ||
               source!=(*q.formation_sources)[i] || (seen_source&(1u<<source)) ||
               (seen_destination&(1u<<destination))) return std::nullopt;
            if(identity&(1u<<source)){if(destination!=source) return std::nullopt;}
            else if(std::find(std::begin(destinations[row]),std::end(destinations[row]),destination)==
                    std::end(destinations[row])) return std::nullopt;
            seen_source=static_cast<std::uint16_t>(seen_source|(1u<<source));
            seen_destination=static_cast<std::uint16_t>(seen_destination|(1u<<destination));
            out.assignments_.push_back({source,destination});
        }
        if((identity&seen_source)!=identity) return std::nullopt;
        return out;
    }
};
}
