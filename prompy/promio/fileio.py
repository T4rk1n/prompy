import os
import re
import pathlib
import shutil

from prompy.promise import Promise


def read_file(file: str, mode='r', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        with open(file, mode) as f:
            resolve(f.read())
    return prom_type(starter, **kwargs)


def write_file(file: str, content, mode='w', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        with open(file, mode) as f:
            f.write(content)
        resolve(None)
    return prom_type(starter, **kwargs)


def delete_file(file: str, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        if os.path.exists(file):
            os.remove(file)
            resolve(None)
        else:
            raise FileNotFoundError(file)
    return prom_type(starter, **kwargs)


def walk(directory,
         filter_directories=None, filter_filename=None, prom_type=Promise, **kwargs) -> Promise[pathlib.Path]:
    def starter(resolve, _):
        dir_filter = None
        file_filter = None
        if filter_directories:
            dir_filter = re.compile(filter_directories)
        if filter_filename:
            file_filter = re.compile(filter_filename)
        for current, sub_directories, files in os.walk(directory):
            if dir_filter:
                to_delete = []
                for s in sub_directories:
                    if dir_filter.match(s):
                        to_delete.append(s)
                for i in to_delete:
                    sub_directories.remove(i)
            file_list = files
            if file_filter:
                file_list = filter(lambda f: not file_filter.match(f), files)
            for fi in file_list:
                file_path = os.path.join(current, fi)
                p = pathlib.Path(file_path)
                resolve(p)

    return prom_type(starter, **kwargs)


def compress_directory(directory, destination,
                       archive_format='zip', root_dir='.', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        archive = shutil.make_archive(destination, archive_format, base_dir=directory, root_dir=root_dir)
        resolve(archive)
    return prom_type(starter, **kwargs)


def decompress(filename, destination,
               archive_format='zip', prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        shutil.unpack_archive(filename, destination, archive_format)
        resolve(destination)
    return prom_type(starter, **kwargs)
