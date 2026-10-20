#include "game/OwnedPveWorldCatalog.h"
#include <cassert>
#include <vector>
// SOURCE ONLY. These are material-affinity checks, not native gameplay or
// socket acceptance. PHASE1 does not execute this target.
int main() {
    std::vector<std::uint8_t> source(37,0);source[0]=0x2a;
    source[2]=0x80;source[13]=0x56;source[27]=0xa5;source[29]=2;
    const nlohmann::json prototype=source;
    auto moved=source;moved[1]=0x23;moved[2]=0x91;moved[25]=7;moved[26]=9;
    moved[29]=0xfe;moved[30]=0x12;moved[31]=0x23;moved[32]=0x34;
    assert(god2::OwnedPveWorldCatalog::same_entry_material(prototype,moved));
    auto changed=moved;changed[13]^=1;
    assert(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[2]^=0x40;
    assert(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[27]^=1;
    assert(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[29]^=1;
    assert(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed.pop_back();
    assert(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
}
