// Offline asset decoder. No client injection, imports or game execution.
// Byte-for-byte contract of omega_assets.decode_csvz; caller owns all buffers.
#include <cstddef>
#include <cstdint>

extern "C" __declspec(dllexport) int decode_asset_lzss(
    const std::uint8_t* src, std::size_t length, std::uint8_t* dst,
    std::size_t capacity, std::uint8_t* ring, std::uint8_t* valid) {
    if (length < 7 || src[0] != 5 || src[1] != 22) return 1;
    const std::uint32_t declared = std::uint32_t(src[2]) |
        (std::uint32_t(src[3]) << 8) | (std::uint32_t(src[4]) << 16) |
        (std::uint32_t(src[5]) << 24);
    if (declared != capacity) return 2;
    for (std::size_t i = 0; i < 4096; ++i) {
        ring[i] = 32;
        valid[i] = i < 0xfee ? 1 : 0;
    }
    std::size_t pos = 7, used = 0, cursor = 0xfee;
    unsigned flags = 0;
    while (pos < length) {
        flags >>= 1;
        if (!(flags & 0x100)) flags = unsigned(src[pos++]) | 0xff00;
        if (flags & 1) {
            if (pos == length) break;
            if (used >= capacity) return 3;
            const auto value = src[pos++];
            dst[used++] = value;
            ring[cursor] = value;
            valid[cursor] = 1;
            cursor = (cursor + 1) & 4095;
        } else {
            if (pos + 2 > length) return 4;
            const unsigned low = src[pos++], high = src[pos++];
            const unsigned offset = low | ((high & 0xf0) << 4);
            for (unsigned i = 0; i < (high & 15) + 3; ++i) {
                const unsigned address = (offset + i) & 4095;
                if (!valid[address]) return 5;
                if (used >= capacity) return 3;
                const auto value = ring[address];
                dst[used++] = value;
                ring[cursor] = value;
                valid[cursor] = 1;
                cursor = (cursor + 1) & 4095;
            }
        }
    }
    return used == capacity ? 0 : 6;
}
