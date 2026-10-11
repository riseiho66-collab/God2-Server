#pragma once
// PRIVATE CUSTOM84 strict53 neighboring ports preserve CUSTOM83 writes.
#include "db/DbTypes.h"
#include "Succession53ReaderDraft.h"
#include "RelationsRepositoryDraft.h"
namespace god2 {
class NeighboringGuild53AdmissionRepositoryDraft {
public:
    using Succession=Succession53ReaderDraft;
    using Original=Succession::Original;
    struct Approved {Succession::EffectiveLeader before,after;StoredGuildMembership joined;std::vector<Original::Application> applications;};
    struct Rejected {Succession::EffectiveLeader before,after;std::vector<Original::Application> applications;};
    NeighboringGuild53AdmissionRepositoryDraft(sqlite3*,Original&,Succession&,bool enabled=false,RelationsRepositoryDraft* relations=nullptr);
    Approved approve(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    Rejected reject(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    Original::Application apply(const Original::Identity&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    void cancel(const Original::Identity&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Application&,const Original::Proof&);
    struct Removed {Succession::EffectiveLeader before,after;Original::Identity identity;StoredGuildMembership previous_join;bool founder_kick;};
    Removed leave(const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    Removed kick(const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    struct OfficeChanged {Succession::EffectiveLeader before,after;Original::Identity target;StoredGuildMembership join;Original::OfficerAction action;};
    OfficeChanged change_officer(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Identity&,const StoredGuildMembership&,Original::OfficerAction,const Original::Proof&);
    struct CreationSnapshot {std::uint64_t next_id{},next_revision{};std::vector<std::vector<std::uint8_t>> guild_rows;bool operator==(const CreationSnapshot&)const=default;};
    struct Created53 {Succession::EffectiveLeader leader;Original::Wallet wallet;};
    CreationSnapshot creation_snapshot();
    Created53 create53(const Original::Identity&,const Original::Wallet&,const std::string&,const Original::Policy&,const CreationSnapshot&,const Original::Proof&,const RelationsRepositoryDraft::Authority&);
private:
    Removed remove_member(bool,const Original::Identity&,const StoredGuildMembership&,const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    sqlite3* db_;Original& original_;Succession& effective_;bool enabled_;
    RelationsRepositoryDraft* relations_{};
    void require_enabled()const {if(!enabled_)throw DatabaseError("PRIVATE CUSTOM84 neighboring53 disabled");effective_.require_exact_schema53();}
};
}
