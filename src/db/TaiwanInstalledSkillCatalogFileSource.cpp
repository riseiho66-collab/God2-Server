#include "db/TaiwanInstalledSkillCatalogFileSource.h"
#include "db/DbTypes.h"
#include <cstdint>
#include <string>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace god2 {
namespace {
#ifdef _WIN32
class ReadHandle final {
public:
    explicit ReadHandle(HANDLE value):value_(value) {
        if(value_==INVALID_HANDLE_VALUE || !value_)throw DatabaseError("TW skill source open failed");
    }
    ~ReadHandle(){CloseHandle(value_);}
    ReadHandle(const ReadHandle&)=delete;
    ReadHandle& operator=(const ReadHandle&)=delete;
    HANDLE get() const noexcept {return value_;}
private:
    HANDLE const value_;
};
BY_HANDLE_FILE_INFORMATION disk_information(const ReadHandle& handle) {
    BY_HANDLE_FILE_INFORMATION information{};
    if(GetFileType(handle.get())!=FILE_TYPE_DISK ||
       !GetFileInformationByHandle(handle.get(),&information) ||
       (information.dwFileAttributes&FILE_ATTRIBUTE_DEVICE))
        throw DatabaseError("TW skill source requires an actual disk file or directory");
    return information;
}
std::wstring final_handle_path(const ReadHandle& handle) {
    const DWORD flags=FILE_NAME_NORMALIZED|VOLUME_NAME_DOS;
    const DWORD needed=GetFinalPathNameByHandleW(handle.get(),nullptr,0,flags);
    // Native extended paths are bounded too; never allocate from an unchecked
    // external length or truncate a handle path to establish containment.
    if(!needed || needed>32768)throw DatabaseError("TW skill source final handle path unavailable");
    std::wstring value(needed,wchar_t(0));
    const DWORD used=GetFinalPathNameByHandleW(handle.get(),value.data(),needed,flags);
    if(!used || used>=needed)throw DatabaseError("TW skill source final handle path changed");
    value.resize(used);return value;
}
void require_contained(const ReadHandle& root,const ReadHandle& file) {
    auto root_path=final_handle_path(root);
    const auto file_path=final_handle_path(file);
    constexpr wchar_t separator=static_cast<wchar_t>(0x5c);
    while(!root_path.empty() && root_path.back()==separator)root_path.pop_back();
    if(root_path.empty() || file_path.size()<=root_path.size() ||
       file_path[root_path.size()]!=separator ||
       CompareStringOrdinal(root_path.data(),static_cast<int>(root_path.size()),
           file_path.data(),static_cast<int>(root_path.size()),FALSE)!=CSTR_EQUAL)
        throw DatabaseError("TW skill source opened file escapes the actual client root");
}
void require_exact_size(const ReadHandle& file) {
    LARGE_INTEGER size{};
    if(!GetFileSizeEx(file.get(),&size) ||
       size.QuadPart!=static_cast<LONGLONG>(TaiwanInstalledSkillCatalogSource::file_bytes))
        throw DatabaseError("TW skill source exact file size differs");
}
#endif
}
std::shared_ptr<const TaiwanInstalledSkillCatalogSource> TaiwanInstalledSkillCatalogFileSource::read_client_root(
    const std::filesystem::path& client_root) {
    if(client_root.empty() ||
       client_root.native().find(std::filesystem::path::value_type(0))!=std::filesystem::path::string_type::npos)
        throw DatabaseError("TW skill source requires an explicit nonempty NUL-free client root");
#ifdef _WIN32
    // Fixed small owning buffer is allocated before file I/O; caller invokes
    // this entire source producer before any DB open, SQL or import operation.
    std::vector<std::uint8_t> bytes(TaiwanInstalledSkillCatalogSource::file_bytes+1);
    ReadHandle root(CreateFileW(client_root.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,
        nullptr,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS,nullptr));
    if(!(disk_information(root).dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY))
        throw DatabaseError("TW skill source client root is not an existing directory");
    const auto fixed=client_root/"Data2"/"Fight"/"Spg"/"cbspec2.bin";
    // Deny concurrent write/delete sharing on this file snapshot. Reparse
    // resolution is checked on THIS opened handle, not a prior path-only probe.
    ReadHandle file(CreateFileW(fixed.c_str(),GENERIC_READ,FILE_SHARE_READ,
        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_SEQUENTIAL_SCAN,nullptr));
    if(disk_information(file).dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)
        throw DatabaseError("TW skill source requires a regular file");
    require_contained(root,file);require_exact_size(file);
    DWORD read=0;
    if(!ReadFile(file.get(),bytes.data(),static_cast<DWORD>(bytes.size()),&read,nullptr) ||
       read!=TaiwanInstalledSkillCatalogSource::file_bytes)
        throw DatabaseError("TW skill source bounded exact binary read failed");
    // A short ReadFile alone is not an EOF receipt. Probe only after exactly
    //112660 bytes: at most one additional byte can ever be consumed, bounded
    // by the original +1 budget. Any extra byte or IO failure rejects the source.
    std::uint8_t extra=0;DWORD eof=0;
    if(!ReadFile(file.get(),&extra,1,&eof,nullptr) || eof!=0)
        throw DatabaseError("TW skill source expected exact EOF");
    require_exact_size(file);require_contained(root,file);
    bytes.resize(TaiwanInstalledSkillCatalogSource::file_bytes);
    auto source=TaiwanInstalledSkillCatalogSource::read_actual_source(bytes);
    if(!source)throw DatabaseError("TW skill source whole installed453 pin qualification failed");
    // Returning the immutable byte proof closes both RAII handles first.
    // Opened-handle containment qualifies this snapshot, never live file Current.
    return source;
#else
    throw DatabaseError("TW installed skill rooted file source requires Windows");
#endif
}
}
