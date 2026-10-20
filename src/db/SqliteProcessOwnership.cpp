#include "db/SqliteProcessOwnership.h"
#include "db/Database.h"
#include <sstream>
#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif
namespace god2 {
struct SqliteProcessOwnership::Impl {
#ifdef _WIN32
    HANDLE handle=INVALID_HANDLE_VALUE;
    OVERLAPPED range{};
    bool locked=false;
    ~Impl(){if(handle!=INVALID_HANDLE_VALUE){if(locked)UnlockFileEx(handle,0,1,0,&range);CloseHandle(handle);}}
#else
    int handle=-1;bool locked=false;
    ~Impl(){if(handle>=0){if(locked)flock(handle,LOCK_UN);close(handle);}}
#endif
};
SqliteProcessOwnership::SqliteProcessOwnership()=default;
SqliteProcessOwnership::~SqliteProcessOwnership()=default;
bool SqliteProcessOwnership::current() const noexcept{return impl_&&impl_->locked;}
std::unique_ptr<SqliteProcessOwnership> SqliteProcessOwnership::acquire(
    const std::filesystem::path& source,Mode mode,bool create) {
    if(source.empty()||source.native().find(std::filesystem::path::value_type(0))!=source.native().npos)
        throw DatabaseError("Database process owner requires an actual path");
    const auto text=source.u8string();
    if(text==u8":memory:" || (text.size()>=5 &&
       (text[0]==u8'f'||text[0]==u8'F')&&(text[1]==u8'i'||text[1]==u8'I')&&
       (text[2]==u8'l'||text[2]==u8'L')&&(text[3]==u8'e'||text[3]==u8'E')&&text[4]==u8':'))
        throw DatabaseError("File ownership forbids memory/URI databases");
    if(mode==Mode::Exclusive&&create)throw DatabaseError("Offline capacity cannot create a database");
    auto result=std::unique_ptr<SqliteProcessOwnership>(new SqliteProcessOwnership);
    result->impl_=std::make_unique<Impl>();result->exclusive_=mode==Mode::Exclusive;
#ifdef _WIN32
    // Allow our subsequent SQLite READWRITE handle. Omit SHARE_DELETE so the
    // retained file cannot be renamed/replaced during this ownership lifetime.
    result->impl_->handle=CreateFileW(source.c_str(),GENERIC_READ|GENERIC_WRITE,
        FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,create?OPEN_ALWAYS:OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(result->impl_->handle==INVALID_HANDLE_VALUE)throw DatabaseError("Cannot retain database file owner");
    BY_HANDLE_FILE_INFORMATION info{};
    if(!GetFileInformationByHandle(result->impl_->handle,&info)||(info.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY))
        throw DatabaseError("Database owner requires a regular file identity");
    // One byte beyond SQLite's maximum supported database size and its lock
    // region at0x40000000. Locking beyond EOF does NOT extend the file.
    result->impl_->range.OffsetHigh=0x7ffffffe;result->impl_->range.Offset=0;
    DWORD flags=LOCKFILE_FAIL_IMMEDIATELY;
    if(result->exclusive_)flags|=LOCKFILE_EXCLUSIVE_LOCK;
    if(!LockFileEx(result->impl_->handle,flags,0,1,0,&result->impl_->range))
        throw DatabaseError("Database is owned by another current server/import process");
    result->impl_->locked=true;
    result->identity_="win:"+std::to_string(info.dwVolumeSerialNumber)+":"+
        std::to_string(info.nFileIndexHigh)+":"+std::to_string(info.nFileIndexLow);
#else
    result->impl_->handle=open(source.c_str(),O_RDWR|O_CLOEXEC|(create?O_CREAT:0),0600);
    if(result->impl_->handle<0)throw DatabaseError("Cannot retain database file owner");
    struct stat info{};
    if(fstat(result->impl_->handle,&info)||!S_ISREG(info.st_mode))throw DatabaseError("Database owner requires a regular file identity");
    if(flock(result->impl_->handle,(result->exclusive_?LOCK_EX:LOCK_SH)|LOCK_NB))
        throw DatabaseError("Database is owned by another current server/import process");
    result->impl_->locked=true;
    result->identity_="posix:"+std::to_string(info.st_dev)+":"+std::to_string(info.st_ino);
#endif
    result->path_=std::filesystem::canonical(source);
    if(!result->path_current())throw DatabaseError("Database file identity changed while acquiring ownership");
    return result;
}
bool SqliteProcessOwnership::path_current() const {
    if(!current())return false;
#ifdef _WIN32
    const HANDLE probe=CreateFileW(path_.c_str(),FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE,
        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(probe==INVALID_HANDLE_VALUE)return false;
    BY_HANDLE_FILE_INFORMATION a{},b{};
    const bool same=GetFileInformationByHandle(impl_->handle,&a)&&GetFileInformationByHandle(probe,&b)&&
        a.dwVolumeSerialNumber==b.dwVolumeSerialNumber&&a.nFileIndexHigh==b.nFileIndexHigh&&a.nFileIndexLow==b.nFileIndexLow;
    CloseHandle(probe);return same;
#else
    struct stat held{},named{};
    return !fstat(impl_->handle,&held)&&!stat(path_.c_str(),&named)&&
        held.st_dev==named.st_dev&&held.st_ino==named.st_ino;
#endif
}
}
