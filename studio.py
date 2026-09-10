#!/usr/bin/env python3
"""Local-only Melody studio. Run python studio.py, then open the printed URL."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import secrets
import tempfile
from urllib.parse import urlsplit
from scipy.io import wavfile
from audio_decode import decode_samples
import melody_bloom as mb

ROOT = Path(__file__).resolve().parent
MAX_UPLOAD = 50 * 1024 * 1024


def handler_for(directory, token, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Never log source text, uploaded filenames or query tokens.

        def reply(self, status, data, kind='application/json'):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.headers.get('Host') != f'127.0.0.1:{port}':
                return self.reply(403, {'error': 'Use the printed loopback URL.'})
            path = urlsplit(self.path).path
            fixed = {'/': ('studio.html', 'text/html; charset=utf-8'),
                     '/studio.js': ('studio.js', 'text/javascript; charset=utf-8'),
                     '/studio.css': ('studio.css', 'text/css; charset=utf-8')}
            if path == '/session':
                return self.reply(200, {'token': token})
            if path in fixed:
                file, kind = fixed[path]
                return self.reply(200, (ROOT / file).read_bytes(), kind)
            if path.startswith('/exports/'):
                name = path.removeprefix('/exports/')
                if '/' in name or '\\' in name or not name.endswith(('.wav', '.mid')):
                    return self.reply(404, {'error': 'Not found.'})
                file = Path(directory) / name
                if file.is_file():
                    return self.reply(200, file.read_bytes(), 'audio/wav' if name.endswith('.wav') else 'audio/midi')
            self.reply(404, {'error': 'Not found.'})

        def do_POST(self):
            expected = f'http://127.0.0.1:{port}'
            if (self.headers.get('Host') != f'127.0.0.1:{port}' or
                self.headers.get('Origin') not in (None, expected) or
                self.headers.get('X-Studio-Token') != token):
                return self.reply(403, {'error': 'This action requires your local studio session.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_UPLOAD:
                    raise ValueError('Input must be 1 byte to 50 MiB.')
                raw = self.rfile.read(length)
                if self.path == '/encode':
                    data = json.loads(raw)
                    text = data['text']
                    if not isinstance(text, str) or len(text.encode('utf-8')) > 512:
                        raise ValueError('The interactive studio accepts up to 512 UTF-8 bytes.')
                    score = mb.compose(text, mode=data.get('mode', 'nocturne'),
                                       bpm=float(data.get('bpm', 92)), phrasing=data.get('phrasing', 'bloom'))
                    samples = mb.render(score)
                    receipt = decode_samples(samples)
                    if receipt['text'] != text:
                        raise ValueError('Fresh audio did not recover the exact source; export rejected.')
                    name = secrets.token_hex(12)
                    mb.save_wav(Path(directory) / (name + '.wav'), samples)
                    mb.save_midi(Path(directory) / (name + '.mid'), score)
                    return self.reply(200, {'wav': '/exports/' + name + '.wav',
                                            'midi': '/exports/' + name + '.mid',
                                            'receipt': {k: v for k, v in receipt.items() if k != 'events'}})
                if self.path == '/decode':
                    sr, values = wavfile.read(io.BytesIO(raw))
                    return self.reply(200, decode_samples(values, sr))
                return self.reply(404, {'error': 'Not found.'})
            except (ValueError, KeyError, TypeError, OverflowError, OSError) as exc:
                return self.reply(400, {'error': str(exc), 'status': 'rejected'})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port from 1024 to 65535.')
    with tempfile.TemporaryDirectory(prefix='melody-studio-') as directory:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(directory, secrets.token_urlsafe(32), args.port))
        print(f'Melody studio: http://127.0.0.1:{args.port} — Ctrl+C stops; temporary exports then disappear.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
