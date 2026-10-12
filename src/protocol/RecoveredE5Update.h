#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c: WORLD4691D9 ->4A3320; E5 is logical9, not a D6 reply contract.
// Direct operands: family0 inventory, family1 world scalars, family2 E3,
// family3 FB. Joint inventory, metadata, clock, HUD/GUI effects are separate.
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
    struct Pet1Writes {
        std::array<FieldWrite,1> fields{};
        std::uint8_t count{};
        bool inventory_property_low_byte_changed{};
    };
    enum class InventoryIndexSource { IncomingSignedByte, ContextSignedByte8 };
    struct InventoryWrite {
        InventoryIndexSource index_source;
        // Relative to native24-byte row at world+8560C, not20-byte metadata.
        FieldWrite field;
    };
    struct WorldScalarWrite {
        std::uint8_t world_offset;
        std::uint32_t mask,inserted_bits;
    };
    struct InventorySyncRead {
        std::uint8_t current_world_offset,right_shift;
        std::uint32_t value_mask;
        std::uint8_t target_row_offset,bytes;
        // Index and value are reread after opaque control/clock calls. This
        // descriptor supplies neither that current index nor a final value.
        InventoryIndexSource index_source=InventoryIndexSource::ContextSignedByte8;
    };
    class Record {
    public:
        std::uint8_t family_raw() const noexcept {return bytes_[6]>>6;}
        std::uint8_t selector_raw() const noexcept {return bytes_[6]&0x3f;}
        std::uint8_t pet_slot_raw() const noexcept {return bytes_[5];}
        std::int16_t incoming_signed_slot() const noexcept {
            const auto raw=pet_slot_raw();
            return raw<128 ? raw : static_cast<std::int16_t>(raw)-256;
        }
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
        // No mutation: native inventory writes are conditional on each family.
        // Family0 has no slot range guard. Family1's later rereads are
        // described separately, not predicted from V. Pet families require the
        // existing row and successful metadata guards described separately.
        std::optional<InventoryWrite> inventory_field_write() const noexcept {
            const auto value=value_raw();
            const auto make=[&](InventoryIndexSource index,std::uint8_t offset,
                               std::uint8_t width,std::uint32_t mask,std::uint32_t bits) {
                return InventoryWrite{index,{offset,width,mask,bits&mask}};
            };
            const auto incoming=InventoryIndexSource::IncomingSignedByte;
            switch(family_raw()) {
            case 0:
                if(selector_raw()==30)return make(incoming,0x12,2,0xffff,value);
                if(selector_raw()==31)return make(incoming,0x14,2,0x7fff,value);
                break;
            case 2:
                if(native_pet_slot_range() && selector_raw()==2)
                    return make(incoming,0x14,4,0xff,value);
                break;
            case 3:
                if(native_pet_slot_range() && selector_raw()==2)
                    return make(incoming,0x14,4,0x7f00,(value&0x7f)<<8);
                break;
            }
            return {};
        }
        std::optional<InventorySyncRead> family1_inventory_sync_read() const noexcept {
            if(family_raw()!=1 || pet_slot_raw()!=45)return {};
            if(selector_raw()>=21 && selector_raw()<=24)
                return InventorySyncRead{0x44,static_cast<std::uint8_t>((selector_raw()-21)*7),
                    0x7f,static_cast<std::uint8_t>(0x10+selector_raw()-21),1};
            if(selector_raw()==28)return InventorySyncRead{0x4c,0,0x3ffff,0x0c,4};
            return {};
        }
        // 4D6DD0 only admits body4==45. Scalar operands do not include the
        // old/new marker comparisons, flag/timestamp writes, context-indexed
        // inventory sync,4D7E40/507150 or4D53F0/4D5970 child effects.
        std::optional<WorldScalarWrite> world_scalar_write() const noexcept {
            if(family_raw()!=1 || pet_slot_raw()!=45)return {};
            const auto value=value_raw();
            switch(selector_raw()) {
            case 21:return WorldScalarWrite{0x44,0x7f,value&0x7f};
            case 22:return WorldScalarWrite{0x44,0x3f80,(value&0x7f)<<7};
            case 23:return WorldScalarWrite{0x44,0x1fc000,(value&0x7f)<<14};
            case 24:return WorldScalarWrite{0x44,0xfe00000,(value&0x7f)<<21};
            case 25:return WorldScalarWrite{0x44,0x10000000,(value&1)<<28};
            case 26:return WorldScalarWrite{0x4c,0x3fc0000,(value&0xff)<<18};
            case 27:return WorldScalarWrite{0x48,0x3ffff,value&0x3ffff};
            case 28:return WorldScalarWrite{0x4c,0x3ffff,value&0x3ffff};
            case 29:return WorldScalarWrite{0x48,0xfffc0000,(value&0x3fff)<<18};
            case 32:return WorldScalarWrite{0x44,0xc0000000,(value&3)<<30};
            default:return {}; // Matching slot can still refresh the panel.
            }
        }
        // 4A33F0 updates existing E3 body52 only after incoming/stored slots
        //42..44, nonzero key,3391..3778 or5DC1..6D60 and459A60 lookup.
        // It does not compare the two slots. Inventory/HUD/GUI effects remain
        // distinct. Offsets here belong to E3; FB layout cannot be substituted.
        std::optional<Pet1Writes> pet1_field_writes() const noexcept {
            if(family_raw()!=2 || !native_pet_slot_range())return {};
            Pet1Writes out;
            const auto value=value_raw();
            const auto add=[&](std::uint8_t offset,std::uint8_t width,
                               std::uint32_t mask,std::uint32_t bits) {
                out.fields[out.count++]={offset,width,mask,bits&mask};
            };
            switch(selector_raw()) {
            case 0:add(0x23,1,0xff,value);break;
            case 1:add(0x18,4,0xfffc00,(value&0x3fff)<<10);break;
            case 2:add(0x22,1,0xff,value);out.inventory_property_low_byte_changed=true;break;
            case 3:add(0,2,0xffff,value);break;
            case 4:add(2,2,0xffff,value);break;
            case 5:add(4,2,0xffff,value);break;
            case 6:add(6,2,0xffff,value);break;
            case 7:add(0x21,1,0xff,value);break;
            case 8:add(0x10,4,0x3ff000,(value&0x3ff)<<12);break;
            case 9:add(0x10,4,0xffc00000,(value&0x3ff)<<22);break;
            case 10:add(0x14,4,0x3ff000,(value&0x3ff)<<12);break;
            case 11:add(0x14,4,0xffc00000,(value&0x3ff)<<22);break;
            case 12:add(0x18,4,0xff000000,(value&0xff)<<24);break;
            case 13:add(0x1e,1,0xff,value);break;
            case 14:add(0x1f,1,0xff,value);break;
            case 15:add(0x20,1,0xff,value);break;
            case 16:add(0x24,2,0xffff,value);break;
            case 17:add(8,4,0xfff,value);break;
            case 18:add(12,4,0xfff,value);break;
            case 19:add(16,4,0xfff,value);break;
            case 20:add(20,4,0xfff,value);break;
            case 33:add(0x30,4,0xffffffff,value);break;
            default:break; // Conditional native refresh still runs.
            }
            return out;
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
