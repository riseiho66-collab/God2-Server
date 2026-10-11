#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <vector>

namespace god2cn {
struct CnSelectedResource {
    std::filesystem::path source_path;
    std::vector<std::uint8_t> encoded_bytes;
};
//0045B270: prefer a Z file with05/16 signature, else plain.
CnSelectedResource read_cn_preferred_resource(const std::filesystem::path& plain_path,
    std::size_t max_encoded_bytes);
//004197E0: appendZ only when the fourth filename byte from the end is'.'.
// Otherwise probe the exact supplied path (including already .romz). A failed
// open/non05-16 signature falls back to the original path, not another asset.
// File selection only: no native slot, allocator, cache, decoder or ACT success.
CnSelectedResource read_cn_rom_resource(const std::filesystem::path& native_path,
    std::size_t max_encoded_bytes);
//00463F10: plain MBD unless absent or its Z file has a newer native timestamp.
// Returns the selected bytes without creating/replacing the client's cache.
CnSelectedResource read_cn_mbd_resource(const std::filesystem::path& plain_path,
    std::size_t max_encoded_bytes);
std::vector<std::uint8_t> read_cn_asset_file(const std::filesystem::path& path,
    std::size_t max_encoded_bytes);
//004657E0 plain fopen failure returns0. Only inability to open is absence;
// short/changing reads, budgets and unsupported formats remain explicit errors.
std::optional<std::vector<std::uint8_t>> try_read_cn_plain_map_file(
    const std::filesystem::path& path,std::size_t max_encoded_bytes);
// 0045A060 native 05/16 wrapper. max_plain_bytes is a caller resource budget,
// not a game-format limit. Non-wrapped bytes are returned unchanged.
std::vector<std::uint8_t> decode_cn_resource(std::span<const std::uint8_t> bytes,
    std::size_t max_plain_bytes);
}
