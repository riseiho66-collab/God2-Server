#pragma once
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <vector>

namespace god2 {
// Address-independent composition of the pinned TW mode2 cell matrix.
// Actual mask selection and a complete ordered object list must come from the
// real resource owner. Structural composition does not supply its lifecycle,
// native addresses, movement rights, cache loading or a pending5D authority.
class TaiwanNativeGrid final {
public:
    struct Mask {
        std::uint8_t frame;
        std::int32_t width,height;
        std::vector<std::uint8_t> bytes; // Full original row-major mask, unchanged.
    };
    struct Overlay {
        std::int32_t actual_x,actual_y; // Actual native object +14/+18.
        std::uint32_t actual_selector; // Actual +30, getter selects low BYTE.
        Mask selected;
    };
    struct Material {
        Mask frame_zero,selected_base;
        std::uint32_t actual_base_selector;
        // Complete actual linked-object traversal order, including nonzero masks.
        std::vector<Overlay> actual_ordered_overlays;
    };
    struct Point {std::int32_t x,y;};
    struct Placement {
        std::int32_t base_origin;
        Point initialization_pixels; // Recovered49B30; not a native address.
    };
    // VA00449B30/RVA00049B30 and VA00449BB0/RVA00049BB0. Native uses
    // signed truncation toward zero. This source rejects overflowing DWORD
    // intermediates instead of reproducing wrapped coordinates or addresses.
    static std::optional<Point> native_to_pixels(std::int32_t,std::int32_t,std::int32_t);
    static std::optional<Point> native_to_grid(std::int32_t,std::int32_t);
    // Makes an immutable deep copy of every full mask alongside the cells.
    // Input must remain stable during the call; retained caller/moved-vector
    // aliases cannot subsequently change this owner's material or cells.
    // Missing/incomplete matrices, wrong selected identity and unsupported
    // arithmetic domains reject. A known mask's geometric OOB uses native AL1;
    // a destination OOB preserves cleared0 via the native assert-and-skip branch.
    static std::optional<TaiwanNativeGrid> compose(Material);
    bool complete() const noexcept;
    std::optional<std::uint8_t> read(std::int32_t,std::int32_t) const noexcept;
    // Empty/moved-from handles reject instead of returning fabricated material.
    std::int32_t side() const;
    const std::vector<std::uint8_t>& bytes() const;
    const Material& material() const;
    const Placement& placement() const;
private:
    struct Storage;
    const Storage& storage() const;
    TaiwanNativeGrid(Material,std::int32_t,Placement,std::vector<std::uint8_t>);
    static bool full(const Mask&) noexcept;
    static std::uint8_t sample(const Mask&,std::int32_t,std::int32_t) noexcept;
    std::shared_ptr<const Storage> storage_;
};
}
