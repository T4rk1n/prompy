"""
call_factory

Meta web api wrapper.

Usage:
```
from prompy.networkio.call_factory import CallRoute, Caller
from prompy.threadio.promise_queue import PromiseQueuePool


class Api(Caller):
    def route_home(self, **kwargs):
        return CallRoute('/')

    def route_data(self, **kwargs):
        return CallRoute('/data', method='POST')


pool = PromiseQueuePool(start=True)
api = Api(base_url='http://localhost:5000', promise_container=pool)
api.route_data(data={'num': 6}).then(print).catch(print)

```

"""
import json
import re
import functools

from prompy.container import BasePromiseContainer
from prompy.networkio import urlcall, http_constants
from prompy.networkio.urlcall import encode_url_params
from prompy.promise import Promise


_route_params_pattern = re.compile('<.*>')


class CallRoute:
    """"""

    def __init__(self,
                 route: str,
                 method: str=http_constants.HTTP_GET,
                 content_type: str=http_constants.CONTENT_TYPE_JSON):
        self.route = route
        self.method = method
        self.route_params = _route_params_pattern.search(self.route)
        self.content_type = content_type

    def format_route_params(self, **kwargs):
        if not self.route_params:
            return self.route
        route = self.route
        for p in self.route_params:
            value = kwargs.get(p)
            if not p:
                raise Exception(f'Missing url parameter <{p}>')
            route = route.replace(p, value)
        return route

    def format_data(self, data):
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
                promise = self.call(route, *args, **kwargs)
                return promise
            return _inner

        for route_name in filter(lambda k: k.startswith('route'), attributes.keys()):
            new_attrs[route_name] = _route_wrap(attributes[route_name])

        return type.__new__(mcs, name, bases, new_attrs)


class Caller(metaclass=_MetaCall):
    """
    Wraps all method starting with `route` with a call.
    route methods must:
    -return a CallRoute object.
    -**kwargs must be there if you want Caller.call and route params kwargs.
    """

    def __init__(self, base_url='',
                 promise_container: BasePromiseContainer=None,
                 prom_type=Promise,
                 prom_args=None):
        self.base_url = base_url
        self.promise_container = promise_container
        self.prom_type = prom_type
        self.prom_args = prom_args or {}

    def call(self,
             route: CallRoute,
             route_params: dict=None,
             params: dict=None,
             headers: dict=None,
             origin_req_host=None,
             unverifiable: bool=False,
             data=None,
             **kwargs) -> Promise:
        url = f'{self.base_url}{route.format_route_params(**kwargs)}'
        if params:
            url = encode_url_params(url, params)
        if route_params:
            url = route.format_route_params(**route_params)

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

    def before_call(self, route: CallRoute, route_params, params):
        """global before call callback."""
        pass

    def after_call(self, route: CallRoute, route_params, params, result, error):
        """global after call callback"""
        pass
