#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c: WORLD4691D9 ->4A3320; E5 is logical9, not a D6 reply contract.
// Only family3 ->4A5A40 is qualified here. Other families remain opaque.
// These are receive-side write operands, never a pet grant or server rule.
struct RecoveredE5Update {
    static constexpr std::uint8_t opcode=0xe5;
    static constexpr std::size_t logical_size=9;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct FieldWrite {
        std::uint8_t body_offset,bytes;
        std::uint32_t mask,inserted_bits;
    };
    struct Pet2Writes {
        std::array<FieldWrite,2> fields{};
        std::uint8_t count{};
        // Selector2 also updates inventory DWORD bits8..14. A complete
        // native operation cannot be represented by changing FB alone.
        bool inventory_packed_field_changed{};
    };
    class Record {
    public:
        std::uint8_t family_raw() const noexcept {return bytes_[6]>>6;}
        std::uint8_t selector_raw() const noexcept {return bytes_[6]&0x3f;}
        std::uint8_t pet_slot_raw() const noexcept {return bytes_[5];}
        bool native_pet_slot_range() const noexcept {
            return pet_slot_raw()>=42 && pet_slot_raw()<=44;
        }
        std::uint32_t value_raw() const noexcept {
            return std::uint32_t{bytes_[1]}|(std::uint32_t{bytes_[2]}<<8)|
                (std::uint32_t{bytes_[3]}<<16)|(std::uint32_t{bytes_[4]}<<24);
        }
        std::span<const std::uint8_t,2> opaque_tail() const noexcept {
            return std::span<const std::uint8_t,logical_size>(bytes_).subspan<7,2>();
        }
        // Conditional operands only: native4A5A40 additionally requires an
        // existing72-byte row, nonzero key, stored slot42..44, inclusive key
        // range6D61..7F58 and actual459A60 metadata lookup. It does not compare
        // stored slot to incoming slot. HUD/panel child effects are separate.
        std::optional<Pet2Writes> pet2_field_writes() const noexcept {
            if(family_raw()!=3 || !native_pet_slot_range())return {};
            Pet2Writes out;
            const auto value=value_raw();
            const auto add=[&](std::uint8_t offset,std::uint8_t width,
                               std::uint32_t mask,std::uint32_t bits) {
                out.fields[out.count++]={offset,width,mask,bits&mask};
            };
            switch(selector_raw()) {
            case 0:add(3,1,0xff,value);break;
            case 1:add(8,4,0xffffff,value);break;
            case 2:add(4,4,0xfe000000,(value&0x7f)<<25);
                out.inventory_packed_field_changed=true;break;
            case 3:add(4,4,0x3fff,value);break;
            case 4:add(12,4,0x3fff,value);break;
            case 5:add(4,4,0x1ffc000,(value&0x7ff)<<14);break;
            case 6:add(12,4,0x1ffc000,(value&0x7ff)<<14);break;
            case 7:add(0x22,1,0xff,value);break;
            case 8:add(0x24,2,0xffff,value);break;
            case 9:add(0x26,2,0xffff,value);break;
            case 10:add(0x28,2,0xffff,value);break;
            case 11:add(0x2a,2,0xffff,value);break;
            case 17:add(0x10,2,0xffff,value);break;
            case 18:add(0x12,2,0xffff,value);break;
            // Actual4A5C50 falls through4A5C54/57: selector19 writes both.
            case 19:add(0x14,2,0xffff,value);[[fallthrough]];
            case 20:add(0x16,2,0xffff,value);break;
            case 34:add(0x23,1,0xff,value);break;
            default:break; // Native still reaches conditional panel refresh.
            }
            return out;
        }
    private:
        friend struct RecoveredE5Update;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord raw;std::copy(bytes.begin(),bytes.end(),raw.begin());return Record(raw);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
