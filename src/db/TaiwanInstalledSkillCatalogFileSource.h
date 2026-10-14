#pragma once
#include "db/TaiwanInstalledSkillCatalogSource.h"
#include <filesystem>
#include <memory>

namespace god2 {
// Explicit operator-only rooted snapshot producer. No default client path,
// alternate filename, resource copy, import, live Current or gameplay grant.
class TaiwanInstalledSkillCatalogFileSource final {
public:
    // Windows native Unicode path; fixed Data2/Fight/Spg/cbspec2.bin only.
    // Qualify the actual opened root/file handles and a bounded full read,
    // then use the existing immutable453 whole-source factory. All handles
    // close before the caller receives the proof or can invoke a DB writer.
    // Path/IO/pin failure and unsupported platforms throw DatabaseError.
    static std::shared_ptr<const TaiwanInstalledSkillCatalogSource> read_client_root(
        const std::filesystem::path&);
private:
    TaiwanInstalledSkillCatalogFileSource()=delete;
};
}
