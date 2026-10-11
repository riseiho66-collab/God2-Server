"""Read-only pre-decode / client checksum-return correlation for recovered RX."""
import hashlib
import json
from pathlib import Path
from recovered_packet_pipeline import record_packet


class CryptoRuntimeObserver:
    def __init__(self, run):
        self.run = Path(run)
        self.pending = {}
        self.tx = {}

    def arm(self, driver):
        # Caller registers/stack proven in native-master-01-stable.bin.
        driver.command('bp260 410a30')
        driver.command('bp261 410a3e')
        driver.command('bp262 410690')

    def handle(self, index, event, driver):
        if index not in (260, 261, 262):
            return False
        identity = (event['pid'], event['tid'])
        sequence = event['sequence']
        directory = self.run / 'crypto-private'
        directory.mkdir(exist_ok=True)
        if index == 262:
            event['event_type'] = 'CRYPTO_TX_PLAINTEXT_ENTRY'
            length, address = event['a1'] + 2, event['a0'] - 2
            if event['ret'] != 0x4109fa or not 4 <= length <= 258 or address <= 0:
                event['capture_supported'] = False
                return True
            path = directory / f'tx-input-{sequence:04}.plain.bin'
            driver.command(f'.writemem "{path.as_posix()}" {address:x} L{length:x}')
            if path.exists() and path.stat().st_size == length:
                self.tx[(event['pid'], event['tid'], address)] = (sequence, path)
                event['plaintext_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            return True
        if index == 260:
            event['event_type'] = 'CRYPTO_RX_WIRE_ENTRY'
            base = directory / f'packet-{sequence:04}'
            output = driver.command(f'!God2Probe.packet @edi @ebx @esi "{base.as_posix()}"')
            records = [line.split('GOD2_PACKET ', 1)[1] for line in output.splitlines() if 'GOD2_PACKET ' in line]
            if not records:
                event['capture_supported'] = False
                return True
            report = json.loads(records[-1])
            if identity in self.pending:
                event['unmatched_previous_entry'] = True
            self.pending[identity] = (dict(event), report)
            event['deterministic_decode'] = report
            return True
        event['event_type'] = 'CRYPTO_RX_CHECKSUM_RETURN'
        entry = self.pending.pop(identity, None)
        if entry is None:
            event['matched'] = False
            return True
        before, report = entry
        # Before CALL, two arguments are already pushed. Both callees use ret 8.
        matched = event['sp'] == before['sp'] + 8 and report.get('pid') == event['pid'] and report.get('tid') == event['tid']
        report['runtime_return_matched'] = matched
        report['client_checksum_pass'] = matched and event['eax'] != 0
        report['client_parser_runtime_validated'] = False
        event['matched'] = matched
        if matched and report.get('decoded') is True:
            actual = directory / f'packet-{before["sequence"]:04}.client-plain.bin'
            driver.command(f'.writemem "{actual.as_posix()}" {report["wire_address"]:x} L{report["wire_len"]:x}')
            expected = directory / f'packet-{before["sequence"]:04}.plain.bin'
            report['client_plaintext_match'] = actual.exists() and expected.exists() and actual.read_bytes() == expected.read_bytes()
            if actual.exists():
                report['client_plaintext_sha256'] = hashlib.sha256(actual.read_bytes()).hexdigest()
        # Checksum acceptance is not opcode/state parser acceptance.
        event['packet_evidence'] = record_packet(self.run, before['sequence'], report,
            direction='S2C', socket=report.get('socket'), caller_rva='0x10a30')
        return True

    def correlate_tx(self, event, report):
        source = self.tx.pop((event['pid'], event['tid'], report.get('wire_address')), None)
        if source is None or report.get('decoded') is not True:
            return
        sequence, path = source
        expected = self.run / 'crypto-private' / f'packet-{event["sequence"]:04}.plain.bin'
        report['client_plaintext_match'] = expected.exists() and path.read_bytes() == expected.read_bytes()
        report['client_plaintext_entry_sequence'] = sequence
        report['client_plaintext_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        report['client_parser_runtime_validated'] = False
