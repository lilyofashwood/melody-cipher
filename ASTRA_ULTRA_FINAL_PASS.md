# Final pass for Astra · Ultra reasoning · VS Code

Continue Lily's Melody Cipher project from the attached `melody-bloom-v2.zip`. Open its `melody-bloom` directory in VS Code and read README.md, PROTOCOL.md, TEST_REPORT.md, melody_bloom.py, audio_decode.py, and test_melody_bloom.py before editing.

Goal: make text-encoded performances sound compelling enough to listen to as music, while recovering exact Unicode from actual audio recordings. Preserve Lily's preference for dark, delicate, playful musical and visual character; preserve combining marks, emoji, case and exact whitespace.

Historical source has been recovered. The original remembered URL `https://github.com/lilyofashwood/melody-cipher` returned 404. An archived copy at `https://github.com/atimics/melody-cipher` preserves four July 30, 2025 commits authored by lilyofashwood. Snapshot: dbeca271847f1cff7e9e97d946d8cd6c0871145d. The four files under historical/ match their original Git blob hashes, recorded in PROVENANCE.json. Treat those as compatibility fixtures. The atimics archive is read-only; establish the intended writable project before any remote integration.

Current implementation: separate v2 framing with UTF-8 bytes, length, CRC32, four two-bit notes per byte, eight-note signature, two pentatonic palettes, equivalent pitch choices optimized by dynamic programming, recurring rhythms, soft synthesized lead/harp/pad/bass, WAV/MIDI exports, and a waveform-based decoder. WAV uses NumPy/SciPy; optional FFmpeg handles compressed audio/video. Legacy token encoding and decoding preserve all six historical palettes on their valid input domains. V2 audio is intentionally a new format.

Already validated: 18 automated tests; exact Unicode and whitespace; legacy compatibility; note-domain transposition and octave changes; full synthesized mixes; 128 kbps MP3; 20 dB white-noise SNR combined with gain reduction and leading/trailing silence; 4% playback speed change; 48 kHz WAV; phase-inverted stereo; full-mix transposition by -5 and +7 semitones; rejection of corrupted/truncated frames, cropped clips, silence and an unrelated pure tone. Both delivered 41-second full mixes and their MP3 copies recover `follow the melody` from audio alone. The supplied test report is not a microphone benchmark. Do not describe unrun tests as passed.

Make the final pass concrete:

1. Run the existing suite, inspect the code and audition the two sample performances. Improve musical phrasing, repetition and variation, harmonic pacing, cadence placement, and instrument realism. Export A/B examples of the SAME text with the same loudness target. Include a glyph-rich Unicode phrase. Preserve decodability after every musical change. Human musical judgment matters more than optimizing a scalar smoothness score.

2. Evaluate a short corpus of real speaker-to-phone recordings if available. Include clean direct audio, speaker playback, room reverb, background sound, a crop, and a dense accompaniment. The current spectral tracker assumes a prominent melody register and an intact opening signature. It has no general source separation or error correction. If there are no real recordings, prepare a minimal recording protocol and reproducible synthetic degradations; mark the microphone portion untested.

3. Compare the current tracker against a monophonic pYIN route and, only where useful, Spotify Basic Pitch. Consult their official documentation. Basic Pitch supports polyphonic notes but works best with one instrument at a time. It is a transcription component, not a cipher decoder. Track onsets separately from pitch so repeated notes remain distinct. Address tuning drift, octave errors, rubato, reverb tails, insertions/deletions and ambiguity explicitly.

4. Consider periodic signatures as recurring musical motifs, independently framed blocks with sequence information, CRC per block, and an error/erasure code such as Reed–Solomon. Version any incompatible protocol change. Make partial recovery explicit and never silently fill missing letters with a language model. Validate decoded payloads against framing, checksums and strict UTF-8. A checksum detects corruption; it does not provide encryption, authentication or error correction by itself.

5. Add a usable interface in the appropriate project: text/file input, musical palette, tempo, Play/Stop, MIDI/WAV download, recording upload, detected-note inspection, and a clear verified/uncertain/rejected result. Keep the historical modes separate and labeled. Use safe text rendering for recovered messages. Prefer the existing application framework; do not replace the working core just to build a new demo. Follow applicable project instructions and establish a concrete preview before any publishing step.

6. Report what changed, an audible A/B result, exact frame-recovery results, false acceptances, remaining recording failures, and the next evidence needed. Return runnable code and fixtures. Avoid claiming universal audio decoding or subjective musical success from synthetic round trips alone.

Primary references:

* [librosa pYIN](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html)
* [Spotify Basic Pitch](https://github.com/spotify/basic-pitch)
* [Spotify Basic Pitch for TypeScript](https://github.com/spotify/basic-pitch-ts)
