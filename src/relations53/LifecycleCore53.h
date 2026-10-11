#pragma once
#include "Succession53ReaderDraft.h"
namespace god2 {
class LifecycleCore53 {
    friend class RelationsRepositoryDraft;
public:
    using Succession=Succession53ReaderDraft;
    using Original=Succession::Original;
private:
    struct CreationSnapshot {std::uint64_t next_id{},next_revision{};std::vector<std::vector<std::uint8_t>> guild_rows;bool operator==(const CreationSnapshot&)const=default;};
    struct Created52 {Succession::EffectiveLeader leader;Original::Wallet wallet;};
    struct Disbanded {Succession::EffectiveLeader before;Original::Guild retired;std::vector<Original::Application> removed_applications;};
    LifecycleCore53(sqlite3*,Original&,Succession&);
    CreationSnapshot creation_snapshot();
    Created52 create52(const Original::Identity&,const Original::Wallet&,const std::string&,const Original::Policy&,const CreationSnapshot&,const Original::Proof&);
    Disbanded disband(const Succession::EffectiveLeader&,const std::vector<Original::Application>&,const Original::Proof&);
    sqlite3* db_;Original& original_;Succession& effective_;
};
}
