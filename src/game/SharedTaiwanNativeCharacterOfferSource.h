#pragma once
#include "game/SharedTaiwanNativeCharacterListSource.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"

namespace god2 {
// Actual TW issuer -> existing shared native-summary writer -> List reader.
// No profile40/candidate36 serializer or invented visible order/token/routes.
class SharedTaiwanNativeCharacterOfferSource final {
public:
    using Source=SharedTaiwanNativeCharacterListSource;
    using Snapshot=NativeCharacterSummarySnapshot;
    using Issuer=SqliteNativeCharacterSummarySnapshotRepository::Issuer;
    class Offer {
    public:
        // Complete75 logical bytes, including flags and inactive physical rows,
        // actual ordered common IDs and real revision/origin/issuer authority.
        static std::optional<Offer> from_actual_source(Snapshot,Issuer);
        Offer(const Offer&)=delete;
        Offer& operator=(const Offer&)=delete;
        Offer(Offer&&) noexcept=default;
        Offer& operator=(Offer&&)=delete;
    private:
        friend class SharedTaiwanNativeCharacterOfferSource;
        friend class TaiwanMainNativeAuthority;
        Offer(Snapshot next,Issuer current):next_(std::move(next)),current_(std::move(current)) {}
        Snapshot next_;
        Issuer current_;
    };
    // Actual issuer/rules/visibility/resource owner. Observe owned full roots
    // and exact expected tuple; return no offer if unavailable. No SQL writes,
    // event pumping, retained borrowed arguments or guessed metadata/defaults.
    using Supply=std::function<std::optional<Offer>(Session&,const Source::Scope&,
        const Source::Target&,std::span<const RecoveredCharacter>,const std::optional<Snapshot>&)>;
    // Build on the same game owner and same actual writer/reader as the list.
    // Writer/accounts/characters outlive the existing Application facade drain.
    // The callback performs its explicit own transaction only when List invokes
    // it. Current/Select never invokes it; no SQL or schema install in create.
    static Source::Prepare create(SqliteNativeCharacterSummarySnapshotRepository&,
        AccountRepository&,RecoveredCharacterRepository&,std::string client_sha256,Supply);
};
}
