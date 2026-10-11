#include "cn/auth/SharedAccountVerifier.h"
#include "auth/PasswordHash.h"
#include <algorithm>
#include <array>
#include <limits>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>

namespace god2::cn {
namespace {
std::size_t worker_count(std::size_t n) {
    if(!n || n>16)throw std::invalid_argument("Invalid shared CN authentication worker count");
    return n;
}
std::string storage_identity(std::string_view bytes,bool ascii_fold) {
    constexpr char hex[]="0123456789abcdef";
    std::string result="god2-bytes:";
    const bool ascii=std::all_of(bytes.begin(),bytes.end(),[](unsigned char c){return c<0x80;});
    for(unsigned char c:bytes) {
        if(ascii_fold && ascii && c>='A' && c<='Z')c=static_cast<unsigned char>(c-'A'+'a');
        result.push_back(hex[c>>4]);result.push_back(hex[c&15]);
    }
    return result;
}
struct Secret {
    explicit Secret(std::string_view input):size(input.size()) {
        std::copy(input.begin(),input.end(),bytes.begin());
    }
    ~Secret() {
        volatile char* p=bytes.data();
        for(std::size_t i=0;i<bytes.size();++i)p[i]=0;
    }
    Secret(const Secret&)=delete;
    Secret& operator=(const Secret&)=delete;
    std::string_view view() const {return {bytes.data(),size};}
    std::array<char,131> bytes{};
    std::size_t size;
};
void clear_string(std::string& value) {
    volatile char* bytes=value.data();
    for(std::size_t i=0;i<value.size();++i)bytes[i]=0;
}
struct VerifiedSnapshot {
    explicit VerifiedSnapshot(Account value):row(std::move(value)) {}
    ~VerifiedSnapshot(){clear_string(row.username);clear_string(row.password_hash);}
    Account row;
};
}
VerifiedCredentialSource::VerifiedCredentialSource(std::uint32_t account,std::function<bool()> current)
    :account_(account),current_(std::move(current)) {}
bool VerifiedCredentialSource::current(std::uint32_t account) const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN credential source owner mismatch");
    if(!account || account!=account_ || !current_)return false;
    try {return current_();}catch(...) {return false;}
}
struct SharedAccountVerifier::State {
    AccountRepository& accounts;
    asio::any_io_executor game;
    std::thread::id thread=std::this_thread::get_id();
    std::size_t capacity;
    std::size_t pending=0;
    bool stopped=false;
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("Shared CN authentication owner mismatch");
    }
};
SharedAccountVerifier::SharedAccountVerifier(AccountRepository& accounts,asio::any_io_executor game,
    std::size_t workers,std::size_t capacity)
    :state_(std::make_shared<State>(State{accounts,std::move(game),std::this_thread::get_id(),capacity})),
     workers_(worker_count(workers)) {
    if(!capacity || capacity>4096)throw std::invalid_argument("Invalid shared CN authentication capacity");
}
SharedAccountVerifier::~SharedAccountVerifier() {
    if(state_->thread!=std::this_thread::get_id())std::terminate();
    state_->stopped=true;
    workers_.stop();workers_.join();
}
void SharedAccountVerifier::verify_raw_ui(std::string_view account,std::string_view password,Completion done) {
    state_->owner();
    if(!done)throw std::invalid_argument("Shared CN authentication completion required");
    if(state_->stopped){done({CredentialOutcome::InternalFailure});return;}
    if(account.empty() || account.size()>23 || account.find('\0')!=std::string_view::npos ||
       password.empty() || password.size()>131 || password.find('\0')!=std::string_view::npos) {
        done({CredentialOutcome::Rejected});return;
    }
    if(state_->pending>=state_->capacity){done({CredentialOutcome::Busy});return;}
    std::optional<Account> snapshot;
    try {
        const auto exact=storage_identity(account,false);
        const auto folded=storage_identity(account,true);
        snapshot=state_->accounts.find_by_username(exact);
        if(!snapshot && folded!=exact)snapshot=state_->accounts.find_by_username(folded);
    } catch(...) {done({CredentialOutcome::InternalFailure});return;}
    if(!snapshot){done({CredentialOutcome::NotRegistered});return;}
    // The shared database has 64-bit identities; CN accountid is a native DWORD.
    // Do not truncate an existing account into another player's identity.
    if(!snapshot->id || snapshot->id>std::numeric_limits<std::uint32_t>::max()) {
        done({CredentialOutcome::InternalFailure});return;
    }
    auto secret=std::make_shared<Secret>(password);
    auto state=state_;
    auto work=asio::make_work_guard(state->game);
    ++state->pending;
    try {
        asio::post(workers_,[state,secret=std::move(secret),snapshot=std::move(*snapshot),
                            done=std::move(done),work=std::move(work)]() mutable {
            CredentialOutcome outcome=CredentialOutcome::InternalFailure;
            try {outcome=PasswordHash::verify(secret->view(),snapshot.password_hash)
                    ?CredentialOutcome::Verified:CredentialOutcome::Rejected;}
            catch(...) { /* Never log credential-bearing buffers or exceptions. */ }
            secret.reset();
            asio::post(state->game,[state,snapshot=std::move(snapshot),outcome,
                                    done=std::move(done),work=std::move(work)]() mutable {
                state->owner();--state->pending;
                if(state->stopped){done({CredentialOutcome::InternalFailure});return;}
                if(outcome==CredentialOutcome::Verified) {
                    try {
                        const auto current=state->accounts.find_by_id(snapshot.id);
                        if(!current || current->username!=snapshot.username || current->password_hash!=snapshot.password_hash)
                            outcome=CredentialOutcome::Changed;
                    } catch(...) {outcome=CredentialOutcome::InternalFailure;}
                }
                if(outcome==CredentialOutcome::Verified) {
                    // This is the exact snapshot verified by PasswordHash and
                    // compared above, not a new row captured after callback.
                    // No callback/yield occurs between that comparison and
                    // token issuance on the shared repository owner thread.
                    std::shared_ptr<const VerifiedCredentialSource> source;
                    const auto account=static_cast<std::uint32_t>(snapshot.id);
                    try {
                        auto binding=std::make_shared<VerifiedSnapshot>(std::move(snapshot));
                        std::weak_ptr<State> weak=state;
                        source=std::shared_ptr<const VerifiedCredentialSource>(new VerifiedCredentialSource(account,
                            [weak,binding] {
                                const auto owner=weak.lock();
                                if(!owner)return false;
                                owner->owner();if(owner->stopped)return false;
                                auto current=owner->accounts.find_by_id(binding->row.id);
                                if(!current)return false;
                                VerifiedSnapshot observation(std::move(*current));
                                return observation.row.id==binding->row.id &&
                                    observation.row.username==binding->row.username &&
                                    observation.row.password_hash==binding->row.password_hash;
                            }));
                    }catch(...) {done({CredentialOutcome::InternalFailure});return;}
                    done({outcome,account,std::move(source)});
                }
                else done({outcome});
            });
        });
    } catch(...) {--state->pending;throw;}
}
}
