import csv

from prompy.promise import Promise


def read_csv(file, newline='', reader_args=None,
             prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        with open(file, newline=newline) as csvfile:
            a = reader_args or {}
            reader = csv.reader(csvfile, **a)
            for row in reader:
                resolve(row)
    return prom_type(starter, **kwargs)


def write_csv(file, data, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, reject):
        pass
    return prom_type(starter, **kwargs)
