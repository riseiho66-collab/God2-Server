#pragma once
#include "cn/net/SharedListenerRegistry.h"
#include "cn/assets/CnClientGroupConfiguration.h"
#include "cn/protocol/CnAccountReplies.h"

namespace god2::cn {
// Original04/05/06 fields plus successfully bound hosting operands. Native
// billing/load/location values must be supplied, not inferred from the socket.
class SharedAccountDirectorySource {
public:
    struct Node {
        std::uint8_t server_index;
        std::uint8_t load;
        std::vector<god2cn::CnAccountReplies::Location> locations;
    };
    struct Group {
        god2cn::CnAccountReplies::Group header;
        std::vector<Node> nodes;
    };
    class Plan {
    public:
        Plan(const Plan&)=default;
        Plan(Plan&&) noexcept=default;
        const std::vector<god2cn::CnAccountReplies::CatalogGroup>& catalog() const {return catalog_;}
        bool current() const {return listeners_.current();}
        // Exact expected04/05/06 fields/order/bound addresses, with complete
        // records inside nonempty native aggregates. No serialization/rewrite.
        bool matches(std::span<const god2cn::Bytes>) const;
    private:
        friend class SharedAccountDirectorySource;
        Plan(std::vector<god2cn::CnAccountReplies::CatalogGroup>,SharedListenerRegistry::Snapshot,
            std::shared_ptr<const god2cn::CnClientGroupConfiguration>);
        std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog_;
        SharedListenerRegistry::Snapshot listeners_;
        std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups_;
    };
    // Actual metadata has NO IP/port or slot-count input: obtain addresses
    // from the same active listener and slots from the actual selected config.
    static std::optional<Plan> from_source(std::span<const Group>,SharedListenerRegistry::Snapshot,
        std::shared_ptr<const god2cn::CnClientGroupConfiguration>);
    // Existing whole-native callback form: require exact agreement with the
    // actual socket registry without rewriting caller-supplied native bytes.
    static std::optional<Plan> from_catalog(
        std::span<const god2cn::CnAccountReplies::CatalogGroup>,SharedListenerRegistry::Snapshot,
        std::shared_ptr<const god2cn::CnClientGroupConfiguration>);
};
}
