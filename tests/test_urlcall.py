import json
import socketserver
import unittest
import threading
from http.server import BaseHTTPRequestHandler

from prompy.networkio.call_factory import Caller, CallRoute
from prompy.networkio.urlcall import url_call, json_call
from prompy.promise import Promise
from prompy.threadio.tpromise import TPromise
from tests.test_promise import threaded_test, _catch_and_raise


class MockServer(BaseHTTPRequestHandler):
    def set_headers(self, response_code=200, content_type='text/html', headers={}):
        self.send_response(response_code)
        self.send_header('Content-Type', content_type)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        self.set_headers()
        if 'testurlparams' in self.path:
            self.wfile.write(self.path.encode('utf-8'))
        else:
            self.wfile.write('hello'.encode('utf-8'))

    def do_HEAD(self):
        self.set_headers()

    def do_POST(self):
        data = self._get_data().decode('utf-8')

        if self.path == '/testjson':
            content_type = self.get_content_type()
            j = json.loads(data)
            msg = j.get('msg')
            self.set_headers(content_type='application/json')
            self.wfile.write(json.dumps({'said': msg}).encode('utf-8'))
        else:
            self.set_headers()
            self.wfile.write(f'You said {data}'.encode('utf-8'))

    def _get_data(self):
        content_len = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_len)
        return post_data

    def get_content_type(self) -> str:
        return self.headers.get('Content-Type')


def mock_server():
    port = 8000
    with socketserver.TCPServer(("", port), MockServer) as httpd:
        httpd.serve_forever()


t = threading.Thread(target=mock_server)
t.daemon = True
t.start()


class TestUrlCall(unittest.TestCase):

    @threaded_test
    def test_urlcall(self):
        def get_then(rep):
            self.assertEqual(rep.content.decode('utf-8'), 'hello')

        get_call = url_call("http://localhost:8000/", prom_type=TPromise)
        get_call.then(get_then).catch(_catch_and_raise)

        def post_then(rep):
            self.assertEqual(rep.content.decode('utf-8'), 'You said hello')

        post_call = url_call('http://localhost:8000/help',
                             method='POST', data='hello'.encode('utf-8'), prom_type=TPromise)
        post_call.then(post_then).catch(_catch_and_raise)

        def json_then(rep):
            print(rep)
            said = rep.content.get('said')
            self.assertEqual(said, 'hello')

        j = json_call('http://localhost:8000/testjson', method='POST', payload={'msg': 'hello'}, prom_type=TPromise)
        j.then(json_then).catch(_catch_and_raise)

    @threaded_test
    def test_call_factory(self):

        class TestCaller(Caller):

            def call_home(self, **kwargs):
                return CallRoute('/')

            def call_post_json(self, **kwargs):
                return CallRoute('/testjson', method='POST')

            def call_url_params(self, p):
                return CallRoute('/testurlparams/<p>')

        caller = TestCaller(base_url='http://localhost:8000', prom_type=TPromise)
        p: Promise = caller.call_home()


        @p.then
        def _p_then(rep):
            self.assertEqual(rep.content, 'hello')

        p.catch(_catch_and_raise)

        p2: Promise = caller.call_post_json(data={'msg': 'you got a call'})

        @p2.then
        def _p2_then(rep):
            self.assertTrue(isinstance(rep.content, dict))
            self.assertEqual(rep.content.get('said'), 'you got a call')

        param = 'option'
        p3: Promise = caller.call_url_params(param)

        @p3.then
        def _p3_then(rep):
            self.assertTrue(param in rep.content)


