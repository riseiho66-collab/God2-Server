// Standalone: compile with C++20 and -I src; no server or shared build required.
#include "game/RecoveredIndoorGrid.h"
#include <array>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>

namespace {
using god2::PassGrid;
using god2::Placement;
using Grid = god2::RecoveredIndoorGrid;

void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
template<class Exception, class F> void rejects(F call) {
    try { call(); } catch (const Exception&) { return; }
    throw std::runtime_error("Invalid indoor input accepted");
}
PassGrid filled(int width, int height, std::uint8_t value = 255) {
    return {width, height, std::vector<std::uint8_t>(
        static_cast<std::size_t>(width) * static_cast<std::size_t>(height), value)};
}

void projection_assertions() {
    const Grid even({2, 4, {1, 2, 3, 4, 5, 6, 7, 255}});
    require(even.side() == 5, "Even width side");
    require(even.cells() == std::vector<std::uint8_t>{
        0,0,1,0,0,
        0,5,3,2,0,
        0,7,6,4,0,
        0,0,255,0,0,
        0,0,0,0,0}, "Even width or row parity projection");
    const Grid odd({3, 3, {0, 2, 3, 4, 5, 6, 7, 128, 254}});
    require(odd.side() == 7, "Odd width side");
    require(odd.cells() == std::vector<std::uint8_t>{
        0,0,0,0,0,0,0,
        0,0,0,7,4,2,0,
        0,0,0,0,128,5,3,
        0,0,0,0,0,254,6,
        0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,
        0,0,0,0,0,0,0}, "Odd width or raw byte projection");
    const Grid tall({1, 5, {11, 22, 33, 44, 55}});
    require(tall.side() == 7 && tall.cell(6, 0) == 11 &&
            tall.cell(6, 1) == 22 && tall.cell(5, 1) == 33 &&
            tall.cell(5, 2) == 44 && tall.cell(4, 2) == 55,
            "Height-dominated side or odd height rounding");
    const Grid smallest({1, 1, {231}});
    require(smallest.side() == 3 && smallest.cell(2, 0) == 231, "Minimum dimensions");
    const Grid largest(filled(512, 512));
    require(largest.side() == 1025 && largest.cells().size() == 1050625 &&
            largest.cell(768, 767) == 255, "Maximum dimensions");
    for (int coordinate : {-1, 5, std::numeric_limits<int>::min(),
                           std::numeric_limits<int>::max()}) {
        require(even.cell(coordinate, 0) == 0 && even.cell(0, coordinate) == 0,
                "Out-of-bounds getter must return zero");
    }
}

void overlay_assertions() {
    const PassGrid base{2, 4, {1, 2, 3, 4, 5, 6, 7, 255}};
    const std::array placements{Placement{{2, 4, {9, 0, 0, 8, 0, 3, 4, 0}}, 0, 0}};
    Grid grid(base, placements);
    require(grid.cells() == std::vector<std::uint8_t>{
        0,0,1,0,0,
        0,0,0,0,0,
        0,7,6,4,0,
        0,0,0,0,0,
        0,0,0,0,0}, "Overlay must erase only zero cells");
    const std::array repeated{Placement{filled(2, 4, 0), 0, 0},
                              Placement{filled(2, 4, 255), 0, 0}};
    grid.build(base, repeated);
    require(grid.cells() == std::vector<std::uint8_t>(25, 0), "Overlay restored erased bytes");
    const std::array shifted{Placement{{1, 2, {0, 0}}, 1, 0}};
    grid.build(base, shifted);
    require(grid.cell(3, 1) == 0 && grid.cell(3, 2) == 0 && grid.cell(2, 0) == 1,
            "Placement coordinates must not be pixel-scaled");

    // -1/2 == 0 and (-2+1)/2 == 0, distinguishing truncation from floor.
    for (const auto& placement : std::array{
            Placement{{1, 2, {0, 0}}, 0, -1},
            Placement{{1, 2, {0, 0}}, 0, -2},
            Placement{{1, 2, {0, 0}}, 1, -3},
            Placement{{1, 2, {0, 0}}, -1, 2}}) {
        const Grid baseline(filled(4, 6, 173));
        Grid actual(filled(4, 6, 173), std::span(&placement, 1));
        auto expected = baseline.cells();
        int x = 4, y = 0;
        if (placement.y == -2) x = 5;
        if (placement.y == -3) x = 6;
        if (placement.y == 2) x = 2;
        expected[static_cast<std::size_t>(y * 9 + x)] = 0;
        expected[static_cast<std::size_t>((y + 1) * 9 + x)] = 0;
        require(actual.cells() == expected, "Signed placement division changed");
    }
    const std::array on_zero{Placement{{1, 1, {200}}, 0, 2}};
    require(Grid(filled(2, 1), on_zero).cell(1, 1) == 0, "Nonzero overlay painted empty cell");
    const auto scene_base = filled(10, 30, 173);
    const Grid scene(scene_base);
    require(scene.side() == 31 && scene.cell(20, 0) == 173 && scene.cell(21, 0) == 0,
            "10x30 scene anchor must be 20");
    const std::array scene_overlay{Placement{{1, 1, {0}}, 2, 8}};
    auto scene_expected = scene.cells();
    require(scene.cell(18, 6) == 173, "Scene overlay fixture must hit base byte");
    scene_expected[6 * 31 + 18] = 0;
    require(Grid(scene_base, scene_overlay).cells() == scene_expected,
            "Scene placement (2,8) must project to (18,6)");
}

void invalid_assertions() {
    const auto base = filled(2, 2);
    for (int dimension : {std::numeric_limits<int>::min(), -1, 0, 513,
                          std::numeric_limits<int>::max()}) {
        for (const auto& bad : {PassGrid{dimension, 1, {}}, PassGrid{1, dimension, {}}}) {
            rejects<std::invalid_argument>([&] { Grid grid(bad); });
            const std::array placements{Placement{bad, 0, 0}};
            rejects<std::invalid_argument>([&] { Grid grid(base, placements); });
        }
    }
    for (const auto& bad : {PassGrid{1, 1, {}}, PassGrid{1, 1, {1, 2}},
                           PassGrid{2, 2, {1, 2, 3}}}) {
        rejects<std::invalid_argument>([&] { Grid grid(bad); });
        const std::array placements{Placement{bad, 0, 0}};
        rejects<std::invalid_argument>([&] { Grid grid(base, placements); });
    }
    std::vector<Placement> placements(1024, Placement{filled(1, 1), 0, 0});
    require(Grid(base, placements).cells() == Grid(base).cells(), "1024 placements rejected");
    placements.push_back(placements.front());
    rejects<std::invalid_argument>([&] { Grid grid(base, placements); });
    for (int coordinate : {-32768, 32768, std::numeric_limits<int>::min(),
                           std::numeric_limits<int>::max()}) {
        for (const auto& placement : {Placement{filled(1, 1), coordinate, 0},
                                      Placement{filled(1, 1), 0, coordinate}})
            rejects<std::invalid_argument>([&] { Grid grid(base, std::span(&placement, 1)); });
    }
    for (int raw : {0, 255}) {
        for (const auto& position : std::array<std::array<int, 2>, 8>{{
                {-3, 0}, {3, 0}, {0, -4}, {0, 10},
                {-32767, 0}, {32767, 0}, {0, -32767}, {0, 32767}}}) {
            const std::array outside{Placement{filled(1, 1, static_cast<std::uint8_t>(raw)),
                                              position[0], position[1]}};
            rejects<std::out_of_range>([&] { Grid grid(base, outside); });
        }
    }
    Grid grid(base);
    const auto before = grid.cells();
    const std::array partial{Placement{filled(4, 1, 0), 0, 0}};
    rejects<std::out_of_range>([&] { grid.build(base, partial); });
    require(grid.side() == 5 && grid.cells() == before, "Failed rebuild published partial grid");
    grid.build({1, 1, {42}});
    require(grid.side() == 3 && grid.cells().size() == 9 && grid.cell(2, 0) == 42,
            "Successful rebuild retained old grid");
}

int read_number(std::istream& input, int minimum, int maximum) {
    int value = 0;
    if (!(input >> value) || value < minimum || value > maximum)
        throw std::invalid_argument("Missing or invalid dump number");
    return value;
}
PassGrid read_grid(std::istream& input) {
    const int width = read_number(input, 1, 512);
    const int height = read_number(input, 1, 512);
    auto grid = filled(width, height, 0);
    for (auto& cell : grid.cells) cell = static_cast<std::uint8_t>(read_number(input, 0, 255));
    return grid;
}
void dump(std::istream& input, std::ostream& output) {
    const auto base = read_grid(input);
    const int count = read_number(input, 0, 1024);
    std::vector<Placement> placements;
    placements.reserve(static_cast<std::size_t>(count));
    for (int i = 0; i < count; ++i) {
        const int x = read_number(input, -32767, 32767);
        const int y = read_number(input, -32767, 32767);
        placements.push_back({read_grid(input), x, y});
    }
    input >> std::ws;
    require(input.eof(), "Trailing dump input");
    const Grid grid(base, placements);
    output << grid.side() << '\n';
    constexpr char digits[] = "0123456789abcdef";
    for (auto byte : grid.cells()) output << digits[byte >> 4] << digits[byte & 15];
    output << '\n';
}
void dump_assertions() {
    std::istringstream input("1 1 171 0");
    std::ostringstream output;
    dump(input, output);
    require(output.str() == "3\n0000ab000000000000\n", "Dump framing or hex encoding");
    std::istringstream overlay("1 1 171 1 0 0 1 1 0");
    std::ostringstream erased;
    dump(overlay, erased);
    require(erased.str() == "3\n000000000000000000\n", "Dump placement parsing");
    for (const auto* text : {"", "0 1", "513 1", "1 1 -1 0", "1 1 256 0",
            "1 1 9", "1 1 9 -1", "1 1 9 1025", "1 1 9 1 0 0 1 1",
            "1 1 9 1 32768 0 1 1 0", "1 1 9 0 extra", "99999999999999999"}) {
        std::istringstream bad(text);
        std::ostringstream result;
        rejects<std::exception>([&] { dump(bad, result); });
        require(result.str().empty(), "Invalid dump emitted partial result");
    }
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--dump") {
            dump(std::cin, std::cout);
        } else {
            require(argc == 1, "Expected --dump or no arguments");
            projection_assertions();
            overlay_assertions();
            invalid_assertions();
            dump_assertions();
            std::cout << "Recovered indoor grid assertions passed\n";
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
