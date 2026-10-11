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
bool RecoveredBankService::permits_items(std::uint64_t session,std::uint16_t target,Clock::time_point now) const {
    const auto at=contexts_.find(session);const auto live=lookup_(session);
    if(at==contexts_.end() || !live || !live->ready)return false;
    const auto& c=at->second;
    return target==c.target && now<c.expires && live->session==c.peer.session && live->account==c.peer.account &&
        live->character==c.peer.character && live->area==c.peer.area && live->scene==c.peer.scene &&
        access_(*live,target) && repo_.load(live->account,live->character)==c.expected;
}
void RecoveredBankService::renew_items(std::uint64_t session,Clock::time_point now) {
    if(const auto at=contexts_.find(session);at!=contexts_.end())at->second.expires=now+std::chrono::seconds(60);
}
std::optional<std::vector<std::uint8_t>> RecoveredBankService::open(std::uint64_t session,
    std::uint16_t target,Clock::time_point now) {
    const auto peer=lookup_(session);
    if(!target || !peer || !peer->ready || !peer->session || !peer->account || !peer->character || !access_(*peer,target))return {};
    repo_.provision_bank(peer->account,peer->character);
    const auto saved=repo_.load(peer->account,peer->character);
    std::vector<std::uint8_t> response;append(response,RecoveredBank::open(target));
    append(response,synchronization(saved));
    contexts_.insert_or_assign(session,Context{*peer,target,saved,now+std::chrono::seconds(60)});
    return response;
}
RecoveredBankService::Result RecoveredBankService::handle(std::uint64_t session,
    std::span<const RecoveredBank::Request> requests,Clock::time_point now) {
    Result result;
    const auto at=contexts_.find(session);const auto live=lookup_(session);
    const auto reject=[&]() {
        result.rejected=true;contexts_.erase(session);
        // This absolute sync does not reopen a bank or authorize any mutation.
        try {
            if(live && live->ready && repo_.load_bank(live->account,live->character))
                result.logical=synchronization(repo_.load(live->account,live->character));
        }catch(const LegacyCoinProjectionError&){result.logical.clear();}
        return result;
    };
    if(at==contexts_.end() || !live || !live->ready || requests.size()!=1)return reject();
    try {
        const auto context=at->second;const auto& r=requests.front();
        require(now<context.expires && live->session==context.peer.session && live->account==context.peer.account &&
            live->character==context.peer.character && live->area==context.peer.area && live->scene==context.peer.scene &&
            access_(*live,context.target) && r.target==context.target,"Bank lease/target/access invalid");
        if(r.kind==RecoveredBank::Kind::Close) {
            require(r.window_kind==1,"Bank window close kind invalid");contexts_.erase(at);return result;
        }
        require(repo_.load(live->account,live->character)==context.expected,"Bank saved snapshot changed");
        const SqliteBankRepository::Request proposal{context.expected,r.kind==RecoveredBank::Kind::Deposit?
            SqliteBankRepository::Operation::Deposit:SqliteBankRepository::Operation::Withdraw,r.amount};
        const auto next=SqliteBankRepository::plan(proposal);
        auto projected=synchronization(next);const auto receipt=receipt_();
        const auto committed=repo_.commit(receipt,proposal);
        // A subsequent same-valued request can be another legitimate click:
        // native61/62 have no unique request ID. Conservation and CAS enforce
        // authority, while duplicate records in one batch are rejected above.
        at->second.expected=committed;at->second.expires=now+std::chrono::seconds(60);
        result.logical=std::move(projected);result.committed=true;return result;
    } catch(const DatabaseError&) {return reject();}
      catch(const LegacyCoinProjectionError&) {return reject();}
}
}
