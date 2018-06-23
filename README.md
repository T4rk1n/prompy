# Prompy

Promises for python.

#### Installation

```bash
cd /path/to/install
git clone https://github.com/T4rk1n/prompy.git
pip install .
```

#### Usage

Create a promise

```python
from prompy.promise import Promise

def promise_starter(resolve, reject):
    resolve('Hello')

promise = Promise(promise_starter)
promise.then(lambda result: print(result))

# Base promises run synchronously.
promise.exec()  # prints hello
```

#### Promise types

* AwaitablePromise - asyncio Promises you can await.
* TPromise - Promise that put itself in threaded queue pool.
* ProcessPromise - Promise to add to a process queue (manual insertion).

#### Url calls

Non-blocking promise wrappers for urllib requests.

Example:

```python
from prompy.threadio.tpromise import TPromise
from prompy.networkio.urlcall import url_call

git = url_call('http://github.com', prom_type=TPromise)


@git.then
def gud(rep):
    print(rep.content)
```

#### Caller factory

Wraps a class methods starting with `call_` with a `url_call`.

Example using AwaitablePromise:

```python
import asyncio

from prompy.networkio.call_factory import CallRoute, Caller
from prompy.awaitable import AwaitablePromise


class Api(Caller):
    def call_users(self, user_id, **kwargs):
        # methods with url params must have the same number of args
        return CallRoute('/users/<user_id>')

    def call_create_post(self, **kwargs):
        return CallRoute('/posts', method='POST')


api = Api(base_url='https://jsonplaceholder.typicode.com', prom_type=AwaitablePromise)


async def call_api():
    home = await api.call_users(1)
    print(home.content)
    data = await api.call_create_post(data={'title': 'foo', 'body': 'bar', 'userId': 3})
    print(data.content)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(call_api())
```

*Note: Since it use urllib, the asyncio loop will still block while waiting for the response.*

#### Promise creators modules

* prompy.promio.fileio - Read, write, delete, compress, decompress and walk files.
* prompy.promio.jsonio - json encoding wrap.
* prompy.processio.proc - subprocess wrap.
