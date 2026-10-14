#!/usr/bin/env python3
"""Read-only Voice Memos export + local transcription. Never deletes recordings."""
import argparse
import hashlib
import json
import math
import mmap
import os
import re
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import tempfile

ROOT = Path.home() / 'Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings'
MODEL = Path.home() / '.cache/voice-memos/ggml-base.bin'


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def embedded(data):
    """Read tsrp atoms; never search arbitrary audio bytes for JSON."""
    found = []
    def walk(start, end, depth=0):
        if depth > 20:
            raise ValueError('Atom nesting too deep')
        while start < end:
            if start + 8 > end:
                raise ValueError('Truncated atom header')
            size, kind = struct.unpack_from('>I4s', data, start)
            header = 8
            if size == 1:
                if start + 16 > end:
                    raise ValueError('Truncated extended atom')
                size = struct.unpack_from('>Q', data, start + 8)[0]
                header = 16
            if size == 0:
                size = end - start
            if size < header or start + size > end:
                raise ValueError('Invalid/truncated atom size')
            a, z = start + header, start + size
            if kind in (b'moov', b'trak', b'udta'):
                walk(a, z, depth + 1)
            elif kind == b'tsrp':
                obj = json.loads(data[a:z].decode('utf-8'))
                attr = obj.get('attributedString', {})
                runs, table = attr.get('runs'), attr.get('attributeTable')
                if not isinstance(table, list):
                    raise ValueError('Unknown transcript attribute table')
                if not isinstance(runs, list) or len(runs) % 2:
                    raise ValueError('Unknown transcript runs schema')
                words, times = [], []
                for i in range(0, len(runs), 2):
                    word, ref = runs[i:i+2]
                    if not isinstance(word, str) or type(ref) is not int or not 0 <= ref < len(table):
                        raise ValueError('Unknown transcript run/reference')
                    words.append(word)
                    tr = table[ref].get('timeRange')
                    if tr is not None:
                        if len(tr) != 2 or any(not isinstance(t, (int, float)) or not math.isfinite(t) for t in tr) or not 0 <= tr[0] <= tr[1]:
                            raise ValueError('Invalid transcript timestamps')
                        times.append(tr)
                text = ''.join(words)
                if not text.strip():
                    raise ValueError('Empty embedded transcript')
                found.append({'text': text, 'source': 'Apple Voice Memos embedded tsrp',
                              'locale': obj.get('locale'),
                              'first_second': min((t[0] for t in times), default=None),
                              'last_second': max((t[1] for t in times), default=None)})
            start = z
    walk(0, len(data))
    if len(found) > 1:
        raise ValueError('Multiple embedded transcripts; review in app instead of guessing')
    return found[0] if found else None


def run(args, timeout=3600):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{Path(args[0]).name} failed: {result.stderr[-2000:]}')
    return result.stdout


def duration(path):
    value = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'default=noprint_wrappers=1:nokey=1', path], 60).strip())
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Invalid audio duration')
    return value


def decode_check(path):
    run(['ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-i', path, '-map', '0:a:0', '-f', 'null', '-'])


def local_asr(audio, model, language):
    if not model.is_file() or model.stat().st_size < 10_000_000:
        raise ValueError('No usable local Whisper model. Supply --model (test-only models are invalid).')
    if language != 'en' and '.en.' in model.name:
        raise ValueError('English-only model cannot transcribe requested language')
    with tempfile.TemporaryDirectory(prefix='voice-memos-asr-') as td:
        wav, output = Path(td) / 'audio.wav', Path(td) / 'transcript'
        run(['ffmpeg', '-v', 'error', '-nostdin', '-i', audio, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav])
        run(['whisper-cli', '-m', model, '-f', wav, '-l', language, '-otxt', '-of', output])
        text = output.with_suffix('.txt').read_text(encoding='utf-8')
    if not text.strip():
        raise ValueError('Local ASR produced no text; review audio, do not delete')
    return {'text': text, 'source': f'Local whisper.cpp ({model.name})', 'language': language}


