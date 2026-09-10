#!/usr/bin/env python3
"""Melody Bloom v2: reversible Unicode music, WAV/MIDI synthesis, legacy tokens.

Requires Python 3.10+, numpy and scipy. This is an artistic encoding, not encryption.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import struct
import zlib

import numpy as np
from scipy.io import wavfile

MAGIC = b'MB\x02'
MAX_PAYLOAD = 65535
MAX_RENDER_SECONDS = 600
MODES = {
    'nocturne': ((0, 7), (3,), (5,), (10,)),  # minor pentatonic
    'luminous': ((0, 7), (4,), (2,), (9,)),   # major pentatonic
}
SYNC_SYMBOLS = (0, 0, 1, 2, 3, 0, 2, 0)
LEGACY_SCALES = {
    'duochroma': 'C C# D D# E F F# G G# A A# B'.split(),
    'octatonic_half_whole': 'E F G G# A# B C# D'.split(),
    'locrian_plus2': 'E F F# G A Bb C D'.split(),
    'dorian_flat2': 'E F G A B C C# D'.split(),
    'diminished_octatonic_whole_half': 'E F# G A A# B C D#'.split(),
    'bebop_mixolydian': 'E F# G# A B C# D D#'.split(),
}
NAMES = 'C C# D D# E F F# G G# A A# B'.split()


class DecodeError(ValueError):
    pass


@dataclass(frozen=True)
class Note:
    start: float  # seconds
    duration: float
    midi: int
    velocity: float
    voice: str = 'lead'
    role: str = 'payload'


def pack(text: str) -> bytes:
    data = text.encode('utf-8', errors='strict')
    if len(data) > MAX_PAYLOAD:
        raise ValueError('Message exceeds the 65535-byte protocol limit.')
    body = MAGIC + len(data).to_bytes(2, 'big') + data
    return body + struct.pack('>I', zlib.crc32(body))


def unpack(frame: bytes) -> str:
    if len(frame) < 9 or frame[:3] != MAGIC:
        raise DecodeError('Missing Melody Bloom v2 header.')
    size = int.from_bytes(frame[3:5], 'big')
    if len(frame) != size + 9:
        raise DecodeError('Truncated frame or unexpected trailing bytes.')
    if zlib.crc32(frame[:-4]) != int.from_bytes(frame[-4:], 'big'):
        raise DecodeError('Checksum failed; message has not been recovered.')
    try:
        return frame[5:-4].decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        raise DecodeError('Invalid UTF-8 payload.') from exc


def symbols_from_bytes(data: bytes) -> list[int]:
    return [(b >> shift) & 3 for b in data for shift in (6, 4, 2, 0)]


def bytes_from_symbols(symbols: list[int]) -> bytes:
    if len(symbols) % 4 or any(s not in (0, 1, 2, 3) for s in symbols):
        raise DecodeError('Invalid or incomplete four-symbol byte.')
    return bytes((symbols[i] << 6) | (symbols[i+1] << 4) |
                 (symbols[i+2] << 2) | symbols[i+3]
                 for i in range(0, len(symbols), 4))


def sync_intervals(mode: str) -> tuple[int, ...]:
    groups = MODES[mode]
    return (0, 7, groups[1][0], groups[2][0], groups[3][0], 7, groups[2][0], 0)


def symbol_for_pitch(midi: int, tonic_pc: int, mode: str) -> int:
    pc = (int(midi) - tonic_pc) % 12
    for symbol, choices in enumerate(MODES[mode]):
        if pc in choices:
            return symbol
    raise DecodeError(f'Pitch {midi} is outside the {mode} alphabet.')


def decode_pitches(pitches: list[int]) -> dict:
    """Find a complete frame using only observed notes; infer mode and transposition.

    Octave errors do not alter data. No score, source text, filename or tempo is read.
    Reject ambiguous different payloads. CRC detects damage; it does not correct it.
    """
    results = []
    for start in range(max(0, len(pitches) - 43)):
        tonic_pc = pitches[start] % 12
        prefix = [(n - tonic_pc) % 12 for n in pitches[start:start+8]]
        for mode in MODES:
            if prefix != list(sync_intervals(mode)):
                continue
            data_start = start + 8
            try:
                first = [symbol_for_pitch(n, tonic_pc, mode)
                         for n in pitches[data_start:data_start+20]]
                header = bytes_from_symbols(first)
                if len(header) != 5 or header[:3] != MAGIC:
                    continue
                frame_notes = 4 * (9 + int.from_bytes(header[3:5], 'big'))
                if data_start + frame_notes > len(pitches):
                    continue
                symbols = [symbol_for_pitch(n, tonic_pc, mode)
                           for n in pitches[data_start:data_start+frame_notes]]
                message = unpack(bytes_from_symbols(symbols))
                results.append({'text': message, 'checksum': 'valid', 'mode': mode,
                                'tonic_pitch_class': tonic_pc, 'tonic': NAMES[tonic_pc],
                                'preamble_note_index': start, 'payload_note_count': frame_notes,
                                'consumed_notes': 8 + frame_notes})
            except DecodeError:
                continue
    if not results:
        raise DecodeError('No complete frame passed its header and CRC32 checks. '
                          'A cropped, old-format or unclear recording may not decode.')
    if len({r['text'] for r in results}) > 1:
        raise DecodeError('Multiple different valid frames found; isolate one performance.')
    return results[0]


def legacy_encode(text: str, cipher: str) -> list[str]:
    """Exact historical mapping on its reversible domain; reject lossy input."""
    notes = LEGACY_SCALES[cipher]
    out = []
    for ch in text:
        if cipher == 'duochroma':
            if ord(ch) >= 144:
                raise ValueError('Legacy Duochroma only distinguishes code points 0..143. Use v2 for Unicode.')
            high, low = divmod(ord(ch), 12)
        elif ch in ' \n':
            out.append('/' if ch == ' ' else '\n')
            continue
        elif ch.isascii() and ch.isalpha():
            high, low = divmod(ord(ch.upper()) - 65, 8)
        else:
            raise ValueError('Legacy base-8 accepts only ASCII letters, spaces and newlines; case is lost.')
        out.extend((notes[high], notes[low]))
    return out


def legacy_decode(tokens: list[str], cipher: str) -> str:
    notes = LEGACY_SCALES[cipher]
    base = len(notes)
    out, i = [], 0
    while i < len(tokens):
        if tokens[i] in ('/', '\n'):
            out.append(' ' if tokens[i] == '/' else '\n')
            i += 1
            continue
        if i + 1 >= len(tokens) or tokens[i] not in notes or tokens[i+1] not in notes:
            raise DecodeError(f'Invalid legacy note pair at token {i}.')
        code = notes.index(tokens[i]) * base + notes.index(tokens[i+1])
        if base == 8 and code >= 26:
            raise DecodeError(f'Legacy pair at token {i} does not encode A-Z.')
        out.append(chr(code if base == 12 else 65 + code))
        i += 2
    return ''.join(out)


def _chords(mode: str) -> tuple[tuple[int, ...], ...]:
    # Relative to D: Dm7 / Bbmaj7 / Fmaj7 / Csus2(add6), or D6 / Bm7 / Gmaj7 / Asus2(add6).
    if mode == 'nocturne':
        return ((0, 3, 7, 10), (8, 0, 3, 7), (3, 7, 10, 2), (10, 0, 5, 7))
    return ((0, 4, 7, 9), (9, 0, 4, 7), (5, 9, 0, 4), (7, 9, 2, 4))


def _voicings(symbols: list[int], mode: str, tonic: int) -> list[int]:
    """Dynamic programming over equivalent pitches; every candidate preserves its bits."""
    if not symbols:
        return []
    groups = MODES[mode]
    candidates = [[n for n in range(tonic, tonic + 25)
                   if (n-tonic) % 12 in groups[s]] for s in symbols]
    costs = {tonic + 12: 0.0}
    back = []
    for i, available in enumerate(candidates):
        center = tonic + 9 + 4 * math.sin(math.pi * (i % 32) / 31)
        chord = _chords(mode)[(i // 8) % 4]
        current, links = {}, {}
        for n in available:
            local = 0.018 * (n-center)**2
            if i % 4 == 0 and (n-tonic) % 12 not in chord:
                local += 0.9
            options = [(v + 0.10*(n-prev)**2 + max(0, abs(n-prev)-7)*2
                        + (0.32 if n == prev else 0), prev) for prev, v in costs.items()]
            cost, previous = min(options)
            current[n], links[n] = cost + local, previous
        costs = current
        back.append(links)
    cursor = min(costs, key=costs.get)
    result = [cursor]
    for i in range(len(symbols)-1, 0, -1):
        cursor = back[i][cursor]
        result.append(cursor)
    return result[::-1]


def compose(text: str, mode: str = 'nocturne', bpm: float = 92,
            transpose: int = 0, seed: int = 7) -> dict:
    if mode not in MODES:
        raise ValueError('Unknown palette.')
    if not math.isfinite(bpm) or not 55 <= bpm <= 160:
        raise ValueError('Tempo must be 55..160 BPM.')
    if not isinstance(transpose, int) or not -12 <= transpose <= 12:
        raise ValueError('Transpose must be an integer in -12..12 semitones.')
    symbols = symbols_from_bytes(pack(text))
    tonic, beat = 62 + transpose, 60 / bpm
    rng = np.random.default_rng(seed)
    melody, backing = [], []
    cursor = 0.25
    # The audible eight-note signature establishes the musical key and data boundary.
    for interval in sync_intervals(mode):
        melody.append(Note(cursor, beat * .40, tonic + 12 + interval, .68, role='sync'))
        cursor += beat * .5
    cursor += beat * .5
    payload_start = cursor
    pitches = _voicings(symbols, mode, tonic)
    rhythms = ((.5, .5, .5, .5, .5, .5, .5, .5),
               (.5, .5, .75, .25, .5, .5, .5, .5),
               (.75, .25, .5, .5, .5, .5, .5, .5),
               (.5, .5, .5, .5, .75, .25, .5, .5))
    for i, pitch in enumerate(pitches):
        beats = rhythms[(i // 8) % 4][i % 8]
        slot = beat * beats
        arc = .07 * math.sin(math.pi * (i % 32) / 31)
        accent = .07 if i % 8 == 0 else (.025 if i % 2 == 0 else 0)
        velocity = .63 + arc + accent + rng.uniform(-.018, .018)
        # Clear re-articulation permits repeated equal pitches to carry separate symbols.
        melody.append(Note(cursor, max(.075, slot - .065), pitch, velocity))
        cursor += slot
    for interval, beats in zip((7, MODES[mode][1][0], 0), (.5, .5, 2.0)):
        melody.append(Note(cursor, beats * beat - .07, tonic + 12 + interval,
                           .61, role='coda'))
        cursor += beats * beat
    # Accompaniment is lower and softer than the message voice.
    bar = 0
    while payload_start + bar * 4 * beat < cursor - beat:
        start = payload_start + bar * 4 * beat
        chord = _chords(mode)[bar % 4]
        root = tonic - 24 + chord[0]
        backing.append(Note(start, 3.5*beat, root, .40, 'bass', 'accompaniment'))
        voicing = []
        for pc in chord:
            n = tonic - 12 + pc
            while n >= tonic:
                n -= 12
            voicing.append(n)
            backing.append(Note(start + .015*len(voicing), 3.6*beat,
                                n, .18, 'pad', 'accompaniment'))
        arpeggio = sorted(voicing)
        for j in range(8):
            backing.append(Note(start + j*.5*beat, .75*beat,
                                arpeggio[(0, 2, 1, 3, 2, 1, 3, 2)[j]],
                                .23 if j % 2 == 0 else .18, 'harp', 'accompaniment'))
        bar += 1
    return {'format': 'melody-bloom-score-v2', 'mode': mode, 'bpm': bpm,
            'tonic_midi': tonic, 'seed': seed,
            'notes': [asdict(n) for n in sorted(melody + backing, key=lambda n: n.start)]}


def _tone(note: Note, sr: int) -> np.ndarray:
    tail = .028 if note.voice == 'lead' else .28
    t = np.arange(max(1, int((note.duration + tail)*sr))) / sr
    freq = 440 * 2 ** ((note.midi-69)/12)
    if note.voice == 'lead':
        # Soft, struck harmonic tone. A sustained fundamental supports pitch estimation.
        signal = (np.sin(2*np.pi*freq*t) * (.48 + .52*np.exp(-t/.34)) +
                  .23*np.sin(2*np.pi*2*freq*t)*np.exp(-t/.16) +
                  .07*np.sin(2*np.pi*3*freq*t)*np.exp(-t/.10))
        attack, level = .008, .24
    elif note.voice == 'harp':
        signal = (np.sin(2*np.pi*freq*t) + .11*np.sin(2*np.pi*2*freq*t))*np.exp(-t/.28)
        attack, level = .008, .18
    elif note.voice == 'bass':
        signal = np.sin(2*np.pi*freq*t) + .08*np.sin(2*np.pi*2*freq*t)
        attack, level = .04, .21
    else:
        signal = np.sin(2*np.pi*freq*t) + .035*np.sin(2*np.pi*2*freq*t)
        attack, level = .11, .19
    envelope = np.minimum(1, t/attack) * np.clip((note.duration + tail - t)/tail, 0, 1)
    return signal * envelope * level * note.velocity


def render(score: dict, sr: int = 22050, stem: bool = False, reverb: float = .06) -> np.ndarray:
    if sr not in (16000, 22050, 32000, 44100, 48000):
        raise ValueError('Use sample rate 16000, 22050, 32000, 44100 or 48000.')
    notes = [Note(**n) for n in score['notes'] if not stem or n['voice'] == 'lead']
    duration = max((n.start+n.duration for n in notes), default=0) + .8
    if duration > MAX_RENDER_SECONDS:
        raise ValueError('Rendering is limited to ten minutes; split the message into shorter phrases.')
    audio = np.zeros((int((duration+.6)*sr), 2), dtype=np.float64)
    for note in notes:
        tone = _tone(note, sr)
        offset = int(note.start*sr)
        pan = 0 if note.voice in ('lead', 'bass') else (-.25 if note.voice == 'harp' else .25)
        audio[offset:offset+len(tone), 0] += tone * math.sqrt((1-pan)/2)
        audio[offset:offset+len(tone), 1] += tone * math.sqrt((1+pan)/2)
    if reverb and not stem:
        dry = audio.copy()
        for seconds, gain in ((.083, 1), (.149, .7), (.233, .45), (.371, .25)):
            shift = int(seconds*sr)
            audio[shift:] += dry[:-shift, ::-1] * reverb * gain
    peak = float(np.max(np.abs(audio)))
    if peak:
        audio *= .88 / peak
    return audio.astype(np.float32)


def save_wav(path: Path, samples: np.ndarray, sr: int = 22050) -> None:
    wavfile.write(str(path), sr, (np.clip(samples, -1, 1) * 32767).astype(np.int16))


def _vlq(n: int) -> bytes:
    if n < 0:
        raise ValueError('Negative MIDI delta time.')
    result = [n & 127]
    while n >> 7:
        n >>= 7
        result.insert(0, (n & 127) | 128)
    return bytes(result)


def save_midi(path: Path, score: dict) -> None:
    """SMF type 1 with a tempo track and separate instrument tracks; no text payload."""
    bpm, ticks = score['bpm'], 480
    tempo = int(60_000_000 / bpm).to_bytes(3, 'big')
    tempo_track = b'\x00\xff\x51\x03' + tempo + b'\x00\xff\x58\x04\x04\x02\x18\x08\x00\xff\x2f\x00'
    tracks = [tempo_track]
    for channel, (voice, program) in enumerate((('lead', 0), ('harp', 46), ('pad', 89), ('bass', 32))):
        events = []
        for n in score['notes']:
            if n['voice'] != voice:
                continue
            start = round(n['start'] * bpm/60 * ticks)
            end = max(start+1, round((n['start']+n['duration']) * bpm/60 * ticks))
            events.extend(((start, bytes((0x90+channel, n['midi'], min(127, max(1, round(n['velocity']*100)))))),
                           (end, bytes((0x80+channel, n['midi'], 0)))))
        data = bytearray(b'\x00\xff\x03' + bytes((len(voice),)) + voice.encode() + b'\x00' + bytes((0xc0+channel, program)))
        previous = 0
        for tick, message in sorted(events, key=lambda e: (e[0], e[1][0])):
            data += _vlq(tick-previous) + message
            previous = tick
        data += b'\x00\xff\x2f\x00'
        tracks.append(bytes(data))
    path.write_bytes(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), ticks) +
                     b''.join(b'MTrk' + struct.pack('>I', len(t)) + t for t in tracks))


def export(text: str, prefix: Path, mode: str, bpm: float, transpose: int = 0) -> dict:
    score = compose(text, mode, bpm, transpose)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    # Render before creating outputs so an overlong request does not leave a partial set.
    mix, lead = render(score), render(score, stem=True)
    save_wav(prefix.with_suffix('.wav'), mix)
    save_wav(prefix.with_name(prefix.name + '_lead').with_suffix('.wav'), lead)
    save_midi(prefix.with_suffix('.mid'), score)
    prefix.with_suffix('.score.json').write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'wav': str(prefix.with_suffix('.wav')), 'seconds': round(len(mix)/22050, 2),
            'mode': mode, 'payload_bytes': len(text.encode('utf-8')),
            'note_roundtrip': decode_pitches([n['midi'] for n in score['notes'] if n['voice']=='lead'])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    enc = sub.add_parser('encode', help='Export music as WAV, lead stem, MIDI and score JSON.')
    source = enc.add_mutually_exclusive_group(required=True)
    source.add_argument('--text')
    source.add_argument('--file', type=Path)
    enc.add_argument('--out', type=Path, default=Path('melody'))
    enc.add_argument('--mode', choices=MODES, default='nocturne')
    enc.add_argument('--bpm', type=float, default=92)
    enc.add_argument('--transpose', type=int, default=0)
    legacy = sub.add_parser('legacy', help='Historical note-token compatibility with explicit input limits.')
    legacy.add_argument('--cipher', choices=LEGACY_SCALES, required=True)
    legacy.add_argument('--text', required=True)
    legacy.add_argument('--decode', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'encode':
            source_text = args.text if args.text is not None else args.file.read_text(encoding='utf-8')
            result = export(source_text, args.out, args.mode, args.bpm, args.transpose)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.decode:
            tokens = args.text.replace('\n', ' \n ').split(' ')
            print(legacy_decode([t for t in tokens if t], args.cipher))
        else:
            print(' '.join(legacy_encode(args.text, args.cipher)))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
