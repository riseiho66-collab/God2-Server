#pragma once
#include "cn/protocol/CnWorldSelectionStatus.h"
#include <cstdint>
#include <optional>
#include <span>
#include <variant>

namespace god2cn {
// 0047E960's two distinct native receive branches. A read-only record view,
// not an official deletion outcome, server error policy or S2C generator.
// Full23-byte02 preserves its existing status view;1E has one payloadBYTE.
// Evidence: cn-character-mutation-contract-01/native/0047ed00-cfg.json.
// cn-delete-completion-lifecycle-01 qualifies the02 branch: status0 makes
// 0047EC3B return EAX0, and the UI then compacts its local07 rows. A nonzero
// status returns that WORD. Neither branch proves shared save deletion;1E's
// decoder EAX0 is a different result consumed before the unresolved API tail.
struct CnCharacterDeleteReply {
    struct NativeControl {
        std::uint8_t value;
        // At0047EF89 the bounded switch control8 returns EAX0. The deletion
        // caller's later instruction boundary remains unresolved. Its declared
        // IAT binding is DeleteFileA (cn-delete-import-binding-01); an on-disk
        // nameRVA must not be interpreted as a loaded callableVA. This accessor
        // cannot authorize deletion or turn a control reply into generic success.
        // cn-delete-exception-frontier-01 traces UI00446BD0 ->007C7472
        // ->0074F0F0 ->007538BC with actual try-count0/EHflags1, plus the
        // bounded CRT filter0074A370. Neither supplies a skip/repair; this
        // does not prove absence of higher/dynamic/loaded exception sources.
        // cn-delete-caller-seh-frontier-01 retains the higher0044A470 EH,
        // actual CRT SEH4 filter/handler and initterm callback roots. Those
        // bounded sources still do not recover the complete1E result.
        // cn-crt-startup-callees-01 retains actual CRT callees, paired init
        // and encoded signal defaults. These do not qualify live per-thread
        // handlers/context repair or turn this decoder into save authority.
        // cn-crt-winapi-thunk-map-01 maps cached API lookup arguments and
        // DLL ranges; uncached/runtime exception sources remain open.
        bool native_control_decoder_returns_zero() const {return value==8;}
    };
    using Record=std::variant<CnWorldSelectionStatus,NativeControl>;
    static std::optional<Record> read(std::span<const std::uint8_t> record) {
        if(const auto status=CnWorldSelectionStatus::read(record))return Record{*status};
        if(record.size()==2 && record[0]==0x1e)return Record{NativeControl{record[1]}};
        return std::nullopt;
    }
};
}
