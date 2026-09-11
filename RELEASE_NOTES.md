# Melody Bloom 2.0.1 · September 10 2026

Recovered Git history retains all four July 30 2025 commits from `atimics/melody-cipher`. The September 5 v2 prototype source snapshot is preserved in the workspace archive; `CHECKSUMS.json`, `TEST_REPORT.md` and `validation.log` refer to that earlier prototype, not this new test run.

New changes: one validation/mono conversion/resampling path for file and direct sample inputs; direct antiphase stereo is no longer canceled; stereo resampling no longer mistakenly operates on the channel dimension. Invalid rate, non-finite samples and excessive layouts are rejected. A tested phrase-breathing option changes duration only, leaving the v2 pitch alphabet and framing intact. Baseline phrasing remains selectable.

The local listening room (`python studio.py`) adds UTF-8 text/file input, palette/tempo/phrasing selection, playback/stop, WAV/MIDI downloads, WAV upload, exact text recovery and detected-note inspection. Fresh compositions are verified from their rendered waveform before export. The server binds only to 127.0.0.1, checks Host/Origin and a per-process action token, and deletes temporary exports when stopped. Run it as a local application.

`python listening_comparison.py` renders matched-RMS same-text A/B pairs including combining marks and astral Unicode. All four WAVs recover their exact message from audio alone. The files are ready for listening; speaker-to-microphone recordings follow RECORDING_PROTOCOL.md.

The original token-only HTML is preserved byte-for-byte at `historical/index.html`; `index.html` dresses the six palettes in the garden's current presentation. Pages hosts the listening gallery, while `python studio.py` opens the local composing and decoding room.
