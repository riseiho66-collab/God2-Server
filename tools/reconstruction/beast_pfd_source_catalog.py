"""Pin all current PFD declarations without assigning gameplay food effects.

The section includes ordinary-looking food and special transformation rows.
Membership in PFD is source provenance, not permission to consume an item.
"""
import hashlib
import json

from .archive_inputs import ArchivedInputs, SERVER
from .beast_panel_contract import section_rows


SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
ORIGINAL = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/gamedata.csvZ'


def main():
    reader = ArchivedInputs()
    try:
        raw = reader.read(ORIGINAL)
    finally:
        reader.close()
    source = section_rows('Data2/Patch/Comm/gamedata.csvZ', b'PFD', None,
                          compressed=raw, path_label=ORIGINAL)
    if source['compressed_sha256'] != SOURCE or source['decoded_sha256'] != DECODED:
        raise ValueError('Original PFD source identity changed')
    rows = source['rows']
    if source['section']['declared_records'] != 65 or len(rows) != 65 or \
       len({row['id'] for row in rows}) != 65:
        raise ValueError('Original PFD declarations incomplete or aliased')
    current = section_rows('Data2/Patch/Comm/gamedata.csvZ', b'PFD', None)
    if [(r['id'], r['raw_hex']) for r in current['rows']] != \
       [(r['id'], r['raw_hex']) for r in rows]:
        raise ValueError('Current PFD rows differ from archived source')
    source['current_asset'] = {
        'path': current['path'],
        'compressed_sha256': current['compressed_sha256'],
        'decoded_sha256': current['decoded_sha256'],
        'scope': 'PFD row identities and exact bytes only; whole-file identity may differ',
    }
    for index, row in enumerate(rows):
        fields = bytes.fromhex(row['raw_hex']).split(b',')
        row['source_record_index'] = index
        row['resource_key'] = fields[2].decode('ascii')
        row['raw_columns_hex'] = [part.hex() for part in fields]
    source['native_section_selector'] = 9
    source['authority'] = ('SOURCE_DECLARATIONS_ONLY; does not establish lane0 food '
                           'eligibility, target, effect, consumption or S2C reply')
    artifact = SERVER / 'artifacts/integration/packet-connections-20261006/beast-pfd-source-catalog-v1.json'
    header_path = SERVER / 'src/db/NativePfdSourceCatalog.h'
    if artifact.exists() or header_path.exists():
        raise FileExistsError('Preserve existing PFD evidence and source')
    header = '''#pragma once
#include <array>
#include <cstdint>
#include <string_view>
namespace god2 {
// Original build-matched PFD section, native tag selector9. Some declarations
// are special transformation items. Lookup proves source membership ONLY;
// it never grants an item or qualifies C2S6B food effects/consumption.
struct NativePfdSourceCatalog {
    static constexpr std::string_view source_sha256="''' + SOURCE + '''";
    static constexpr std::string_view decoded_sha256="''' + DECODED + '''";
    struct Declaration {
        std::uint16_t key,source_record_index;
        std::uint32_t source_line,decoded_offset;
        std::string_view resource_key,row_sha256;
    };
    inline static constexpr std::array<Declaration,65> declarations{{
'''
    for row in rows:
        header += '        {' + ','.join((str(row['id']), str(row['source_record_index']),
            str(row['line']), str(row['decoded_offset']), json.dumps(row['resource_key']),
            json.dumps(row['row_sha256']))) + '},\n'
    header += '''    }};
    static constexpr const Declaration* lookup(std::uint16_t key) noexcept {
        for(const auto& row:declarations)if(row.key==key)return &row;
        return nullptr;
    }
};
}
'''
    artifact.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    header_path.write_text(header, encoding='utf-8')
    print(json.dumps({'pfd_declarations': len(rows), 'artifact': str(artifact),
                      'header_sha256': hashlib.sha256(header.encode()).hexdigest(),
                      'gameplay_effects_added': 0, 'tests_builds_client_execution': False}))


if __name__ == '__main__':
    main()
