// The real snapshot/restore implementation against fake native COM surfaces.
#include "battle_background.cpp"
#include <array>
#include <cassert>
#include <iostream>
struct Fake {
    void** table{};
    std::array<unsigned char,48> pixels{};
    bool lost{},negative{},lock_failed{},restore_failed{};
    unsigned locks{},unlocks{},restores{};
    DWORD width{5},height{3};
};
HRESULT __stdcall lost(IDirectDrawSurface7* p){return reinterpret_cast<Fake*>(p)->lost?DDERR_SURFACELOST:DD_OK;}
HRESULT __stdcall restore(IDirectDrawSurface7* p){
    auto& s=*reinterpret_cast<Fake*>(p);++s.restores;
    if(s.restore_failed)return DDERR_GENERIC;
    s.lost=false;s.pixels.fill(0);return DD_OK;
}
HRESULT __stdcall lock(IDirectDrawSurface7* p,LPRECT rect,LPDDSURFACEDESC2 d,DWORD,HANDLE){
    auto& s=*reinterpret_cast<Fake*>(p);assert(!rect && d->dwSize==124);++s.locks;
    if(s.lock_failed)return DDERR_WASSTILLDRAWING;
    d->dwWidth=s.width;d->dwHeight=s.height;d->lPitch=s.negative?-16:16;
    d->lpSurface=s.pixels.data()+(s.negative?32:0);
    d->ddpfPixelFormat.dwFlags=DDPF_RGB;d->ddpfPixelFormat.dwRGBBitCount=16;
    d->ddpfPixelFormat.dwRBitMask=0xf800;d->ddpfPixelFormat.dwGBitMask=0x7e0;d->ddpfPixelFormat.dwBBitMask=31;
    return DD_OK;
}
HRESULT __stdcall unlock(IDirectDrawSurface7* p,LPRECT rect){assert(!rect);++reinterpret_cast<Fake*>(p)->unlocks;return DD_OK;}
template<class T,std::size_t N>void put(std::array<unsigned char,N>& a,unsigned off,T p){std::memcpy(a.data()+off,&p,sizeof(p));}
int main(){
    static_assert(sizeof(void*)==4);
    std::array<void*,45> table{};table[24]=reinterpret_cast<void*>(lost);table[25]=reinterpret_cast<void*>(lock);
    table[27]=reinterpret_cast<void*>(restore);table[32]=reinterpret_cast<void*>(unlock);
    Fake a{},b{};a.table=b.table=table.data();
    std::array<unsigned char,0xc0> renderer{};std::array<unsigned char,0x90> cdx{};
    auto* screen=reinterpret_cast<void*>(0x1234);
    put(renderer,0x9c,screen);put(renderer,0xa4,cdx.data());put(cdx,0x80,&a);
    for(unsigned y=0;y<3;++y)for(unsigned x=0;x<10;++x)a.pixels[y*16+x]=static_cast<unsigned char>(1+y*10+x);
    const auto initial=a.pixels;
    battle_background::captured(renderer.data());assert(a.locks==1 && a.unlocks==1);
    for(unsigned n=0;n<60;++n)battle_background::before_battle_draw(renderer.data());
    assert(a.locks==1 && a.pixels==initial); // No per-frame pixel copy.
    a.pixels.fill(0xee);battle_background::screen_rebuilt(screen);
    battle_background::before_battle_draw(renderer.data());
    for(unsigned y=0;y<3;++y)for(unsigned x=0;x<16;++x)assert(a.pixels[y*16+x]==(x<10?initial[y*16+x]:0xee));
    assert(a.locks==2); // Same COM pointer is still repaired on generation change.
    put(cdx,0x80,&b);b.negative=true;
    battle_background::before_battle_draw(renderer.data());
    for(unsigned y=0;y<3;++y)for(unsigned x=0;x<10;++x)assert(b.pixels[(2-y)*16+x]==initial[y*16+x]);
    b.lost=true;b.restore_failed=true;b.pixels.fill(0);
    battle_background::before_battle_draw(renderer.data());assert(b.restores==1 && b.locks==1);
    b.restore_failed=false;b.lock_failed=true;
    battle_background::before_battle_draw(renderer.data());assert(b.restores==2 && b.locks==2);
    b.lock_failed=false;battle_background::before_battle_draw(renderer.data());
    assert(b.pixels[32]==1 && b.pixels[0]==21 && b.unlocks==2);
    auto before=b.locks;battle_background::screen_rebuilt(reinterpret_cast<void*>(9));
    battle_background::before_battle_draw(renderer.data());assert(b.locks==before);
    b.width=6;battle_background::screen_rebuilt(screen);battle_background::before_battle_draw(renderer.data());
    assert(battle_background::saved.pixels.empty()); // Never copy wrong-size data.
    b.width=5;b.negative=false;b.lock_failed=true;battle_background::captured(renderer.data());
    assert(battle_background::saved.pixels.empty()); // Failed new battle cannot reuse an old map.
    b.lock_failed=false;battle_background::captured(renderer.data());
    put(renderer,0xa4,static_cast<void*>(nullptr));battle_background::before_battle_draw(renderer.data());
    assert(battle_background::saved.pixels.empty());
    std::cout<<"battle background: generation reuse, replacement, loss, retry, format, pitch and lifecycle passed\n";
}
