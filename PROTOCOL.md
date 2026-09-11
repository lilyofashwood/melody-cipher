# Melody Bloom v2 · reproducible wire and music specification

Melody Bloom v2 · implemented September 5, 2026. The audio frame has its own wire format; all six legacy Duochroma/base-8 mappings remain separately available.

## Framing

Text is encoded as UTF-8 without case conversion, normalization, trimming or removal of combining marks. Unpaired surrogates are rejected. Frame layout:

| Bytes | Value |
| --- | --- |
| 0–2 | ASCII `M`, ASCII `B`, byte `0x02` |
| 3–4 | UTF-8 payload length, unsigned 16-bit big-endian |
| 5 onward | Exactly that many UTF-8 payload bytes |
| Final 4 | CRC32 from Python `zlib.crc32(header + payload)`, unsigned big-endian |

The payload may contain 0–65535 bytes. The frame is exactly `payload_length + 9` bytes. The audio renderer has a separate ten-minute bound. The CRC covers the magic, version, length and payload. A valid frame requires an exact length, valid CRC and strict UTF-8 decoding.

Each byte becomes four two-bit symbols, most significant first: shifts 6, 4, 2 and 0. Every note carrying a symbol is a distinct onset, including consecutive notes with identical pitch.

## Pitch alphabet

Intervals are semitones above the inferred tonic, modulo 12. All octaves are equivalent for data.

| Symbol | Bits | Nocturne intervals / in D | Luminous intervals / in D |
| --- | --- | --- | --- |
| 0 | 00 | 0 or 7 / D or A | 0 or 7 / D or A |
| 1 | 01 | 3 / F | 4 / F# |
| 2 | 10 | 5 / G | 2 / E |
| 3 | 11 | 10 / C | 9 / B |

Groups are disjoint in each mode. A composer's choice of D versus A for symbol 0 and any choice of octave cannot change the symbol. Octaves are ignored by the protocol decoder, though the current acoustic front end still needs a separated melody register.

The opening signature has eight intervals:

* Nocturne: `0, 7, 3, 5, 10, 7, 5, 0`.
* Luminous: `0, 7, 4, 2, 9, 7, 2, 0`.

The first signature note identifies tonic pitch class. Its third, fourth and fifth notes distinguish the two modes. The current renderer starts the signature one octave above the payload register floor. The acoustic front end relies on this convention when choosing its frequency band.

Immediately following the signature, the next 20 melody onsets contain the five-byte header. Length then determines exactly how many more melody onsets belong to the frame. Three coda notes follow and are ignored by data decoding. There are 44 framing/signature notes plus four notes per payload byte, and three non-data coda notes in the supplied renderer.

No duration, gap, amplitude, timbre, filename, MIDI metadata, accompaniment note or source-text sidecar carries payload bits. Whitespace is encoded as UTF-8 data, not inferred from musical rests. All data notes require distinct attacks, so fully tied repetitions are not a supported performance transformation.

## Composition

For each symbol the reference composer generates every allowed MIDI pitch from `tonic_midi` through `tonic_midi + 24`. The default tonic is D4, MIDI 62. A deterministic dynamic-programming pass minimizes a cost for successive pitch distance, leaps larger than a fifth, register distance, repeated exact pitch, and chord mismatch on selected strong positions. The composer can be replaced as long as its emitted pitches retain the symbol mapping and recognizable framing.

Groups of eight data notes occupy four beats. Four recurring patterns combine eighth notes and occasional dotted-eighth/sixteenth pairs. Velocity follows a 32-note arc plus seeded small variation. The message voice is centered; softer bass, pad and harp parts sit below its register. The re-articulation gap and restrained reverb support audio segmentation.

The four-symbol alphabet gives each symbol a disjoint pitch-class group and the composer an octave-wide canvas. Redundant encodings, additional motif choices or error-correcting blocks belong in a separately versioned format with explicit decoding rules.

## Decoding and failure

`decode_pitches` searches observed note sequences for a matching signature, infers tonic/mode, reads header and frame, validates CRC32 and decodes strict UTF-8. It rejects multiple distinct valid messages in one input. It does not need tempo or absolute octave.

`audio_decode.py` estimates pitch and note boundaries from audio, using spectral peaks, amplitude gates and repeated-note valleys. It tries at most twelve combinations of window/gate parameters. A successful checksum accepts the recovered frame. Pitch deviations and relative amplitudes in event reports are measured signal features. Sender authentication is a separate layer.

The decoder requires a full signature and valid frame. Substituted, inserted or deleted notes produce a rejected frame unless the intact message is recovered; detected events remain available for inspection. Independent blocks, periodic resynchronization and error correction are future format extensions.

Acoustic coverage is recorded in TEST_REPORT.md and VERIFICATION.md. The pitch-class layer accepts octave changes; the waveform tracker still needs the prominent melody register described above. Speaker-to-microphone recordings follow RECORDING_PROTOCOL.md.
