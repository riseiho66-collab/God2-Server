#include "net/TaiwanChannelServers.h"
#include "protocol/RecoveredServerRoutes.h"
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
void require_complete(const TaiwanChannelServers::Sources& source) {
    const auto& h=source.characters;
    if(!source.packet||!source.disconnected||!source.authenticate||!h.native_list||!h.native_select||
       !h.native_list_current||!h.native_list_complete||!h.create||h.list||h.select_created||h.select_existing||
       !h.world_entry||!h.world_ready||!h.world_records||h.movement||h.common_world_lifecycle||
       !h.common_world_lifecycle_factory||!h.common_world_cleanup_owner||!h.common_world_lifecycle_abandon||
       !h.common_world_publication_owner)
        throw std::invalid_argument("Each native channel needs its complete independent game-owned source facades");
}
}
TaiwanChannelServers::TaiwanChannelServers(asio::io_context& network,asio::any_io_executor game,
        const SharedTaiwanChannelWorlds& worlds,std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration,
        std::uint8_t group,std::uint8_t group_byte_1,const std::array<EndpointPolicy,3>& policies,
        std::size_t capacity,bool packet_dump,SourceFactory factory) {
    if(!configuration||configuration->configured_slots(group)!=std::optional<std::uint8_t>{3}||group>=10||!capacity||!factory)
        throw std::invalid_argument("Three channels require three actual configured slots and complete source factory");
    std::array<Sources,3> sources;
    for(std::uint8_t k=0;k<3;++k) {
        if(policies[k].address[0]!=127||!policies[k].route_body[0])
            throw std::invalid_argument("Native channels require explicit loopback routes and nonzero snapshot keys");
        for(std::uint8_t j=0;j<k;++j)
            if(policies[k].port&&policies[k].port==policies[j].port&&policies[k].address==policies[j].address)
                throw std::invalid_argument("Native channels cannot alias a configured endpoint");
        sources[k]=factory(k,worlds.world(k));require_complete(sources[k]);
    }
    try {
        std::array<RecoveredServerRoutes::ChannelEndpoint,3> actual;
        for(std::uint8_t k=0;k<3;++k) {
            auto& source=sources[k];
            // G source cannot run a different world's native selection before
            // eventual lifecycle refusal. Weak registry is locked only on GAME.
            const auto weak=std::weak_ptr<SharedWorldPresence>(worlds.world(k)->presence());
            auto select=std::move(source.characters.native_select);
            source.characters.native_select=[weak,thread=thread_,select=std::move(select)](Session& session,
                    const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created) {
                if(thread!=std::this_thread::get_id())throw std::logic_error("Channel selection requires actual game owner");
                const auto presence=weak.lock();
                if(!presence||!session.native_channel_bound()||!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel selection does not own the accepted world");
                const auto selected=select(session,input,created);
                if(!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel retired during character selection");
                return selected;
            };
            auto ready=std::move(source.characters.world_ready);
            source.characters.world_ready=[weak,thread=thread_,ready=std::move(ready)](Session& session) {
                if(thread!=std::this_thread::get_id())throw std::logic_error("Channel readiness requires actual game owner");
                const auto presence=weak.lock();
                if(!presence||!session.native_channel_bound()||!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel readiness lost its accepted world");
                ready(session);
                if(!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel retired during readiness");
            };
            auto records=std::move(source.characters.world_records);
            source.characters.world_records=[weak,thread=thread_,records=std::move(records)](Session& session,
                    std::span<const RecoveredWorldRecords::Record> batch) {
                if(thread!=std::this_thread::get_id())throw std::logic_error("Channel records require actual game owner");
                const auto presence=weak.lock();
                if(!presence||!session.native_channel_bound()||!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel records lost their accepted world");
                auto result=records(session,batch);
                if(!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel retired during record dispatch");
                return result;
            };
            auto lifecycle=std::move(source.characters.common_world_lifecycle_factory);
            source.characters.common_world_lifecycle_factory=[weak,thread=thread_,lifecycle=std::move(lifecycle)](Session& session) {
                if(thread!=std::this_thread::get_id())throw std::logic_error("Channel lifecycle requires actual game owner");
                const auto presence=weak.lock();
                if(!presence||!session.native_channel_bound()||!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel lifecycle lost its accepted world");
                auto result=lifecycle(session);
                if(!session.native_channel_allows_presence(presence)||session.closing())
                    throw std::runtime_error("Native channel retired during lifecycle construction");
                return result;
            };
            listeners_[k]=std::make_unique<TcpServer>(network,game,
                asio::ip::address_v4(policies[k].address).to_string(),policies[k].port,capacity,packet_dump,
                std::move(source.packet),std::move(source.disconnected),ProtocolMode::God2CharacterConnection,
                std::move(source.authenticate),std::move(source.characters));
            listeners_[k]->bind_native_channel(worlds.world(k)->presence(),group,k);
            const auto endpoint=listeners_[k]->bound_endpoint();
            actual[k]={endpoint.address().to_v4().to_bytes(),endpoint.port(),policies[k].status,policies[k].route_body};
        }
        const auto wire=RecoveredServerRoutes::wire_three_available_channels(group,group_byte_1,actual);
        advertisement_.assign(wire.begin(),wire.end());
    } catch(...) {
        // Nothing has started accepting. Close every successfully bound socket
        // synchronously instead of advertising a partial topology.
        for(auto& listener:listeners_)if(listener)listener->discard_unstarted();
        throw;
    }
}
TaiwanChannelServers::~TaiwanChannelServers() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    try{stop();}catch(...){std::terminate();}
}
void TaiwanChannelServers::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Native channel servers game owner mismatch");
}
void TaiwanChannelServers::start() {
    owner();if(stopped_)throw std::logic_error("Retired native channels cannot restart");
    if(started_)return;
    try{for(auto& listener:listeners_)listener->start();started_=true;}
    catch(...){stop();throw;}
}
void TaiwanChannelServers::stop() {
    owner();if(stopped_)return;stopped_=true;
    std::exception_ptr failure;
    for(auto& listener:listeners_)if(listener)try{listener->stop();}catch(...){if(!failure)failure=std::current_exception();}
    if(failure)std::rethrow_exception(failure);
}
asio::ip::tcp::endpoint TaiwanChannelServers::endpoint(std::uint8_t channel) const {
    owner();if(channel>=3)throw std::out_of_range("Native channel ordinal must be0..2");
    return listeners_[channel]->bound_endpoint();
}
std::vector<std::uint8_t> TaiwanChannelServers::advertisement() const {
    owner();if(stopped_)throw std::logic_error("Retired channels cannot publish new advertisements");
    return advertisement_;
}
}
