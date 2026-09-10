# 𝄞̷ Melody Bloom · Melody Cipher v2 prototype

Lily's text-to-music project, recovered and extended on September 5, 2026.

This package creates a soft pentatonic performance from exact Unicode text, exports WAV and MIDI, and recovers a complete message from a WAV or MP3 recording of the new performance. The four historical source files are preserved byte for byte in `historical/`.

## Listen first

Both examples encode **follow the melody** and last approximately 41.27 seconds. The mix includes a struck, piano-like lead, low harp figures, a soft sustained accompaniment, and restrained stereo echoes. The lead is synthesized from harmonics; it is not a sampled acoustic piano.

| Example | Sound palette | Files |
| --- | --- | --- |
| Nocturne | D minor pentatonic; Dm7, Bbmaj7, Fmaj7 and suspended C colors | `examples/follow_the_melody_nocturne.mp3` and `.wav` |
| Luminous | D major pentatonic; D6, Bm7, Gmaj7 and suspended A colors | `examples/follow_the_melody_luminous.mp3` and `.wav` |

Each has a separate `_lead.wav`, a `.mid` for a DAW or better instrument sounds, and a `.score.json`. `nocturne_decoded.json` and `luminous_decoded.json` contain the notes actually detected from their WAVs. Audio decoding does not read those sidecars or the MIDI files.

## Run

Use Python 3.10 or newer in a virtual environment:

```sh
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` in PowerShell. Then:

```sh
python -m pip install -r requirements.txt
python melody_bloom.py encode --text "follow the melody" --mode nocturne --out examples/my_message
python audio_decode.py examples/my_message.wav --events detected_notes.json
python -m unittest -v
```

For text containing combining marks, emoji, exact whitespace or multiple lines, a UTF-8 file avoids terminal quoting problems:

```sh
python melody_bloom.py encode --file message.txt --mode luminous --bpm 92 --out examples/my_message
```

`--transpose` accepts an integer from -12 through +12 semitones. Tempo accepts 55–160 BPM; the automated audio tests do not establish equal robustness at every possible tempo and transposition. Rendering and input processing are bounded to ten minutes. Use short messages; the codec carries only two bits per melody note.

WAV input uses NumPy and SciPy. If FFmpeg is installed and on PATH, the decoder also accepts compressed audio and video files through its audio stream:

```sh
python audio_decode.py examples/follow_the_melody_nocturne.mp3
```

MP3 at 128 kbps has been tested. M4A, FLAC and MP4 rely on FFmpeg format support and have not been separately tested here. Video input uses the first default audio stream and ignores the picture. The adapter processes at most the first ten minutes.

## What changed musically

The original project assigns a fixed pair of note names to a character. The v2 codec assigns bits to **sets of equivalent pitches**. The composer chooses among those pitches using dynamic programming, with costs for large jumps, register drift and weak chord alignment. The decoder recovers the same bits from any permitted choice.

Four recurring rhythmic patterns, changing accents, phrase-level loudness contours, a closing cadence and low accompaniment give the sequence musical shape. Rhythm, loudness and accompaniment do not encode characters. An octave change does not alter a pitch-class symbol, so octave errors from a pitch tracker can be tolerated at the protocol layer.

For the delivered phrase, the optimized payload's mean absolute pitch change is 2.641 semitones in Nocturne and 2.621 in Luminous. Assigning each symbol its first allowed pitch in a fixed octave gives 3.350 and 3.107 respectively. This measures smoother movement within the new codec, not a controlled comparison with the old cipher or proof of subjective beauty. Musical taste still needs listening and iteration.

## Historical source recovery

