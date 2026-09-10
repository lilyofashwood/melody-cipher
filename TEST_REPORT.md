# Validation report · 2026-09-05

**18 tests passed**, with zero skipped tests in this environment. NumPy 2.3.5, SciPy 1.17.0 and FFmpeg were available. Command: `python3 -m unittest -v`.

These checks validate a controlled prototype. No real microphone recordings or human listening panel were available for this pass.

| Check | Observed result |
| --- | --- |
| Exact Unicode, combining marks, emoji, case, empty text, tabs, CR/LF, repeated spaces and NUL | Exact protocol round trips |
| All 256 byte values; 100 deterministic randomized Unicode strings | Exact protocol round trips |
| Maximum frame length and invalid length/tempo inputs | Boundary accepted; over-limit/invalid inputs rejected |
| All six historical palettes on supported text | Token output matches recovered original Python encoder |
| Known historical Unicode losses and multi-character uppercase case | Hardened legacy adapter rejects unsupported input explicitly |
| Both palettes, twelve note-domain transpositions, mixed octave shifts | Exact message recovery |
| Note substitution or deletion; corrupted/truncated byte frames | Rejected |
| Full synthesized mix containing `𝔩̸\n👾` (with a real newline) | Exact audio-only UTF-8 recovery |
| Luminous full mix at 104 BPM | Exact audio recovery |
| Full-mix transposition by -5 and +7 semitones | Text recovered and tonic inferred correctly |
| 20 dB SNR white noise + gain ×0.15 + leading/trailing silence | Exact audio recovery on one deterministic test fixture |
| Resampling to create 4% faster playback, changing pitch and time together | Exact audio recovery |
| 48 kHz WAV and phase-inverted stereo | Exact audio recovery |
| 128 kbps MP3 through the optional FFmpeg adapter | Exact audio recovery |
| Half-length crop, unrelated 440 Hz sine wave, silence | No message accepted |

## Delivered listening examples

The decoder was run independently on each full WAV and each MP3. It receives the audio file only, never the score, MIDI, source text or a filename-to-message lookup.

| Input | Duration | Observed notes | Recovered text | CRC |
| --- | --- | --- | --- | --- |
| Nocturne WAV | 41.27 s | 115 | `follow the melody` | Valid |
| Luminous WAV | 41.27 s | 115 | `follow the melody` | Valid |
| Nocturne MP3, 128 kbps | About 41.27 s plus codec padding | 115 | `follow the melody` | Valid |
| Luminous MP3, 128 kbps | About 41.27 s plus codec padding | 115 | `follow the melody` | Valid |

Each contains 8 signature notes, 104 frame notes and 3 coda notes. All four used the first segmentation attempt: 2048-sample window, relative gate 0.22, repeat-valley prominence 0.13. The detected tuning offset was approximately +0.08 cents.

## What remains unknown

Real speaker-to-phone transfer, room reverb, changing background noise, dense polyphony, singing, arbitrary MIDI instrument renders, very short data notes, loss of the opening signature, and insertion/deletion correction remain unvalidated. The first audible signature note is used to infer register. Tests of global playback speed do not validate local rubato or gradual drift. White-noise tests do not model all real background sounds.

The two negative audio fixtures and selected damaged frames do not establish a general false-positive rate. CRC32 is an error-detection gate, not authentication, calibrated confidence or error correction. Detected-note amplitude ratios are not probabilities.

Pitch smoothing was measured, but beauty was not objectively established. Both performances and MIDI files are included for listening and musical revision. The Astra handoff identifies the remaining acoustic and aesthetic work.
