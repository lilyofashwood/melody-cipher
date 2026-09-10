import unittest
import numpy as np
from scipy import signal
import melody_bloom as mb
from audio_decode import decode_samples, prepare_samples


class RegressionTests(unittest.TestCase):
    def test_direct_stereo_resampling_and_antiphase(self):
        mono = mb.render(mb.compose('lily')).mean(axis=1)
        stereo = np.stack((mono, -mono), axis=1)
        stereo = signal.resample_poly(stereo, 320, 147, axis=0)
        self.assertEqual(decode_samples(stereo, 48000)['text'], 'lily')

    def test_audio_boundary_rejects_malformed(self):
        for values, rate in ((np.array([]), 22050), (np.zeros(100), 0),
                             (np.ones(100), float('nan')),
                             (np.array([np.nan]*5000), 22050),
                             (np.zeros((100, 9)), 22050)):
            with self.assertRaises(mb.DecodeError):
                prepare_samples(values, rate)

    def test_both_phrasings_audio_only(self):
        for mode in mb.MODES:
            for phrasing in ('baseline', 'bloom'):
                score = mb.compose('𝔩̸ 👾', mode, phrasing=phrasing)
                self.assertEqual(decode_samples(mb.render(score))['text'], '𝔩̸ 👾')

    def test_multiple_distinct_frames_rejected(self):
        pitches = []
        for text in ('first', 'second'):
            pitches.extend(n['midi'] for n in mb.compose(text)['notes'] if n['voice'] == 'lead')
        with self.assertRaises(mb.DecodeError):
            mb.decode_pitches(pitches)
