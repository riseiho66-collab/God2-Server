#pragma once
#include "cn/protocol/CnPreWorldCloseControl.h"
#include "cn/protocol/CnPreWorldCloseReply.h"
#include <array>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <utility>

namespace god2::cn {
// Complete native03 plus its actual operation owner. This is a source boundary,
// not an official reason/status generator or a native permission rule.
class SharedPreWorldCloseReply {
public:
    using Form=god2cn::CnPreWorldCloseControl::Form;
    enum class MutationKind {None,CharacterCreation,CharacterDeletion};
    struct Scope {
        std::uint64_t account,world_session;
        Form form;
        // Serial-owner identity of the designated mutation, not a native slot,
        // status/reason or durable replay key. Retain its actual lifetime.
        MutationKind mutation_kind=MutationKind::None;
        std::shared_ptr<const void> mutation_owner;
        bool operator==(const Scope&) const=default;
    };
    // Must check the real operation/phase/replay state for this exact session.
    // A control value, role, account or parsed record alone cannot supply it.
    // Runs on the serial game owner; captures must own their needed lifetimes.
    using CurrentOperation=std::function<bool(const Scope&)>;
    static std::optional<SharedPreWorldCloseReply> from_native(
        Scope scope,std::span<const std::uint8_t> record,CurrentOperation current) {
        const auto native=god2cn::CnPreWorldCloseReply::read(record);
        if(!scope.account || !scope.world_session || !native || !current)return std::nullopt;
        switch(scope.mutation_kind) {
        case MutationKind::None:if(scope.mutation_owner)return std::nullopt;break;
        case MutationKind::CharacterCreation:case MutationKind::CharacterDeletion:
            if(!scope.mutation_owner)return std::nullopt;break;
        default:return std::nullopt;
        }
        switch(scope.form) {
        case Form::Native0:case Form::OrdinaryCreateFailure:case Form::AfterCharacterDeletion:break;
        default:return std::nullopt;
        }
        return SharedPreWorldCloseReply(scope,native->record_bytes(),std::move(current));
    }
    SharedPreWorldCloseReply(const SharedPreWorldCloseReply&)=delete;
    SharedPreWorldCloseReply& operator=(const SharedPreWorldCloseReply&)=delete;
    SharedPreWorldCloseReply(SharedPreWorldCloseReply&&)=default;
    SharedPreWorldCloseReply& operator=(SharedPreWorldCloseReply&&)=default;
    bool current(const Scope& scope) const {
        return scope==scope_ && current_ && current_(scope_);
    }
    std::array<std::uint8_t,3> record_bytes() const {return record_;}
private:
    SharedPreWorldCloseReply(Scope scope,std::array<std::uint8_t,3> record,CurrentOperation current)
        :scope_(scope),record_(record),current_(std::move(current)) {}
    Scope scope_;
    std::array<std::uint8_t,3> record_;
    CurrentOperation current_;
};
}
