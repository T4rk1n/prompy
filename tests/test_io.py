import unittest
import os

from prompy.promio import fileio, jsonio
from prompy.threadio.tpromise import TPromise
from tests.test_promise import threaded_test, _catch_and_raise


class TestIO(unittest.TestCase):
    @threaded_test
    def test_read(self):
        p = fileio.read_file('testfile', prom_type=TPromise)
        p.then(lambda x: self.assertEqual(x, 'hello')).catch(_catch_and_raise)

    @threaded_test
    def test_json(self):
        j = jsonio.dumps({'test': 'test'}, prom_type=TPromise).catch(_catch_and_raise)
        j.then(lambda x: jsonio.loads(x, prom_type=TPromise).then(print).catch(_catch_and_raise))

    @threaded_test
    def test_walk(self):
        w = fileio.walk('..',
                        filter_directories='(threadio|\.git|venv|.idea)',
                        filter_filename='(__init__\.py|\.pyc)',
                        prom_type=TPromise)
        w.then(lambda x: print(x.absolute()))

    @threaded_test
    def test_write_read_delete(self):
        filename = 'test123'
        content = 'hello world'

        def _delete_then(_):
            self.assertFalse(os.path.exists(filename))

        def _read_then(data):
            self.assertEqual(data, content)
            fileio.delete_file(filename, prom_type=TPromise).then(_delete_then).catch(_catch_and_raise)

        def _write_then(_):
            fileio.read_file(filename, prom_type=TPromise).then(_read_then).catch(_catch_and_raise)

        p = fileio.write_file(filename, content, prom_type=TPromise)
        p.then(_write_then).catch(_catch_and_raise)
