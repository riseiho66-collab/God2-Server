#include "cn/auth/SharedAccountSuccess.h"
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct Wipe {
    std::span<std::uint8_t> bytes;
    ~Wipe(){volatile std::uint8_t* p=bytes.data();for(std::size_t i=0;i<bytes.size();++i)p[i]=0;}
};
}
SharedAccountSuccess::NativeData::NativeData(god2cn::Bytes issued,god2cn::Bytes billing,Scope scope,Current current)
    :issued_(std::move(issued)),billing_(std::move(billing)),scope_(scope),current_(std::move(current)) {}
SharedAccountSuccess::NativeData::~NativeData() {Wipe clear{issued_};}
std::optional<SharedAccountSuccess::NativeData> SharedAccountSuccess::NativeData::from_source(
    god2cn::Bytes issued,god2cn::Bytes billing,Scope scope,Current current) {
    Wipe clear{issued};
    auto parsed=god2cn::CnAccountWire::parse_issued_login(issued);
    if(!parsed)return std::nullopt;
    Wipe parsed_clear{parsed->payload};
    const auto billing_view=god2cn::CnAccountBilling::read(billing);
    const auto flags=god2cn::CnIssuedLoginFlags::read(issued);
    if(!billing_view || !flags || !scope.account_session || !scope.verified_account ||
       parsed->account_id()!=scope.verified_account || !current)return std::nullopt;
    const Observation observation{issued,billing,*billing_view,*flags,{},std::nullopt};
    if(!current(scope,Check::Prepared,observation))return std::nullopt;
    // 0A's copied byte5 and all other opaque/native billing values remain raw.
    // Parsing proves layout, not entitlement, native serialization or issuance.
    NativeData result(std::move(issued),std::move(billing),scope,std::move(current));
    clear.bytes={}; // Ownership moved: do not wipe the returned native record.
    return result;
}
bool SharedAccountSuccess::NativeData::bind_directory_source(SharedAccountDirectorySource::Plan plan) {
    if(!current_ || !plan.current())return false;
    // Prepare the wrapper completely before replacing this actual source gate.
    Current current=[original=current_,plan=std::move(plan)](
        const Scope& scope,Check check,const Observation& observation) {
        if(!plan.current())return false;
        if(check==Check::Prepared) {
            if(!observation.catalog_records.empty() || observation.grant_deadline)return false;
        } else if(check==Check::BeforeIssue || check==Check::BeforePublish) {
            if(!plan.matches(observation.catalog_records))return false;
        } else return false;
        return original(scope,check,observation) && plan.current();
    };
    current_=std::move(current);return true;
}
std::shared_ptr<SharedAccountSelection> SharedAccountSuccess::attach(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<Admission> admission,
    std::uint64_t session,std::shared_ptr<const god2cn::CnAccountWire::Login> request,
    NativeData native,Admission::Clock::time_point deadline,RecoveredCharacterRepository& characters,
    std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog,SharedAccountSelection::SummarySource source,
    Admission::Clock::time_point now,Connection::Transport::Completion queued,
    std::optional<SharedAccountSelection::NameSources> naming) {
    if(!queued)throw std::invalid_argument("CN account success queue continuation required");
    // Shared completion also covers synchronous preparation/post failures.
    // Move before invoking, so exceptions/reentrant close cannot call it twice.
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(queued));
    const auto finish=[completion](bool accepted) {
        if(!*completion)return;auto done=std::move(*completion);*completion={};done(accepted);
    };
    const auto reject=[&]() -> std::shared_ptr<SharedAccountSelection> {finish(false);return {};};
    try {
    if(!connection || !admission || !source || !session || connection->closing() ||
       connection->role()!=Connection::Transport::Role::Account ||
       !connection->owns_verified_login(request))return reject();
    const auto account=connection->verified_account_id();
    auto credentials=connection->retain_verified_credentials(request);
    if(!credentials)return reject();
    const NativeData::Scope scope{session,account};
    if(native.scope_!=scope || !native.current_)return reject();
    auto issued=god2cn::CnAccountWire::parse_issued_login(native.issued_);
    if(!issued)return reject();
    Wipe issued_clear{issued->payload};
    const auto billing=god2cn::CnAccountBilling::read(native.billing_);
    const auto flags=god2cn::CnIssuedLoginFlags::read(native.issued_);
    if(!account || issued->account_id()!=account || issued->account()!=request->account() ||
       issued->credential()!=request->credential() || !billing || !flags)return reject();
    // Qualify and prepare the entire directory before changing admission state.
    auto frames=god2cn::CnAccountReplies::catalog(catalog);
    // Retain the SAME complete ordered directory bytes for held publication;
    // no later regeneration or source-only claim about a different catalog.
    auto literal_catalog=frames;
    std::set<Admission::Target> destinations;
    for(const auto& group:catalog)
        for(const auto& node:group.nodes)
            if(group.header.enabled_servers&(std::uint16_t{1}<<node.endpoint.server_index))
                destinations.insert({group.header.index,node.endpoint.server_index});
    if(destinations.empty())return reject();
    const NativeData::Observation observation{native.issued_,native.billing_,*billing,*flags,
        frames,deadline};
    if(!native.current_(scope,NativeData::Check::BeforeIssue,observation) || connection->closing() ||
       !connection->verified_credentials_current(credentials,request) || connection->verified_account_id()!=account)return reject();
    const auto grant=admission->issue(session,
        {Admission::Protocol::Mainland,account,issued->check_key()},
        std::vector<Admission::Target>(destinations.begin(),destinations.end()),deadline,now);
    if(!grant)return reject();
    try {
        auto selection=SharedAccountSelection::attach(connection,admission,*grant,session,
            std::string(request->account()),characters,std::move(catalog),std::move(source),now);
        if(!selection) {admission->revoke_pending(*grant,session);connection->close();return reject();}
        if(naming && !selection->install_name_sources(std::move(*naming))) {
            admission->revoke_pending(*grant,session);connection->close();return reject();
        }
        // Integration output order accepted by0047FE30's receive switch:
        // 1D replaces the login record but loops;04/05/06 populate directory;
        // 0A copies billing and exits via its local gate. Never queue1D or
        // directory after0A, or let source preparation fail after publishing it.
        // This is not a claim of recovered official server emission order.
        std::vector<god2cn::Bytes> sequence;sequence.reserve(frames.size()+2);
        // Retain exact native originals for the final source observation. The
        // bounded additional wire copy enters the existing IO encoder; it is
        // not another source, default serializer or durable credential store.
        sequence.push_back(native.issued_);
        for(auto& frame:frames)sequence.push_back(std::move(frame));
        sequence.push_back(native.billing_);
        // Complete source/record/grant ownership is observed behind the actual
        // IO encoding/capacity barrier, before ANY success bytes leave. The
        // original verified request is retained only through this bounded
        // publication; it is never logged or saved and keeps its wipe deleter.
        struct Publication {
            NativeData native;
            std::shared_ptr<const god2cn::CnAccountWire::Login> request;
            std::shared_ptr<const VerifiedCredentialSource> credentials;
            std::vector<god2cn::Bytes> catalog;
            Admission::Clock::time_point deadline;
            bool published=false;
        };
        auto publication=std::make_shared<Publication>(Publication{std::move(native),std::move(request),
            std::move(credentials),std::move(literal_catalog),deadline,false});
        std::weak_ptr<Connection> weak=connection;
        connection->send_account_batch_with_publication(std::move(sequence),
          [weak,publication,grant=*grant,session,account] {
            const auto current=weak.lock();
            const auto billing=god2cn::CnAccountBilling::read(publication->native.billing_);
            const auto flags=god2cn::CnIssuedLoginFlags::read(publication->native.issued_);
            if(!billing || !flags)return false;
            const NativeData::Observation observation{publication->native.issued_,publication->native.billing_,
                *billing,*flags,publication->catalog,publication->deadline};
            if(!current || publication->published || current->closing() || current->verified_account_id()!=account ||
               !current->owns_verified_login(publication->request) ||
               !publication->native.current_(publication->native.scope_,NativeData::Check::BeforePublish,observation) ||
               current->closing() || !current->verified_credentials_current(publication->credentials,publication->request) ||
               !current->confirm_account_success_queue(grant,session,Admission::Clock::now()))return false;
            publication->published=true;return true;
          },[weak,admission,publication,grant=*grant,session,account,finish](bool accepted) {
            const auto current=weak.lock();
            bool valid=false;
            try {valid=accepted && publication->published && current && !current->closing() &&
                current->verified_account_id()==account && current->owns_verified_login(publication->request) &&
                current->account_success_current(grant,session,Admission::Clock::now());}catch(...) {valid=false;}
            // No source/entitlement/old-preparation predicate after bytes leave.
            // A failed local release closes this exact transport and revokes the
            // still-unselected grant; there is no remote rollback/receipt claim.
            if(!valid) {admission->revoke_pending(grant,session);if(current)current->close();}
            publication->request.reset();publication->credentials.reset();publication->native.current_={};
            publication->catalog.clear();
            {Wipe clear{publication->native.issued_};}
            publication->native.issued_.clear();publication->native.billing_.clear();
            finish(valid);
        });
        return selection;
    }catch(...) {admission->revoke_pending(*grant,session);connection->close();finish(false);throw;}
    }catch(...) {if(connection)connection->close();finish(false);throw;}
}
}
