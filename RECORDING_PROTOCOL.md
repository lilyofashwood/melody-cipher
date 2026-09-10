# Speaker to microphone evidence plan

No real microphone recordings were supplied or made in this pass. Synthetic degradation tests are not substitutes for them.

Use a consenting listener and the same short message for each take. Keep the intact opening signature. Record the speaker playback as WAV, with automatic processing documented where known. Preserve the unedited recording and device/app settings. Do not put private messages in shared fixtures.

Collect: direct digital reference; quiet room at 0.5 m and 2 m; room with longer reverberation; ordinary background sound; a deliberately cropped negative control; a lead stem and a dense accompaniment comparison. Record actual distance, playback level, sample rate, device model and processing settings rather than guessing them.

Run `python audio_decode.py anonymous.wav --events observed.json` using only the recording. Compare the recovered UTF-8 bytes against the separately held source after decoding. Report complete/failed/ambiguous, CRC, exact byte equality and detected onsets. Never infer missing words or use a language model to fill them.

Audition the matched-RMS baseline/Bloom pairs in `examples/comparison/`. Score phrasing, repetition, timbre, fatigue and preference blind to labels where practical. Integrated RMS matching is reproducible but is not a perceptual LUFS guarantee. Do not turn an interval-smoothness metric into a claim of musical beauty.
