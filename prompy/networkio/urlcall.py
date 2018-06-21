import json
from typing import NamedTuple, Dict, Any, Callable
from urllib import request, parse, error

from prompy.errors import UrlCallError
from prompy.networkio.http_constants import HTTP_POST, HTTP_PUT
from prompy.promise import Promise


class UrlCallResponse(NamedTuple):
    url: str
    content_type: str
    content: str
    status: int
    headers: dict
    msg: str
    reason: str


def encode_url_params(url: str, params: Dict[str, Any]) -> str:
    data = parse.urlencode(params)
    return f"{url}?{data}"


def default_mapper(content_type, content):
    if 'application/json' in content_type:
        return json.loads(content)
    return content


def url_call(url, data=None, headers=None, origin_req_host=None, unverifiable=False, method=None,
             content_mapper: Callable[[str, str], Any] = default_mapper,
             prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    """Base request call."""
    def starter(resolve, reject):
        try:
            req = request.Request(url, data=data, headers=headers or {},
                                  origin_req_host=origin_req_host, method=method, unverifiable=unverifiable)
            with request.urlopen(req) as rep:
                content_type = rep.headers.get_content_type()
                rep_headers = {}
                for k, v in rep.headers.items():
                    rep_headers[k] = v
                content = rep.read()
                if content_mapper:
                    content = content_mapper(content_type, content)
                resolve(UrlCallResponse(url, content_type, content, rep.status, headers, rep.msg, rep.reason))
        except error.HTTPError as e:
            e.read()
            reject(UrlCallError(f"{e.code} : {e.reason}"))
    return prom_type(starter, **kwargs)


def post(url, data=None, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    return url_call(url, method=HTTP_POST, data=data, prom_type=prom_type, **kwargs)


def get(url, params: dict=None, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    if params:
        url = encode_url_params(url, params)
    return url_call(url, prom_type=prom_type, **kwargs)


def put(url, data, prom_type=Promise, **kwargs) -> Promise[UrlCallResponse]:
    return url_call(url, data, method=HTTP_PUT, prom_type=prom_type, **kwargs)


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

