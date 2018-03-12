from prompy.promise import Promise


def read_file(file, mode='r', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, reject):
        try:
            with open(file, mode) as f:
                resolve(f.read())
        except IOError as err:
            reject(err)
    return prom_type(starter, **kwargs)


def write_file(file, content, mode='w', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, reject):
        try:
            with open(file, mode) as f:
                f.write(content)
                resolve()
        except IOError as err:
            reject(err)
    return prom_type(starter, **kwargs)