The remembered `lilyofashwood/melody-cipher` URL returned 404 through the available GitHub connection. A public archived copy survives at [atimics/melody-cipher](https://github.com/atimics/melody-cipher). Its four July 30, 2025 commits are attributed to `lilyofashwood`. This is evidence of preserved historical source; it does not establish why the original URL is unavailable or who currently owns a writable successor.

Recovered snapshot: [`dbeca271847f1cff7e9e97d946d8cd6c0871145d`](https://github.com/atimics/melody-cipher/commit/dbeca271847f1cff7e9e97d946d8cd6c0871145d).

| Historical file | Observed behavior |
| --- | --- |
| [melody_cipher.py](https://github.com/atimics/melody-cipher/blob/dbeca271847f1cff7e9e97d946d8cd6c0871145d/melody_cipher.py) | Six palettes: chromatic Duochroma plus five eight-note palettes; outputs note tokens. |
| [melody_cipher_cli.py](https://github.com/atimics/melody-cipher/blob/dbeca271847f1cff7e9e97d946d8cd6c0871145d/melody_cipher_cli.py) | Adds note-token decoding. Base-8 letters use A=0 through Z=25, split into two octal digits; case is lost. |
| [index.html](https://github.com/atimics/melody-cipher/blob/dbeca271847f1cff7e9e97d946d8cd6c0871145d/index.html) | Shows colored note names; this snapshot contains no audio playback engine or decode-button wiring. |
| [decoder.js](https://github.com/atimics/melody-cipher/blob/dbeca271847f1cff7e9e97d946d8cd6c0871145d/decoder.js) | Expects a decode button and script inclusion that the archived HTML does not supply. |

The source is genuinely pair-based. A prior conversational description using a single scale-degree modulo 7 is not the recovered implementation and should not be used as its compatibility specification.

Concrete old-code limitations: Duochroma wraps the high digit, which reduces code points modulo 144 in Python; for example, `é` round-trips as `Y`. JavaScript handles UTF-16 code units, so astral characters diverge further. Python base-8 encoding can throw on `ß` because uppercasing produces more than one character. The separate JavaScript fallback for punctuation can index an undefined fourth octal digit. The Python CLI can also add blank lines when encoding newlines. None of those behaviors is necessary for a sound-based decoder.

The `legacy` command preserves all six original note palettes and valid mappings, while explicitly rejecting input that cannot be represented reversibly. It preserves spaces and newlines without the old CLI's extra blank lines:

```sh
python melody_bloom.py legacy --cipher bebop_mixolydian --text "HELLO LILY"
python melody_bloom.py legacy --cipher bebop_mixolydian --decode --text "E E"
```

The five historical eight-note palettes retain their original labels and note arrays. Their names should not be treated as a verified music-theory taxonomy. V2 is a new, explicitly versioned format; old note sequences do not silently become v2 audio packets.

## Audio-decoder boundary

The prototype identifies the prominent melody register from the opening eight-note signature, estimates pitches with a short-time spectrum, splits repeated pitches at their attacks, and tries a bounded set of segmentations. It infers the palette, transposition and small tuning offset, reads the length, then checks CRC32 and strict UTF-8. It reports success only after the complete frame validates.

It works on both supplied full mixes and their 128 kbps MP3 copies, without a score or known plaintext. It also passed the synthetic conditions listed in `TEST_REPORT.md`. These are controlled signal tests, not microphone recordings.

Real phone recordings, singing, dense accompaniment, long room reverberation, overlapping lead notes, unrelated opening music, MIDI rendered with arbitrary instruments, and samples missing the opening signature remain unvalidated. Existing v1 audio is not decoded by the v2 audio command. For v1, note-token decoding is available; a recording would first need trustworthy transcription and known palette/boundaries, and has no built-in CRC.

For a next-stage recorder, [librosa pYIN](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html) is a candidate for monophonic fundamental-frequency tracking. [Spotify Basic Pitch](https://github.com/spotify/basic-pitch) is a candidate for polyphonic note transcription; its maintainers say it works best with one instrument at a time. Neither has been integrated or benchmarked in this package. Neither alone turns arbitrary audio into a reliably decoded cipher.

This is an artistic encoding, not encryption or authentication. CRC32 detects accidental corruption; it does not correct errors or prove who sent the message.

## Next pass

See `ASTRA_ULTRA_FINAL_PASS.md` for a concrete VS Code continuation. The most valuable next evidence is a small set of real speaker-to-phone recordings, followed by an audition of several renderings of the same message. The recovered archive is read-only, and no remote repository or live site was changed in this work.
