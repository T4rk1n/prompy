import unittest
import asyncio
import functools

from prompy.awaitable import AsyncPromiseRunner, AwaitablePromise
from prompy.networkio.urlcall import url_call, UrlCallResponse


def async_test(func):

    @functools.wraps(func)
    def _wrap(self: AwaitableTestCase, *args, **kwargs):
        runner = AsyncPromiseRunner()
        errors = []

        def exc_handler(loop, context):
            loop.stop()
            exception = context.get('exception')
            errors.append(exception)

        runner.loop.set_exception_handler(exc_handler)
        func(self, *args, **kwargs)
        runner.start()

        self.assertEqual(self.expected_calls, self.calls,
                         f'Expected {self.expected_calls} async calls but got {self.calls}')

        for error in errors:
            raise error

    return _wrap


class AwaitableTestCase(unittest.TestCase):
    def setUp(self):
        self.calls = 0
        self.expected_calls = 0


class TestAwaitable(AwaitableTestCase):

    @async_test
    def test_awaitable_then(self):
        self.expected_calls = 3

        def starter(resolve, _):
            self.calls += 1
            resolve(2)

        p = AwaitablePromise(starter)

        @p.then
        async def _then(result):
            self.calls += 1

            def _starter(r, _):
                self.calls += 1
                r(result + 2)

            res = await AwaitablePromise(_starter)
            self.assertEqual(4, res)
            asyncio.get_event_loop().stop()

    @async_test
    def test_awaitable_catch(self):
        self.expected_calls = 2

        def starter(_, reject):
            self.calls += 1
            reject(Exception('catch me'))

        p = AwaitablePromise(starter)

        @p.catch
        def _catch(error):
            self.calls += 1
            self.assertTrue('catch me' in str(error))
            asyncio.get_event_loop().stop()

    @async_test
    def test_awaitable_call(self):
        self.expected_calls = 3

        async def _call_starter(resolve, _):
            self.calls += 1
            # noinspection PyUnresolvedReferences
            google = await url_call('http://www.google.com', prom_type=AwaitablePromise)
            self.calls += 1
            resolve(google)

        p = AwaitablePromise(_call_starter)

        @p.then
        def _then(result):
            self.calls += 1
            self.assertTrue(isinstance(result, UrlCallResponse))
            asyncio.get_event_loop().stop()


if __name__ == '__main__':
    unittest.main()
