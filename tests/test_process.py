import unittest
import time

from prompy.processio.process_promise import PromiseProcessPool, ProcessPromise
from prompy.errors import UnhandledPromiseError


class TestProcess(unittest.TestCase):

    def test_process_pool(self):
        pool = PromiseProcessPool(pool_size=2)

        def simple_task(resolve, _):
            import time
            resolve(time.time())

        def task_unhandled(resolve, _):
            raise Exception('Should be raised & unhandled')

        def task_handled(resolve, _):
            raise Exception('Should be handled')

        def _then(results):
            import time
            t = time.time()
            assert t >= results, f'{t} >= {results} ?'

        p1 = ProcessPromise(simple_task).then(_then)
        unhandled = ProcessPromise(task_unhandled)
        handled = ProcessPromise(task_handled).catch(lambda x: print(x))

        pool.add_promises(p1, unhandled, handled)

        while pool.num_tasks > 0:
            time.sleep(0.2)
        pool.stop()  # comment out to debug.

        for error in pool.get_errors():
            # test that the exception was thrown back.
            if str(unhandled.id) in str(error):
                self.assertTrue(isinstance(error, UnhandledPromiseError))
            else:
                raise error


if __name__ == '__main__':
    unittest.main()
