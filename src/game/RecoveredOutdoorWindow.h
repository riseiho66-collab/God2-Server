#pragma once
#include "game/RecoveredIndoorGrid.h"
#include <array>
#include <optional>

namespace god2 {
struct OutdoorPlacement {
    PassGrid grid;
    int x=0, y=0;
    std::array<std::array<int,2>,2> points{{{-1,-1},{-1,-1}}};
};

// Native static layers only. Callers supply native-sorted placements.
// Unknown source coverage is not a native zero or a movement permission.
class RecoveredOutdoorWindow {
public:
    static constexpr int side=63, block_side=21;
    static constexpr std::size_t block_bytes=21*21*8;
    using Blocks=std::array<std::span<const std::uint8_t>,9>;
    explicit RecoveredOutdoorWindow(const Blocks& blocks,
                                    std::span<const OutdoorPlacement> placements={}) {
        if(placements.size()>20000) throw std::invalid_argument("Outdoor placement limit");
        for(std::size_t i=0;i<blocks.size();++i) {
            const auto block=blocks[i];
            if(block.empty()) continue;
            if(block.size()!=block_bytes) throw std::invalid_argument("Outdoor block size");
            const int bx=static_cast<int>(i%3)*21, by=static_cast<int>(i/3)*21;
            for(int y=0;y<21;++y) for(int x=0;x<21;++x)
                put(bx+x,by+y,static_cast<std::uint8_t>((block[(y*21+x)*8+7]>>6)&1));
        }
        for(const auto& p:placements) {
            const auto& g=p.grid;
            if(g.width<1 || g.width>512 || g.height<1 || g.height>512 ||
               g.cells.size()!=static_cast<std::size_t>(g.width*g.height))
                throw std::invalid_argument("Outdoor Pass dimensions");
            bounded(p.x);bounded(p.y);
            for(const auto& point:p.points) { bounded(point[0]);bounded(point[1]); }
            for(int row=0;row<g.height;++row) for(int col=0;col<g.width;++col)
                if(g.cells[row*g.width+col]==0) put(p.x+col-row/2,p.y+col+(row+1)/2,0);
            for(const auto& point:p.points) if(point[0]>=0)
                put(p.x+point[0]-point[1]/2,p.y+point[0]+(point[1]+1)/2,2);
        }
    }
    [[nodiscard]] std::optional<std::uint8_t> cell(int x,int y) const noexcept {
        if(x<0 || y<0 || x>=side || y>=side) return std::nullopt;
        return cells_[static_cast<std::size_t>(y*side+x)];
    }
private:
    static void bounded(int value) {
        if(value < -32768 || value > 32767) throw std::invalid_argument("Outdoor placement bounds");
    }
    void put(int x,int y,std::uint8_t value) noexcept {
        if(x>=0 && y>=0 && x<side && y<side) cells_[static_cast<std::size_t>(y*side+x)]=value;
    }
    std::array<std::optional<std::uint8_t>,side*side> cells_{};
};
}
