#pragma once
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "net/Session.h"
#include <map>
#include <memory>
#include <optional>
namespace god2 {
// CUSTOM-0142: persist only an actual user's B4 choice, replay its E8 display
// on genuine subsequent normal entry. No default, battle slot or pet rule.
// The fixed pin identifies the qualified protocol/source policy, not an
// attestation of the executable used by the remote peer.
class OwnedBattleRowPreference final {
public:
    static constexpr const char* client_pin="aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48";
    static constexpr const char* record_kind="tw_b4_row_choice_e8_v1";
    static constexpr const char* source_record="CUSTOM-0142 explicit C2S B4 user choice -> E8 display; TW aaf0:4E8910/4E8D8D; E8 46B46E/4E8550/4E8580; no battle deployment/default rule";
    OwnedBattleRowPreference(SqliteNativeWorldEntrySnapshotRepository&,AccountRepository&,
        RecoveredCharacterRepository&,std::size_t capacity);
    // Guard the WHOLE actual final callback, including original inner runs.
    bool begin() noexcept;
    void end() noexcept {busy_=false;}
    bool current() const noexcept {return busy_ && !poisoned_ && !stopped_;}
    void ready(const Session&) noexcept;
    void disconnect(const Session&) noexcept;
    void defer_unavailable_replay(Session&); // Error marker, never an absent/default row.
    void stop() noexcept {stopped_=true;if(busy_)poisoned_=true;}
    // Own frame/state/merged allocation precedes persistence and expect().
    // Null supplied means replay only. False rejects this actual callback;
    // committed persistence is never reported as rolled back or retried.
    bool synchronize(Session&,std::optional<std::uint8_t> supplied,std::vector<std::uint8_t>& wire);
private:
    struct Entry {
        std::weak_ptr<Session> session;
        std::uint64_t account,character;
        Session::NormalWorldInitialization initialization;
        bool pending;
        bool source_unavailable;
        std::optional<Session::NormalWorldResponseAttempt> response;
    };
    using State=std::map<std::uint64_t,Entry>;
    SqliteNativeWorldEntrySnapshotRepository& repository_;
    RecoveredCharacterRepository& characters_;
    std::size_t capacity_;
    std::shared_ptr<const State> state_=std::make_shared<const State>();
    bool busy_=false,poisoned_=false,stopped_=false;
};
}
