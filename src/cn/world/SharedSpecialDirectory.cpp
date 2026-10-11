#include "cn/world/SharedSpecialDirectory.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedSpecialDirectory::SharedSpecialDirectory(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),world_(world) {}
void SharedSpecialDirectory::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN special directory game owner mismatch");
}
bool SharedSpecialDirectory::current() const {
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->world_session_id()!=lease_.session ||
       connection->verified_account_id()!=lease_.account || !connection->world_character_offered(lease_.character) ||
       !presence_->ready(lease_))return false;
    const auto source=connection->world_offer_source();if(!source)return false;
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);
    return summary && !summary->native_mode_bit0();
}
std::shared_ptr<SharedSpecialDirectory> SharedSpecialDirectory::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world) {
    if(!connection || !presence)return {};
    auto result=std::shared_ptr<SharedSpecialDirectory>(new SharedSpecialDirectory(connection,std::move(presence),lease,world));
    result->owner();return result->current()?result:std::shared_ptr<SharedSpecialDirectory>{};
}
SharedSpecialDirectory::Connection::Ingress SharedSpecialDirectory::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes records,Connection::Transport::Completion done) {
        self->receive(std::move(records),std::move(done));
    };
}
bool SharedSpecialDirectory::dispatch(const Request& request) {
    if(!current())return false;
    auto publication=world_.resolve(lease_,request);
    if(!publication || !publication->source_revision)return false;
    const auto page=Wire::read_page(publication->record);
    if(!page || page->selector()!=request.selector || !page->within_initial_clear() ||
       !page->consumed_text_regions_terminated())return false;
    if(page->selector()==Wire::Selector::Display25) {
        if(!publication->npc_names && publication->npc_resource) {
            if(god2cn::CnCurrentNpcNameCatalog::matches(*publication->npc_resource))
                publication->npc_names=god2cn::CnCurrentNpcNameCatalog::evidence(*page,*publication->npc_resource);
            else if(god2cn::CnNpcNameCatalog::matches(*publication->npc_resource))
                publication->npc_names=god2cn::CnNpcNameCatalog::evidence(*page,*publication->npc_resource);
        }
        if(!publication->npc_names || !page->npc_names_qualified(*publication->npc_names))return false;
    }
    if(!world_.qualify_delivery(lease_,request,*publication) || !current())return false;
    const auto connection=connection_.lock();if(!connection)return false;
    // Preserve actual page/count/header/padding/tail. Native response causality
    // and page echo are not inferred from the client's two-byteD1 producer.
    connection->send(std::move(publication->record));
    return !connection->closing();
}
void SharedSpecialDirectory::receive(god2cn::Bytes records,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN special directory completion required");
    bool accepted=false;
    try {
        const auto process=[&] {
            if(records.empty() || records.size()>god2cn::CnTransport::max_logical ||
               records.size()%Wire::request_size || !current())return false;
            std::vector<Request> requests;const auto bytes=std::span<const std::uint8_t>(records);
            for(std::size_t offset=0;offset<records.size();offset+=Wire::request_size) {
                auto request=Wire::read_request(bytes.subspan(offset,Wire::request_size));
                if(!request)return false;
                requests.push_back(std::move(*request));
            }
            for(const auto& request:requests)if(!dispatch(request))return false;
            return true;
        };
        accepted=process();
    }catch(...) {accepted=false;}
    if(!accepted)if(const auto connection=connection_.lock())connection->close();
    done(accepted); // Source queue acceptance only.
}
}
