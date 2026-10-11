"""Hash-bound transform motif lowering. Not a general x86 decompiler."""
import argparse
import hashlib
import json
from pathlib import Path
from capsule import load_capsule
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[2]
MOTIFS = {
    'encrypt': {0x4106a2: ('mov', 'dl, byte ptr [edi + 0x2556]'),
                0x4106ac: ('xor', 'eax, eax'), 0x4106b3: ('mov', 'cl, byte ptr [esi]'),
                0x4106c7: ('mov', 'bl, byte ptr [ebx + edi + 0x2420]'),
                0x4106ce: ('xor', 'bl, cl'), 0x4106d0: ('add', 'bl, dl'),
                0x4106d2: ('mov', 'dl, cl'), 0x4106d4: ('sub', 'bl, 3'),
                0x4106d8: ('mov', 'byte ptr [esi], bl')},
    'decrypt': {0x410702: ('mov', 'cl, byte ptr [edi + 0x2556]'),
                0x41070c: ('xor', 'esi, esi'), 0x410712: ('mov', 'dl, 3'),
                0x410714: ('sub', 'dl, cl'), 0x410716: ('mov', 'cl, byte ptr [eax]'),
                0x410718: ('add', 'cl, dl'), 0x410730: ('mov', 'cl, byte ptr [ecx + edi + 0x2420]'),
                0x410737: ('xor', 'cl, dl'), 0x41073a: ('mov', 'byte ptr [eax], cl')},
}


def transform_ir(capsule):
    manifest = load_capsule(capsule)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    instructions = {}
    for region in manifest['regions']:
        if region['kind'] == 'CODE':
            data = (Path(capsule).parent / region['file']).read_bytes()
            instructions.update({i.address: (i.mnemonic, i.op_str) for i in decoder.disasm(data, region['address'])})
    for name, motif in MOTIFS.items():
        if any(instructions.get(address) != expected for address, expected in motif.items()):
            raise ValueError('Unsupported instruction motif; refuse candidate generation')
    return {'format_version': 1, 'source': 'HASH_BOUND_STATIC_SEMANTIC_LOWERING',
            'capsule_sha256': hashlib.sha256(Path(capsule).read_bytes()).hexdigest(),
            'execution_trace': False, 'scope': 'TX/RX transform only; initializer remains separate clean C++',
            'loop': {'index_start': 0, 'key_index': 'i & 255', 'feedback_start': 'state.feedback',
                     'persistent_state_update': False, 'arithmetic': 'uint8 modulo 256'},
            'encrypt': [('LOAD', 'v0', 'input[i]'), ('TABLE_LOOKUP', 'k0', 'key[i & 255]'),
                        ('XOR', 'v1', 'v0', 'k0'), ('ADD', 'v2', 'v1', 'feedback'),
                        ('SUB', 'v3', 'v2', '3'), ('STORE', 'output[i]', 'v3'),
                        ('STATE_UPDATE', 'feedback', 'v0')],
            'decrypt': [('LOAD', 'v0', 'input[i]'), ('ADD', 'v1', 'v0', '3'),
                        ('SUB', 'v2', 'v1', 'feedback'), ('TABLE_LOOKUP', 'k0', 'key[i & 255]'),
                        ('XOR', 'v3', 'v2', 'k0'), ('STORE', 'output[i]', 'v3'),
                        ('STATE_UPDATE', 'feedback', 'v3')]}


def cpp_from_ir(ir):
    def block(operations):
        lines = []
        for op, *args in operations:
            if op in ('LOAD', 'TABLE_LOOKUP'):
                lines.append(f'const std::uint8_t {args[0]} = {args[1]};')
            elif op in ('XOR', 'ADD', 'SUB'):
                symbol = {'XOR': '^', 'ADD': '+', 'SUB': '-'}[op]
                lines.append(f'const auto {args[0]} = static_cast<std::uint8_t>({args[1]} {symbol} {args[2]});')
            elif op in ('STORE', 'STATE_UPDATE'):
                lines.append(f'{args[0]} = {args[1]};')
            else:
                raise ValueError('Unsupported semantic IR operation')
        return '\n'.join('            ' + line for line in lines)
    return ('// Generated local candidate from hash-bound semantic IR; not a production API.\n'
            '#include <array>\n#include <cstdint>\n#include <algorithm>\n'
            'extern "C" __declspec(dllexport) int God2LiftedRaw(int decrypt,\n'
            '    const std::uint8_t* key, unsigned key_size, unsigned feedback,\n'
            '    const std::uint8_t* input, unsigned size, std::uint8_t* destination, unsigned capacity) {\n'
            '    if ((decrypt != 0 && decrypt != 1) || !key || key_size != 256 || feedback > 255 ||\n'
            '        size > 4096 || capacity < size || (size && (!input || !destination))) return -1;\n'
            '    std::array<std::uint8_t,4096> output{};\n'
            '    for (unsigned i=0;i<size;++i) {\n        if (decrypt) {\n' + block(ir['decrypt']) +
            '\n        } else {\n' + block(ir['encrypt']) + '\n        }\n    }\n'
            '    if (size) std::copy_n(output.begin(),size,destination);\n'
            '    return static_cast<int>(size);\n}\n')


def trace_ir(trace):
    """SSA-like witnessed values, not equivalence proof for unexecuted branches."""
    versions, result = {}, []
    operations = {'xor': 'XOR', 'add': 'ADD', 'sub': 'SUB', 'and': 'AND', 'or': 'OR',
                  'shl': 'SHIFT', 'shr': 'SHIFT', 'sar': 'SHIFT', 'rol': 'ROL', 'ror': 'ROR'}
    for event in trace:
        mnemonic = event['instruction'].split(' ', 1)[0]
        reads = [f'{name}.{versions.get(name, 0)}' for name in event['register_reads']]
        writes = []
        for name in event['register_writes']:
            versions[name] = versions.get(name, 0) + 1
            writes.append(f'{name}.{versions[name]}')
        memory = [r for r in event['memory_reads'] + event['memory_writes'] if r['kind'] != 'STACK']
        if mnemonic in operations or memory:
            result.append({'rva': event['rva'], 'operation': operations.get(mnemonic, 'MEMORY_TRANSFER'),
                           'reads': reads, 'writes': writes, 'memory': memory,
                           'register_before': event['register_before'], 'register_after': event.get('register_after')})
    return {'source': 'EXECUTED_MISMATCH_TRACE', 'partial_register_aliases': 'witnessed, not normalized SSA',
            'operations': result, 'FIRST_SEMANTIC_DIVERGENCE': None,
            'limitation': 'No aligned clean instruction trace; first output/state divergence is authoritative.'}


def generate(capsule, output_cpp, output_ir):
    ir = transform_ir(capsule)
    for path, content in ((Path(output_cpp), cpp_from_ir(ir)), (Path(output_ir), json.dumps(ir, indent=2))):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding='utf-8') != content:
                raise ValueError('Refuse to replace a different generated artifact')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--output-cpp', type=Path, default=ROOT / 'generated/crypto_candidate.cpp')
    parser.add_argument('--output-ir', type=Path, default=ROOT / 'artifacts/crypto-oracle/semantic-ir.json')
    args = parser.parse_args()
    generate(args.capsule, args.output_cpp, args.output_ir)
