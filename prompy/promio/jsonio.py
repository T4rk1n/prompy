import json

from prompy.promise import Promise


def loads(data: str, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        resolve(json.loads(data))
    return prom_type(starter, **kwargs)


def dumps(data: dict, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        resolve(json.dumps(data))
    return prom_type(starter, **kwargs)


def read_json_file(file: str, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        with open(file, 'rb') as f:
            resolve(json.load(f))
    return prom_type(starter, **kwargs)


def write_json_file(file: str, content, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        with open(file, 'wb') as f:
            json.dump(content, f)
            resolve()
    return prom_type(starter, **kwargs)
