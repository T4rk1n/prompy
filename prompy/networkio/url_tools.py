import json
import re
from typing import NamedTuple, Dict, Any, Union
from urllib import parse

from prompy.networkio import http_constants as _http
from prompy.promio import encodio

_url_pattern = re.compile(
    r'(https?)://([\w.]*)(:\d*)?([/\w.]*)\??([\w/=&\-+]*)#?([\w-]*)')
_content_type_detect_re = re.compile('charset=(.*)')


def encode_url_params(url: str, params: Dict[str, Any]) -> str:
    data = parse.urlencode(params)
    return f"{url}?{data}"


def default_content_mapper(content_type: str, content: bytes,
                           encoding: str=None):
    """
    Default mapper for :py:func:`url_call`

    :param content_type: support `application/json`,`text/html`,`text/plain`
    :param content: to deserialize
    :param encoding: charset from the content-type
    :return: deserialized content if possible
    """
    if not encoding:
        info = encodio.detect(content)
        encoding = info.encoding

    if _http.CONTENT_TYPE_JSON in content_type:
        return json.loads(content, encoding=encoding)
    if any(x in content_type for x in (
            _http.CONTENT_TYPE_PLAIN, _http.CONTENT_TYPE_HTML)):
        return content.decode(encoding)
    return content


def detect_content_charset(content_type):
    encoding = _content_type_detect_re.search(content_type)
    if encoding:
        return encoding.group(1)


def json_headers(encoding='utf-8'):
    return {
        _http.CONTENT_TYPE: f'{_http.CONTENT_TYPE_JSON}; charset={encoding}',
    }


class Url:
    def __init__(self, url):
        r = _url_pattern.search(url)
        if not r:
            raise TypeError(f'Not a valid url -- {url}')
        groups = r.groups()

        self.url = url
        self.protocol: str = groups[0]
        self.host: str = groups[1]
        port = groups[2]
        self.port: int = int(port[1:]) if port else None
        self.path: str = groups[3]
        self._params: str = groups[4]
        self.tag: str = groups[5]

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value: Union[str, dict]):
        if isinstance(value, str):
            self._params = value
        else:
            self._params = parse.urlencode(value)


class UrlCallResponse(NamedTuple):
    url: str
    content_type: str
    content: str
    status: int
    headers: dict
    msg: str
    reason: str
    charset: str


class UrlCallResponse2:
    def __init__(self, url: str,
                 content_type: str,
                 content: str, status: int,
                 headers: dict,
                 msg: str='', reason: str='', charset: str=''):
        self.url = url
        self.content_type = content_type
        self.content = content
        self.status = status
        self.headers = headers
        self.msg = msg
        self.reason = reason
        self.charset = charset
