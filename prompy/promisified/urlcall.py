import json
from typing import NamedTuple, Dict, Any
from urllib import request, parse, error

from prompy.errors import UrlCallError
from prompy.promise import Promise

HTTP_GET = 'GET'
HTTP_POST = 'POST'
HTTP_PUT = 'PUT'


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


def url_call(url, data=None, headers=None, origin_req_host=None, unverifiable=False, method=None,
             prom_type=Promise, **kwargs) -> Promise:
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
                resolve(UrlCallResponse(url, content_type, content, rep.status, headers, rep.msg, rep.reason))
        except error.HTTPError as e:
            e.read()
            reject(UrlCallError(f"{e.code} : {e.reason}"))
    return prom_type(starter, **kwargs)


def post(url, data=None, prom_type=Promise, **kwargs) -> Promise:
    return url_call(url, method=HTTP_POST, data=data, prom_type=prom_type, **kwargs)


def get(url, params: dict=None, prom_type=Promise, **kwargs) -> Promise:
    if params:
        url = encode_url_params(url, params)
    return url_call(url, prom_type=prom_type, **kwargs)


def put(url, data, prom_type=Promise, **kwargs) -> Promise:
    return url_call(url, data, prom_type=prom_type, **kwargs)


def json_call(url, payload=None, encoding='UTF-8', prom_type=Promise, headers=None, **kwargs) -> Promise:
    headers = headers or {}

    def starter(resolve, reject):
        pay = json.dumps(payload) if payload else None
        headers['Content-Type'] = f'application/json ; charset={encoding}'
        call = url_call(url, data=pay.encode(encoding), prom_type=prom_type, headers=headers, **kwargs)

        def on_call_end(rep: UrlCallResponse):
            if 'application/json' in rep.content_type:
                resolve(json.loads(rep.content))
            else:
                reject(UrlCallError(f"json_call: Content-Type is not json: {rep.content_type}"))

        call.then(on_call_end).catch(reject)
    return prom_type(starter)

