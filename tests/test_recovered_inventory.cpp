#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredWorldFrame.h"
#include "inventory_guarded_record.h"
#ifdef NDEBUG
#undef NDEBUG // Standalone regression checks must also run in Release builds.
#endif
#include <cassert>
#include <charconv>
#include <cstdio>
#include <string_view>
#include <vector>

using Inventory = god2::RecoveredInventory;

static void dump(std::span<const std::uint8_t> bytes) {
    for (auto byte : bytes) std::printf("%02x", static_cast<unsigned>(byte));
    std::puts("");
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string_view(argv[1]) == "--updates") {
        if (argc < 5 || (argc - 2) % 3 != 0 ||
            static_cast<std::size_t>((argc - 2) / 3) >
                god2::RecoveredWorldFrame::max_logical_size / Inventory::logical_size) return 2;
        std::vector<std::uint8_t> logical;
        for (int i = 2; i < argc; i += 3) {
            std::array<unsigned, 3> fields{};
            for (int j = 0; j < 3; ++j) {
                const std::string_view arg(argv[i + j]);
                const auto parsed = std::from_chars(arg.data(), arg.data() + arg.size(), fields[j]);
                if (parsed.ec != std::errc{} || parsed.ptr != arg.data() + arg.size()) return 2;
            }
            if (fields[0] > 0xffff || fields[1] > 0xff || fields[2] > 0xff) return 2;
            const auto record = Inventory::encode_slot_update({
                static_cast<std::uint16_t>(fields[0]), static_cast<std::uint8_t>(fields[1]),
                static_cast<std::uint8_t>(fields[2])});
            if (!record) return 2;
            logical.insert(logical.end(), record->begin(), record->end());
        }
        dump(god2::RecoveredWorldFrame::encode(logical));
        return 0;
    }
    if (argc == 2 && std::string_view(argv[1]) == "--dump") {
        dump(god2::RecoveredWorldFrame::encode(Inventory::empty_owned_inventory()));
        return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--clear") {
        std::size_t slot = 0;
        const std::string_view arg(argv[2]);
        const auto parsed = std::from_chars(arg.data(), arg.data() + arg.size(), slot);
        if (parsed.ec != std::errc{} || parsed.ptr != arg.data() + arg.size()) return 2;
        const auto frame = Inventory::clear_slot(slot);
        if (!frame) return 2;
        dump(god2::RecoveredWorldFrame::encode(*frame));
        return 0;
    }
    const std::string_view mode = argc > 1 ? argv[1] : "";
    const bool guarded = mode == "--guarded-decode" || mode == "--guarded-decode-item-request";
    if (argc == 3 && (mode == "--decode" || mode == "--decode-item-request" ||
                     mode == "--decode-wire" || mode == "--frame-logical" || guarded)) {
        const std::string_view hex(argv[2]);
        if (hex.size() % 2 != 0) return 2;
        std::vector<std::uint8_t> bytes;
        for (std::size_t i = 0; i < hex.size(); i += 2) {
            unsigned value = 0;
            const auto parsed = std::from_chars(hex.data() + i, hex.data() + i + 2, value, 16);
            if (parsed.ec != std::errc{} || parsed.ptr != hex.data() + i + 2) return 2;
            bytes.push_back(static_cast<std::uint8_t>(value));
        }
        // Test-only composition adapter: validate every record before output.
        if (mode == "--decode-wire") {
            const auto logical = god2::RecoveredWorldFrame::decode(bytes);
            if (!logical || logical->size() % Inventory::logical_size != 0) return 2;
            for (std::size_t offset = 0; offset < logical->size(); offset += Inventory::logical_size)
                if (!Inventory::decode_slot_update(std::span(*logical).subspan(
                        offset, Inventory::logical_size))) return 2;
            dump(*logical);
            return 0;
        }
        if (mode == "--frame-logical") {
            if (bytes.empty() || bytes.size() > god2::RecoveredWorldFrame::max_logical_size) return 2;
            dump(god2::RecoveredWorldFrame::encode(bytes));
            return 0;
        }
        if (guarded) {
            // Each placement catches a different out-of-span access. For an
            // empty suffix placement, even reading opcode hits PAGE_NOACCESS.
            for (bool at_end : {false, true}) {
                const InventoryGuardedRecord protected_record(bytes, at_end);
                if (mode == "--guarded-decode-item-request") {
                    const auto expected = god2::RecoveredInventoryItemRequest::decode(bytes);
                    const auto actual = god2::RecoveredInventoryItemRequest::decode(protected_record.bytes());
                    assert(actual.has_value() == expected.has_value());
                    if (actual) {
                        assert(actual->client_item_id == expected->client_item_id);
                        assert(actual->raw_slot == expected->raw_slot);
                        assert(actual->raw_tail == expected->raw_tail);
                    }
                } else {
                    const auto expected = Inventory::decode_slot_update(bytes);
                    const auto actual = Inventory::decode_slot_update(protected_record.bytes());
                    assert(actual.has_value() == expected.has_value());
                    if (actual) {
                        assert(actual->client_item_id == expected->client_item_id);
                        assert(actual->slot == expected->slot);
                        assert(actual->raw_count == expected->raw_count);
                    }
                }
            }
        }
        if (mode == "--decode-item-request" || mode == "--guarded-decode-item-request") {
            const auto request = god2::RecoveredInventoryItemRequest::decode(bytes);
            if (!request) return 2;
            std::printf("%u %u %u\n", static_cast<unsigned>(request->client_item_id),
                        static_cast<unsigned>(request->raw_slot),
                        static_cast<unsigned>(request->raw_tail));
            return 0;
        }
        const auto record = Inventory::decode_slot_update(bytes);
        if (!record) return 2;
        std::printf("%u %u %u\n", static_cast<unsigned>(record->client_item_id),
                    static_cast<unsigned>(record->slot), static_cast<unsigned>(record->raw_count));
        return 0;
    }
    assert(argc == 1);
    for (std::size_t slot = 0; slot < 50; ++slot) assert(Inventory::clear_slot(slot));
    assert(!Inventory::clear_slot(50));
    assert(!Inventory::clear_slot(static_cast<std::size_t>(-1)));
    for (unsigned slot = 0; slot < 256; ++slot) {
        for (unsigned count = 0; count < 256; ++count) {
            const auto encoded = Inventory::encode_slot_update({0x9234,
                static_cast<std::uint8_t>(slot), static_cast<std::uint8_t>(count)});
            assert(encoded.has_value() == (slot < Inventory::slot_count));
            if (!encoded) continue;
            const Inventory::LogicalRecord expected{0x41, 0x34, 0x92,
                static_cast<std::uint8_t>(slot), static_cast<std::uint8_t>(count)};
            assert(*encoded == expected);
            if (count == 0) assert(Inventory::encode_slot_update({0,
                static_cast<std::uint8_t>(slot), 0}) == Inventory::clear_slot(slot));
        }
    }
    for (unsigned id = 0; id <= 0xffff; ++id) {
        const auto encoded = Inventory::encode_slot_update({static_cast<std::uint16_t>(id), 49, 127});
        assert(encoded && (*encoded)[1] == (id & 255) && (*encoded)[2] == (id >> 8));
        const auto roundtrip = Inventory::decode_slot_update(*encoded);
        assert(roundtrip && roundtrip->client_item_id == id && roundtrip->slot == 49 &&
               roundtrip->raw_count == 127);
    }
    const std::array<std::uint8_t, 5> logical{0x41, 0x34, 0x92, 49, 0xff};
    const auto decoded = Inventory::decode_slot_update(logical);
    assert(decoded && decoded->client_item_id == 0x9234 && decoded->slot == 49 &&
           decoded->raw_count == 255);
    for (std::size_t size = 0; size < 5; ++size)
        assert(!Inventory::decode_slot_update(std::span(logical).first(size)));
    using ItemRequest = god2::RecoveredInventoryItemRequest;
    const std::array<std::uint8_t, 5> request{0x25, 0x34, 0x92, 49, 0xff};
    const auto parsed_request = ItemRequest::decode(request);
    assert(parsed_request && parsed_request->client_item_id == 0x9234 &&
           parsed_request->raw_slot == 49 && parsed_request->raw_tail == 255);
    for (std::size_t size = 0; size < request.size(); ++size)
        assert(!ItemRequest::decode(std::span(request).first(size)));
    assert(!ItemRequest::decode(logical));
    const std::array<std::uint8_t, 6> extended{0x25, 0x34, 0x92, 49, 0xff, 0};
    assert(!ItemRequest::decode(extended));
    // Structural decoding must preserve every raw byte without assigning an
    // inventory slot, a nonzero-item rule, or quantity semantics to this request.
    for (unsigned value = 0; value <= 255; ++value) {
        const auto byte = static_cast<std::uint8_t>(value);
        const std::array<std::uint8_t, 5> raw{0x25, byte, byte, byte, byte};
        const auto decoded_request = ItemRequest::decode(raw);
        assert(decoded_request && decoded_request->client_item_id == value * 257 &&
               decoded_request->raw_slot == byte && decoded_request->raw_tail == byte);
    }
    std::puts("RecoveredInventory standalone assertions passed");
}
