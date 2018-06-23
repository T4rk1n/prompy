"""Json related promise creators."""
import json
from typing import Union

from prompy.promise import Promise


def loads(data: str, prom_type=Promise, **kwargs) -> Promise:
    """
    Resolve the loaded data from a string.

    :param data:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        resolve(json.loads(data))
    return prom_type(starter, **kwargs)


def dumps(data: Union[dict, list], prom_type=Promise, **kwargs) -> Promise:
    """
    Resolve the dumped data.

    :param data:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        resolve(json.dumps(data))
    return prom_type(starter, **kwargs)


def read_json_file(file: str, prom_type=Promise, **kwargs) -> Promise:
    """
    Resolve a json file content.

    :param file:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        with open(file, 'rb') as f:
            resolve(json.load(f))
    return prom_type(starter, **kwargs)


def write_json_file(file: str, content, prom_type=Promise, **kwargs) -> Promise:
    """
    Write the content to a json file. Resolve when done.

    :param file:
    :param content:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        with open(file, 'wb') as f:
            json.dump(content, f)
            resolve(None)
    return prom_type(starter, **kwargs)
