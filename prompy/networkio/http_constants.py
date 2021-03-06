"""CONSTANTS"""

GET = 'GET'
POST = 'POST'
PUT = 'PUT'
HEAD = 'HEAD'
DELETE = 'DELETE'
CONNECT = 'CONNECT'
OPTIONS = 'OPTIONS'
TRACE = 'TRACE'
PATCH = 'PATCH'

METHODS = (
    GET, POST, PUT, HEAD, DELETE, CONNECT, OPTIONS, TRACE, PATCH
)

CONTENT_TYPE = 'Content-Type'

CONTENT_TYPE_HTML = 'text/html'
CONTENT_TYPE_PLAIN = 'text/plain'
CONTENT_TYPE_JSON = 'application/json'

CONTENT_TYPES = (
    CONTENT_TYPE_HTML, CONTENT_TYPE_PLAIN, CONTENT_TYPE_JSON
)

PROTOCOL_HTTP = 'http'
PROTOCOL_HTTPS = 'https'
PROTOCOL_WS = 'ws'
