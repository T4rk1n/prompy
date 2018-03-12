class PromiseError(Exception):
    """Base promise error"""


class UnhandledPromiseError(PromiseError):
    """Unhandled promise rejection error"""


class PromiseRejectionError(PromiseError):
    """Raised when a promise is called with raise_again option"""


class UrlCallError(PromiseError):
    """Web call error"""
