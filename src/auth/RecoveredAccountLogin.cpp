#include "auth/RecoveredAccountLogin.h"
#include "auth/PasswordHash.h"
#include <stdexcept>
#include <algorithm>
#include <string>
#include <string_view>

namespace god2 {
std::optional<RecoveredAccountLogin::Attempt> RecoveredAccountLogin::prepare(const RecoveredC2S0002::Parsed& request) {
    // Do not trust a caller-constructed Parsed object to have passed the decoder.
    const auto checked=RecoveredC2S0002::parse(request.raw,request.logical[0]);
    if(!checked || checked->logical!=request.logical) return std::nullopt;
    const auto& p=checked->logical;
    const auto name_end=std::find(p.begin()+1,p.begin()+25,0);
    const auto password_end=std::find(p.begin()+25,p.begin()+157,0);
    if(name_end==p.begin()+1 || password_end==p.begin()+25) return std::nullopt;
    // Preserve the exact identity first for existing accounts.
    // This namespaced hex identity is not a display name or a UTF-8 conversion.
    constexpr char hex[]="0123456789abcdef";
    std::string identity="god2-bytes:";
    for(auto it=p.begin()+1;it!=name_end;++it) {
        identity.push_back(hex[*it>>4]);identity.push_back(hex[*it&15]);
    }
    const std::string_view password(reinterpret_cast<const char*>(p.data()+25),
        static_cast<std::size_t>(password_end-(p.begin()+25)));
    // The original client used to force ASCII account names to lowercase.
    // Keep existing exact identities reachable while allowing the fixed
    // client to display and submit the case the player actually typed.
    std::string folded_identity=identity;
    // Only fold wholly ASCII names: a Big5/GBK trailing byte can be A-Z.
    if(std::all_of(p.begin()+1,name_end,[](unsigned char byte){return byte<0x80;})) {
        folded_identity="god2-bytes:";
        for(auto it=p.begin()+1;it!=name_end;++it) {
            auto byte=*it;
            if(byte>='A' && byte<='Z') byte=static_cast<unsigned char>(byte-'A'+'a');
            folded_identity.push_back(hex[byte>>4]);folded_identity.push_back(hex[byte&15]);
        }
    }
    auto account=accounts_.find_by_username(identity);
    if(!account && folded_identity!=identity) account=accounts_.find_by_username(folded_identity);
    if(!account && (!allow_registration_ || p[0]!=4)) return std::nullopt;
    return Attempt{folded_identity,std::string(password),account};
}
std::uint64_t RecoveredAccountLogin::authenticate(const RecoveredC2S0002::Parsed& request) {
    auto attempt=prepare(request);
    if(!attempt) return 0;
    if(attempt->account) return PasswordHash::verify(attempt->password,attempt->account->password_hash)
        ? attempt->account->id : 0;
    return accounts_.create(attempt->identity,PasswordHash::create(attempt->password)).id;
}
void RecoveredAccountLogin::authenticate_async(const RecoveredC2S0002::Parsed& request,
    asio::any_io_executor workers,asio::any_io_executor game,Completion done) {
    // Entry and completion run on the serial game executor. Only hashing runs
    // on workers; no worker touches the game-owned SQLite connection.
    std::optional<Attempt> attempt;
    try {
        if(pending_>=64) throw std::runtime_error("Authentication queue full");
        attempt=prepare(request);
    } catch(...) { done(0,std::current_exception());return; }
    if(!attempt) { done(0,{});return; }
    ++pending_;
    auto work=asio::make_work_guard(game);
    asio::post(workers,[this,work,attempt=std::move(*attempt),request,workers,game,done]() mutable {
        bool verified=false;
        std::string created_hash;
        std::exception_ptr error;
        try {
            if(attempt.account) verified=PasswordHash::verify(attempt.password,attempt.account->password_hash);
            else created_hash=PasswordHash::create(attempt.password);
        } catch(...) { error=std::current_exception(); }
        asio::post(game,[this,work,attempt=std::move(attempt),request,workers,game,done,verified,
                         created_hash=std::move(created_hash),error]() mutable {
            --pending_;
            if(error) { done(0,error);return; }
            std::uint64_t id=0;
            try {
                if(attempt.account) {
                    auto current=accounts_.find_by_id(attempt.account->id);
                    if(current && current->password_hash==attempt.account->password_hash && verified)
                        id=current->id;
                    else if(current && current->password_hash!=attempt.account->password_hash) {
                        authenticate_async(request,workers,game,done);return;
                    }
                } else if(accounts_.find_by_username(attempt.identity)) {
                    // Another concurrent first login won registration. Verify
                    // its original password; never overwrite or blindly bind.
                    authenticate_async(request,workers,game,done);return;
                } else id=accounts_.create(attempt.identity,created_hash).id;
            } catch(...) { done(0,std::current_exception());return; }
            done(id,{});
        });
    });
}
}
