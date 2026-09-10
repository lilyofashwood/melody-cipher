# September 10 2026 verification

Fresh tests on Python 3.12, NumPy 2.3.5, SciPy 1.18.1, FFmpeg 7.1 (optional imageio-ffmpeg binary): `PATH=.venv/bin:$PATH .venv/bin/python -m unittest -v`. All 23 tests passed with zero skips, including fresh 128 kbps MP3 recovery and the local HTTP studio integration test (session protection, render, download, uploaded-waveform recovery).

Four newly rendered comparisons recover exact text from their WAV bytes alone: baseline and Bloom phrasing for `follow the melody` and `𝔩̸ 👾`. Every take was matched to −20 dBFS integrated RMS. See `examples/comparison/report.json`. This is not a perceptual loudness or human preference measurement.

Chrome for Testing 151 / Playwright: compose `lily`, verify freshly rendered audio, expose two working export links, no JavaScript page errors. Desktop and 390 px screenshots inspected; no horizontal page overflow. The first visual check exposed a missing treble-clef font glyph; the studio heading now uses the more widely supported ♫.

No live microphone recordings were available. No subjective audition, pYIN/Basic Pitch benchmark, arbitrary MIDI-instrument recording, long-reverb corpus or generic false-positive rate is claimed. Negative fixtures include silence, unrelated pure tone, crop, malformed frames and conflicting valid note streams. CRC is not authentication.

Source coverage: all Python/JS/HTML and prose under the recovered Melody Bloom source were read completely, including the four historical source files. Large machine-generated score/event sidecars and existing audio/MIDI binaries were identified and exercised as fixtures, but not every sidecar scalar has been semantically inspected and audio has not been human-auditioned. They are not counted as full human-style reading.
