"""CUSTOM-0012: isolated native-loader input, never official starter bindings."""
from contextlib import contextmanager
from pathlib import Path
import struct


def fixture_bytes(*, revival=False):
    if type(revival) is not bool:
        raise ValueError('Explicit diagnostic revival boolean required')
    data = bytearray(b'\xff' * (60 + 960) + bytes(36))
    # CUSTOM-0017 only changes the explicit diagnostic skill identity.
    struct.pack_into('<HHH', data, 60, 2, 3 if revival else 0, 8 if revival else 1)
    data.extend(struct.pack('<III', 0x3b, 10, 10))
    return bytes(data)


@contextmanager
def isolated_hotbar(client, run, enabled=False, *, revival=False):
    if not enabled:
        yield
        return
    client, run = Path(client).resolve(), Path(run).resolve()
    if client.name != 'client' or client.parent.parent.name != 'capture_work':
        raise ValueError('Hotbar fixture requires capture_work client copy')
    directory = client / 'Save'
    directory.mkdir(exist_ok=True)
    if directory.resolve().parent != client:
        raise ValueError('Hotbar directory escapes isolated client')
    path = directory / 'CodexTrial.hky'
    payload = fixture_bytes(revival=revival)
    with path.open('xb') as stream:
        stream.write(payload)
    try:
        (run / 'hotbar-fixture-input.bin').write_bytes(payload)
        yield
    finally:
        if path.is_file():
            (run / 'hotbar-fixture-final.bin').write_bytes(path.read_bytes())
            path.unlink()
