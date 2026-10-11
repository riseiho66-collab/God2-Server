#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Lossless logical records from current 004AA040/004AA200/004AA660.
// No gameplay field defaults, formula, acquisition or owner authorization.
struct RecoveredDeityState {
    template<std::uint8_t Opcode,std::size_t Size> class Record {
    public:
        using Bytes=std::array<std::uint8_t,Size>;
        static constexpr auto opcode=Opcode;
        static constexpr auto logical_size=Size;
        static std::optional<Record> parse(std::span<const std::uint8_t> input) noexcept {
            if(input.size()!=Size || input[0]!=Opcode) return std::nullopt;
            Bytes bytes;std::copy(input.begin(),input.end(),bytes.begin());return Record(bytes);
        }
        const Bytes& encode() const noexcept { return bytes_; }
        std::uint8_t key_raw() const noexcept { return bytes_[1]; }
    private:
        explicit Record(Bytes bytes):bytes_(bytes) {}
        Bytes bytes_;
    };
    using Declaration=Record<0x30,19>;
    using Status=Record<0x31,29>;
    using Skill=Record<0x34,4>;
    struct Snapshot {
        Declaration declaration;
        Status status;
        std::vector<Skill> skills;
    };
    static constexpr std::size_t row_capacity=16;
    static constexpr std::size_t skill_capacity=100;
    // Current 004A9AC0 maps keys <=100 to key-1 and >100 to key-67,
    // all in bank5 (FieldComm3/Pic_God). Its 42 original ACT_DATA rows
    // contain34 native deities and8 profession portraits. Key100 maps99,
    // not a valid custom portrait. Never restore a row that can assert
    // at action.cpp:2289 when the deity panel/HUD is refreshed.
    static constexpr unsigned current_portrait_count=42;
    static constexpr unsigned current_native_template_count=34;
    static constexpr bool has_current_portrait(unsigned key) noexcept {
        return (key>=1 && key<=current_native_template_count) || (key>=101 && key<=108);
    }
    static constexpr std::array<std::uint16_t,4> current_skill_bank_counts{121,129,87,111};
    // CUSTOM-0058: installed client bridge supplies this one custom icon/effect.
    // Native bank counts and the original448 catalog remain unchanged.
    static constexpr bool is_custom_shunying(unsigned kind,unsigned id) noexcept {
        return kind==0 && id==126;
    }
    // CUSTOM-0059 installed custom skill; reserved122..149 remain excluded.
    static constexpr bool is_custom_thousand_bulls(unsigned kind,unsigned id) noexcept {
        return kind==0 && id==150;
    }
    // Current God2.exe 6bf75ef8: read-only inspection of all448 original icon
    // entries (private-deity-skills-20260927-06) found39 unavailable actions.
    // 004A9510 ->005068C0 ->0041E710 dereferences ACT_DATA+30 without a null
    // check; kind0/id120 reproduced the AV at0041E731. Raw codecs/catalogs
    // retain all448 definitions; only owned learned-state projection is gated.
    // This certifies display resources, not learning permission or casting.
    static constexpr bool has_current_skill_icon(unsigned kind,unsigned id) noexcept {
        if(kind>=current_skill_bank_counts.size() || id==0 || id>current_skill_bank_counts[kind]) return false;
        switch(kind) {
        case 0:return id<120;
        case 1:return id<73 || id>88;
        case 2:return id<63 || id>68;
        case 3:return id<84 || id>98;
        default:return false;
        }
    }
    static unsigned absolute_declaration_key(const Declaration& declaration) noexcept {
        const auto key=declaration.key_raw();return key<128 ? key : 256u-key;
    }
    // Caller must establish account/character ownership and source provenance.
    // Low keys use 00459A60(key+0xAF0), not the packet's ignored name bytes;
    // require their presence in an independently qualified current catalog.
    static bool valid(const Snapshot& snapshot,std::span<const std::uint8_t> qualified_template_keys,
                      const std::array<std::uint16_t,4>& bank_counts=current_skill_bank_counts) noexcept {
        const auto key=absolute_declaration_key(snapshot.declaration);
        if(!has_current_portrait(key) || snapshot.status.key_raw()!=key || snapshot.skills.size()>skill_capacity)
            return false;
        const auto& declaration=snapshot.declaration.encode();
        if(declaration[18]==1) return false; // duplicate/skill-reset branch, not restoration
        if(key<100) {
            if(std::find(qualified_template_keys.begin(),qualified_template_keys.end(),key)==qualified_template_keys.end())
                return false;
        } else if(std::find(declaration.begin()+2,declaration.begin()+18,0)==declaration.begin()+18) return false;
        for(std::size_t i=0;i<snapshot.skills.size();++i) {
            const auto& skill=snapshot.skills[i].encode();
            if(skill[1]!=key || (!is_custom_shunying(skill[2],skill[3]) && !is_custom_thousand_bulls(skill[2],skill[3]) &&
               (skill[2]>=bank_counts.size() || skill[3]==0 || skill[3]>bank_counts[skill[2]] ||
                !has_current_skill_icon(skill[2],skill[3]))))
                return false;
            for(std::size_t j=0;j<i;++j) if(snapshot.skills[j].encode()==skill) return false;
        }
        return true;
    }
    // S2C31 suffix also selects the matching row (source+D0/CF). Replaying
    // this exact stored record preserves opaque bytes and unknown scalars.
    static std::optional<Status> selection_response(std::uint8_t requested_key,const Snapshot& owned,
            std::span<const std::uint8_t> qualified_template_keys) noexcept {
        if(!valid(owned,qualified_template_keys) || requested_key!=owned.status.key_raw()) return std::nullopt;
        return owned.status;
    }
    // Restore only caller-supplied owned rows. Selected row is emitted last
    // because every S2C31 selects its row. Empty ownership emits no records.
    static std::optional<std::vector<std::uint8_t>> restore(
            std::span<const Snapshot> owned,std::optional<std::uint8_t> selected_key,
            std::span<const std::uint8_t> qualified_template_keys) {
        if(owned.size()>row_capacity || (owned.empty() && selected_key)) return std::nullopt;
        std::optional<std::size_t> selected;
        for(std::size_t i=0;i<owned.size();++i) {
            if(!valid(owned[i],qualified_template_keys)) return std::nullopt;
            const auto key=owned[i].status.key_raw();
            for(std::size_t j=0;j<i;++j) if(owned[j].status.key_raw()==key) return std::nullopt;
            if(selected_key==key) selected=i;
        }
        if(selected_key && !selected) return std::nullopt;
        std::vector<std::uint8_t> bytes;
        const auto append=[&](const auto& record) {
            const auto& raw=record.encode();bytes.insert(bytes.end(),raw.begin(),raw.end());
        };
        for(const auto& snapshot:owned) append(snapshot.declaration);
        for(std::size_t i=0;i<owned.size();++i) {
            if(selected!=i) append(owned[i].status);
            for(const auto& skill:owned[i].skills) append(skill);
        }
        if(selected) append(owned[*selected].status);
        return bytes;
    }
};
}
