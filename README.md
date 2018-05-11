# Prompy

Implementation of the javascript Promise interface in Python.

#### Installation

```bash
cd /path/to/install
git clone https://github.com/T4rk1n/prompy.git
pip install .
```

### Usage

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

#### 3 types of promises.

1. TPromise - Threaded Promise.
2. ProcessPromise - WIP.
3. AwaitablePromise - asyncio compatible, WIP.

All promise wrapper methods take an optional prom_type argument, default: Promise.

** Note: Synchronous code inside `AwaitablePromise` will block (ie: requests will block). **

#### UrlCall

Non-blocking promise wrappers for urllib requests.

Example using pooled_caller (threaded):

```python
from prompy.threadio.pooled_caller import PooledCaller

caller =  PooledCaller(pool_size=2) # two threads will be generated.

gh = caller.get('https://github.com')
gh.then(lambda rep: print(rep.content))
```

#### promio

Promise wrapped standard lib io.

##### fileio

Read, write and delete files.

```python
from prompy.threadio.tpromise import TPromise
from prompy.promio import fileio

filename = 'myfile'

f = fileio.write_file(filename, 'content', prom_type=TPromise)
f.then(lambda _: fileio.read_file(filename).then(lambda data: print(data)))
```
