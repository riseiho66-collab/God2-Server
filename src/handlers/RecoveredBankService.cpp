#include "handlers/RecoveredBankService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredTrade.h"
namespace god2 {
namespace {
template<class Bytes>void append(std::vector<std::uint8_t>& out,const Bytes& bytes){out.insert(out.end(),bytes.begin(),bytes.end());}
void require(bool valid,const char* reason){if(!valid)throw DatabaseError(reason);}
}
std::vector<std::uint8_t> RecoveredBankService::synchronization(const SqliteBankRepository::Snapshot& s) {
    std::vector<std::uint8_t> out;append(out,RecoveredBank::balance(s.bank.amount));
    append(out,RecoveredTrade::wallet(s.wallet.amount));return out;
}
bool RecoveredBankService::permits_items(std::uint64_t session,std::uint16_t target,Clock::time_point now) {
    auto operation=callbacks_.enter();
    const auto deny=[&]{contexts_.erase(session);return false;};
    try {
    std::optional<Context> held;
    if(const auto found=contexts_.find(session);found!=contexts_.end())held=found->second;
    const auto live=invoke_adapter(lookup_,session);
    if(!held || !live || !live->ready || live->session!=session)return deny();
    const auto& c=*held;
    if(target!=c.target || now>=c.expires || live->session!=c.peer.session || live->account!=c.peer.account ||
       live->character!=c.peer.character || live->area!=c.peer.area || live->scene!=c.peer.scene ||
       !invoke_adapter(access_,*live,target))return deny();
    const bool saved=repo_.load(live->account,live->character)==c.expected;
    callbacks_.require_current();return saved?true:deny();
    }catch(...){contexts_.erase(session);return false;}
}
void RecoveredBankService::renew_items(std::uint64_t session,Clock::time_point now) {
    auto operation=callbacks_.enter();
    if(const auto found=contexts_.find(session);found!=contexts_.end())found->second.expires=now+std::chrono::seconds(60);
}
std::optional<std::vector<std::uint8_t>> RecoveredBankService::open(std::uint64_t session,
    std::uint16_t target,Clock::time_point now) {
    auto operation=callbacks_.enter();
    try {
        const auto peer=invoke_adapter(lookup_,session);
        if(!target || !peer || !peer->ready || peer->session!=session || !peer->account || !peer->character ||
           !invoke_adapter(access_,*peer,target)){contexts_.erase(session);return {};}
        const auto current=[&]{callbacks_.require_current();};
        repo_.provision_bank(peer->account,peer->character,current);callbacks_.require_current();
        const auto saved=repo_.load(peer->account,peer->character);callbacks_.require_current();
        std::vector<std::uint8_t> response;append(response,RecoveredBank::open(target));
        append(response,synchronization(saved));
        const auto live=invoke_adapter(lookup_,session);
        require(live&&live->ready&&live->session==session&&live->account==peer->account&&live->character==peer->character&&
            live->area==peer->area&&live->scene==peer->scene&&invoke_adapter(access_,*live,target),"Bank open callback changed world owner/access");
        callbacks_.require_current();
        contexts_.insert_or_assign(session,Context{*peer,target,saved,now+std::chrono::seconds(60)});return response;
    }catch(...){contexts_.erase(session);throw;}
}
RecoveredBankService::Result RecoveredBankService::handle(std::uint64_t session,
    std::span<const RecoveredBank::Request> requests,Clock::time_point now) {
    auto operation=callbacks_.enter();Result result;
    std::optional<Peer> live;std::optional<Context> opened;
    const auto reject=[&]() {
        result.rejected=true;contexts_.erase(session);
        if(callbacks_.invalidated())return result;
        // Recovery never reopens a lease and does not run after revocation.
        try {
            const auto recovery=invoke_adapter(lookup_,session);
            if(opened&&recovery&&recovery->ready&&recovery->session==session&&recovery->account==opened->peer.account&&
               recovery->character==opened->peer.character&&recovery->area==opened->peer.area&&recovery->scene==opened->peer.scene) {
                const auto exists=repo_.load_bank(recovery->account,recovery->character);callbacks_.require_current();
                if(exists){const auto saved=repo_.load(recovery->account,recovery->character);callbacks_.require_current();result.logical=synchronization(saved);}
            }
        }catch(...){result.logical.clear();}
        return result;
    };
    try {
        if(const auto found=contexts_.find(session);found!=contexts_.end())opened=found->second;
        require(requests.size()==1,"Bank batch invalid");const auto r=requests.front();
        live=invoke_adapter(lookup_,session);
        if(!opened || !live || !live->ready || live->session!=session)return reject();
        const auto context=*opened;
        const auto check_live=[&] {
            const auto peer=invoke_adapter(lookup_,session);
            require(peer&&peer->ready&&peer->session==session&&now<context.expires&&peer->account==context.peer.account&&
                peer->character==context.peer.character&&peer->area==context.peer.area&&peer->scene==context.peer.scene&&
                r.target==context.target&&invoke_adapter(access_,*peer,context.target),"Bank lease/target/access invalid");
            callbacks_.require_current();
        };
        check_live();
        if(r.kind==RecoveredBank::Kind::Close) {
            require(r.window_kind==1,"Bank window close kind invalid");contexts_.erase(session);return result;
        }
        require(repo_.load(live->account,live->character)==context.expected,"Bank saved snapshot changed");callbacks_.require_current();
        const SqliteBankRepository::Request proposal{context.expected,r.kind==RecoveredBank::Kind::Deposit?
            SqliteBankRepository::Operation::Deposit:SqliteBankRepository::Operation::Withdraw,r.amount};
        const auto next=SqliteBankRepository::plan(proposal);
        auto projected=synchronization(next);const auto receipt=invoke_adapter(receipt_);check_live();
        const auto committed=repo_.commit(receipt,proposal,[&]{callbacks_.require_current();});
        // A commit is durable even if a later callback retires its lease.
        static_assert(std::is_nothrow_copy_assignable_v<SqliteBankRepository::Snapshot>);
        static_assert(std::is_nothrow_move_assignable_v<std::vector<std::uint8_t>>);
        static_assert(std::is_nothrow_move_constructible_v<Result>);
        result.logical=std::move(projected);result.committed=true;
        if(callbacks_.invalidated()){contexts_.erase(session);result.logical.clear();return result;}
        if(const auto fresh=contexts_.find(session);fresh!=contexts_.end()) {
            fresh->second.expected=committed;fresh->second.expires=now+std::chrono::seconds(60);
        }
        return result;
    }catch(...){return reject();}
}
}
