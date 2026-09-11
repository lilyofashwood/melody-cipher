import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from studio import handler_for


class StudioTests(unittest.TestCase):
    def test_local_session_and_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(directory, 'test-token', 0))
            port = server.server_address[1]
            server.RequestHandlerClass = handler_for(directory, 'test-token', port)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f'http://127.0.0.1:{port}'
                with urlopen(url) as response:
                    self.assertIn(b'Melody Bloom', response.read())
                    self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
                for asset in ('presentation.js', 'presentation.css'):
                    with urlopen(url + '/' + asset) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn(b'garden', response.read().lower())
                for private_path in ('/test_studio.py', '/historical/decoder.js'):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(url + private_path)
                    self.assertEqual(error.exception.code, 404)
                for headers in ({'Content-Type':'application/json'},
                                {'X-Studio-Token':'test-token','Origin':'https://untrusted.example'}):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(url+'/encode', b'{"text":"lily"}', headers))
                    self.assertEqual(error.exception.code, 403)
                headers = {'Content-Type':'application/json', 'X-Studio-Token':'test-token'}
                with urlopen(Request(url+'/encode', b'{"text":"lily"}', headers), timeout=30) as response:
                    result = json.load(response)
                self.assertEqual(result['receipt']['text'], 'lily')
                with urlopen(url+result['wav']) as response:
                    wav = response.read()
                self.assertEqual(wav[:4], b'RIFF')
                with urlopen(Request(url+'/decode', wav, {'X-Studio-Token':'test-token'}), timeout=30) as response:
                    self.assertEqual(json.load(response)['text'], 'lily')
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
