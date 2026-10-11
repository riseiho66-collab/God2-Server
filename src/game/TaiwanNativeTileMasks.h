#pragma once
#include "game/TaiwanNativeGrid.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// Actual TW ModelDat/Pass declarations, not IGSROM image objects or CN proof.
// The prefix caller supplies the actual v1.6 header and TileModel count. This
// library owns the full decoded input and leaves the placement cursor intact.
class TaiwanNativeTileMasks final {
public:
    struct Layer {std::int32_t tile_index,offset_x,offset_y;};
    struct Frame {
        std::uint8_t frame;
        std::int32_t anchor_x,anchor_y,width,height;
        std::vector<std::uint8_t> bytes; // Native setter stores signed input's low BYTE.
        std::size_t source_begin,source_end;
    };
    struct Model {
        std::size_t model;
        std::array<Layer,3> layers;
        std::array<std::array<std::int32_t,2>,4> declared_markers;
        std::vector<Frame> frames; // Only actual declared frames, no ROM defaults.
        std::size_t source_begin,source_end;
    };
    struct Consumption {
        enum class Kind {Word,Decimal};
        Kind kind;
        std::size_t begin,token_begin,end; // Includes exact skipped source whitespace.
        std::optional<std::int32_t> integer;
    };
    static std::optional<TaiwanNativeTileMasks> read_v16_prefix(
        std::span<const std::uint8_t> full_decoded,std::size_t modeldat_cursor,
        std::size_t actual_tile_count,std::string_view actual_version);
    // Native selection is low BYTE. Zero-size declarations are retained above
    // but cannot supply the positive full matrix required by TaiwanNativeGrid.
    // Missing, undeclared, or ROM-derived frames reject instead of gaining AL1.
    std::optional<TaiwanNativeGrid::Mask> select(std::size_t model,std::uint32_t actual_selector) const;
    std::optional<TaiwanNativeGrid::Mask> frame_zero(std::size_t model) const;
    const std::vector<Model>& models() const;
    const std::vector<std::uint8_t>& decoded_bytes() const;
    const std::vector<Consumption>& consumption() const;
    std::size_t begin_cursor() const;
    std::size_t end_cursor() const;
private:
    struct Storage;
    explicit TaiwanNativeTileMasks(std::shared_ptr<const Storage>);
    const Storage& storage() const;
    std::shared_ptr<const Storage> storage_;
};
}
