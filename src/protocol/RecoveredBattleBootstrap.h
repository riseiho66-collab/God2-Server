#pragma once
#include "protocol/RecoveredBattleEntry.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredWorldFrame.h"
#include <limits>

namespace god2 {

// S2C1C is construction input, unlike the existing-actor 83/84 messages.
// Evidence: current-monster-side-initialization-20260920.md. Opaque bytes are
// deliberately retained; this codec supplies no character/monster defaults.
struct RecoveredBattleIdentity {
    static constexpr std::size_t logical_size = 45;
    using Bytes = std::array<std::uint8_t, logical_size>;
    class Record {
    public:
        std::uint8_t position() const noexcept { return bytes_[1]; }
        std::uint8_t displayed_level() const noexcept { return bytes_[2]; }
        std::uint16_t identity_word() const noexcept { return word(3); }
        std::uint16_t variant() const noexcept { return word(5); }
        std::uint16_t ordinal() const noexcept { return word(7); }
        // These accessors apply to the qualified normal EnyName variant only.
        std::optional<std::uint8_t> enemy_area() const noexcept {
            if (variant() != 0x400) return std::nullopt;
            return bytes_[9];
        }
        std::optional<std::uint16_t> enemy_scene() const noexcept {
            if (variant() != 0x400) return std::nullopt;
            return word(11);
        }
    private:
        friend struct RecoveredBattleIdentity;
        explicit Record(Bytes bytes) : bytes_(bytes) {}
        std::uint16_t word(std::size_t offset) const noexcept {
            return static_cast<std::uint16_t>(bytes_[offset] | (unsigned{bytes_[offset+1]} << 8));
        }
        Bytes bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.size() != logical_size || bytes[0] != 0x1c || bytes[1] >= 28)
            return std::nullopt;
        Bytes copy;
        std::copy(bytes.begin(), bytes.end(), copy.begin());
        return Record(copy);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};

// CUSTOM-0005: explicit bootstrap batch policy, not a captured official sequence.
// Builds bytes only. The caller must separately validate catalog/resource
// identity, world/session ownership and client initialization before sending.
struct RecoveredBattleBootstrap {
    // Width-only legacy HP projection. Inspect the complete shared value before
    // any native DWORD writer; this does not authorize an extended client profile.
    static std::uint32_t native_hp_dword(std::uint64_t value) {
        if(value>std::numeric_limits<std::uint32_t>::max())
            throw std::invalid_argument("Battle HP needs a qualified extended profile");
        return static_cast<std::uint32_t>(value);
    }
    struct Actor {
        RecoveredBattleIdentity::Record identity;
        RecoveredBattleVitals::Record hp;
        std::optional<RecoveredBattleVitals::Record> mp;
    };
    static std::vector<std::uint8_t> logical(
            std::uint32_t context_a, std::uint32_t context_b, std::span<const Actor> actors) {
        if (actors.empty() || actors.size() > 28)
            throw std::invalid_argument("Battle bootstrap requires 1..28 explicit actors");
        std::array<bool,28> occupied{};
        for (const auto& actor : actors) {
            const auto position = actor.identity.position();
            if (occupied[position]) throw std::invalid_argument("Duplicate battle position");
            occupied[position] = true;
            validate_vital(actor.hp, position, RecoveredBattleVitals::Resource::Hp);
            if (actor.mp) validate_vital(*actor.mp, position, RecoveredBattleVitals::Resource::Mp);
        }
        const auto entry=RecoveredBattleEntry::encode_logical({context_a,context_b});
        std::vector<std::uint8_t> result(entry.begin(),entry.end());
        for (const auto& actor : actors) {
            const auto identity = RecoveredBattleIdentity::encode_logical(actor.identity);
            result.insert(result.end(), identity.begin(), identity.end());
            append(result, actor.hp);
            if (actor.mp) append(result, *actor.mp);
        }
        return result;
    }
    static std::vector<std::uint8_t> wire(
            std::uint32_t context_a, std::uint32_t context_b, std::span<const Actor> actors) {
        return RecoveredWorldFrame::encode(logical(context_a, context_b, actors));
    }
    // CUSTOM-0005: isolated initial first-control sequence. Native live evidence
    // requires 88 before 86/5 for counter initialization; this is not turn policy.
    static std::vector<std::uint8_t> ready_logical(
            std::uint32_t context_a, std::uint32_t context_b, std::span<const Actor> actors,
            const RecoveredBattleVitalsBatch::Record& batch, std::span<const std::uint8_t> grant) {
        auto result = logical(context_a, context_b, actors);
        if (grant.size() != 17 || grant[0] != 0x86 || grant[1] != 5 ||
            grant[3] != 1 || grant[4] >= 14)
            throw std::invalid_argument("Explicit initial first-control grant required");
        const auto bulk = RecoveredBattleVitalsBatch::encode_logical(batch);
        if (std::all_of(bulk.begin()+1, bulk.begin()+5, [](auto b) { return b == 0xff; }))
            throw std::invalid_argument("Initial counter must not be the uninitialized sentinel");
        std::array<const Actor*,14> friendly{};
        for (const auto& actor : actors)
            if (actor.identity.position() < 14) friendly[actor.identity.position()] = &actor;
        if (!friendly[grant[4]]) throw std::invalid_argument("Grant references an absent actor");
        for (std::size_t slot=0; slot<friendly.size(); ++slot) {
            const auto values = *batch.at(slot);
            const auto* actor = friendly[slot];
            if (actor ? (!actor->mp || values.hp != actor->hp.current() || values.mp != actor->mp->current())
                      : (values.hp != 0 || values.mp != 0))
                throw std::invalid_argument("Initial bulk vitals must match explicit participants");
        }
        result.insert(result.end(), bulk.begin(), bulk.end());
        result.insert(result.end(), grant.begin(), grant.end());
        return result;
    }
private:
    static void validate_vital(const RecoveredBattleVitals::Record& vital, std::uint8_t position,
                               RecoveredBattleVitals::Resource resource) {
        if (vital.position() != position || vital.resource() != resource ||
            !vital.native_actor_write_supported() || vital.current() > vital.maximum())
            throw std::invalid_argument("Invalid or unsupported bootstrap vital update");
    }
    static void append(std::vector<std::uint8_t>& result, const RecoveredBattleVitals::Record& vital) {
        const auto bytes = RecoveredBattleVitals::encode_logical(vital);
        result.insert(result.end(), bytes.begin(), bytes.end());
    }
};
}
