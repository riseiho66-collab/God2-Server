#pragma once
#include "cn/auth/SharedAccountSelection.h"
#include "cn/protocol/CnRoleStatus.h"
#include <span>
#include <utility>

namespace god2::cn {
// Actual common character name/explicit native role level -> CN07. Other fields/visibility retain
// their own source; common40 is not a CN36 profile, slot or entitlement map.
class SharedCommonCharacterSummarySource {
public:
    using Summary=SharedAccountSelection::NativeSummary;
    using Scope=Summary::Scope;
    enum class NameSource { CommonIdentity, NativePromptMarker };
    class RoleLevel {
    public:
        // Actual full CN22 plus its real source revision, explicitly tied to
        // the Row common ID by the same observing native metadata owner.
        // Never obtained from the CUSTOM-0013 diagnostic role repository.
        static std::optional<RoleLevel> from_native22(std::span<const std::uint8_t>,std::uint64_t revision);
        const god2cn::CnRoleStatus& native_status() const noexcept {return status_;}
        std::uint64_t revision() const noexcept {return revision_;}
        bool operator==(const RoleLevel&) const = default;
    private:
        RoleLevel(god2cn::CnRoleStatus status,std::uint64_t revision):status_(status),revision_(revision) {}
        god2cn::CnRoleStatus status_;
        std::uint64_t revision_;
    };
    struct Row {
        std::uint64_t character;
        NameSource name_source;
        // Absent retains actual native07 level. Presence explicitly supplies
        // actual CN22; no optional0, default level1 or common profile offset.
        std::optional<RoleLevel> role_level;
        Row(std::uint64_t id,NameSource source):character(id),name_source(source) {}
        Row(std::uint64_t id,NameSource source,RoleLevel level)
            :character(id),name_source(source),role_level(std::move(level)) {}
        bool operator==(const Row&) const = default;
    };
    class NativeMetadata {
    public:
        struct Observation {
            // Complete actual native input and exact resulting output. Active
            // names and explicitly supplied level alone may differ. PostNUL
            // and other bytes are retained; rows expose full CN22/revision.
            std::span<const std::uint8_t> native_record,summary_record;
            std::span<const Row> rows;
            std::span<const RecoveredCharacter> account_roots;
        };
        // The real owner observes its revision, visibility, native metadata,
        // explicit prompt mode, projected common names AND supplied role22
        // identity/revision/level dependencies. No writes/yields,
        // fallback true, temporary references or inferred all-visible policy.
        using Current=std::function<bool(const Scope&,std::uint64_t,Summary::Check,const Observation&)>;
        static std::optional<NativeMetadata> from_source(Scope,std::uint64_t revision,
            god2cn::Bytes native07,std::vector<Row>,Current);
        NativeMetadata(const NativeMetadata&)=delete;
        NativeMetadata& operator=(const NativeMetadata&)=delete;
        NativeMetadata(NativeMetadata&&) noexcept=default;
        NativeMetadata& operator=(NativeMetadata&&)=delete;
    private:
        friend class SharedCommonCharacterSummarySource;
        NativeMetadata(Scope,std::uint64_t,god2cn::Bytes,std::vector<Row>,Current);
        Scope scope_;
        std::uint64_t revision_;
        god2cn::Bytes record_;
        std::vector<Row> rows_;
        Current current_;
    };
    // The source receives actual complete common roots from this same backend.
    // It supplies explicit ordered ID/visibility/native-slot mapping, not names
    // used as keys. All75 native bytes, including inactive rows, are mandatory.
    using Prepare=std::function<std::optional<NativeMetadata>(Scope,const std::vector<RecoveredCharacter>&)>;
    struct Config {
        Prepare prepare;
        explicit Config(Prepare source):prepare(std::move(source)) {}
    };
    // Same serial game owner/backend as real login/selection. The repository
    // must outlive the source and account drain. No DB is opened by this factory.
    static SharedAccountSelection::SummarySource create(RecoveredCharacterRepository&,Config);
};
}
