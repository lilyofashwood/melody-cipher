# September 10 2026 verification

Fresh tests on Python 3.12, NumPy 2.3.5, SciPy 1.18.1, FFmpeg 7.1 (optional imageio-ffmpeg binary): `PATH=.venv/bin:$PATH .venv/bin/python -m unittest -v`. All 23 tests passed with zero skips, including fresh 128 kbps MP3 recovery and the local HTTP studio integration test (session protection, render, download, uploaded-waveform recovery).

Four newly rendered comparisons recover exact text from their WAV bytes alone: baseline and Bloom phrasing for `follow the melody` and `𝔩̸ 👾`. Every take was matched to −20 dBFS integrated RMS. See `examples/comparison/report.json`. RMS is the matching measure; the exported pairs are available for listening.

Chrome for Testing 151 / Playwright: compose `lily`, verify freshly rendered audio, expose two working export links, no JavaScript page errors. Desktop and 390 px screenshots inspected; no horizontal page overflow. The first visual check exposed a missing treble-clef font glyph; the studio heading now uses the more widely supported ♫.

Recording coverage: synthesized performances and their digital transformations. Speaker-to-microphone recordings are the next collection step in RECORDING_PROTOCOL.md. Negative fixtures include silence, unrelated pure tone, crop, malformed frames and conflicting valid note streams. CRC checks corruption; sender authentication is separate.

Source coverage: all recovered Python, JavaScript, HTML and prose were read, including the four historical files. Machine-generated score/event sidecars and audio/MIDI binaries were exercised as fixtures. Original source hashes are recorded in PROVENANCE.json.
