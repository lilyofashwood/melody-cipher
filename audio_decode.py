#!/usr/bin/env python3
"""Decode complete Melody Bloom v2 WAV performances from audio samples alone.

Designed for the supplied synthesis and a prominent, separated melody register.
It is not a general polyphonic music transcriber. Recording robustness is empirical.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np
from scipy import signal, ndimage
from scipy.io import wavfile

from melody_bloom import DecodeError, decode_pitches


def prepare_samples(values: np.ndarray, sr: int) -> np.ndarray:
    """One validated boundary for both file and in-memory audio callers."""
    if not isinstance(sr, (int, np.integer)) or not 8000 <= sr <= 192000:
        raise DecodeError('Unsupported WAV sample rate; expected 8–192 kHz.')
    values = np.asarray(values)
    if values.size == 0 or values.ndim not in (1, 2) or (values.ndim == 2 and values.shape[1] > 8):
        raise DecodeError('Empty or unsupported WAV channel layout.')
    if len(values)/sr > 600:
        raise DecodeError('Audio decoding is limited to ten minutes per file.')
    dtype = values.dtype
    if np.issubdtype(dtype, np.unsignedinteger):
        midpoint = (np.iinfo(dtype).max + 1)/2
        values = (values.astype(np.float32)-midpoint)/midpoint
    elif np.issubdtype(dtype, np.signedinteger):
        values = values.astype(np.float32) / (2.0 ** (8*dtype.itemsize-1))
    else:
        values = values.astype(np.float32)
    if not np.isfinite(values).all():
        raise DecodeError('WAV contains non-finite sample values.')
    if values.ndim == 2:
        # Avoid cancellation in phase-inverted stereo; otherwise averaging reduces noise.
        average = values.mean(axis=1)
        channel = values[:, np.argmax(np.mean(values**2, axis=0))]
        values = average if np.mean(average**2) >= .12*np.mean(channel**2) else channel
    if np.max(np.abs(values)) < 1e-8:
        raise DecodeError('WAV is silent.')
    divisor = math.gcd(int(sr), 22050)
    if sr != 22050:
        values = signal.resample_poly(values, 22050//divisor, sr//divisor)
    return values


def read_audio(path: Path) -> tuple[int, np.ndarray]:
    sr, values = wavfile.read(str(path))
    return 22050, prepare_samples(values, sr)


def _peaks(spectrum: np.ndarray, frequencies: np.ndarray, low: float,
           high: float) -> tuple[np.ndarray, np.ndarray]:
    indices = np.flatnonzero((frequencies >= low) & (frequencies <= high))
    if len(indices) < 3:
        raise DecodeError('Could not establish a melody frequency range.')
    chosen = indices[np.argmax(spectrum[indices], axis=0)]
    chosen = np.clip(chosen, 1, len(frequencies)-2)
    cols = np.arange(spectrum.shape[1])
    left, center, right = (np.log(np.maximum(spectrum[chosen+d, cols], 1e-12))
                           for d in (-1, 0, 1))
    denominator = left - 2*center + right
    adjustment = np.divide(.5*(left-right), denominator,
                           out=np.zeros_like(center), where=np.abs(denominator)>1e-10)
    adjustment = np.clip(adjustment, -.5, .5)
    hz = (chosen + adjustment) * (frequencies[1]-frequencies[0])
    midi = 69 + 12*np.log2(np.maximum(hz, 1)/440)
    return midi, spectrum[chosen, cols]


def analyse(samples: np.ndarray, sr: int = 22050, window: int = 2048) -> dict:
    if len(samples) < window*2:
        raise DecodeError('Recording is too short for a complete frame.')
    hop = 220
    freq, times, stft = signal.stft(samples, fs=sr, nperseg=window,
                                   noverlap=window-hop, nfft=4096,
                                   boundary=None, padded=False)
    magnitude = np.abs(stft)
    # The first audible signature note is an octave above the payload's register floor.
    broad_midi, broad_amplitude = _peaks(magnitude, freq, 100, 4000)
    early_end = min(len(times), int(15*sr/hop))
    early = broad_amplitude[:early_end]
    audible = np.flatnonzero(early > max(float(np.quantile(early, .92)) * .30, 1e-7))
    if len(audible) < 5:
        raise DecodeError('No clear opening signature note detected.')
    first_indices = audible[:max(5, min(12, len(audible)))]
    initial_midi = float(np.median(broad_midi[first_indices]))
    tuning = initial_midi - round(initial_midi)
    tonic_midi = round(initial_midi) - 12
    low = 440 * 2**((tonic_midi - .45 - 69 + tuning)/12)
    high = 440 * 2**((tonic_midi + 24.45 - 69 + tuning)/12)
    midi, amplitude = _peaks(magnitude, freq, low, high)
    labels = ndimage.median_filter(np.rint(midi-tuning).astype(int), size=3)
    return {'times': times, 'midi': midi, 'labels': labels,
            'amplitude': ndimage.gaussian_filter1d(amplitude, .65),
            'tuning_cents': tuning*100, 'initial_tonic_midi': tonic_midi,
            'hop_seconds': hop/sr}


def segment(analysis: dict, threshold: float, valley_prominence: float = .13) -> list[dict]:
    amp, times = analysis['amplitude'], analysis['times']
    labels = analysis['labels'].copy()
    reference = float(np.quantile(amp, .98))
    labels[amp < reference*threshold] = -1
    boundaries = np.r_[0, np.flatnonzero(labels[1:] != labels[:-1])+1, len(labels)]
    events = []
    min_frames = max(2, round(.025/analysis['hop_seconds']))
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        if labels[a] < 0 or b-a < min_frames:
            continue
        # Repeated pitches need a fresh attack even when the release never reaches silence.
        valleys, _ = signal.find_peaks(-amp[a:b], prominence=reference*valley_prominence,
                                       distance=max(3, round(.09/analysis['hop_seconds'])))
        cuts = [a] + [a+int(v) for v in valleys
                      if min(v, b-a-int(v)) >= min_frames and amp[a+v] < reference*.75] + [b]
        for start, end in zip(cuts[:-1], cuts[1:]):
            if end-start < min_frames:
                continue
            pitch = int(labels[start])
            cents = float(np.median((analysis['midi'][start:end] -
                                     analysis['tuning_cents']/100 - pitch)*100))
            events.append({'start': round(float(times[start]), 4),
                           'end': round(float(times[end-1]+analysis['hop_seconds']), 4),
                           'midi': pitch, 'cents_deviation': round(cents, 2),
                           'relative_amplitude': round(float(np.mean(amp[start:end])/reference), 3)})
    return events


def decode_samples(samples: np.ndarray, sr: int = 22050) -> dict:
    """Try bounded acoustic segmentations, accepting only a frame with a valid CRC."""
    samples = prepare_samples(samples, sr)
    attempts, last_events = [], []
    for window in (2048, 1024):
        analysed = analyse(samples, 22050, window)
        for threshold, valley in ((.22, .13), (.15, .13), (.30, .13),
                                  (.38, .13), (.22, .20), (.15, .08)):
            events = segment(analysed, threshold, valley)
            attempts.append({'window': window, 'threshold': threshold,
                             'valley_prominence': valley, 'detected_notes': len(events)})
            last_events = events
            try:
                result = decode_pitches([e['midi'] for e in events])
                return {**result, 'audio_only': True,
                        'tuning_cents': round(analysed['tuning_cents'], 2),
                        'segmentation': attempts[-1], 'attempts': len(attempts),
                        'events': events}
            except DecodeError:
                continue
    error = DecodeError('No complete message passed CRC32 after audio transcription. '
                        'Try the lead stem or inspect the detected-note events. '
                        'Cropped clips and historical v1 music are not v2 frames.')
    error.diagnostics = {'checksum': 'not_validated', 'attempts': attempts, 'events': last_events}
    raise error


def decode_wav(path: Path) -> dict:
    sr, samples = read_audio(path)
    return decode_samples(samples, sr)


def decode_audio(path: Path) -> dict:
    """Read WAV directly, or use optional FFmpeg for compressed audio/video files."""
    if path.suffix.lower() in ('.wav', '.wave'):
        return decode_wav(path)
    if not path.is_file():
        raise DecodeError('Audio input is not a local file.')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise DecodeError('Install FFmpeg for this format, or convert the recording to WAV.')
    result = subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(path.resolve()),
                             '-t', '600', '-vn', '-ac', '1', '-ar', '22050',
                             '-f', 'f32le', 'pipe:1'], capture_output=True, timeout=60)
    if result.returncode or not result.stdout:
        raise DecodeError('FFmpeg could not decode the input audio.')
    return decode_samples(np.frombuffer(result.stdout, dtype='<f4').copy())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path, help='WAV, or compressed audio/video with optional FFmpeg.')
    parser.add_argument('--events', type=Path, help='Save observed notes, including failed decoding attempts.')
    args = parser.parse_args()
    try:
        result = decode_audio(args.audio)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        if args.events and hasattr(exc, 'diagnostics'):
            args.events.write_text(json.dumps(exc.diagnostics, indent=2), encoding='utf-8')
        parser.exit(2, f'{exc}\n')
    if args.events:
        args.events.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'events'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
