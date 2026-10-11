#pragma once
#include "cn/assets/CnOutdoorTerrain.h"
#include <optional>
#include <string>
#include <string_view>

namespace god2cn {
//00472380/00475BE0/004749A0 ->0046CE10. Native renderer/camera
// projection only; not a C2S coordinate decoder or movement permission.
struct CnOutdoorCamera {
    struct Point {std::int32_t x,y;};
    struct View {
        Point camera;
        // Actual map+FD8 viewport+1C/+20 and loaded center+34/+38 tile
        // extents. No defaults, assumed desktop size or packet-derived values.
        std::int32_t viewport_width,viewport_height,tile_width,tile_height;
    };
    struct Projection {
        Point native_grid;
        Point shift; // Each axis -1/0/1; thresholds -19/40 from0046CE10.
        std::array<bool,9> visible_slots; // Native map+1000..1020.
    };
    static std::optional<Projection> project_mode0(const View&);
    //00537D40 ->0046C780 ->00470C10 ->004751C0, then -400/-300.
    // Use the actual selected/clamped initial placement, not packet coordinates.
    // This is BEFORE00473120's conditional successful cache-switch rebase;
    // neither a live frame camera nor a viewport/tile-size/default supplier.
    static std::optional<Point> initial_mode0_before_cache_switch(
        const CnOutdoorTerrain::InitialWorldPlacement&);
    //004621F0 uses "%c%d", quotient+65 and remainder, not decimal text.
    // This is the ASCII alphabet/digit subset accepted by00461ED0. Native
    // producer emits nonalphabet bytes above259; those variants stay open.
    static std::optional<std::string> map_reference(std::string_view native_owner_prefix,
        CnOutdoorTerrain::ChunkCoordinate);
    static std::optional<std::int32_t> decode_ascii_axis(std::string_view);
    //00470440's actual nine screen offsets; not chunk/world coordinates.
    static std::optional<Point> success_camera(Point original,Point shift);
};
}
