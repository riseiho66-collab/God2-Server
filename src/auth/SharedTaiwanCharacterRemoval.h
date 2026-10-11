#pragma once
#include "auth/RecoveredAccountLogin.h"
#include "auth/SharedCharacterRemoval.h"
#include "net/Session.h"
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <thread>

namespace god2 {
// Additive TW19 adapter for the actual Session delete_character callback.
// Explicit opt-in only: frozen Application/Session auth, parser and02/03 queue
// remain unchanged. A common idle character is NOT native deletion permission.
class SharedTaiwanCharacterRemoval {
public:
    using Phase=SharedCharacterRemoval::Phase;
    class Attempt {
        friend class SharedTaiwanCharacterRemoval;
        Attempt()=default;
    };
    struct Scope {
        std::uint64_t account,session,character;
        std::uint8_t native_slot;
        std::shared_ptr<const Attempt> attempt;
        bool operator==(const Scope&) const=default;
    };
    // Actual native permission/guild/operation/replay predicate, prepared with
    // copied common identity BEFORE SQL. BeforeCommit has the root/descendants
    // staged absent: missing guild membership then is not proof of permission.
    // No borrowed Scope/snapshot captures, credentials, mutation, nested SQL,
    // event pump or yield. This is not a default-true rules implementation.
    using Current=std::function<bool(const Scope&,Phase)>;
    struct Sources {
        AccountRepository* accounts=nullptr;
        RecoveredAccountLogin* login=nullptr;
        SqliteRecoveredCharacterRepository* characters=nullptr;
        std::shared_ptr<SharedWorldAdmission> admission;
        std::shared_ptr<const SharedCharacterRemovalPresence> presence;
        std::function<std::optional<Current>(const Scope&,const RecoveredCharacter&)> prepare;
        explicit operator bool() const noexcept {
            return accounts && login && characters && admission && presence && prepare;
        }
    };
    using Handler=std::function<bool(Session&,const RecoveredCharacterDelete&)>;
    // Same signature as Session::RecoveredCharacterHandlers.delete_character.
    // Host retains actual account/login/character/legacy objects for handler
    // lifetime and supplies the SAME admission/presence used by TW and CN.
    // An invalid/mismatched source returns no handler, never a legacy fallback.
    static Handler handler(Sources);
private:
    explicit SharedTaiwanCharacterRemoval(Sources);
    void owner() const;
    bool handle(Session&,const RecoveredCharacterDelete&);
    std::uint64_t verify(const RecoveredCharacterDelete&);
    std::optional<RecoveredCharacter> resolve(std::uint64_t,const RecoveredCharacterDelete&);
    std::thread::id thread_=std::this_thread::get_id();
    Sources sources_;
    bool busy_=false;
};
}
