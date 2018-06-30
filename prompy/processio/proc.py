"""
Wraps subprocess module.

:Example:

.. code-block:: python

    from prompy.processio.proc import command

    p = command('python application.py')
    p.then(print)
    p.exec()

"""
import itertools
import time
import asyncio
import shlex
import re

import subprocess
from typing import NamedTuple, Tuple, Callable

from prompy.awaitable import AwaitablePromise
from prompy.promio import encodio
from prompy.promise import Promise

_re_endline = re.compile('[\r\n]+')


def _default_command_mapper(out, err, encoding=None):
    enc = encoding
    if not enc:
        info = encodio.detect(out)
        if info.confidence > 0.75:
            enc = info.encoding
        else:
            enc = 'utf-8'

    return out.decode(enc) if isinstance(out, bytes) else out, \
           err.decode(enc) if isinstance(err, bytes) else err


def format_output(output: Tuple, indent=0):
    indentation = ' ' * indent
    o = itertools.chain(*[_re_endline.split(x) for x in output])
    return f'\n'.join([indentation + x for x in o])


class CommandOutput(NamedTuple):
    cmd: str
    out: Tuple
    err: Tuple
    started: float
    completed: float
    return_code: int


def command(cmd: str,
            timeout: float = 0,
            communicate_timeout: float = 0.02,
            sleep_time: float=0.02,
            output_mapper: Callable=_default_command_mapper,
            encoding: str='utf-8',
            posix: bool=True,
            proc_kwargs: dict=None,
            prom_type=Promise, **kwargs) -> Promise:
    """
    Start a process with subprocess.Popen, resolve when it stops.

    :param cmd: The command to execute as a string.
    :param timeout: The max amount of time the process will stay open.
    :param communicate_timeout: Timeout to `proc.communicate`
    :param sleep_time: arg to yield from asyncio.sleep
    :param output_mapper: method to receive the output of the process.
    :param encoding: Encoding of the output.
    :param posix: arg to `shlex.split`
    :param proc_kwargs: kwargs to subprocess.Popen
    :param prom_type: Type of promise to return
    :param kwargs: kwargs to `prom_type(**kwargs)`
    :return:
    """

    promise = None

    def starter(resolve, reject):
        pkw = proc_kwargs or {}
        line = shlex.split(cmd, posix=posix)
        future: asyncio.Future = getattr(promise, 'future', None)
        started = time.time()
        status = None
        results = []
        errs = []
        try:
            with subprocess.Popen(line, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, **pkw) as proc:
                while status is None:

                    try:
                        out, err = output_mapper(*proc.communicate(timeout=communicate_timeout),
                                                 encoding=encoding)
                        status = proc.poll()
                        if out:
                            results.append(out)
                        if err:
                            errs.append(err)
                    except subprocess.TimeoutExpired as err:
                        if 0 < timeout < time.time() - started:
                            proc.kill()
                            reject(err)
                    if future:
                        yield from asyncio.sleep(sleep_time)
        except Exception as e:
            reject(e)
        completed = time.time()
        resolve(CommandOutput(cmd, tuple(results), tuple(errs), started, completed, status))

    if prom_type == AwaitablePromise:
        starter = asyncio.coroutine(starter)

    promise = prom_type(starter, **kwargs)
    return promise

