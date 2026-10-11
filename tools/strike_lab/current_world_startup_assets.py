"""Original startup path arguments and symbolic handle handoff; no world/slots.

Reuses the complete native FieldComm3 reader and its explicit CRT/CSV adapters.
Only argument-building slices and the ROM filename prefix execute here; loader
returns below are symbolic provenance, never invented runtime handle values.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import struct

from .current_world_ui_resource import (
    NativeWorldUIResource, ROOT, IMAGE_SHA, SOURCE, SOURCE_SHA, SOURCE_PLAIN_SHA,
    ASSET_SHA, ASSET_PLAIN_SHA, CWD, UI, STRIDE, BASE, STACK, SP, SCRATCH,
    pinned_sources, decode_csvz)
from unicorn.x86_const import (
    UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_EDI, UC_X86_REG_ECX)


@dataclass(frozen=True)
class StartupAsset:
    record: int
    inline_offset: int
    start_rva: int
    load_call_rva: int
    literal_path: str
    raw_size: int
    decoded_size: int
    raw_sha256: str
    decoded_sha256: str
    condition: str = 'always'

    @property
    def asset(self):
        path = self.literal_path.lstrip('\\').replace('\\', '/')
        return path if path.endswith('.ROMZ') else path + 'Z'


ASSETS = (
    StartupAsset(2, 0x214, 0x64cb6, 0x64ce1, r'\Data3\Flow\DTitleGui.ROM',
                 10310, 30310, ASSET_SHA, ASSET_PLAIN_SHA),
    StartupAsset(3, 0x31c, 0x64d32, 0x64d5d, r'\Data3\Flow\StateEft.ROM',
                 150825, 369164,
                 'dd7e4f767b5821db267d1ad109af39b94b8f316e63557b0a207a4025369a0a88',
                 'f7792beb9deef4eeffe026d6b403ec629052dc1eedf3d8b01eaaf9d9d826e842'),
    StartupAsset(10, 0xa54, 0x64d6c, 0x64d97, r'\Data3\Fight\Gui\Eft2_8302.ROM',
                 793930, 2262740,
                 '37241f1e1af509e8254b7b182eeaee43b541ecdbfdfa979463f6ffc483723254',
                 '54303d9af579c7b5f5cc4e65b5ab31c843a53643846eaf13a50eeddd80636ed0'),
    StartupAsset(12, 0xc64, 0x64dc0, 0x64deb, r'\Data3\Flow\motion.ROM',
                 281578, 567998,
                 'efa62f3528d9b9e8d19d3885eca4706f851cc4dbaed62b7438fd80a808c6ed7f',
                 '86a71831926432c81835873bd37de73c3b0bfa1677c968d487a16cf2f9fffd95'),
    StartupAsset(8, 0x844, 0x64e0b, 0x64e36, r'\Data3\Flow\gcall.ROM',
                 1175259, 3424824,
                 'e27e8ab9d5859c1337609095e90fa116898fd06722242edc8cdf5001d4a67901',
                 'a562820d3f8f31955a309cc5916561c7eaa3c13eb49b5e864d406f8debcc3a5c'),
    StartupAsset(9, 0x94c, 0x64e3f, 0x64ead, r'\Data3\Flow\speceff2.ROM',
                 313016, 1156346,
                 '6867c8639cafafb95077de1a583d737262f4f2f50b98e1ce26b4c49a1e3502b8',
                 '6694fbe66c07e31553ae50a11757ce8a6660b1f3024846534711f3d223b33739',
                 '[world+0x398] == 0'),
    StartupAsset(46, 0x2f74, 0x64eeb, 0x64f16, r'\Data3\Flow\NameShadow.ROMZ',
                 92448, 251378,
                 '6ecd4b398d344e28bf704a9436981a1c8670a4e562c74bf61a25c77d7a4c8dc9',
                 'e1b35fc578842049e6b55da80615047572e9a4602a58f293e0cc4c3691fb5fba'),
)

# (writer RVA, source record, storage base, offset, width). "world" is EBP;
# "secondary" is EBX=world+ABA32E0; "primary" is EDI=world+39C.
# Stack offsets refer to the startup frame between calls, not callee ESP.
HANDLE_STORES = (
    (0x64d12, 2, 'secondary', 0xa7e004c, 2),
    (0x64d22, 2, 'secondary', 0xa7e0050, 2),
    (0x64d62, 3, 'stack', 0x14, 4),
    (0x64d66, 3, 'world', 0xaba32f8, 4),
    (0x64d9c, 10, 'stack', 0x18, 4),
    (0x64da0, 10, 'world', 0xaba32f4, 2),
    (0x64da7, 10, 'secondary', 0xa7e0040, 2),
    (0x64df0, 12, 'world', 0x15383338, 2),
    (0x64df7, 12, 'stack', 0x20, 4),
    (0x64dfb, 12, 'secondary', 0xa7e0054, 2),
    (0x64e3b, 8, 'stack', 0x1c, 4),
    (0x64f1d, 46, 'stack', 0x10, 4),
    (0x64f58, 3, 'world', 0x3b4, 4),
    (0x64f62, 10, 'world', 0x3b0, 2),
    (0x64f69, 10, 'primary', 0xa7e0040, 2),
    (0x64f86, 12, 'world', 0xa7e03f4, 2),
    (0x64f8d, 2, 'primary', 0xa7e0050, 2),
    (0x64f9d, 12, 'primary', 0xa7e0054, 2),
    (0x64fb1, 46, 'world', 0xa7e03e4, 4),
    (0x64fb7, 46, 'world', 0x15383328, 4),
)

CONSUMERS = (
    {'call_rva': 0x64d0d, 'target_rva': 0x1081c0, 'this': 'world+0xaba32e0',
     'arguments': ['[world+0xa7e05dc]', '[world+0xaba32dc]', '[world+0xa7e05c8]',
                   'return(60A90, record=2)', '[world+0xaa36480]']},
    {'call_rva': 0x64ec0, 'target_rva': 0x10fa50, 'this': '[world+0x398]',
     'arguments': ['[world+0xaa36484]', 'return(60A90, record=9)'],
     'condition': '[world+0x398] was null before allocation',
     'stores': ['this+0 = arg1 (u32)', 'this+8 = arg2 (u16)']},
    {'call_rva': 0x64f4b, 'target_rva': 0x1081c0, 'this': 'world+0x39c',
     'arguments': ['[world+0xa7e05dc]', '[world+0xaba32dc]', '[world+0xa7e05c8]',
                   'return(60A90, record=2)', '[world+0xaa36480]']},
    {'call_rva': 0x64fcb, 'target_rva': 0x10dc70, 'this': 'world+0xaa36488',
     'arguments': ['[world+0xaba32dc]', 'return(60A90, record=8)'],
     'stores': ['this+0 = arg1 (u32)', 'this+0x2c = arg2 (u16)'],
     'then_call_rva': 0x10dc90},
    {'call_rva': 0x64fdd, 'target_rva': 0xff3c0, 'this': 'world+0xa7e04d0',
     'arguments': ['[world+0xaba32dc]'], 'stores': ['this+0x28 = arg1 (u32)']},
)


def pinned_assets(client_root=ROOT.parent / 'God2'):
    _, rows = pinned_sources(client_root)
    result = {}
    for asset in ASSETS:
        if (asset.inline_offset != asset.record * STRIDE + 4 or
                rows[asset.record][1] != asset.literal_path):
            raise ValueError('Startup source record mismatch')
        path = client_root / asset.asset
        if path.stat().st_size != asset.raw_size:
            raise ValueError('Startup raw size mismatch: ' + asset.asset)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != asset.raw_sha256:
            raise ValueError('Startup raw hash mismatch: ' + asset.asset)
        plain = decode_csvz(raw, limit=4*1024*1024)
        if (len(plain) != asset.decoded_size or
                hashlib.sha256(plain).hexdigest() != asset.decoded_sha256):
            raise ValueError('Startup decoded hash mismatch: ' + asset.asset)
        if not plain.startswith(b'IGSROM02\0\0\0\0ACTINDEX'):
            raise ValueError('Startup ROM signature mismatch: ' + asset.asset)
        result[asset.record] = (raw, plain)
    return result


class NativeStartupAssets(NativeWorldUIResource):
    def run(self, start, stop=0x1000, **bounds):
        if start == 0x1ec0:
            # Largest pinned output is 3.43 MB; the title oracle was 30 KB.
            bounds.setdefault('instruction_limit', 400000000)
            bounds.setdefault('timeout_us', 60000000)
        return super().run(start, stop, **bounds)

    def __init__(self):
        super().__init__()
        self.assets = pinned_assets()

    def verify_native_decodes(self):
        """Original 1EC0 for all additional assets, once per bounded oracle."""
        for asset in ASSETS[len(self.native_decoded)-1:]:
            self._check_decompression(*self.assets[asset.record])
        return dict(zip((2,) + tuple(a.record for a in ASSETS[1:]),
                        self.native_decoded[1:]))

    def argument(self, asset, *, first_open=False):
        """Stop BEFORE 60A90; optionally run 29820's first-open prefix.

        For record 9 the formatting and argument slices are separate: the
        condition, allocation and owner constructor are not executed. No
        manager/bank is bound, and no loader return or handle is manufactured.
        """
        context = self.vm.context_save()
        stack = bytes(self.vm.mem_read(STACK, 0x80000))
        seh = bytes(self.vm.mem_read(0, 4))
        try:
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, (UI-0xa7f2f6c) & 0xffffffff)
            self.vm.reg_write(UC_X86_REG_EDI, 0)
            if asset.record == 9:
                self.run(asset.start_rva, 0x64e60)
                # Account for the original add esp,10 at 64E66 without
                # touching world+398. The following slice uses [esp+60].
                self.run(0x64e66, 0x64e69)
                self.run(0x64e9b, asset.load_call_rva)
            else:
                self.run(asset.start_rva, asset.load_call_rva)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP-4:
                raise AssertionError('Startup argument stack mismatch')
            path = self.string(self.u32(SP-4))
            if path != CWD + asset.literal_path.encode('ascii'):
                raise AssertionError('Original startup path mismatch')
            if not first_open:
                return path
            self.vm.mem_write(SCRATCH, path+b'\0')
            # Slot 0 is only the input required to enter the filename prefix.
            # It is never inserted into a bank or returned as a startup handle.
            self.vm.mem_write(SP, struct.pack('<III', BASE+0x1000, SCRATCH, 0))
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_ECX, 0)
            self.run(0x29820, 0x298ed)
            sp = self.vm.reg_read(UC_X86_REG_ESP)
            if self.string(self.u32(sp+4)) != b'rb':
                raise AssertionError('Startup ROM open mode mismatch')
            return self.string(self.u32(sp))
        finally:
            self.vm.mem_write(0, seh)
            self.vm.mem_write(STACK, stack)
            self.vm.context_restore(context)


def main():
    native = NativeStartupAssets()
    hashes = native.verify_native_decodes()
    manifest = []
    for asset in ASSETS:
        item = asdict(asset)
        item.update(asset=asset.asset, source_line=asset.record+5,
                    native_argument=native.argument(asset).decode('ascii'),
                    native_first_open=native.argument(asset, first_open=True).decode('ascii'),
                    native_decoded_sha256=hashes[asset.record])
        manifest.append(item)
    print(json.dumps(dict(image_sha256=IMAGE_SHA, source=SOURCE,
                          source_sha256=SOURCE_SHA, source_decoded_sha256=SOURCE_PLAIN_SHA,
                          assets=manifest, symbolic_handle_stores=HANDLE_STORES,
                          consumers=CONSUMERS,
                          loader_executed=False, world_constructed=False), indent=2))


if __name__ == '__main__':
    main()
