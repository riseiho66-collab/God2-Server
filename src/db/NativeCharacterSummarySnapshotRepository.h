#pragma once
#include "db/AccountRepository.h"
#include "db/RecoveredCharacterRepository.h"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// Version-keyed raw delivery snapshots, not duplicate gameplay/character state.
// Only actual issuer outputs belong here. Provenance is not rule authority.
struct NativeCharacterSummarySnapshot {
    // Storage tags matching explicit source modes; these are not wire flags.
    enum class NameSource:std::uint8_t {CommonIdentity=0,NativePromptMarker=1};
    struct Role {
        std::vector<std::uint8_t> record;
        std::uint64_t revision;
        std::string source_sha256,source_record;
        bool operator==(const Role&) const=default;
    };
    struct Row {
        std::uint64_t character;
        NameSource name_source;
        std::optional<Role> role;
        bool operator==(const Row&) const=default;
    };
    std::uint64_t account,revision;
    std::uint16_t group,server;
    std::string client_sha256,source_sha256,source_record;
    std::vector<std::uint8_t> record;
    std::vector<Row> rows; //Exact issuer ordinal order, never common slot/name order.
    bool operator==(const NativeCharacterSummarySnapshot&) const=default;
};
class NativeCharacterSummarySnapshotRepository {
public:
    virtual ~NativeCharacterSummarySnapshotRepository()=default;
    virtual bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept=0;
    // Missing snapshot is absent; missing schema/malformed/incomplete bindings
    // are errors. Single game-owner read; actual authority must still observe.
    virtual std::optional<NativeCharacterSummarySnapshot> load(std::uint64_t account,
        std::uint16_t group,std::uint16_t server,std::string_view client_sha256)=0;
};
}
