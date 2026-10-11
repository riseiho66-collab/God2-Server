#include "cn/world/SharedDirectory.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedDirectory::SharedDirectory(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world,bool mode)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),world_(world),native_mode_(mode) {}
void SharedDirectory::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN directory game owner mismatch");
}
bool SharedDirectory::current() const {
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->world_session_id()!=lease_.session ||
       connection->verified_account_id()!=lease_.account || !connection->world_character_offered(lease_.character) ||
       !presence_->ready(lease_))return false;
    const auto source=connection->world_offer_source();
    if(!source)return false;
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);
    return summary && summary->native_mode_bit0()==native_mode_;
}
std::shared_ptr<SharedDirectory> SharedDirectory::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world) {
    if(!connection || !presence)return {};
    const auto source=connection->world_offer_source();if(!source)return {};
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);if(!summary)return {};
    auto result=std::shared_ptr<SharedDirectory>(new SharedDirectory(connection,std::move(presence),lease,world,
        summary->native_mode_bit0()));
    result->owner();return result->current()?result:std::shared_ptr<SharedDirectory>{};
}
SharedDirectory::Connection::Ingress SharedDirectory::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes records,Connection::Transport::Completion done) {
        self->receive(std::move(records),std::move(done));
    };
}
bool SharedDirectory::dispatch(const Request& request) {
    if(!current())return false;
    auto publication=world_.resolve(lease_,request,native_mode_);
    if(!publication || !publication->source_revision || publication->records.empty())return false;
    // Local queue budget equals transport's aggregate budget. This is not a
    // recovered rule for native directory result count/order or response pairing.
    std::size_t bytes=0;
    for(const auto& record:publication->records) {
        if(record.empty() || record.size()>god2cn::CnTransport::max_logical-bytes)return false;
        bytes+=record.size();
        if(record[0]==0xae) {
            const auto summary=god2cn::CnDirectoryWire::read_summary(record);
            if(!summary || summary->channel!=request.channel)return false;
        }else if(record[0]==0xb0) {
            const auto page=god2cn::CnDirectoryWire::read_page(record);
            if(!page || page->channel!=request.channel || !page->rows_within_initial_clear(native_mode_))return false;
            // Source publication is limited to the actual2000-byte initialized
            // row region for these three channels. This is not a claim that
            // all native variants have a50-row capacity. Actual owner still
            // qualifies native strings, identities, rules and output revision.
        }else return false; // No same-opcode94/D1 fabricated replies.
    }
    if(!world_.qualify_delivery(lease_,request,native_mode_,*publication) || !current())return false;
    const auto connection=connection_.lock();if(!connection)return false;
    // Fully retain supplier order and bytes. B0 cursor is not an94 echo;
    // native row/text/summary fields stay opaque unless specifically recovered.
    for(auto& record:publication->records)connection->send(std::move(record));
    return !connection->closing();
}
void SharedDirectory::receive(god2cn::Bytes records,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN directory completion required");
    bool accepted=false;
    try {
        const auto process=[&] {
            if(records.empty() || records.size()>god2cn::CnTransport::max_logical || !current())return false;
            std::vector<Request> requests;const auto bytes=std::span<const std::uint8_t>(records);
            for(std::size_t offset=0;offset<records.size();) {
                const auto size=records[offset]==0x94?god2cn::CnDirectoryWire::request_size:
                    records[offset]==0xa4?god2cn::CnDirectoryWire::page_request_size:0;
                if(!size || size>records.size()-offset)return false;
                auto request=god2cn::CnDirectoryWire::read_request(bytes.subspan(offset,size));
                if(!request)return false;
                requests.push_back(std::move(*request));offset+=size;
            }
            // Format-qualify the complete run before dispatch. Permission/data
            // revision remain per request with the actual authority; this is
            // not a native gameplay transaction or a route-completion claim.
            for(const auto& request:requests)if(!dispatch(request))return false;
            return true;
        };
        accepted=process();
    }catch(...) {accepted=false;}
    if(!accepted)if(const auto connection=connection_.lock())connection->close();
    done(accepted); // Source queue acceptance only, no rendered/native acceptance.
}
}
