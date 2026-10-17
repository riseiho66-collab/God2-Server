#pragma once
#include "db/AccountRepository.h"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// Version-scoped delivery data, not duplicated account/gameplay authority.
// Origin metadata records provenance; its mere presence is not native proof,
// an entitlement, permission or a replacement for current issuer observation.
struct NativeAccountSnapshot {
    std::uint64_t account,revision;
    std::string client_sha256,source_sha256,source_record;
    std::vector<std::uint8_t> metadata,billing;
    bool operator==(const NativeAccountSnapshot&) const = default;
};
class NativeAccountSnapshotRepository {
public:
    virtual ~NativeAccountSnapshotRepository()=default;
    // Same actual authenticated account backend.
    virtual bool owns_accounts(const AccountRepository&) const noexcept=0;
    // Missing row is absent. Missing schema/backend or malformed stored data
    // is an error, never an all-zero/free/default-success snapshot.
    // Serial game-owner read; callers keep the database alive through drain.
    virtual std::optional<NativeAccountSnapshot> load(std::uint64_t account,std::string_view client_sha256)=0;
};
}
