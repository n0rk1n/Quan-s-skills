#!/usr/bin/env python3
"""Archive observed Bilibili metadata and images. Never operates an account."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit, urlunsplit

DOWNLOADS = Path.home() / 'Downloads'
MIMES = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def http_url(value):
    require(isinstance(value, str) and value.strip() == value and bool(value), 'Missing image/source URL')
    if value.startswith('//'):
        value = 'https:' + value
    parsed = urlsplit(value)
    require(parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username
            and not parsed.password and not any(ord(c) < 33 for c in value), 'Expected an observed HTTP(S) URL')
    return value


def validate(payload, kind):
    require(kind in ('favorites', 'following'), 'Invalid archive kind')
    require(isinstance(payload, dict), 'Input must be a JSON object')
    json.dumps(payload, allow_nan=False)
    source = http_url(payload.get('source_url'))
    items = payload.get('items')
    require(isinstance(items, list), 'items must be an array')
    require(1 <= len(items) <= 40 if kind == 'favorites' else len(items) == 24, 'Invalid batch size')
    if kind == 'favorites' and len(items) < 40:
        require(payload.get('end_confirmed') is True, 'Short favorites batch requires confirmed folder end')
    seen, result = set(), []
    for raw in items:
        require(isinstance(raw, dict), 'Each item must be an object')
        identity = raw.get('id')
        pattern = r'BV[0-9A-Za-z]{10}' if kind == 'favorites' else r'[0-9]+'
        require(isinstance(identity, str) and re.fullmatch(pattern, identity), 'Invalid stable ID')
        require(identity not in seen, 'Duplicate stable ID')
        seen.add(identity)
        prefix = 'https://www.bilibili.com/video/' if kind == 'favorites' else 'https://space.bilibili.com/'
        require(raw.get('canonical_url') == prefix + identity, 'ID/canonical URL mismatch')
        name = raw.get('display_name')
        require(isinstance(name, str) and name.strip(), 'display_name must be nonempty')
        metadata = raw.get('metadata', {})
        require(isinstance(metadata, dict), 'metadata must be an object')
        result.append(dict(id=identity, canonical_url=prefix+identity, display_name=name,
                           image_source_url=http_url(raw.get('image_source_url')), metadata=metadata,
                           tags=['Bilibili', 'Bilibili ' + kind.title()]))
    return dict(source_url=source, end_confirmed=payload.get('end_confirmed') is True, items=result)


def preflight():
    for executable in ('curl', 'file'):
        require(shutil.which(executable), f'Missing executable: {executable}')
    require(DOWNLOADS.is_dir(), 'Downloads directory is unavailable')
    with tempfile.TemporaryFile(dir=DOWNLOADS) as probe:
        probe.write(b'bilibili'); probe.seek(0)
        require(probe.read() == b'bilibili', 'Downloads read-back failed')
    return {'downloads': str(DOWNLOADS.resolve()), 'ready': True}


def safe_path(batch, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe archive path')
    current = batch
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), 'Symlink in archive path')
    require(current.resolve().is_relative_to(batch.resolve()), 'Archive path escapes batch')
    return current


def batch_path(value, kind):
    value = Path(value).expanduser().absolute()
    require(not value.is_symlink() and value.is_dir(), 'Batch must be an existing non-symlink directory')
    require(value.parent.resolve() == DOWNLOADS.resolve(), 'Batch must be directly beneath Downloads')
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2} Archived Bilibili ' + kind.title() + r' Batch \d{2,}', value.name), 'Wrong batch kind/name')
    return value.resolve()


def atomic_write(batch, relative, text):
    target = safe_path(batch, relative)
    fd, temporary = tempfile.mkstemp(prefix='.writing-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            out.write(text); out.flush(); os.fsync(out.fileno())
        os.replace(temporary, target)
        require(target.read_text(encoding='utf-8') == text, 'File read-back mismatch')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def lock(batch):
    path = safe_path(batch, '.archive.lock')
    with path.open('x', encoding='utf-8') as out:
        out.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def markdown_text(value):
    escaped = html.escape(value)
    escaped = re.sub(r'([\\`*_{}\[\]()#!|])', r'\\\1', escaped)
    return escaped.replace('\r', '').replace('\n', '<br>')


def status_text(item):
    if item['archive_status'] != 'verified':
        return '归档未完成'
    return {'pending': '已归档，待清理', 'removed': '已归档，浏览器已核验移除',
            'unresolved': '已归档，清理结果待解决'}[item['cleanup_status']]


def record(item):
    text = (f"# {markdown_text(item['display_name'])}\n\n"
            f"- ID：{item['id']}\n- 状态：{status_text(item)}\n\n"
            f"[打开 Bilibili 页面]({item['canonical_url']})\n\n")
    if item['archive_status'] == 'verified':
        text += f"![本地图片]({Path(item['image_path']).name})\n\n"
    if item['cleanup_evidence']:
        text += '核验证据：' + markdown_text(item['cleanup_evidence']) + '\n\n'
    if item['error']:
        text += '失败原因：' + markdown_text(item['error']) + '\n\n'
    text += '## 页面资料\n\n<pre>' + html.escape(json_text(item['metadata'])) + '</pre>\n\n'
    return text + '<details><summary>归档元数据</summary>\n<pre>' + html.escape(json_text(item)) + '</pre>\n</details>\n'


def summary(manifest):
    text = (f"# Bilibili 归档总结\n\n本批 {len(manifest['items'])} 条。"
            '账号操作证据由浏览器提供；脚本只核验本地文件。\n\n')
    for item in manifest['items']:
        text += (f"- [{markdown_text(item['display_name'])}]({item['id']}/record.md)"
                 f"（{item['id']}）：{status_text(item)}\n")
    return text + '\n<details><summary>完整清单与核验证据</summary>\n<pre>' + html.escape(json_text(manifest)) + '</pre>\n</details>\n'


def save(batch, manifest):
    # Each replacement is atomic. A crash between files fails the read-back gate.
    for item in manifest['items']:
        directory = safe_path(batch, item['id'])
        directory.mkdir(exist_ok=True)
        atomic_write(batch, item['record_path'], record(item))
    atomic_write(batch, 'archive.json', json_text(manifest))
    atomic_write(batch, 'summary.md', summary(manifest))


def load(batch, kind):
    manifest = json.loads(safe_path(batch, 'archive.json').read_text(encoding='utf-8'))
    require(isinstance(manifest, dict), 'Manifest must be a JSON object')
    require(manifest.get('version') == 1 and manifest.get('kind') == kind, 'Unknown archive format/kind')
    canonical = validate(manifest, kind)
    require(manifest.get('archived_ids') == [i['id'] for i in canonical['items']], 'Manifest ID set mismatch')
    for item, original in zip(manifest['items'], canonical['items']):
        require(all(item[k] == v for k, v in original.items()), 'Manifest source metadata mismatch')
        require(item.get('record_path') == item['id'] + '/record.md', 'Record path mismatch')
        require(item.get('archive_status') in ('pending', 'failed', 'verified'), 'Invalid archive status')
        require(item.get('cleanup_status') in ('pending', 'removed', 'unresolved'), 'Invalid cleanup status')
        require(isinstance(item.get('cleanup_evidence'), str), 'Invalid cleanup evidence')
        if item['cleanup_status'] != 'pending':
            require(item['cleanup_evidence'].strip(), 'Missing cleanup evidence')
    return manifest


def download(url, destination):
    """Bounded curl download with an exact-host fallback for TLS errors only."""
    def run(address):
        return subprocess.run(['curl', '--globoff', '--silent', '--show-error', '--fail', '--location',
                               '--connect-timeout', '15', '--max-time', '60', '--retry', '2',
                               '--proto', '=http,https', '--proto-redir', '=http,https',
                               '--output', str(destination), address], capture_output=True, text=True, timeout=200)
    response = run(url)
    parsed = urlsplit(url)
    actual = url
    if response.returncode in (35, 51, 58, 60, 77, 80, 82, 83, 90, 91) and parsed.hostname == 'i0.hdslb.com':
        netloc = 'i1.hdslb.com' + (f':{parsed.port}' if parsed.port else '')
        actual = urlunsplit(parsed._replace(netloc=netloc))
        response = run(actual)
    require(response.returncode == 0, f'Image download failed (curl exit {response.returncode})')
    return actual


def image_info(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0, 'Missing or empty image')
    result = subprocess.run(['file', '--brief', '--mime-type', str(path)], capture_output=True, text=True, timeout=10, check=True)
    mime = result.stdout.strip()
    require(mime in MIMES, f'Unsupported actual image MIME: {mime}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return mime, digest


def check_image(batch, item, kind):
    mime = item.get('image_mime')
    require(mime in MIMES, 'Missing image MIME')
    stem = 'cover' if kind == 'favorites' else 'avatar'
    expected = f"{item['id']}/{stem}.{MIMES[mime]}"
    require(item.get('image_path') == expected, 'Image path mismatch')
    require(image_info(safe_path(batch, expected)) == (mime, item.get('image_sha256')), 'Image content changed')


def populate(batch, manifest):
    kind = manifest['kind']
    for item in manifest['items']:
        try:
            if item['archive_status'] == 'verified':
                check_image(batch, item, kind)
                continue
            directory = safe_path(batch, item['id'])
            directory.mkdir(exist_ok=True)
            stem = 'cover' if kind == 'favorites' else 'avatar'
            require(not any(directory.glob(stem + '.*')), 'Existing unverified image; manual inspection required')
            fd, temporary = tempfile.mkstemp(prefix='.image-', dir=directory)
            os.close(fd)
            try:
                actual = download(item['image_source_url'], Path(temporary))
                mime, digest = image_info(Path(temporary))
                relative = f"{item['id']}/{stem}.{MIMES[mime]}"
                os.link(temporary, safe_path(batch, relative))  # Atomic, never overwrites.
                item.update(image_path=relative, image_mime=mime, image_sha256=digest,
                            image_download_url=actual, archive_status='verified', error='')
                check_image(batch, item, kind)
            finally:
                Path(temporary).unlink(missing_ok=True)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            item.update(archive_status='failed', error=str(exc))
        save(batch, manifest)
    save(batch, manifest)


def failure(batch, errors):
    return dict(batch=str(batch), cleanup_ready=False, verified_ids=[], remaining_ids=[], failed=errors)


def verify_files(batch, kind):
    errors = []
    try:
        manifest = load(batch, kind)
        for item in manifest['items']:
            try:
                require(item['archive_status'] == 'verified', item.get('error') or 'Image not verified')
                check_image(batch, item, kind)
                require(safe_path(batch, item['record_path']).read_text(encoding='utf-8') == record(item), 'Record content mismatch')
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                errors.append({'id': item['id'], 'error': str(exc)})
        require(safe_path(batch, 'summary.md').read_text(encoding='utf-8') == summary(manifest), 'Summary content mismatch')
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        errors.append({'error': str(exc)})
    if errors:
        return failure(batch, errors)
    return dict(batch=str(batch), cleanup_ready=True, verified_ids=manifest['archived_ids'],
                remaining_ids=[i['id'] for i in manifest['items'] if i['cleanup_status'] != 'removed'], failed=[])


def verify(value, kind):
    batch = batch_path(value, kind)
    if (batch / '.archive.lock').exists() or (batch / '.archive.lock').is_symlink():
        return failure(batch, [{'error': 'Archive mutation in progress; do not use cleanup targets'}])
    return verify_files(batch, kind)


def archive(payload, kind):
    manifest = validate(payload, kind)
    preflight()
    prefix = datetime.now().strftime('%Y-%m-%d') + f' Archived Bilibili {kind.title()} Batch '
    number = 1
    while True:
        batch = DOWNLOADS.resolve() / f'{prefix}{number:02d}'
        try:
            batch.mkdir()
            break
        except FileExistsError:
            number += 1
    manifest.update(version=1, kind=kind, created_at=datetime.now().astimezone().isoformat(),
                    archived_ids=[i['id'] for i in manifest['items']])
    for item in manifest['items']:
        item.update(record_path=item['id'] + '/record.md', archive_status='pending',
                    cleanup_status='pending', cleanup_evidence='', image_path=None,
                    image_mime=None, image_sha256=None, image_download_url=None, error='')
    try:
        with lock(batch):
            save(batch, manifest)
            populate(batch, manifest)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return failure(batch, [{'error': str(exc)}])
    return verify(batch, kind)


def resume(value, kind):
    batch = batch_path(value, kind)
    preflight()
    with lock(batch):
        manifest = load(batch, kind)
        require(all(i['cleanup_status'] == 'pending' for i in manifest['items']), 'Cleanup already started; do not resume images')
        for item in manifest['items']:
            path = safe_path(batch, item['record_path'])
            if path.exists():
                require(path.read_text(encoding='utf-8') == record(item), 'Existing record changed; manual inspection required')
        path = safe_path(batch, 'summary.md')
        if path.exists():
            require(path.read_text(encoding='utf-8') == summary(manifest), 'Existing summary changed; manual inspection required')
        populate(batch, manifest)
    return verify(batch, kind)


def update(value, payload, kind):
    batch = batch_path(value, kind)
    with lock(batch):
        require(verify_files(batch, kind)['cleanup_ready'], 'Local archive verification failed')
        manifest = load(batch, kind)
        require(isinstance(payload, dict) and isinstance(payload.get('items'), list) and payload['items'], 'Expected nonempty status items')
        targets = {i['id']: i for i in manifest['items']}
        seen = set()
        for change in payload['items']:
            require(isinstance(change, dict), 'Invalid status item')
            identity = change.get('id')
            require(isinstance(identity, str) and identity in targets and identity not in seen, 'Unknown or duplicate status ID')
            seen.add(identity)
            status, evidence = change.get('status'), change.get('evidence')
            require(status in ('removed', 'unresolved') and isinstance(evidence, str) and evidence.strip(), 'Status requires browser evidence')
            item = targets[identity]
            require(item['cleanup_status'] != 'removed' or status == 'removed', 'Cannot retarget a verified-removed ID')
            item.update(cleanup_status=status, cleanup_evidence=evidence)
        save(batch, manifest)
    return verify(batch, kind)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    command = commands.add_parser('archive'); command.add_argument('--input', required=True)
    for name in ('verify', 'resume', 'update'):
        command = commands.add_parser(name); command.add_argument('--batch', required=True)
        if name == 'update':
            command.add_argument('--input', required=True)
    args = parser.parse_args()
    kind = Path(__file__).resolve().parents[1].name.removeprefix('archiving-bilibili-')
    try:
        if args.command == 'preflight':
            result = preflight()
        elif args.command == 'archive':
            result = archive(json.loads(Path(args.input).read_text(encoding='utf-8')), kind)
        elif args.command == 'update':
            result = update(args.batch, json.loads(Path(args.input).read_text(encoding='utf-8')), kind)
        else:
            result = {'verify': verify, 'resume': resume}[args.command](args.batch, kind)
        print(json_text(result), end='')
        return 0 if result.get('ready') or result.get('cleanup_ready') else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json_text(failure(getattr(args, 'batch', ''), [{'error': str(exc)}])), end='')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
