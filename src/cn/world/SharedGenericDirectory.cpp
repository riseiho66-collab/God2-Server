#include "cn/world/SharedGenericDirectory.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedGenericDirectory::SharedGenericDirectory(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),world_(world) {}
void SharedGenericDirectory::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN generic directory game owner mismatch");
}
bool SharedGenericDirectory::current() const {
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->world_session_id()!=lease_.session ||
       connection->verified_account_id()!=lease_.account || !connection->world_character_offered(lease_.character) ||
       !presence_->ready(lease_))return false;
    const auto source=connection->world_offer_source();if(!source)return false;
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);
    return summary && !summary->native_mode_bit0();
}
std::shared_ptr<SharedGenericDirectory> SharedGenericDirectory::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world) {
    if(!connection || !presence)return {};
    auto result=std::shared_ptr<SharedGenericDirectory>(new SharedGenericDirectory(connection,std::move(presence),lease,world));
    result->owner();return result->current()?result:std::shared_ptr<SharedGenericDirectory>{};
}
SharedGenericDirectory::Connection::Ingress SharedGenericDirectory::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes records,Connection::Transport::Completion done) {
        self->receive(std::move(records),std::move(done));
    };
}
bool SharedGenericDirectory::dispatch(const Request& request) {
    if(!current())return false;
    auto publication=world_.resolve(lease_,request);
    if(!publication || !publication->source_revision || publication->records.empty())return false;
    std::size_t bytes=0;
    for(const auto& record:publication->records) {
        if(record.size()>god2cn::CnTransport::max_logical-bytes)return false;
        bytes+=record.size();
        const auto page=god2cn::CnGenericDirectoryWire::read_page(record);
        if(!page || page->selector()!=request.selector)return false;
        const auto fit=page->fits_initialized_generic_slot();if(fit && !*fit)return false;
        // Special14 capacity/empty-text fallback is still qualified by the
        // actual supplier; the normal initialized region is not a shared rule.
    }
    if(!world_.qualify_delivery(lease_,request,*publication) || !current())return false;
    const auto connection=connection_.lock();if(!connection)return false;
    // Preserve supplied cursor. Special14 AF writes301C8 but94 reads generic
    // 27BCC: no alias or echo is imposed. Never reply with unrelated S2C94.
    for(auto& record:publication->records)connection->send(std::move(record));
    return !connection->closing();
}
void SharedGenericDirectory::receive(god2cn::Bytes records,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN generic directory completion required");
    bool accepted=false;
    try {
        const auto process=[&] {
            constexpr auto size=god2cn::CnGenericDirectoryWire::request_size;
            if(records.empty() || records.size()>god2cn::CnTransport::max_logical || records.size()%size || !current())return false;
            std::vector<Request> requests;const auto bytes=std::span<const std::uint8_t>(records);
            for(std::size_t offset=0;offset<records.size();offset+=size) {
                auto request=god2cn::CnGenericDirectoryWire::read_request(bytes.subspan(offset,size));
                if(!request)return false;
                requests.push_back(std::move(*request));
            }
            for(const auto& request:requests)if(!dispatch(request))return false;
            return true;
        };
        accepted=process();
    }catch(...) {accepted=false;}
    if(!accepted)if(const auto connection=connection_.lock())connection->close();
    done(accepted); // Source queue acceptance, not native client/gameplay acceptance.
}
}
