"""
call_factory

Meta web api wrapper.

Usage:

.. code-block:: python

    from prompy.networkio.call_factory import CallRoute, Caller
    from prompy.threadio.promise_queue import PromiseQueuePool


    class Api(Caller):
        def call_home(self, **kwargs):
            return CallRoute('/')

        def call_data(self, **kwargs):
            return CallRoute('/data', method='POST')


    pool = PromiseQueuePool(start=True)
    api = Api(base_url='http://localhost:5000', promise_container=pool)
    api.call_data(data={'num': 6}).then(print).catch(print)

"""
import json
import re
import functools
from typing import Any, Optional, Union, Dict, List

from prompy.container import BasePromiseContainer
from prompy.networkio import urlcall, http_constants
from prompy.networkio.urlcall import encode_url_params
from prompy.promise import Promise


_route_params_pattern = re.compile('<(\w*)>')


class CallRoute:
    """Route object used by :class:`Caller`"""

    def __init__(self,
                 route: str,
                 method: str=http_constants.HTTP_GET,
                 content_type: str=http_constants.CONTENT_TYPE_JSON):
        """
        Route data object with format methods.

        :param route: url to call, with optional templating.
        :param method: http method
        :param content_type:
        """
        self.route = route
        self.method = method
        self.route_params = _route_params_pattern.findall(self.route)
        self.route_params_length = len(self.route_params)
        self.content_type = content_type

    def format_route_params(self, *args):
        """
        Format the route params.

        :Example:

        .. code-block:: python

            route = CallRoute('/user/<user>')
            r = route.format_route_params(user='bob')

        :param kwargs:
        :return:
        """
        if not self.route_params:
            return self.route
        route = self.route
        if len(args) != self.route_params_length:
            s = ','.join(self.route_params[len(args):])
            raise Exception(f'Missing url parameter <{s}>')
        for i in range(self.route_params_length):
            p = self.route_params[i]
            value = args[i]
            route = route.replace(f'<{p}>', str(value))
        return route

    def format_data(self, data: Optional[Union[Dict, List, str]]):
        """
        Serialize the data according to content-type.

        :param data:
        :return:
        """
        if not data:
            return
        if http_constants.CONTENT_TYPE_JSON in self.content_type:
            return json.dumps(data).encode('utf-8')
        return data.encode('utf-8')


class _MetaCall(type):
    def __new__(mcs, name, bases, attributes):

        new_attrs = dict(**attributes)

        def _route_wrap(func):
            @functools.wraps(func)
            def _inner(self: Caller, *args, **kwargs):
                route: CallRoute = func(self, *args, **kwargs)
                promise = self.call(route, args, **kwargs)
                return promise
            return _inner

        for route_name in filter(lambda k: k.startswith('call_'), attributes.keys()):
            new_attrs[route_name] = _route_wrap(attributes[route_name])

        return type.__new__(mcs, name, bases, new_attrs)


class Caller(metaclass=_MetaCall):
    """
    Wraps all method starting with `call_` with a call.

    **route methods must:**

    - return a CallRoute object.
    - kwargs must be there if you want Caller.call and route params kwargs.
    """

    def __init__(self, base_url: str='',
                 promise_container: BasePromiseContainer=None,
                 prom_type=Promise,
                 prom_args: dict=None):
        """
        :param base_url:
        :param promise_container:
        :param prom_type:
        :param prom_args:
        """
        self.base_url = base_url
        self.promise_container = promise_container
        self.prom_type = prom_type
        self.prom_args = prom_args or {}

    def call(self,
             route: CallRoute,
             route_params: list=None,
             params: dict=None,
             headers: dict=None,
             origin_req_host=None,
             unverifiable: bool=False,
             data=None,
             **kwargs) -> Promise:
        """
        Call a route, used by the wrapped route methods.

        :param route:
        :param route_params:
        :param params:
        :param headers:
        :param origin_req_host:
        :param unverifiable:
        :param data:
        :param kwargs:
        :return:
        """
        url = f'{self.base_url}{route.format_route_params(*route_params)}'
        if params:
            url = encode_url_params(url, params)

        self.before_call(route, route_params, params)

        headers = headers or {}
        headers['Content-Type'] = route.content_type

        _data = route.format_data(data)

        promise = urlcall.url_call(url,
                                   data=_data,
                                   method=route.method,
                                   headers=headers,
                                   origin_req_host=origin_req_host,
                                   unverifiable=unverifiable,
                                   prom_type=self.prom_type,
                                   **self.prom_args)

        promise.complete(lambda result, error: self.after_call(route, route_params, params, result, error))

        if self.promise_container:
            self.promise_container.add_promise(promise)
        return promise

    def before_call(self, route: CallRoute, route_params: list, params: dict):
        """
        global before call callback.

        :param route: The route that was called.
        :param route_params: The params of the route if any
        :param params: The url params
        :return:
        """
        pass

    def after_call(self, route: CallRoute, route_params: list, params: dict, result: Any, error: Any):
        """
        global after call callback

        :param route: The route that was called.
        :param route_params: The params of the route if any
        :param params: The url params
        :param result: The result of the call if any
        :param error: The error of the call if any
        :return:
        """
        pass
