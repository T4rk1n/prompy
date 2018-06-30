import json
from typing import Any, Callable
from urllib import request, error

from prompy.errors import UrlCallError
from prompy.networkio.http_constants import POST, PUT
from prompy.networkio.url_tools import UrlCallResponse, encode_url_params, default_content_mapper
from prompy.promise import Promise


def url_call(url,
             data=None,
             headers=None,
             origin_req_host=None,
             unverifiable=False,
             method=None,
             content_mapper: Callable[[str, str, str], Any] = default_content_mapper,
             prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    """
    Base http call using urllib.

    :param url:
    :param data:
    :param headers:
    :param origin_req_host:
    :param unverifiable:
    :param method:
    :param content_mapper:
    :param prom_type:
    :param kwargs:
    :return: A promise to resolve with a response.
    """
    def starter(resolve, reject):
        try:
            req = request.Request(url, data=data, headers=headers or {},
                                  origin_req_host=origin_req_host, method=method, unverifiable=unverifiable)
            with request.urlopen(req) as rep:
                content_type = rep.headers.get_content_type()
                encoding = rep.headers.get_content_charset()
                rep_headers = {}
                for k, v in rep.headers.items():
                    rep_headers[k] = v
                content = rep.read()
                if content_mapper:
                    content = content_mapper(content_type, content, encoding)
                resolve(UrlCallResponse(url, content_type, content, rep.status,
                                        rep_headers, rep.msg, rep.reason, encoding))
        except error.HTTPError as e:
            e.read()
            reject(UrlCallError(f" {url} : {e.code} : {e.reason}"))
    return prom_type(starter, **kwargs)


def post(url, data=None, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    return url_call(url, method=POST, data=data, prom_type=prom_type, **kwargs)


def get(url, params: dict=None, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    if params:
        url = encode_url_params(url, params)
    return url_call(url, prom_type=prom_type, **kwargs)


def put(url, data, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    return url_call(url, data, method=PUT, prom_type=prom_type, **kwargs)


def json_call(url,
              payload=None, encoding='UTF-8', prom_type=Promise, headers=None, **kwargs) -> Promise[UrlCallResponse]:
    """Auto encode payload and decode response in json."""
    headers = headers or {}

    def starter(resolve, reject):
        pay = json.dumps(payload) if payload else None
        headers['Content-Type'] = f'application/json ; charset={encoding}'
        call = url_call(url, data=pay.encode(encoding), prom_type=prom_type, headers=headers, **kwargs)

        call.then(resolve).catch(reject)

    return prom_type(starter)

