import tempfile
import unittest
import os
import itertools
import shutil

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
        dir_filters = ['threadio', '\\.git', 'venv', '\\.idea']
        file_filters = ['__init__\.py', '.*\.pyc', '.*idea.*', '.gitignore']

        w = fileio.walk('..',
                        filter_directories='(' + '|'.join(dir_filters) + ')',
                        filter_filename='(' + '|'.join(file_filters) + ')',
                        prom_type=TPromise)

        w.then(lambda x: self.assertTrue(all([y not in str(x) for y in itertools.chain(dir_filters, file_filters)])))

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

    @threaded_test
    def test_compression(self):
        work_dir = tempfile.mkdtemp('test_compress')
        filename = os.path.join(work_dir, 'test_compress')

        compressed = fileio.compress_directory('prompy', filename, prom_type=TPromise)
        compressed.catch(_catch_and_raise)

        @compressed.then
        def compress_then(result):
            name = filename + '.zip'
            self.assertTrue(os.path.exists(name))
            self.assertTrue(name == result)

            decompressed = fileio.decompress(name, os.path.join(work_dir, 'decompressed'), prom_type=TPromise)
            decompressed.catch(_catch_and_raise)

            @decompressed.then
            def _then(r):
                self.assertTrue(os.path.exists(os.path.join(r, 'prompy')))

            @decompressed.complete
            def _c(*args):
                shutil.rmtree(work_dir)
