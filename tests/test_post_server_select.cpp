#include "protocol/RecoveredPostServerSelect.h"
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <vector>

namespace {
void check(bool value) {
    if (!value) throw std::runtime_error("test_post_server_select check failed");
}
}

void test_post_server_select() {
    using namespace god2;
    constexpr RecoveredPostServerSelect::Wire fixture{0x06, 0x00, 0xa3, 0xa3, 0xfd, 0xd5};
    const auto parsed = ParsePostServerSelectRequest(fixture);
    check(parsed.has_value());
    check(parsed->raw == fixture && parsed->consumed == fixture.size());
    check(parsed->logical == std::array<std::uint8_t, 3>{0xa6, 0x00, 0x00});
    check(parsed->checksum == 0xd8);

    // Independently check the zero-key arithmetic against the captured bytes.
    unsigned checksum = 6 + 5 * 0x3c;
    for (const auto byte : parsed->logical) checksum += byte;
    check(static_cast<std::uint8_t>(checksum) == parsed->checksum);
    auto roundtrip = fixture;
    std::uint8_t previous = 0;
    for (std::size_t i = 0; i < 4; ++i) {
        check(recovered_zero_seed_key[i] == 0);
        const auto clear = i < 3 ? parsed->logical[i] : parsed->checksum;
        roundtrip[i + 2] = static_cast<std::uint8_t>(clear + previous - 3);
        previous = clear;
    }
    check(roundtrip == fixture);

    std::ifstream capture(GOD2_SOURCE_DIR "/artifacts/runs/ui-gate-real-04/C2S_SERVER_SELECT_0001.bin",
                          std::ios::binary);
    check(capture.is_open());
    const std::vector<std::uint8_t> captured((std::istreambuf_iterator<char>(capture)), {});
    check(captured == std::vector<std::uint8_t>(fixture.begin(), fixture.end()));
    check(ParsePostServerSelectRequest(captured).has_value());

    for (std::size_t size = 0; size < fixture.size(); ++size)
        check(!ParsePostServerSelectRequest(std::span<const std::uint8_t>(fixture).first(size)));
    for (std::size_t i = 0; i < fixture.size(); ++i) {
        for (unsigned byte = 0; byte < 256; ++byte) {
            if (byte == fixture[i]) continue;
            auto changed = fixture;
            changed[i] = static_cast<std::uint8_t>(byte);
            check(!ParsePostServerSelectRequest(changed));
        }
    }
    auto extra = captured;
    extra.push_back(0);
    check(!ParsePostServerSelectRequest(extra));
    extra = captured;
    extra.insert(extra.end(), captured.begin(), captured.end());
    check(!ParsePostServerSelectRequest(extra));

    // A different body with a valid zero-seed checksum must still be rejected.
    constexpr RecoveredPostServerSelect::Wire other{0x06, 0x00, 0xa4, 0xa4, 0xfd, 0xd6};
    check(!ParsePostServerSelectRequest(other));
}

#ifdef GOD2_POST_SERVER_SELECT_STANDALONE_TEST
int main() {
    test_post_server_select();
}
#endif
