import time
import functools
import unittest

from prompy.threadio.tpromise import TPromise, _prom_pool

from prompy.promtools import pall, piter

threads = []
_prom_pool.on_thread_stop(lambda e: threads.append(e))


def threaded_test(func):
    @functools.wraps(func)
    def _wrap(*args, **kwargs):
        global threads
        r = func(*args, **kwargs)
        while _prom_pool.is_running():
            time.sleep(0.03)
        try:
            for t in threads:
                t._thread.join()
                if t.error:
                    raise t.error
        finally:
            threads = []
        return r
    return _wrap


def _catch_and_raise(err):
    raise err


class TPromiseTest(unittest.TestCase):

    @threaded_test
    def test_tpromise(self):
        t = TPromise.wrap(lambda x: x + 3)
        print('hello')
        e = t(4).then(lambda x: self.assertEqual(x, 7, "4+3 = 7")).catch(_catch_and_raise)
        self.assertTrue(isinstance(e, TPromise))
        print('world')

    @threaded_test
    def test_piter(self):
        p = piter(lambda x: x + 2, [2, 4, 6], prom_type=TPromise)
        p.then(lambda x: self.assertTrue(x % 2 == 0)).catch(_catch_and_raise)


if __name__ == '__main__':
    unittest.main()
