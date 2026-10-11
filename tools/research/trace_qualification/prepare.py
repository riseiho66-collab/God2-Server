"""Generate bounded gate-disarming experiments; never modify sealed captures."""
import argparse
from pathlib import Path

HOME = Path(__file__).resolve().parents[3]
OUT = HOME / 'artifacts/capture_work/host-20260918-1430/output'


def prepare(run):
    if run not in ('frame-a', 'frame-b'):
        raise ValueError('Unapproved experiment name')
    source = (OUT / 'capture-mode-a.txt').read_text()
    source = source.replace('mode-a-', run + '-')
    source = source.replace('bp /1 @$t1\ng',
                            'bd 0\nbp /1 @$t1\nk\nu @$t1 L3\ng')
    source = source.replace('r\n.if ((@eip', 'r\nk\ndd @esp L10\nbe 0\n.if ((@eip')
    source = source.replace('.echo MODE_BRIDGE_MISMATCH; q',
        '.echo MODE_BRIDGE_MISMATCH; k; dd @esp L10; '
        f'.writemem ..\\output\\{run}-mismatch.bin @$t0 L307000; q')
    source = source.replace('dd @esp L8\nbd 0',
        f'dd @esp L8\n.writemem ..\\output\\{run}-boundary.bin @$t0 L307000\nbd 0', 1)
    if run == 'frame-b':
        source = source.replace(f'{run}-end.bin @$t0 L307000; q',
            f'{run}-end.bin @$t0 L307000; t 0n32; '
            '.printf "FRAME_LIVENESS pid=%x tid=%x pc=%p sp=%p time=%I64x\\n", '
            '@$tpid, @$tid, @eip, @esp, @$dbgtime; r; '
            f'.writemem ..\\output\\{run}-live.bin @$t0 L307000; q')
    with (OUT / f'capture-{run}.txt').open('x', encoding='ascii') as stream:
        stream.write(source)
    print(OUT / f'capture-{run}.txt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', choices=('frame-a', 'frame-b'))
    prepare(parser.parse_args().run)
