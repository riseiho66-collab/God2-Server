"""Read-only pagefile resolution and current-client branch preflight."""
import argparse
import ctypes
from ctypes import wintypes
import json
import ntpath
from pathlib import Path


def client_math(p, s, b, free):
    p &= 0xffffffff
    signed_p = p if p < 0x80000000 else p - 0x100000000
    q = ((((s * b) & 0xffffffff) >> 10) * free) & 0xffffffff
    t = (q + p) & 0xffffffff
    branch = ('EARLIER_MESSAGE_916_BRANCH' if signed_p < 700 and t > 700
              else 'MESSAGE_905_BRANCH' if t < 700 else 'NO_WARNING_PATH')
    return {'P': signed_p, 'Q': q, 'T': t, 'predicted_branch': branch}


def resolve_paths(values):
    paths = []
    for value in values:
        path = value[4:] if value.startswith('\\??\\') else value
        drive, tail = ntpath.splitdrive(path)
        if len(drive) != 2 or drive[1] != ':' or not drive[0].isascii() or not drive[0].isalpha() or not tail.startswith('\\'):
            raise ValueError('Active pagefile does not identify a drive root')
        paths.append(path)
    roots = sorted({ntpath.splitdrive(p)[0].upper() + '\\' for p in paths})
    if len(roots) != 1:
        raise ValueError('Expected exactly one active pagefile volume')
    return paths, roots


def preflight():
    import winreg
    key_name = r'SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management'
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name, 0, winreg.KEY_READ) as key:
        paging, paging_type = winreg.QueryValueEx(key, 'PagingFiles')
        existing, existing_type = winreg.QueryValueEx(key, 'ExistingPageFiles')
    result = {
        'pagingfiles': paging, 'existing_pagefiles': existing,
        'resolution_source': 'HKLM\\' + key_name + '\\ExistingPageFiles',
        'fresh_client_started': False, 'warning_905_reached': None,
        'winsock_reached': None, 'normalization_applied': False,
        'environment_modified': False, 'runtime_acceptance': 'NOT_RUN',
        'scope': 'Host real-OS API preflight, not injected client or ddraw wrapper execution',
    }
    if paging_type != winreg.REG_MULTI_SZ or paging != [r'?:\pagefile.sys']:
        result['verdict'] = 'PAGINGFILES_WILDCARD_PRECONDITION_FAILED'
        return result
    try:
        if existing_type != winreg.REG_MULTI_SZ:
            raise ValueError('Unexpected ExistingPageFiles registry type')
        paths, roots = resolve_paths(existing)
    except ValueError as exc:
        result.update(verdict='PAGINGFILE_WILDCARD_NORMALIZATION_AMBIGUOUS', reason=str(exc))
        return result
    result.update(active_pagefile_paths=paths, active_pagefile_volumes=roots,
                  original_path='?:\\', normalized_root=roots[0])
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    api = kernel.GetDiskFreeSpaceA
    api.argtypes = [wintypes.LPCSTR] + [ctypes.POINTER(wintypes.DWORD)] * 4
    api.restype = wintypes.BOOL
    values = [wintypes.DWORD() for _ in range(4)]
    success = bool(api(roots[0].encode('ascii'), *(ctypes.byref(v) for v in values)))
    error = ctypes.get_last_error() if not success else None
    s, b, free, total = [v.value for v in values]
    result['real_GetDiskFreeSpaceA'] = dict(success=success, S=s, B=b, F=free,
        total=total, last_error=error, real_api_address=hex(ctypes.cast(api, ctypes.c_void_p).value),
        address_scope='This preflight host process only')
    if not success:
        result['verdict'] = 'REAL_DISK_QUERY_FAILED'
        return result
    result['client_math'] = client_math(0, s, b, free)
    compatible = result['client_math']['predicted_branch'] == 'NO_WARNING_PATH'
    result['preflight_no_warning_compatible'] = compatible
    result['verdict'] = ('PREFLIGHT_PASS_RUNTIME_REQUIRED' if compatible
                         else result['client_math']['predicted_branch'])
    result['branch_evidence'] = {
        'signed_minimum_check_rva': '0xf180',
        'unsigned_sum_check_rva': '0xf18f',
        'jbe_no_adjustment_rva': '0xf195',
        'registry_write_attempt_call_rva': '0xf1f0',
        'message_916_lookup_rva': '0xf1f5',
        'message_905_guard_rva': '0xf246',
        'qualification': 'Prediction from current-image instructions and real OS outputs, not a fresh-client observation'
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = preflight()
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
