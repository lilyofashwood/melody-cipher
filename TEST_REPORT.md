# Validation report · 2026-09-05

**18 tests passed**, with zero skipped tests in this environment. NumPy 2.3.5, SciPy 1.17.0 and FFmpeg were available. Command: `python3 -m unittest -v`.

This report covers synthesized performances, protocol checks and digital audio transformations.

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

## Recording profile

The decoder uses an intact opening signature and a prominent melody register. The fixtures above cover full mixes, white noise and global playback-speed changes. Speaker-to-phone transfer, room reverberation, singing, dense polyphony and alternate instrument recordings belong to the recording collection described in RECORDING_PROTOCOL.md.

CRC32 checks frame corruption. Sender authentication and error correction are separate layers. Detected-note amplitude ratios describe the measured signal; the table records the exact positive and negative fixtures exercised.

Both performances and MIDI files are included for listening and musical revision. Pitch smoothing gives the notes a gentler path; the listening pairs invite a choice of phrasing.
