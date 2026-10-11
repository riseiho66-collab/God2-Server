#pragma once
// PRIVATE CUSTOM0083 actual effective52 writes, never fake old Governance/Leader.
#include "db/SqliteOwnedGuildSuccessionRepositoryDraft.h"
namespace god2 {
class EffectiveGuildAdmissionRepositoryDraft {
public:
    using Succession=SqliteOwnedGuildSuccessionRepositoryDraft;
    using Original=Succession::Original;
    struct Approved {Succession::EffectiveLeader before,after;StoredGuildMembership joined;std::vector<Original::Application> applications;};
    struct Rejected {Succession::EffectiveLeader before,after;std::vector<Original::Application> applications;};
    EffectiveGuildAdmissionRepositoryDraft(sqlite3*,Original&,Succession&);
    Approved approve(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    Rejected reject(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    Original::Application apply(const Original::Identity&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    void cancel(const Original::Identity&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    struct Removed {Succession::EffectiveLeader before,after;Original::Identity identity;StoredGuildMembership previous_join;bool founder_kick;};
    Removed leave(const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    Removed kick(const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    struct OfficeChanged {Succession::EffectiveLeader before,after;Original::Identity target;StoredGuildMembership join;Original::OfficerAction action;};
    OfficeChanged change_officer(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Identity&,const StoredGuildMembership&,Original::OfficerAction,const Original::Proof&);
    struct Disbanded {Succession::EffectiveLeader before;Original::Guild retired;std::vector<Original::Application> removed_applications;};
    Disbanded disband(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    struct CreationSnapshot {std::uint64_t next_id{},next_revision{};std::vector<std::vector<std::uint8_t>> guild_rows;bool operator==(const CreationSnapshot&)const=default;};
    struct Created52 {Succession::EffectiveLeader leader;Original::Wallet wallet;};
    CreationSnapshot creation_snapshot();
    Created52 create52(const Original::Identity&,const Original::Wallet&,const std::string&,const Original::Policy&,const CreationSnapshot&,const Original::Proof&);
private:
    Removed remove_member(bool,const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    sqlite3* db_;Original& original_;Succession& effective_;
};
}
