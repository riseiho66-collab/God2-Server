#include "cn/net/OperationalTransportSeed.h"
#include <algorithm>
#include <memory>
#include <set>
#include <stdexcept>
#include <thread>
#include <utility>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2::cn {
namespace {
using Endpoint=SharedServerPlan::Endpoint;
using Role=SharedServerPlan::Role;

#ifdef _WIN32
bool same_endpoint(const Endpoint& a,const Endpoint& b) {
    if(a.host!=b.host || a.port!=b.port || a.role!=b.role ||
       a.target.has_value()!=b.target.has_value())return false;
    return !a.target || (a.target->group==b.target->group && a.target->server==b.target->server);
}
#endif

void qualified_endpoints(const std::vector<Endpoint>& endpoints) {
    std::size_t accounts=0,worlds=0;
    std::set<std::pair<asio::ip::address,std::uint16_t>> sockets;
    std::set<std::pair<std::uint16_t,std::uint16_t>> targets;
    for(const auto& e:endpoints) {
        const auto address=asio::ip::make_address(e.host);
        if(!e.port || !sockets.emplace(address,e.port).second)
            throw std::invalid_argument("CN seed source requires actual unique listener endpoints");
        if(e.role==Role::Account && !e.target)++accounts;
        else if(e.role==Role::World && e.target && e.target->group<64 && e.target->server<10 &&
                targets.emplace(e.target->group,e.target->server).second)++worlds;
        else throw std::invalid_argument("CN seed source endpoint role/target unqualified");
    }
    if(accounts!=1 || !worlds)
        throw std::invalid_argument("CN seed source requires one account and actual world listeners");
}

#ifdef _WIN32
struct Issuer {
    const std::thread::id owner=std::this_thread::get_id();
    const std::vector<Endpoint> endpoints;
    std::uint64_t last_connection=0;
    explicit Issuer(std::vector<Endpoint> e):endpoints(std::move(e)) {}

    std::optional<std::array<std::uint8_t,16>> issue(std::uint64_t id,const Endpoint& endpoint) {
        // Check thread before reading mutable state. The listener obtains IDs
        // on its serial game owner via the existing next_connection_identity.
        if(owner!=std::this_thread::get_id())
            throw std::logic_error("CN seed issuer game owner mismatch");
        if(!id || id<=last_connection || std::none_of(endpoints.begin(),endpoints.end(),
            [&endpoint](const auto& actual){return same_endpoint(actual,endpoint);}))return std::nullopt;
        // Consume even a failed issuance: never retry/replay on the same socket.
        // Values are not forced unique; actual CNG output may contain any byte.
        last_connection=id;
        std::array<std::uint8_t,16> bytes{};
        const auto status=BCryptGenRandom(nullptr,bytes.data(),static_cast<ULONG>(bytes.size()),
                                         BCRYPT_USE_SYSTEM_PREFERRED_RNG);
        if(!BCRYPT_SUCCESS(status)) {
            SecureZeroMemory(bytes.data(),bytes.size());
            return std::nullopt;
        }
        std::optional<std::array<std::uint8_t,16>> result{bytes};
        SecureZeroMemory(bytes.data(),bytes.size());
        return result;
    }
};
#endif
}

SharedServerPlan::Controllers::Seed make_operational_transport_seed_source(
    OperationalTransportSeedPolicy policy,std::vector<Endpoint> endpoints) {
    if(policy!=OperationalTransportSeedPolicy::WindowsSystemCngV1)
        throw std::invalid_argument("CN transport seed operational policy unavailable");
    qualified_endpoints(endpoints);
#ifdef _WIN32
    auto issuer=std::make_shared<Issuer>(std::move(endpoints));
    return [issuer=std::move(issuer)](std::uint64_t id,const Endpoint& endpoint) {
        return issuer->issue(id,endpoint);
    };
#else
    throw std::runtime_error("CN Windows system CNG transport seed unavailable on this platform");
#endif
}
}
