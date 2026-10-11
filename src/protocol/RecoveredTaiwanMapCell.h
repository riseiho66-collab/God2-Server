#pragma once
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Exact read-only TW VA00446FF0/RVA00046FF0 -> VA00436B60/RVA00036B60
// cell layouts from the pinned mapped image
// 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
// Native address values identify retained snapshots, never host pointers to
// dereference. Actual resource/scene/frame ownership remains a mandatory input.
struct RecoveredTaiwanMapCell {
    struct Buffer {
        std::uint32_t address;
        std::span<const std::uint8_t> bytes;
    };
    struct Input {
        Buffer map;
        std::optional<Buffer> grid;
        std::optional<Buffer> cells;
    };

    // Structural qualification only. This neither initializes a map nor
    // certifies resource identity, current cache center or walk permissions.
    static bool complete(const Input& input) {return layout(input).has_value();}

    // Return a real in-bounds raw byte unchanged, including 0/2/254/255.
    // Native fallback zero for unsupported/missing/out-of-bounds states is
    // deliberately not represented as a fabricated raw sample here.
    static std::optional<std::uint8_t> read(const Input& input,std::int32_t x,std::int32_t y) {
        const auto actual=layout(input);
        if(!actual)return std::nullopt;
        if(actual->window) {
            // The native DWORD subtract/add wrap before signed bounds checks.
            // Reproduce those bits without C++ signed overflow or narrowing.
            x=std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(x)-
                static_cast<std::uint32_t>(actual->center_x)+21u);
            y=std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(y)-
                static_cast<std::uint32_t>(actual->center_y)+21u);
        }
        if(x<0 || y<0 || x>=actual->width || y>=actual->height)return std::nullopt;
        const auto offset=static_cast<std::uint64_t>(y)*static_cast<std::uint32_t>(actual->width)+
            static_cast<std::uint32_t>(x);
        if(offset>=actual->cells.size())return std::nullopt;
        return actual->cells[static_cast<std::size_t>(offset)];
    }

private:
    struct Layout {
        bool window;
        std::int32_t center_x,center_y,width,height;
        std::span<const std::uint8_t> cells;
    };
    static bool retained(const Buffer& buffer) {
        // Bound the whole supplied snapshot's x86 address extent. Complete
        // raw-cell matrix qualification is separate from this pointer check.
        return buffer.address && !buffer.bytes.empty() &&
            buffer.bytes.size()<=std::uint64_t{0x100000000}-buffer.address;
    }
    static std::uint32_t word32(std::span<const std::uint8_t> bytes,std::size_t offset) {
        return std::uint32_t(bytes[offset]) | (std::uint32_t(bytes[offset+1])<<8) |
            (std::uint32_t(bytes[offset+2])<<16) | (std::uint32_t(bytes[offset+3])<<24);
    }
    static std::optional<Layout> layout(const Input& input) {
        if(!retained(input.map) || input.map.bytes.size()<0x34)return std::nullopt;
        const auto mode=word32(input.map.bytes,0x30);
        if(mode==0) {
            // VA00442B50/RVA00042B50(4) reads map+FDC+4*4 = FEC; asserts when zero
            // but continues. This source requires initialized retained state.
            if(input.map.bytes.size()<0x1044 || !word32(input.map.bytes,0xFEC))return std::nullopt;
            return Layout{true,std::bit_cast<std::int32_t>(word32(input.map.bytes,0x103C)),
                std::bit_cast<std::int32_t>(word32(input.map.bytes,0x1040)),63,63,
                input.map.bytes.subspan(0x50,63*63)};
        }
        if(mode!=2 || input.map.bytes.size()<0x1034 || !input.grid || !input.cells ||
           !retained(*input.grid) || !retained(*input.cells) || input.grid->bytes.size()<0x98 ||
           word32(input.map.bytes,0x1030)!=input.grid->address ||
           word32(input.grid->bytes,0x8C)!=input.cells->address)return std::nullopt;
        const auto width=std::bit_cast<std::int32_t>(word32(input.grid->bytes,0x90));
        const auto height=std::bit_cast<std::int32_t>(word32(input.grid->bytes,0x94));
        if(width<=0 || height<=0)return std::nullopt;
        const auto footprint=static_cast<std::uint64_t>(width)*static_cast<std::uint32_t>(height);
        // The source requires the whole actual grid, not an aliased native
        // 32-bit multiplication overflow or an arbitrary missing-data prefix.
        if(footprint>input.cells->bytes.size())return std::nullopt;
        return Layout{false,0,0,width,height,input.cells->bytes.first(static_cast<std::size_t>(footprint))};
    }
};
}
