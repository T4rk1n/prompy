"""
Async calls
"""
import asyncio
import time
import socket

from typing import Callable, Any, Optional
from http import client

from prompy.awaitable import AwaitablePromise
from prompy.networkio import http_constants as _http
from prompy.networkio import url_tools
from prompy import errors


def call(url: str,
         data: bytes=None,
         method: str=_http.GET,
         headers: dict=None,
         connection_timeout: float=2,
         response_timeout: float=0.01,
         timeout: float=5,
         sleep_time: float=0.01,
         content_mapper: Callable[[str, bytes, Optional[str]], Any]=url_tools.default_content_mapper,
         **kwargs) -> AwaitablePromise:
    """
    Asyncio non-blocking url call.

    :param url: The address to call.
    :param data: Data to send
    :param method: Http method
    :param headers: dict containing the headers of the request.
    :param connection_timeout: Duration of the connection attempt, blocking.
    :param response_timeout: Timeout after connection to try for response.
    :param timeout: timeout after which the call will be rejected.
    :param sleep_time: arg to `yield from asyncio.sleep(sleep_time)`
    :param content_mapper: Map the response data.
    :param kwargs: promise kwargs
    :return:
    """
    promise: AwaitablePromise

    @asyncio.coroutine
    def starter(resolve, reject):
        yield from asyncio.sleep(response_timeout)
        u = url_tools.Url(url)
        started = time.time()
        completed = False

        if u.protocol == 'http':
            connection = client.HTTPConnection(u.host,
                                               port=u.port,
                                               timeout=connection_timeout)
        elif u.protocol == 'https':
            connection = client.HTTPSConnection(u.host,
                                                port=u.port,
                                                timeout=connection_timeout)
        else:
            return reject(errors.UrlCallError(
                f'Invalid protocol: {u.protocol}'))
        try:
            path = f'{u.path}?{u.params}' if u.params else u.path
            connection.request(method, path,
                               body=data, headers=headers or {})
        except ConnectionRefusedError as e:
            reject(e)
        except socket.timeout as e:
            reject(e)

        connection.sock.settimeout(response_timeout)
        try:

            while not completed:
                try:
                    response = connection.getresponse()
                    rep_headers = {k: v for k, v in response.getheaders()}
                    content_type = rep_headers.get(_http.CONTENT_TYPE)
                    code = response.getcode()
                    encoding = url_tools.detect_content_charset(content_type)
                    results = response.read()
                    content = content_mapper(content_type, results, encoding)
                    rep = url_tools.UrlCallResponse(url, content_type, content,
                                                    code, rep_headers, '',
                                                    '', encoding)

                    response.close()
                    completed = True
                    resolve(rep)

                except socket.timeout:
                    if 0 < timeout < time.time() - started:
                        raise
                    yield from asyncio.sleep(sleep_time, loop=promise.loop)
        finally:
            connection.close()
            return

    promise = AwaitablePromise(starter, **kwargs)
    return promise

