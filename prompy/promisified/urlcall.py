import enum
from typing import NamedTuple
from urllib import request, parse, robotparser, error

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


class UrlCallError(Exception):
    """Web call error"""


def url_call(url, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, reject):
        try:
            req = request.Request(url)
            with request.urlopen(req) as rep:
                content_type = rep.headers.get_content_type()
                headers = {}
                for k, v in rep.headers.items():
                    headers[k] = v
                content = rep.read()
                resolve(UrlCallResponse(url, content_type, content, rep.status, headers, rep.msg, rep.reason))
        except error.HTTPError as e:
            e.read()
            reject(UrlCallError(f"{e.code} : {e.reason}"))
    return prom_type(starter, **kwargs)


def post(url, data=None):
    pass


if __name__ == '__main__':
    from prompy.threaded.tpromise import TPromise
    p = url_call("http://www.google.com", prom_type=TPromise)
    p.then(lambda r: print(r))
