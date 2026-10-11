#pragma once
#include "game/SharedTaiwanWorldRecordSource.h"
#include "game/SharedTaiwanNativeChatSource.h"
#include "game/SharedTaiwanNativeSpectatorSource.h"

namespace god2 {
// Explicit ordered actual handler assembly for the native mixed dispatcher.
// Raw2F headers and all other variants retain their separate native domains;
// no frozen CUSTOM handler is selected implicitly.
class SharedTaiwanNativeRecordHandlerSource final {
public:
    using Binding=SharedTaiwanWorldRecordSource::OtherBinding;
    // Existing parser emits four separate2F variants. Normalization copies the
    // exact original header/text only and checks the parser's selector domain;
    // it never grants membership, resolves names or narrows an actor identity.
    static bool native_chat_record(const RecoveredWorldRecords::Record&) noexcept;
    static std::optional<RecoveredChat::Request> chat_request(const RecoveredWorldRecords::Record&);
    // Use from RecordSources construction on the same Application Context.
    // Both actual providers own their dependencies strongly on game; remaining
    // receives every maximal non-chat span, including controls/diagnostics.
    // Native chat returns this sender's encrypted frames instead of submitting
    // them ahead of earlier accumulated replies in the mixed batch.
    static Binding create(SharedTaiwanNativeChatSource::Binding,Binding remaining,
        std::size_t actual_output_byte_budget);
    // Explicit typed6E owner, not a generic remaining handler or parser flag.
    // Complete batch/request copies precede every child effect; encrypted
    // replies retain chat/spectator/remaining record order.
    static Binding create(SharedTaiwanNativeChatSource::Binding,
        SharedTaiwanNativeSpectatorSource::Binding,Binding remaining,
        std::size_t actual_output_byte_budget);
};
}
