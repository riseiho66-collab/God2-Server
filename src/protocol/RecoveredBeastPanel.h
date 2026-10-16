#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include "protocol/RecoveredCompanionControl6B.h"

namespace god2 {
// Current mapped image 149c1b45...: 497EE0/4D8F50 producers;
// 469D46 -> 4A0840 and 469D6C -> 4A0970 receivers.
// PET/beast panel contract, distinct from COM/E3 combat companions.
// This codec does not authorize acquisition, activation, food consumption,
// teleportation, exploration, lifetime changes or actor appearance changes.
// OwnedBeastPanelService connects a custom25->4B/4C display-only route.
// Controls/food/gameplay remain open; codec recovery is not route completion.
struct RecoveredBeastPanel {
    static constexpr std::uint8_t control7_opcode=0x6c, control8_opcode=0x9d, food_opcode=0x6b;
    static constexpr std::uint8_t snapshot_opcode=0x4c, delta_opcode=0x4d;
    static constexpr std::size_t request_size=5, snapshot_size=17, delta_size=9;
    enum class Control : std::uint8_t {Seven=control7_opcode,Eight=control8_opcode};
    struct Request {
        Control control;
        std::uint16_t metadata_key;
        // Primary+448E, also assigned to UI+85ABD by S2C4C. Its complete
        // server selection/ownership domain has not yet been recovered.
        std::uint8_t selector;
    };
    // 4A0470 control11 (ProgramMsg96 food button) calls
    // 4972F0(0,selector,slot). The producer REVERSES formal arguments:
    // C2S wire body is slot,selector,0. Earlier V1 notes/code mislabeled it.
    // Opcode6B is shared with other companion lanes. This models only the
    // beast lane0 and must not swallow combat-pet lane1/3 as beast requests.
    // Lane0 sends the dragged food slot plus the live selected-panel byte
    // (UI+85ABD). Native S2C41 also compares that byte with a physical slot
    // when closing the panel, but this does not establish a persistent
    // selector==inventory_slot invariant for an owned beast.
    struct FoodRequest {std::uint8_t inventory_slot,selector;};
    using SnapshotBytes=std::array<std::uint8_t,snapshot_size>;
    using DeltaBytes=std::array<std::uint8_t,delta_size>;
    using InventoryMetadata=std::array<std::uint8_t,20>;
    struct Snapshot {
        SnapshotBytes bytes;
        bool operator==(const Snapshot&) const=default;
        std::uint16_t metadata_key() const noexcept {return word(bytes,1);}
        std::uint8_t selector() const noexcept {return bytes[3];}
        // Native4A0790 control5 formats this BYTE with literal denominator100
        // using "%d/%d". No clamp, loyalty name or gameplay cap is established.
        std::uint8_t percentage_display_raw() const noexcept {return bytes[4];}
        // Native4A0903..4A095C builds a NEW fully initialized20-byte display
        // item from this key: DWORD0=key|0x000C0000 (class DECIMAL12), BYTE18
        // =logical13, WORD10=((DWORDlogical9>>24)&7)<<13, all other bits zero.
        // 4A0610 copies all20 to UI+23D604 for control1; distinct from PET class5 metadata;
        // WORD10 high3 has no qualified palette meaning or storage/grant rule.
        std::uint16_t carried_item_key() const noexcept {return word(bytes,5);}
        // Native4A0700 multiplies this WORD by FLOAT0.01 and formats%6.2f
        // plus ProgramMsg362 percent sign. NOT a qualified lifetime unit.
        std::uint16_t percentage_word_raw() const noexcept {return word(bytes,7);}
        // Native4A07E0 control6 formats raw low11 / bits11..21 via "%d/%d".
        // This does not name fatigue, prove numerator<=denominator or a cap.
        std::uint16_t meter_numerator_raw11() const noexcept {return dword(bytes,9)&0x7ff;}
        std::uint16_t meter_denominator_raw11() const noexcept {return (dword(bytes,9)>>11)&0x7ff;}
        // Values0/1/2 select ProgramMsg645/646/647; native initialization
        // fills only three label pointers. Value3 has no qualified label.
        // ProgramMsg96 is a separate food label, not a fourth beast kind.
        std::uint8_t kind_display_raw2() const noexcept {return (dword(bytes,9)>>22)&3;}
        bool control7_alternate() const noexcept {return (dword(bytes,9)&0x08000000)!=0;}
        bool control8_alternate() const noexcept {
            return (dword(bytes,9)&0x10c00000)==0x10800000;
        }
        // 4D body3 also writes inventory level BYTE+9. Panel retains low3.
        std::uint8_t level_display_raw3() const noexcept {return dword(bytes,9)>>29;}
    };
    struct Delta {
        DeltaBytes bytes;
        std::uint8_t inventory_slot() const noexcept {return bytes[1];}
        std::uint8_t percentage_display_raw() const noexcept {return bytes[2];}
        std::uint8_t inventory_palette_raw() const noexcept {return bytes[3];}
        std::uint8_t level_raw() const noexcept {return bytes[4];}
        std::uint16_t meter_numerator_raw11() const noexcept {return word(bytes,5)&0x7ff;}
        std::uint16_t percentage_word_raw() const noexcept {return word(bytes,7);}
    };
    static std::optional<Request> decode_request(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=request_size ||
           (bytes[0]!=control7_opcode && bytes[0]!=control8_opcode) || bytes[4]!=1)return {};
        // Native serializers copy a WORD and a BYTE. No additional key range,
        // selector limit or invented operation enum is inferred here.
        return Request{static_cast<Control>(bytes[0]),word(bytes,1),bytes[3]};
    }
    static std::array<std::uint8_t,request_size> encode_request(const Request& request) noexcept {
        return {static_cast<std::uint8_t>(request.control),static_cast<std::uint8_t>(request.metadata_key),
            static_cast<std::uint8_t>(request.metadata_key>>8),request.selector,1};
    }
    static std::optional<FoodRequest> decode_food_request(std::span<const std::uint8_t> bytes) noexcept {
        const auto request=RecoveredCompanionControl6B::decode(bytes);
        if(!request||request->lane!=0)return {};
        return FoodRequest{request->inventory_slot,request->selector};
    }
    static std::array<std::uint8_t,4> encode_food_request(const FoodRequest& request) noexcept {
        return RecoveredCompanionControl6B::encode({request.inventory_slot,request.selector,0});
    }
    static std::optional<Snapshot> decode_snapshot(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=snapshot_size || bytes[0]!=snapshot_opcode)return {};
        Snapshot result{};std::copy(bytes.begin(),bytes.end(),result.bytes.begin());return result;
    }
    static std::optional<Delta> decode_delta(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=delta_size || bytes[0]!=delta_opcode)return {};
        Delta result{};std::copy(bytes.begin(),bytes.end(),result.bytes.begin());return result;
    }
    // Native 4A0970 updates only these four selected-panel fields. Preserve
    // the key, selected instance, denominator, controls and every opaque bit.
    // Pure projection operation; callers must independently establish owner,
    // instance and current state. It neither commits nor grants a beast.
    static Snapshot apply_panel_delta(Snapshot before,const Delta& delta) noexcept {
        before.bytes[4]=delta.percentage_display_raw();
        before.bytes[7]=delta.bytes[7];before.bytes[8]=delta.bytes[8];
        auto packed=dword(before.bytes,9);
        packed=(packed&0x1ffff800)|((std::uint32_t{delta.level_raw()}&7)<<29)|delta.meter_numerator_raw11();
        for(unsigned i=0;i<4;++i)before.bytes[9+i]=static_cast<std::uint8_t>(packed>>(8*i));
        return before;
    }
    // Native A0A11..A0A8C is a separate inventory side effect of4D. The
    // inventory BYTE in body0 chooses a native slot, while body2 is a low3
    // palette value admitted only at1..6. It is distinct from the selected
    // panel's body2 instance selector BYTE (tooltip B9141 labels palette).
    // Given the already resolved slot's metadata20, mirror the native guards
    // and writes exactly. Other types/out-of-domain values leave it unchanged.
    // No slot bounds, ownership, persistence or food rule is established here.
    static InventoryMetadata apply_inventory_delta(InventoryMetadata before,const Delta& delta) noexcept {
        const auto palette=delta.inventory_palette_raw();
        if((before[2]&0x3f)!=5||palette<1||palette>6)return before;
        // UI+85610 already points at metadata0; do not subtract record+4
        // again. Native writes UI+8561A, +85618 highBYTE and +8561C.
        before[10]=static_cast<std::uint8_t>((before[10]&0xf8)|(palette&7));
        before[9]=delta.level_raw(); // full BYTE, unlike selected panel low3
        before[12]=delta.bytes[7];before[13]=delta.bytes[8];
        // WORD+12 is experience percent only when PET column27 lowBYTE=0.
        // Date-flagged definitions share bytes; this copy grants no EXP rule.
        return before;
    }
private:
    static std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t offset) noexcept {
        return static_cast<std::uint16_t>(bytes[offset]|(std::uint16_t{bytes[offset+1]}<<8));
    }
    static std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t offset) noexcept {
        return std::uint32_t{word(bytes,offset)}|(std::uint32_t{word(bytes,offset+2)}<<16);
    }
};
}
