# -*- coding: utf-8 -*-
from typing import NamedTuple

from prompy.promise import Promise

try:
    import cchardet as chardet
except ImportError:
    import chardet


class EncodingInfo(NamedTuple):
    encoding: str
    confidence: float = 1
    language: str = ''


class EncodedData(NamedTuple):
    data: bytes
    info: EncodingInfo


class DecodedData(NamedTuple):
    data: str
    info: EncodingInfo


def detect(bytes_string: bytes):
    return EncodingInfo(**chardet.detect(bytes_string))


def _decode(data: bytes,
            encoding: str = None,
            default_encoding: str = 'utf-8',
            confidence_check: float = 0.8, ):
    enc = encoding
    info = None
    if not enc:
        info = detect(data)
        if info.confidence > confidence_check:
            enc = info.encoding
        else:
            enc = default_encoding
    return DecodedData(data.decode(enc), info or EncodingInfo(enc))


def decode(data: bytes,
           encoding: str = None,
           default_encoding: str = 'utf-8',
           confidence_check: float = 0.8,
           prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        resolve(_decode(data, encoding, default_encoding, confidence_check))
    return prom_type(starter, **kwargs)


def encode(s: str, encoding, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        resolve(EncodedData(s.encode(encoding), EncodingInfo(encoding)))
    return prom_type(starter, **kwargs)

