#pragma once
#include "game/SharedWorldPresence.h"
#include "text/OwnedCharacterNameText.h"
#include <memory>
#include <string_view>

namespace god2 {
// Common ready character/name identity only. This source grants no permission,
// native actor/header mapping, offline existence, membership or sender reply.
class SharedChatIdentitySource {
    struct Identity;
    struct Storage;
public:
    enum class Result {Matched,NoReadyMatch,Ambiguous,UnqualifiedTarget};
    class Lookup {
    public:
        Lookup(const Lookup&)=default;
        Lookup& operator=(const Lookup&)=default;
        // Both handles retain the same immutable complete identity observation.
        Lookup(Lookup&&) noexcept;
        Lookup& operator=(Lookup&&) noexcept;
        Result result() const noexcept;
        std::string_view raw_target() const noexcept;
        std::uint16_t codepage() const noexcept;
        std::optional<std::string_view> original_utf8() const noexcept;
        const std::vector<SharedWorldPresence::ReadyCharacter>& population() const noexcept;
        const std::vector<OwnedCharacterNameText>& names() const noexcept;
        const SharedWorldPresence::ReadyCharacter* matched() const noexcept;
        const OwnedCharacterNameText* matched_name() const noexcept;
    private:
        friend class SharedChatIdentitySource;
        explicit Lookup(std::shared_ptr<const Storage>);
        std::shared_ptr<const Storage> storage_;
    };
    static std::shared_ptr<SharedChatIdentitySource> create(std::shared_ptr<SharedWorldPresence>);
    ~SharedChatIdentitySource();
    SharedChatIdentitySource(const SharedChatIdentitySource&)=delete;
    SharedChatIdentitySource& operator=(const SharedChatIdentitySource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const;
    // Raw target is qualified only through strict original encoding. No script
    // conversion, folding, trimming, normalization, replacements or defaults.
    // Wire target page must be explicit936/950; stored page0 qualifies only
    // unchanged ASCII through existing common name metadata, not host ACP.
    // UnqualifiedTarget is an explicit result for actual Owner policy, with a
    // real complete population. An unqualified stored name fails the read.
    std::optional<Lookup> lookup(std::string_view raw_target,std::uint16_t explicit_codepage) const;
    bool current(const Lookup&) const;
private:
    explicit SharedChatIdentitySource(std::shared_ptr<SharedWorldPresence>);
    void owner() const;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<const Identity> identity_;
    std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,reentered_=false;
    bool terminal_=false;
};
}
