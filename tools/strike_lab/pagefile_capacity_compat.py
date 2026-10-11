"""Opt-in, process-local effective-capacity policy, not InitialSize recovery."""
import hashlib
import json
import re
import subprocess

EXPECTED_HASH = 'fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1'
KEY = r'SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management'


def live_state():
    script = r"""
$ErrorActionPreference='Stop'
$m=Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management'
[pscustomobject]@{
 raw=@($m.PagingFiles); existing=@($m.ExistingPageFiles)
 automatic=(Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile
 usage=@(Get-CimInstance Win32_PageFileUsage | Select-Object Name,AllocatedBaseSize)
 settings=@(Get-CimInstance Win32_PageFileSetting | Select-Object Name,InitialSize,MaximumSize)
} | ConvertTo-Json -Depth 5 -Compress
"""
    return json.loads(subprocess.check_output(['powershell.exe', '-NoProfile', '-NonInteractive',
        '-Command', script], text=True, timeout=15))


def contract(state):
    if state['automatic'] is not True or state['raw'] != [r'?:\pagefile.sys'] or state['settings']:
        raise ValueError('Effective-capacity policy preconditions failed')
    if len(state['existing']) != 1 or len(state['usage']) != 1:
        raise ValueError('Ambiguous active pagefile')
    path = state['existing'][0]
    if path.startswith('\\??\\'):
        path = path[4:]
    record = state['usage'][0]
    if not re.fullmatch(r'[A-Za-z]:\\pagefile\.sys', path, re.I) or path.casefold() != record['Name'].casefold():
        raise ValueError('Pagefile identity mismatch')
    capacity = record['AllocatedBaseSize']
    if type(capacity) is not int or not 700 <= capacity <= 0x7fffffff:
        raise ValueError('Real capacity below requirement or outside signed parser bounds')
    return path, capacity, f'{path} {capacity}'


def number(driver, expression):
    text = driver.command(f'.printf "PFVALUE=%p\\n", {expression}')
    match = re.search(r'PFVALUE=([0-9a-fA-F`]+)', text)
    if not match:
        raise ValueError('Cannot read debugger expression: ' + text)
    return int(match[1].replace('`', ''), 16)


def memory(driver, address, length):
    text = driver.command(f'db {address:x} L{length:x}')
    data = []
    for line in text.splitlines():
        match = re.match(r'^\s*[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{2}[ -]){1,16})', line)
        if match:
            data.extend(bytes.fromhex(match[1].replace('-', ' ')))
    if len(data) != length:
        raise ValueError('Incomplete debugger memory read')
    return bytes(data)


def cstring(driver, address, limit=256):
    return memory(driver, address, limit).split(b'\0', 1)[0].decode('ascii')


