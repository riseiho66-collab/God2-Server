#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <string_view>
#include <algorithm>
#include <optional>

namespace god2cn {
// Imported read-only from God2-Server-CN; original SHA/source and native
// consumer snapshots: cn-account-selection-owner-01/integration-manifest.json.
// S2C07: opcode + count + flags + two 36-byte character records.
// 00481640 copies the 74-byte payload; 00443080 / 00443640 consume it.
// This view documents recovered fields for authoritative state integration.
// It is not a writable game model and never supplies a fabricated character.
class CnCharacterSummary {
public:
    static constexpr std::size_t record_size=75;
    static constexpr std::size_t character_stride=36;
    static constexpr std::size_t capacity=2;
    struct AppearancePart {
        std::uint8_t category;
        std::uint8_t family;
        std::uint8_t variant;
        std::uint8_t color;
    };
    class Character {
    public:
        std::string_view name_bytes() const {
            const auto end=std::find(bytes_.begin(),bytes_.begin()+16,0);
            return {reinterpret_cast<const char*>(bytes_.data()),static_cast<std::size_t>(end-bytes_.begin())};
        }
        // Normal UI state13 at00447C32 selects the name prompt only for this
        // exact raw-byte marker. Consumer branch, not server permission or
        // a name-equivalence/uniqueness rule. Do not trim/convert its bytes.
        bool native_name_prompt_marker() const {
            const auto name=name_bytes();
            return name.size()>=3 && name.front()=='%' && name.back()=='%';
        }
        std::uint8_t level() const {return bytes_[16];}
        std::uint8_t profession_code() const {return bytes_[17];}
        // Byte 18 remains unnamed: copying a field is not proof of its meaning.
        std::uint8_t unresolved_byte_18() const {return bytes_[18];}
        std::uint8_t native_slot() const {return bytes_[19]&7;}
        // 00443640 labels these bits using ProgramMsg 505 (轉生次數).
        std::uint8_t reincarnation_count() const {return bytes_[19]>>3;}
        std::array<std::uint8_t,4> portrait_bits() const {
            return {bytes_[20],bytes_[21],bytes_[22],bytes_[23]};
        }
        std::optional<AppearancePart> appearance(unsigned part) const {
            if(part>=4)return std::nullopt;
            const auto a=bytes_[24+part*2], b=bytes_[25+part*2];
            return AppearancePart{static_cast<std::uint8_t>(a&15),static_cast<std::uint8_t>(a>>4),
                                  static_cast<std::uint8_t>(b&31),static_cast<std::uint8_t>(b>>5)};
        }
        std::array<std::uint8_t,4> location_bytes() const {
            return {bytes_[32],bytes_[33],bytes_[34],bytes_[35]};
        }
        std::array<std::uint8_t,character_stride> row_bytes() const {
            std::array<std::uint8_t,character_stride> result;
            std::copy(bytes_.begin(),bytes_.end(),result.begin());return result;
        }
        // LOCAL display mutation in00443640, applied after00443080 has
        // selected this row's four preview resources. This owned projection
        // never changes received07, common storage, level rules or reply bytes.
        // Repeated preview calls can observe these normalized local bytes;
        // the first resource selection observes the original row instead.
        std::array<std::uint8_t,character_stride> selection_panel_row_bytes() const {
            auto result=row_bytes();
            result[24]=static_cast<std::uint8_t>((result[24]&0xf0)|(result[24]&1));
            const auto a=static_cast<unsigned>(result[20])+(static_cast<unsigned>(result[21])<<8);
            const auto b=static_cast<unsigned>(result[22])+(static_cast<unsigned>(result[23])<<8);
            // Preserve low3/high8 of the first WORD; modulo7 only its bits5..7.
            const auto next_a=(a&0xff00)|(a&7)|((((a>>5)&7)%7)<<5);
            // Preserve low4 of the second WORD; modulo10 for each six-bit field.
            const auto next_b=(b&15)|((((b>>4)&63)%10)<<4)|(((b>>10)%10)<<10);
            result[20]=static_cast<std::uint8_t>(next_a);
            result[21]=static_cast<std::uint8_t>(next_a>>8);
            result[22]=static_cast<std::uint8_t>(next_b);
            result[23]=static_cast<std::uint8_t>(next_b>>8);
            if(result[16]==0xff)result[16]=1; // Existing native display sentinel only.
            return result;
        }
        // 0047D1C0 matches this nonzero byte against S2C06 payload0 when
        // selecting the endpoint. Its wider map/location semantics are pending.
        std::uint8_t endpoint_routing_key() const {return bytes_[32];}
    private:
        friend class CnCharacterSummary;
        explicit Character(std::span<const std::uint8_t,character_stride> bytes):bytes_(bytes){}
        std::span<const std::uint8_t,character_stride> bytes_;
    };
    static std::optional<CnCharacterSummary> read(std::span<const std::uint8_t> record) {
        if(record.size()!=record_size || record[0]!=0x07 || record[1]>capacity)return std::nullopt;
        for(unsigned index=0;index<record[1];++index) {
            const auto start=record.begin()+3+index*character_stride;
            if(std::find(start,start+16,0)==start+16)return std::nullopt;
        }
        CnCharacterSummary result;
        std::copy(record.begin()+1,record.end(),result.payload_.begin());return result;
    }
    std::uint8_t count() const {return payload_[0];}
    std::uint8_t flags() const {return payload_[1];}
    // Exact original07 snapshot, including flags and inactive/opaque rows.
    // Reconstruct only the already validated opcode, not missing payload data.
    std::array<std::uint8_t,record_size> record_bytes() const {
        std::array<std::uint8_t,record_size> record;
        record[0]=0x07;std::copy(payload_.begin(),payload_.end(),record.begin()+1);
        return record;
    }
    // Optional LOCAL output of00481640/0047F750 after accepted07. These
    // functions clear124 bytes, then copy only count/name/level/profession/
    // opaque18/low3 slot bits. Evidence: cn-summary-local-cache-01.
    // This is NOT an S2C1F payload or a server-issued character model.
    // Normal00444FE0 still selects from the raw07. Transfer0047E060 later
    // overwrites this entire local buffer with the independently supplied1F.
    std::array<std::uint8_t,124> local_selection_cache_bytes() const {
        std::array<std::uint8_t,124> cache{};
        cache[0]=count();
        for(unsigned index=0;index<count();++index) {
            const auto row=character(index);
            const auto name=row->name_bytes();
            const auto stride=index*40;
            // read() required a NUL within16 bytes; native copies through it.
            std::copy(name.begin(),name.end(),cache.begin()+4+stride);
            cache[32+stride]=row->level();
            cache[33+stride]=row->profession_code();
            cache[36+stride]=row->unresolved_byte_18();
            cache[38+stride]=row->native_slot();
        }
        return cache;
    }
    // 00481854..59 /0047F98E..93 store only this bit in network+4200,
    // copied account->world.00446BD0 uses it in its count0 and controls8/9
    // branches. Native consumer effect only: no recovered business role or
    // server issuance rule. Preserve flags() bits1..7 and do not invent values.
    // Evidence: cn-summary-opaque-agent-01/findings.json.
    // World owner binding via0048CAA0 ->004AC850 ->004B09C0 is recorded in
    // cn-summary-world-lineage-01. This also selects native world UI/request
    // variants; it still does not establish server entitlement/issuance.
    bool native_mode_bit0() const {return (flags()&1)!=0;}
    // Only the normal login UI state4 at00447A5B. This describes the
    // receiving client's next branch, not authoritative create permission.
    // count0 +mode1 selects SystemMessage1240 (owner+B2F58 table pointer,
    // offset4D74 within that table),
    // then004497F0(1). The older opaque-summary receipt called this
    // ProgramMsg1240 incorrectly; preserve it as history with the correction
    // in cn-summary-mode-resource-01. Actual native mode issuance stays open.
    enum class NativeNormalSelectionPath {
        ExistingRows,EmptyEnterCreationUI,EmptyDisplay1240AndReset
    };
    NativeNormalSelectionPath native_normal_selection_path() const {
        if(count()!=0)return NativeNormalSelectionPath::ExistingRows;
        return native_mode_bit0()?NativeNormalSelectionPath::EmptyDisplay1240AndReset:
                                 NativeNormalSelectionPath::EmptyEnterCreationUI;
    }
    static constexpr std::uint16_t native_empty_mode_system_message_id=1240;
    std::optional<Character> character(unsigned index) const {
        if(index>=count())return std::nullopt;
        return Character{std::span<const std::uint8_t,character_stride>(payload_.data()+2+index*character_stride,character_stride)};
    }
    // CF's extra selector (payloadCC, outside the204-byte login record) is
    // matched against07's native_slot by0044D5F0, not used as a row ordinal.
    // Unmatched remains absent; no implicit row0. Native searches first match;
    // the authoritative selection controller separately rejects duplicate slots.
    std::optional<unsigned> row_for_native_slot(unsigned slot) const {
        if(slot>7)return std::nullopt;
        for(unsigned index=0;index<count();++index)
            if(character(index)->native_slot()==slot)return index;
        return std::nullopt;
    }
    // Character views borrow this object's storage; do not keep after it moves.
private:
    std::array<std::uint8_t,74> payload_{};
};
}
