import unittest

from prompy.promio.fileio import read_file
from prompy.threaded.tpromise import TPromise
from tests.test_promise import threaded_test, _catch_and_raise


class TestIO(unittest.TestCase):
    @threaded_test
    def test_read(self):
        p = read_file('testfile', prom_type=TPromise)
        p.then(lambda x: self.assertEqual(x, 'hello')).catch(_catch_and_raise)