def new_output(path):
    path.mkdir(parents=True, exist_ok=False)


def write_json(path, obj, exclusive=False):
    if exclusive:
        with path.open('x', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    else:
        # State is private working metadata, outside the three-file deliverable folder.
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def check_files(folder, state):
    expected = state['files']
    if len(expected) != 3 or {p.name for p in folder.iterdir()} != set(expected):
        raise ValueError('Exactly three verified deliverables required')
    for name, digest in expected.items():
        p = folder / name
        if Path(name).name != name or p.is_symlink() or not p.is_file() or p.stat().st_size == 0 or sha(p) != digest:
            raise ValueError(f'Missing/changed deliverable: {name}')


def inventory(args):
    db = args.recordings / 'CloudRecordings.db'
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as c:
        c.execute('PRAGMA query_only=ON')
        c.row_factory = sqlite3.Row
        rows = c.execute('SELECT ZUNIQUEID AS id,ZENCRYPTEDTITLE AS title,ZPATH AS path,ZDURATION AS seconds,ZFLAGS AS flags,datetime(ZDATE+978307200,\'unixepoch\') AS recorded_utc FROM ZCLOUDRECORDING ORDER BY ZDATE DESC LIMIT ?', (args.limit,)).fetchall()
    print(json.dumps({'warning': 'Includes deleted/hidden records. Match current All Recordings UI; never select by flags or filename alone.',
                      'recordings': [dict(row) for row in rows]}, ensure_ascii=False, indent=2))


def export(args):
    src, out, state_path = args.source.resolve(), args.out.resolve(), args.state.resolve()
    if state_path.is_relative_to(out):
        raise ValueError('--state must be outside the deliverable folder')
    if state_path.exists() or out.exists():
        raise FileExistsError('Output or state already exists; use a fresh path')
    if src.suffix.lower() not in ('.m4a', '.wav', '.mp3', '.flac'):
        raise ValueError('Export .qta/edited/multitrack recordings via app first; do not rename them .m4a')
    original_hash, seconds = sha(src), duration(src)
    if abs(seconds - args.expected_duration) > 2:
        raise ValueError('Duration differs from selected UI recording')
    new_output(out)
    audio = out / ('01_原始录音' + src.suffix.lower())
    shutil.copy2(src, audio)
    if sha(audio) != original_hash or sha(src) != original_hash:
        raise ValueError('Source changed or copy mismatch; do not delete')
    decode_check(audio)
    result = None
    if not args.force_local_asr and src.suffix.lower() == '.m4a':
        with audio.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            result = embedded(data)
    if result is None:
        result = local_asr(audio, args.model.expanduser(), args.language)
    if result.get('last_second') is not None and result['last_second'] > seconds + 2:
        raise ValueError('Transcript extends beyond audio duration')
    raw = out / '02_原始转录.txt'
    header = f"{args.title}｜原始转录\n录制时间：{args.recorded_at}\n时长：{seconds:.3f} 秒\n来源：{result['source']}\n说明：以下为自动识别原文，未修订；可能存在识别错误。\n\n"
    with raw.open('x', encoding='utf-8') as f:
        f.write(header + result['text'])
    state = {'out': str(out), 'source_path': str(src), 'source_sha256': original_hash,
             'recording_id': args.recording_id, 'title': args.title, 'recorded_at': args.recorded_at,
             'duration': seconds, 'audio': audio.name, 'raw': raw.name,
             'transcription': {k: v for k, v in result.items() if k != 'text'},
             'files': {p.name: sha(p) for p in (audio, raw)}, 'complete': False}
    write_json(state_path, state, exclusive=True)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def safe_title(value):
    value = re.sub(r'[\x00-\x1f/\\:*?"<>|]', '_', value).strip(' .')[:60].rstrip(' .')
    if not value:
        raise ValueError('Content title must not be empty')
    return value


def finalize(args):
    state = json.loads(args.state.read_text())
    out = Path(state['out'])
    if state['complete']:
        raise ValueError('Already finalized; verify existing files')
    for name, digest in state['files'].items():
        if sha(out / name) != digest:
            raise ValueError('Exported audio/raw text changed')
    text = args.edited.read_text(encoding='utf-8')
    if not text.strip():
        raise ValueError('Empty edited transcript')
    title = safe_title(args.content_title)
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', state['recorded_at'])
    stem = title + ('_' + date_match[0] if date_match else '')
    audio_name = '01_' + stem + '_原始录音' + Path(state['audio']).suffix
    raw_name = '02_' + stem + '_原始转录.txt'
    edited_name = '03_' + stem + '_整理后转录.txt'
    targets = [audio_name, raw_name, edited_name]
    if any((out / name).exists() for name in targets):
        raise FileExistsError('Content-title filename already exists')
    # Hard-link then unlink: unlike rename(), a concurrent destination is never overwritten.
    for old, new in [(state['audio'], audio_name), (state['raw'], raw_name)]:
        os.link(out / old, out / new)
        (out / old).unlink()
    edited = out / edited_name
    with edited.open('x', encoding='utf-8') as f:
        f.write(text)
    state['content_title'] = title
    state['audio'], state['raw'] = audio_name, raw_name
    state['files'] = {name: sha(out / name) for name in targets}
    check_files(out, state)
    decode_check(out / state['audio'])
    state['complete'] = True
    write_json(args.state, state)
    print('Three files finalized. Run verify, review content, then apply user-authorized UI deletion only.')


def verify(args):
    state = json.loads(args.state.read_text())
    if not state.get('complete'):
        raise ValueError('Transcripts not finalized; do not delete')
    out = Path(state['out'])
    check_files(out, state)
    decode_check(out / state['audio'])
    src = Path(state['source_path'])
    if src.exists() and sha(src) != state['source_sha256']:
        raise ValueError('Original recording changed since export; do not delete')
    print(json.dumps({'verified': True, 'out': str(out), 'title': state['title'],
                      'recording_id': state['recording_id'], 'recorded_at': state['recorded_at'],
                      'duration': state['duration'], 'files': state['files'],
                      'note': 'Integrity verified, not transcription accuracy or deletion authorization.'}, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest='command', required=True)
    s = subs.add_parser('inventory', help='Read DB metadata; includes deleted records, confirm in UI')
    s.add_argument('--recordings', type=Path, default=ROOT);s.add_argument('--limit', type=int, default=10);s.set_defaults(func=inventory)
    s = subs.add_parser('export', help='Copy audio, extract Apple transcript or run local whisper.cpp')
    for flag in ('source', 'out', 'state'):
        s.add_argument('--'+flag, type=Path, required=True)
    for flag in ('title', 'recorded-at', 'recording-id'):
        s.add_argument('--'+flag, required=True)
    s.add_argument('--expected-duration', type=float, required=True)
    s.add_argument('--model', type=Path, default=MODEL);s.add_argument('--language', default='zh')
    s.add_argument('--force-local-asr', action='store_true');s.set_defaults(func=export)
    s = subs.add_parser('finalize');s.add_argument('--state', type=Path, required=True);s.add_argument('--edited', type=Path, required=True);s.add_argument('--content-title', required=True);s.set_defaults(func=finalize)
    s = subs.add_parser('verify');s.add_argument('--state', type=Path, required=True);s.set_defaults(func=verify)
    args = p.parse_args()
    try:
        args.func(args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, sqlite3.Error, subprocess.SubprocessError) as e:
        p.exit(1, f'ERROR: {e}\nDo not delete the recording. Preserve partial exports and retry in a fresh folder.\n')

if __name__ == '__main__':
    main()
