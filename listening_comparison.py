"""Reproduce same-text baseline/Bloom WAV comparisons and audio-only receipts."""
import json
from pathlib import Path
import numpy as np
import melody_bloom as mb
from audio_decode import decode_wav

output = Path(__file__).resolve().parent / 'examples' / 'comparison'
output.mkdir(exist_ok=True)
report = {'source': 'synthetic waveforms only', 'microphone_tested': False,
          'subjective_audition': 'Requires human listening; no listening judgment is claimed.', 'cases': []}
for label, text in (('melody', 'follow the melody'), ('glyphs', '𝔩̸ 👾')):
    takes = []
    for phrasing in ('baseline', 'bloom'):
        score = mb.compose(text, phrasing=phrasing)
        samples = mb.render(score)
        rms = float(np.sqrt(np.mean(samples**2)))
        takes.append((phrasing, score, samples, rms))
    # Identical integrated RMS, with a shared target low enough to avoid clipping.
    target = min(.1, *(rms * .95 / float(np.max(np.abs(samples))) for _, _, samples, rms in takes))
    for phrasing, score, samples, rms in takes:
        path = output / f'{label}_{phrasing}.wav'
        normalized = samples * (target / rms)
        mb.save_wav(path, normalized)
        result = decode_wav(path)  # only WAV bytes go to the decoder
        assert result['text'] == text
        report['cases'].append({'file': path.name, 'text': text, 'phrasing': phrasing,
                                'seconds': round(len(samples) / 22050, 3),
                                'rms_dbfs': round(20 * np.log10(target), 3),
                                'peak': round(float(np.max(np.abs(normalized))), 5),
                                'checksum': result['checksum'], 'audio_only': result['audio_only']})
(output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
