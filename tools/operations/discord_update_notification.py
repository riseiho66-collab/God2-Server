"""Send one Discord update card per GitHub push; never build or run the game."""
from __future__ import annotations

import base64
import datetime
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


def git(*args: str, env=None) -> bytes:
    return subprocess.check_output(['git', *args], env=env, stderr=subprocess.DEVNULL)


def safe_text(value: str) -> str:
    value = ''.join(c if ord(c) >= 32 and ord(c) != 127 else ' ' for c in value)
    return re.sub(r'([\\`*_{}\[\]()<>~|])', r'\\\1', value).replace('@', '@\u200b')


def changes(before: str, after: str):
    if not re.fullmatch(r'[0-9a-f]{40}', after):
        raise ValueError('Invalid commit SHA')
    if not before or before == '0' * 40:
        return [('新增', p.decode('utf-8', 'replace')) for p in
                git('ls-tree', '-r', '--name-only', '-z', after).split(b'\0') if p]
    if not re.fullmatch(r'[0-9a-f]{40}', before):
        raise ValueError('Invalid base SHA')
    try:
        git('cat-file', '-e', before + '^{commit}')
    except subprocess.CalledProcessError:
        # A force-push may remove the old commit from the checked out history.
        env = os.environ.copy()
        auth = base64.b64encode(('x-access-token:' + env['GH_TOKEN']).encode()).decode()
        env.update(GIT_CONFIG_COUNT='1',
                   GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                   GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth)
        git('fetch', '--no-tags', 'origin', before, env=env)
    parts = iter(git('diff', '--name-status', '-z', '-M', before, after).split(b'\0'))
    result = []
    for raw in parts:
        if not raw:
            continue
        status = raw.decode('ascii')
        old = next(parts).decode('utf-8', 'replace')
        if status[0] in 'RC':
            new = next(parts).decode('utf-8', 'replace')
            result.append(('重新命名' if status[0] == 'R' else '複製', old + ' → ' + new))
        else:
            result.append(({'A': '新增', 'D': '刪除'}.get(status[0], '修改'), old))
    return result


def main() -> None:
    webhook = os.environ.get('DISCORD_WEBHOOK_URL', '').strip()
    if not re.fullmatch(r'https://discord\.com/api/webhooks/\d+/[A-Za-z0-9_.-]+', webhook):
        raise ValueError('DISCORD_WEBHOOK_URL is missing or invalid')
    repo = os.environ['GITHUB_REPOSITORY']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository name')
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as stream:
        event = json.load(stream)
    after = os.environ['GITHUB_SHA']
    before = event.get('before', '')
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        ancestors = git('rev-list', '--parents', '-n', '1', after).decode().split()
        before = ancestors[1] if len(ancestors) > 1 else ''
    entries = changes(before, after)
    lines = ['• ' + kind + '：' + safe_text(path) for kind, path in entries]
    visible = []
    for line in lines:
        if sum(len(x) + 1 for x in visible) + len(line) > 1750:
            break
        visible.append(line)
    overflow = len(visible) < len(lines)
    if overflow:
        visible.append(f'\n共 {len(lines)} 個檔案；完整清單見附件。')
    branch = os.environ.get('GITHUB_REF_NAME', 'main')
    embed = {
        'title': safe_text(f'{repo}：{branch} 已更新')[:256],
        'url': f'https://github.com/{repo}/commit/{after}',
        'description': '\n'.join(visible) or '本次推送沒有檔案內容變更。',
        'color': 0x2ECC71,
        'footer': {'text': f'{after[:7]} · {len(entries)} 個檔案'},
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    payload = {'username': 'GitHub Actions', 'allowed_mentions': {'parse': []},
               'embeds': [embed]}
    headers = {'User-Agent': 'God2-Server-GitHub-Actions/1.0'}
    if overflow:
        attachment = '\n'.join(kind + '：' + path for kind, path in entries).encode('utf-8')
        if len(attachment) > 7_000_000:
            raise ValueError('File list exceeds attachment budget')
        boundary = 'god2-' + uuid.uuid4().hex
        payload['attachments'] = [{'id': 0, 'filename': 'changed-files.txt',
                                   'description': '完整檔案變更清單'}]
        body = io.BytesIO()
        body.write((f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
                    'Content-Type: application/json\r\n\r\n').encode())
        body.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        body.write((f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="files[0]"; '
                    'filename="changed-files.txt"\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n').encode())
        body.write(attachment)
        body.write(f'\r\n--{boundary}--\r\n'.encode())
        data = body.getvalue()
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    else:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    for attempt in range(4):
        request = urllib.request.Request(webhook + '?wait=true', data=data,
                                         headers=headers, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                message = json.load(response)
            if message.get('channel_id') != os.environ['EXPECTED_DISCORD_CHANNEL']:
                raise ValueError('Discord response channel mismatch')
            print(f"Discord update delivered: message {message['id']}; {len(entries)} files")
            return
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 3:
                delay = float(json.loads(error.read()).get('retry_after', 2))
                time.sleep(min(max(delay, 1), 30))
                continue
            # Avoid echoing the request URL, which contains the credential.
            raise RuntimeError(f'Discord HTTP status {error.code}') from None
        except urllib.error.URLError:
            raise RuntimeError('Discord network request failed; inspect delivery before retrying') from None
    raise RuntimeError('Discord rate limit retry budget exhausted')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Do not include tracebacks/URLs or arbitrary external error bodies.
        print('Notification failed (' + type(error).__name__ + ').', file=sys.stderr)
        sys.exit(1)
