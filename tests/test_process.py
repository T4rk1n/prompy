import unittest
import pickle
import functools

from prompy.promise import Promise
from prompy.processio.process_promise import PromiseProcessPool, ProcessPromise


class TestProcess(unittest.TestCase):
    def test_process_pool(self):
        pool = PromiseProcessPool(pool_size=2, populate=True)

        done = 0

        def task_one(resolve, _):
            resolve(1)
            global done
            done += 1
            print(done)

        def task_two(resolve, _):
            resolve(2)
            global done
            done += 1
            print(done)

        # def _then(results):
        #     done = done + 1
        #
        # print(_then.__closure__)
        #
        namespace = {}
        namespace['done'] = 0

        p1 = ProcessPromise(task_one, namespace=namespace)
        p2 = ProcessPromise(task_two, namespace=namespace)

        pool.add_promises(p1, p2)

        while done != 2:
            pass
        # pool.stop()


if __name__ == '__main__':
    unittest.main()
