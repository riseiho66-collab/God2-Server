// Generated local candidate from hash-bound semantic IR; not a production API.
#include <array>
#include <cstdint>
#include <algorithm>
extern "C" __declspec(dllexport) int God2LiftedRaw(int decrypt,
    const std::uint8_t* key, unsigned key_size, unsigned feedback,
    const std::uint8_t* input, unsigned size, std::uint8_t* destination, unsigned capacity) {
    if ((decrypt != 0 && decrypt != 1) || !key || key_size != 256 || feedback > 255 ||
        size > 4096 || capacity < size || (size && (!input || !destination))) return -1;
    std::array<std::uint8_t,4096> output{};
    for (unsigned i=0;i<size;++i) {
        if (decrypt) {
            const std::uint8_t v0 = input[i];
            const auto v1 = static_cast<std::uint8_t>(v0 + 3);
            const auto v2 = static_cast<std::uint8_t>(v1 - feedback);
            const std::uint8_t k0 = key[i & 255];
            const auto v3 = static_cast<std::uint8_t>(v2 ^ k0);
            output[i] = v3;
            feedback = v3;
        } else {
            const std::uint8_t v0 = input[i];
            const std::uint8_t k0 = key[i & 255];
            const auto v1 = static_cast<std::uint8_t>(v0 ^ k0);
            const auto v2 = static_cast<std::uint8_t>(v1 + feedback);
            const auto v3 = static_cast<std::uint8_t>(v2 - 3);
            output[i] = v3;
            feedback = v0;
        }
    }
    if (size) std::copy_n(output.begin(),size,destination);
    return static_cast<int>(size);
}
