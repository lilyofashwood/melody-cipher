"""Protocol, legacy-compatibility and audio-boundary tests. Run: python -m unittest -v."""
import copy
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

import numpy as np
from scipy.io import wavfile
from scipy import signal

import melody_bloom as mb
from audio_decode import decode_samples, decode_wav, decode_audio


class ProtocolTests(unittest.TestCase):
    def test_exact_unicode_and_whitespace(self):
        for message in ('', 'Hello, lily!\n\n', '  a\tB\r\n', '𝔩̸𝔦̲𝔩̷𝔶 👾', 'é e\u0301 𓆙', '\x00'):
            self.assertEqual(mb.unpack(mb.pack(message)), message)

    def test_byte_symbol_codec_all_values(self):
        raw = bytes(range(256))
        self.assertEqual(mb.bytes_from_symbols(mb.symbols_from_bytes(raw)), raw)

    def test_random_unicode_roundtrip(self):
        rng = random.Random(73)
        alphabet = 'aAZ19 \n\t!?éßΩ猫🪷𝔩\u0301\u0338\x00'
        for _ in range(100):
            message = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(100)))
            self.assertEqual(mb.unpack(mb.pack(message)), message)

    def test_corruption_and_truncation_rejected(self):
        frame = bytearray(mb.pack('keep every letter'))
        frame[9] ^= 1
        with self.assertRaises(mb.DecodeError):
            mb.unpack(bytes(frame))
        with self.assertRaises(mb.DecodeError):
            mb.unpack(mb.pack('keep every letter')[:-1])

    def test_frame_limits(self):
        self.assertEqual(mb.unpack(mb.pack('x'*65535)), 'x'*65535)
        with self.assertRaises(ValueError):
            mb.pack('x'*65536)
        with self.assertRaises(ValueError):
            mb.compose('x', bpm=float('nan'))

    def test_modes_transpositions_and_octave_errors(self):
        message = 'lily\n𝔩̸'
        for mode in mb.MODES:
            score = mb.compose(message, mode)
            pitches = [n['midi'] for n in score['notes'] if n['voice']=='lead']
            for shift in range(12):
                altered = [p+shift+(12 if i%3==0 else -12) for i,p in enumerate(pitches)]
                self.assertEqual(mb.decode_pitches(altered)['text'], message)

    def test_note_loss_and_substitution_rejected(self):
        score = mb.compose('a small message')
        notes = [n['midi'] for n in score['notes'] if n['voice']=='lead']
        with self.assertRaises(mb.DecodeError):
            mb.decode_pitches(notes[:41]+notes[42:])
        notes[45] += 1
        with self.assertRaises(mb.DecodeError):
            mb.decode_pitches(notes)

    def test_legacy_all_six_match_recovered_encoder(self):
        spec = importlib.util.spec_from_file_location('original', Path(__file__).parent/'historical'/'melody_cipher_cli.py')
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        for cipher, palette in mb.LEGACY_SCALES.items():
            message = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ xyz'
            if cipher == 'duochroma':
                expected = original.encode_base12(message, palette)
                recovered = message
            else:
                expected = original.encode_base8(message, palette)
                recovered = message.upper()
            actual = mb.legacy_encode(message, cipher)
            self.assertEqual(actual, expected)
            self.assertEqual(mb.legacy_decode(actual, cipher), recovered)

    def test_legacy_rejects_known_unicode_loss(self):
        for message in ('é', '👾', '𝔩̸'):
            with self.assertRaises(ValueError):
                mb.legacy_encode(message, 'duochroma')
        with self.assertRaises(ValueError):
            mb.legacy_encode('ß', 'bebop_mixolydian')
        message = ' A\n\nB '
        self.assertEqual(mb.legacy_decode(mb.legacy_encode(message, 'bebop_mixolydian'), 'bebop_mixolydian'), message)


class AudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.message = '𝔩̸\n👾'
        cls.score = mb.compose(cls.message)
        cls.samples = mb.render(cls.score)

    def test_full_mix_unicode_audio_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'anonymous.wav'
            mb.save_wav(path, self.samples)
            result = decode_wav(path)
        self.assertEqual(result['text'], self.message)
        self.assertEqual(result['checksum'], 'valid')

    def test_luminous_audio(self):
        samples = mb.render(mb.compose('lily', 'luminous', bpm=104))
        self.assertEqual(decode_samples(samples)['text'], 'lily')

    def test_transposed_full_mix(self):
        for shift in (-5, 7):
            samples = mb.render(mb.compose('key', transpose=shift))
            result = decode_samples(samples)
            self.assertEqual(result['text'], 'key')
            self.assertEqual(result['tonic_pitch_class'], (2+shift)%12)

    @unittest.skipUnless(shutil.which('ffmpeg'), 'Optional FFmpeg is not installed.')
    def test_mp3_audio_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            wav, mp3 = Path(directory)/'input.wav', Path(directory)/'anonymous.mp3'
            mb.save_wav(wav, self.samples)
            subprocess.run([shutil.which('ffmpeg'), '-nostdin', '-v', 'error', '-i',
                            str(wav), '-codec:a', 'libmp3lame', '-b:a', '128k', str(mp3)],
                           check=True, capture_output=True, timeout=30)
            self.assertEqual(decode_audio(mp3)['text'], self.message)

    def test_noise_gain_and_leading_silence(self):
        rng = np.random.default_rng(4)
        samples = self.samples.mean(axis=1)
        rms = np.sqrt(np.mean(samples**2))
        noisy = (samples + rng.normal(0, rms/10, len(samples))) * .15  # 20 dB SNR
        noisy = np.r_[np.zeros(9923), noisy, np.zeros(5500)]
        self.assertEqual(decode_samples(noisy)['text'], self.message)

    def test_four_percent_speed_change(self):
        sped = signal.resample_poly(self.samples, 25, 26, axis=0)
        self.assertEqual(decode_samples(sped)['text'], self.message)

    def test_48khz_wav_and_antiphase_stereo(self):
        values = signal.resample_poly(self.samples.mean(axis=1), 320, 147)
        values = np.stack((values, -values), axis=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'recording.wav'
            mb.save_wav(path, values, 48000)
            self.assertEqual(decode_wav(path)['text'], self.message)

    def test_cropped_clip_and_unrelated_audio_rejected(self):
        with self.assertRaises(mb.DecodeError):
            decode_samples(self.samples[:len(self.samples)//2])
        with self.assertRaises(mb.DecodeError):
            decode_samples(.3*np.sin(2*np.pi*440*np.arange(22050*4)/22050))

    def test_silence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'silence.wav'
            wavfile.write(str(path), 22050, np.zeros(22050, dtype=np.int16))
            with self.assertRaises(mb.DecodeError):
                decode_wav(path)


if __name__ == '__main__':
    unittest.main()
