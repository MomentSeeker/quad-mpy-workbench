import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def _read_body(handler):
    length_raw = handler.headers.get('content-length', '0')
    try:
        length = int(length_raw)
    except ValueError:
        length = 0
    if length <= 0:
        return b''
    return handler.rfile.read(length)


def _send_json(handler, status, payload):
    data = json.dumps(payload).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(data)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
    handler.end_headers()
    handler.wfile.write(data)


def _normalize_base_url(base_url):
    base_url = (base_url or '').strip()
    if not base_url:
        return ''
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in ('http', 'https'):
        return ''
    if not parsed.netloc:
        return ''
    return f'{parsed.scheme}://{parsed.netloc}'


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip('/') != '/api/control':
            _send_json(self, HTTPStatus.NOT_FOUND, {'status': '404', 'msg': 'not found'})
            return

        raw = _read_body(self)
        try:
            req = json.loads(raw.decode('utf-8') if raw else '{}')
        except Exception:
            _send_json(self, HTTPStatus.BAD_REQUEST, {'status': '400', 'msg': 'invalid json'})
            return

        command = req.get('command')
        base_url = req.get('baseUrl') or os.environ.get('ROBOT_BASE_URL')

        if not command or not isinstance(command, str):
            _send_json(self, HTTPStatus.BAD_REQUEST, {'status': '400', 'msg': 'missing command'})
            return

        base_url = _normalize_base_url(base_url)
        if not base_url:
            _send_json(self, HTTPStatus.BAD_REQUEST, {'status': '400', 'msg': 'missing baseUrl'})
            return

        target = f'{base_url}/control'
        body = json.dumps({'command': command}).encode('utf-8')
        r = urllib.request.Request(
            target,
            data=body,
            method='POST',
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(r, timeout=15) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            msg = ''
            try:
                msg = e.read().decode('utf-8', errors='ignore')
            except Exception:
                msg = str(e)
            _send_json(self, HTTPStatus.BAD_GATEWAY, {'status': '502', 'msg': msg or 'bad gateway'})
        except Exception as e:
            _send_json(self, HTTPStatus.BAD_GATEWAY, {'status': '502', 'msg': str(e)})


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args(argv)

    directory = os.path.abspath(os.path.dirname(__file__))
    handler = lambda *h_args, **h_kwargs: Handler(*h_args, directory=directory, **h_kwargs)

    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    print(f'Serving workbench on http://{args.host}:{args.port}/')
    print('Tip: open /?robot=http://192.168.x.x to prefill robot address')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main(sys.argv[1:])

