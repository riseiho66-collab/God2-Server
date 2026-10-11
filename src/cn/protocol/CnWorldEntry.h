#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned CN consumers 00481190/00492E70, producer004815B0.
// These directional views preserve unknown bits; they are not a world handler,
// an authoritative actor model, or a serializer for a fabricated BEGINPLAY.
struct CnWorldEntry {
    struct Ready {
        std::uint16_t claimed_actor_handle;
        std::uint16_t native_language_value;
        // Current00405A30 returns0. This field cannot authenticate the client,
        // identify Windows language, or change an account's text preference.
    };
    static std::optional<Ready> parse_ready(std::span<const std::uint8_t> record) {
        if(record.size()!=5 || record[0]!=0x1c)return std::nullopt;
        return Ready{word(record,1),word(record,3)};
    }
    class BeginPlay {
    public:
        bool operator==(const BeginPlay&) const = default; // Exact retained36-byte native input.
        struct AppearanceInput {
            std::uint8_t category,family,variant_input,palette;
        };
        struct TransferLocation {
            std::uint8_t scene_mode;
            std::uint16_t x,y;
            bool native_reload_branch;
        };
        std::uint16_t actor_handle() const {return static_cast<std::uint16_t>(dword(payload_,0)&0x3fff);}
        // Normal00492E70 fields, not re-applied by CF's0048FCC0 branch.
        // Names denote native resource/renderer consumption, not gameplay
        // properties or issuer rules. All36 payload bytes remain preserved.
        std::uint8_t render_layer_fallback_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,0)>>14)&3);}
        std::uint8_t auxiliary_appearance_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,0)>>16)&0x7f);}
        std::uint8_t appearance_frame_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,0)>>23)&7);}
        bool native_world_render_flag_raw() const {return (dword(payload_,0)>>31)!=0;}
        std::uint8_t direction_raw() const {return static_cast<std::uint8_t>(dword(payload_,4)&7);}
        std::uint8_t native_direction() const {return static_cast<std::uint8_t>((direction_raw()+7)&7);}
        std::uint8_t unresolved_five_bit_metadata() const {return static_cast<std::uint8_t>((dword(payload_,4)>>3)&0x1f);}
        std::uint8_t mount_frame_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,4)>>8)&7);}
        std::uint8_t resource_string_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,4)>>11)&0x1f);}
        std::uint8_t mount_driver_selector_raw() const {return static_cast<std::uint8_t>((dword(payload_,4)>>16)&0xff);}
        // 0049357B -> actor+FC ->0044A470/00446BD0 -> UI+1615C.
        // Later1B's004411F0/00449450 use bits0..3 to disable four UI
        // options. Issuer/gameplay permissions and high bits remain unknown.
        std::uint8_t appearance_option_disable_mask_raw() const {return payload_[7];}
        std::optional<AppearanceInput> appearance_input(unsigned part) const {
            if(part>=4)return std::nullopt;
            const auto a=payload_[12+part*2],b=payload_[13+part*2];
            return AppearanceInput{static_cast<std::uint8_t>(a&15),static_cast<std::uint8_t>(a>>4),
                static_cast<std::uint8_t>(b&31),static_cast<std::uint8_t>(b>>5)};
        }
        std::array<std::uint8_t,8> appearance_components_raw() const {
            std::array<std::uint8_t,8> result;
            std::copy_n(payload_.begin()+12,8,result.begin());return result;
        }
        // Inputs only: slot1 variant is resolved using slot2 resources;
        // mounted slot3 uses family8/variant0. Native context may force
        // palette7; valid alternate key replaces the resource-selection path.
        // Never serialize resolved sprites/these getters as authoritative
        // equipment, copied TW profile data or gameplay attributes.
        std::uint16_t alternate_appearance_resource_key_raw() const {return word(payload_,32);}
        std::uint8_t render_layer_selector_raw() const {return payload_[34];}
        std::uint8_t render_secondary_layer_selector_raw() const {return payload_[35];}
        std::uint8_t map_family() const {return static_cast<std::uint8_t>(dword(payload_,24)&0x3f);}
        std::uint16_t map_index() const {return static_cast<std::uint16_t>((dword(payload_,24)>>6)&0x3ff);}
        std::uint8_t scene_mode() const {return static_cast<std::uint8_t>(dword(payload_,28)&3);}
        std::uint16_t x() const {return static_cast<std::uint16_t>((dword(payload_,28)>>2)&0x7fff);}
        std::uint16_t y() const {return static_cast<std::uint16_t>(dword(payload_,28)>>17);}
        // CF copies payload24..31 to0048EF40. Only when the old native
        // family/index match and bit16 is set does that consumer clear bit16
        // (which overlaps x's high bit) and suppress the reload branch. Normal
        // initial2A does not make this edit. Previous map is owner state,
        // never a guessed map, packet claim or freshly prepared destination.
        TransferLocation transfer_location(std::uint16_t previous_family,std::uint16_t previous_index) const {
            auto packed=dword(payload_,28);
            const bool reload=!(previous_family==map_family() && previous_index==map_index() && (packed&0x10000));
            if(!reload)packed&=~std::uint32_t{0x10000};
            return {static_cast<std::uint8_t>(packed&3),static_cast<std::uint16_t>((packed>>2)&0x7fff),
                static_cast<std::uint16_t>(packed>>17),reload};
        }
        bool initial_consumer_accepts_map_family() const {return map_family()!=0 && map_family()<17;}
        // Only compares bytes recovered at native callsites. Caller must still
        // prove connection/actor ownership and the correct transition phase.
        bool has_ready_handle(const Ready& ready) const {return ready.claimed_actor_handle==actor_handle();}
        // Opaque: dword0 bits26..30, bytes8..11, retained appearance bytes20..23
        // and map bytes26..27. No zero-fill or fabricated serializer. Actor+44
        // initialization also depends on old actor metadata (driver0 path).
        // Primary evidence: cn-beginplay-fields-agent-01/findings.json.
    private:
        friend struct CnWorldEntry;
        BeginPlay()=default;
        std::array<std::uint8_t,36> payload_{};
    };
    static std::optional<BeginPlay> read_begin_play(std::span<const std::uint8_t> record) {
        if(record.size()!=37 || record[0]!=0x2a)return std::nullopt;
        BeginPlay result;
        std::copy(record.begin()+1,record.end(),result.payload_.begin());
        return result;
    }
    class MapChange {
    public:
        std::uint8_t map_family() const {return static_cast<std::uint8_t>(word(payload_,0)&0x3f);}
        std::uint16_t map_index() const {return word(payload_,0)>>6;}
        std::uint16_t unresolved_word_2() const {return word(payload_,2);}
        std::uint32_t packed_location() const {return dword(payload_,4);}
        // 0048EF40 clears bit16 ONLY in its same-map branch. It overlaps x's
        // high bit: expose the raw word, do not silently strip it as padding.
        bool same_map_branch_bit() const {return (packed_location()&0x10000)!=0;}
    private:
        friend struct CnWorldEntry;
        MapChange()=default;
        std::array<std::uint8_t,8> payload_{};
    };
    static std::optional<MapChange> read_map_change(std::span<const std::uint8_t> record) {
        if(record.size()!=9 || record[0]!=0x61)return std::nullopt;
        MapChange result;
        std::copy(record.begin()+1,record.end(),result.payload_.begin());
        return result;
    }
private:
    static std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) {
        return static_cast<std::uint16_t>(bytes[at]|(std::uint16_t(bytes[at+1])<<8));
    }
    static std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t at) {
        return std::uint32_t(word(bytes,at))|(std::uint32_t(word(bytes,at+2))<<16);
    }
};
}