class CapacityAdapter:
    def __init__(self, client, run):
        if hashlib.sha256((client / 'God2.exe').read_bytes()).hexdigest() != EXPECTED_HASH:
            raise ValueError('Client hash mismatch')
        self.before = live_state()
        self.path, self.capacity, self.view = contract(self.before)
        self.run = run
        self.boundary = None
        self.applied = False
        self.slot = None
        self.report = dict(policy='AUTO_MANAGED_PAGEFILE_EFFECTIVE_CAPACITY',
            host_automatic_managed=True, active_pagefile=self.path,
            effective_capacity=dict(value_mb=self.capacity, source='Win32_PageFileUsage.AllocatedBaseSize'),
            legacy_view=self.view, claimed_initial_size=False, host_before=self.before,
            runtime_acceptance='NOT_RUN', verdict='NOT_VERIFIED')
        self.report['adapter_sha256'] = hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest()
        self.save()

    def save(self):
        (self.run / 'pagefile-capacity-policy.json').write_text(json.dumps(self.report, indent=2)+'\n')

    def arm(self, driver):
        for index, pc in [(280,0x40f0d6),(281,0x40f0db),(282,0x40f186),(283,0x40f1f5)]:
            driver.command(f'bp{index} {pc:x}')

    def handle(self, index, event, driver):
        if index == 280:
            sp = event['sp']
            if cstring(driver,number(driver,f'poi({sp:x})')) != KEY:
                raise ValueError('Unexpected registry key')
            if cstring(driver,number(driver,f'poi({sp+4:x})'),32) != 'PagingFiles':
                raise ValueError('Unexpected registry value')
            if number(driver,'poi(@ecx+4)') != 0x80000002:
                raise ValueError('Unexpected registry hive')
            self.boundary = (event['pid'],event['tid'],number(driver,f'poi({sp+8:x})'))
            event['event_type'] = 'PAGEFILE_QUERY_SCOPED'
            return True
        if index == 281:
            if self.applied or not self.boundary or self.boundary[:2] != (event['pid'],event['tid']):
                raise ValueError('Registry return context mismatch')
            address = self.boundary[2]
            if event['eax'] != 1 or cstring(driver,address) != r'?:\pagefile.sys':
                raise ValueError('Unexpected raw query output')
            fresh = live_state()
            if contract(fresh) != (self.path,self.capacity,self.view):
                raise ValueError('Live pagefile state changed')
            payload = self.view.encode('ascii') + b'\0'
            if len(payload) > 256:
                raise ValueError('View exceeds original buffer')
            event['write'] = driver.command(f'eb {address:x} ' + payload.hex(' '))
            if memory(driver,address,len(payload)) != payload:
                raise ValueError('View write verification failed')
            event.update(event_type='PAGEFILE_EFFECTIVE_VIEW', raw=r'?:\pagefile.sys', view=self.view,
                         capacity_source='AUTO_MANAGED_EFFECTIVE_CAPACITY')
            self.applied = True
            self.report.update(host_at_translation=fresh, translation_count=1)
            self.save()
            return True
        if index == 272:
            if not self.applied or cstring(driver,number(driver,'poi(@esp)'),16) != self.path[:3]:
                raise ValueError('DISK_NORMALIZATION_FAILED')
            self.slot = number(driver,'poi(57040c)')
            saved = number(driver,'poi(ddraw+53abc)')
            kernel = number(driver,'kernel32!GetDiskFreeSpaceA')
            base = number(driver,'kernelbase!GetDiskFreeSpaceA')
            # The wrapper's saved target may be its own trampoline. Bind the
            # semantic OS boundary explicitly, not an unclassified trampoline.
            original = base
            event['os_api_code'] = driver.command(f'u {base:x} L8')
            event['os_api_module'] = driver.command(f'lm a {base:x}')
            event['saved_wrapper_target'] = hex(saved)
            event['kernel32_export'] = hex(kernel)
            if 'KERNELBASE' not in event['os_api_module'].upper():
                raise ValueError('OS API module mismatch')
            if 'ddraw' in event['os_api_code'].lower():
                raise ValueError('OS API entry redirects to compatibility wrapper')
            if self.slot != number(driver,'ddraw+24bd0'):
                raise ValueError('Unexpected query wrapper')
            driver.command(f'ed 57040c {original:x}')
            if number(driver,'poi(57040c)') != original:
                raise ValueError('API binding verification failed')
            event['real_api_address'] = hex(original)
            self.report['real_api_address'] = hex(original)
        if index == 273 and self.slot is not None:
            driver.command(f'ed 57040c {self.slot:x}')
            if number(driver,'poi(57040c)') != self.slot:
                raise ValueError('API binding restoration failed')
            self.report['disk_slot_restored'] = True
            self.slot = None
            self.save()
        if index == 282:
            event.update(event_type='PAGEFILE_P_BRANCH', branch=driver.command('u @eip L1'),
                         registers=driver.command('r'))
            return True
        if index == 283:
            raise ValueError('MESSAGE_916_STILL_REACHED')
        return False

    def restore(self, driver):
        if self.slot is not None:
            driver.command(f'ed 57040c {self.slot:x}')
            if number(driver,'poi(57040c)') != self.slot:
                raise ValueError('Pending API binding restoration failed')
            self.slot = None
            self.report['disk_slot_restored'] = True
        self.save()
