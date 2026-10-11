#include "battle_background.h"
#include <windows.h>
#include <ddraw.h>
#include <cstdint>
#include <cstring>
#include <vector>
#include <limits>

namespace battle_background {
namespace {
template<class T> T read(const void* p, unsigned offset) {
    T value{};
    std::memcpy(&value, static_cast<const unsigned char*>(p)+offset, sizeof(value));
    return value;
}
struct Snapshot {
    void* renderer{};
    void* screen{};
    void* cdx{};
    IDirectDrawSurface7* surface{};
    DWORD width{},height{},bits{},red{},green{},blue{};
    bool pending{};
    std::vector<unsigned char> pixels;
} saved;
void note(const char* line) {
    HANDLE file=CreateFileA("shunying-clone.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,
        nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file!=INVALID_HANDLE_VALUE) {
        DWORD written{};WriteFile(file,line,static_cast<DWORD>(std::strlen(line)),&written,nullptr);
        CloseHandle(file);
    }
}
bool layout(const DDSURFACEDESC2& d, std::size_t& row) {
    if(!d.lpSurface || !d.dwWidth || !d.dwHeight || d.dwWidth>4096 || d.dwHeight>4096 ||
       !(d.ddpfPixelFormat.dwFlags&DDPF_RGB) ||
       (d.ddpfPixelFormat.dwRGBBitCount!=16 && d.ddpfPixelFormat.dwRGBBitCount!=32))return false;
    row=static_cast<std::size_t>(d.dwWidth)*(d.ddpfPixelFormat.dwRGBBitCount/8);
    const auto pitch=static_cast<std::int64_t>(d.lPitch);
    return (pitch<0?-pitch:pitch)>=static_cast<std::int64_t>(row) && row*d.dwHeight<=32*1024*1024;
}
bool same_format(const DDSURFACEDESC2& d) {
    return d.dwWidth==saved.width && d.dwHeight==saved.height &&
        d.ddpfPixelFormat.dwRGBBitCount==saved.bits && d.ddpfPixelFormat.dwRBitMask==saved.red &&
        d.ddpfPixelFormat.dwGBitMask==saved.green && d.ddpfPixelFormat.dwBBitMask==saved.blue;
}
}
void captured(void* renderer) {
    // A new battle replaces the old snapshot, including on capture failure.
    saved=Snapshot{};
    if(!renderer)return;
    auto* cdx=read<void*>(renderer,0xa4);
    if(!cdx)return;
    auto* surface=read<IDirectDrawSurface7*>(cdx,0x80);
    if(!surface)return;
    DDSURFACEDESC2 d{};d.dwSize=sizeof(d);
    if(FAILED(surface->Lock(nullptr,&d,DDLOCK_WAIT|DDLOCK_READONLY,nullptr)))return;
    std::size_t row{};
    if(layout(d,row)) {
        try {
            saved.pixels.resize(row*d.dwHeight);
            for(DWORD y=0;y<d.dwHeight;++y)
                std::memcpy(saved.pixels.data()+y*row,
                    static_cast<const unsigned char*>(d.lpSurface)+static_cast<std::ptrdiff_t>(y)*d.lPitch,row);
            saved.renderer=renderer;saved.screen=read<void*>(renderer,0x9c);
            saved.cdx=cdx;saved.surface=surface;
            saved.width=d.dwWidth;saved.height=d.dwHeight;saved.bits=d.ddpfPixelFormat.dwRGBBitCount;
            saved.red=d.ddpfPixelFormat.dwRBitMask;saved.green=d.ddpfPixelFormat.dwGBitMask;
            saved.blue=d.ddpfPixelFormat.dwBBitMask;
        } catch(...) {saved=Snapshot{};}
    }
    if(FAILED(surface->Unlock(nullptr)))saved=Snapshot{};
    if(!saved.pixels.empty())note("BATTLE BACKGROUND snapshot captured\r\n");
}
void screen_rebuilt(void* screen) {
    // Explicit generation signal is necessary: COM allocation can reuse the
    // same address for the new, empty surface.
    if(screen && screen==saved.screen && !saved.pixels.empty())saved.pending=true;
}
void before_battle_draw(void* renderer) {
    if(renderer!=saved.renderer || saved.pixels.empty())return;
    if(read<void*>(renderer,0x9c)!=saved.screen || read<void*>(renderer,0xa4)!=saved.cdx) {
        saved=Snapshot{};return;
    }
    auto* surface=read<IDirectDrawSurface7*>(saved.cdx,0x80);
    if(!surface)return;
    const auto state=surface->IsLost();
    if(state==DDERR_SURFACELOST) {
        saved.pending=true;
        if(FAILED(surface->Restore()))return;
    } else if(FAILED(state))return;
    if(surface!=saved.surface)saved.pending=true;
    if(!saved.pending)return;
    DDSURFACEDESC2 d{};d.dwSize=sizeof(d);
    if(FAILED(surface->Lock(nullptr,&d,DDLOCK_WAIT|DDLOCK_WRITEONLY,nullptr)))return;
    std::size_t row{};
    const bool compatible=layout(d,row)&&same_format(d);
    if(compatible)for(DWORD y=0;y<d.dwHeight;++y)
        std::memcpy(static_cast<unsigned char*>(d.lpSurface)+static_cast<std::ptrdiff_t>(y)*d.lPitch,
            saved.pixels.data()+y*row,row);
    const auto unlocked=surface->Unlock(nullptr);
    if(!compatible){saved=Snapshot{};return;}
    if(SUCCEEDED(unlocked)) {
        saved.surface=surface;saved.pending=false;
        note("BATTLE BACKGROUND snapshot restored after surface recovery\r\n");
    }
}
}
