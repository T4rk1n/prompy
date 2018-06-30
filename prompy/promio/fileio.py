"""
Promise creators to deal with files.

Read, write, delete, compress, decompress, walk.

:Example:

.. code-block:: python

    from prompy.threadio.tpromise import TPromise
    from prompy.promio import fileio

    filename = 'myfile'

    f = fileio.write_file(filename, 'content', prom_type=TPromise)
    f.then(lambda _: fileio.read_file(filename).then(lambda data: print(data)))
"""
import os
import re
import pathlib
import shutil
from typing import Any

from prompy.promise import Promise


def read_file(file: str, mode='r', prom_type=Promise, **kwargs) -> Promise:
    """
    Read a file in a promise.

    :param file: to open
    :param mode: open mode ('r', 'rb')
    :param prom_type: Type of the promise to instantiate.
    :param kwargs: kwargs of the promise initializer.
    :return: Promise that will resolve with the content of the file.
    """
    def starter(resolve, _):
        with open(file, mode) as f:
            resolve(f.read())
    return prom_type(starter, **kwargs)


def write_file(file: str, content: Any,
               mode: str='w', prom_type=Promise, **kwargs) -> Promise:
    """
    Write to a file and resolve when it's done.

    :param file: to open.
    :param content: to write.
    :param mode: open mode ('w', 'wb')
    :param prom_type: Type of the promise to instantiate.
    :param kwargs: kwargs of the promise initializer.
    :return:
    """
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


def walk(directory: str,
         filter_directories: str=None,
         filter_filename: str=None,
         on_found=None,
         prom_type=Promise, **kwargs) -> Promise[pathlib.Path]:
    """
    Resolve a list of paths that were walked.

    :param directory: path to walk.
    :param on_found: called for each path that was found.
    :param filter_directories: a regex filter to exclude directories.
    :param filter_filename: a regex filter to exclude filenames.
    :param prom_type: Type of the promise to instantiate.
    :param kwargs: kwargs of the promise initializer.
    :return:
    """

    def starter(resolve, _):
        dir_filter = None
        file_filter = None
        walked = []
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
                walked.append(p)
                if on_found:
                    on_found(p)

        resolve(walked)

    return prom_type(starter, **kwargs)


def compress_directory(directory: str, destination: str,
                       archive_format: str='zip',
                       root_dir: str='.',
                       prom_type=Promise, **kwargs) -> Promise:
    """

    :param directory:
    :param destination:
    :param archive_format:
    :param root_dir:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        archive = shutil.make_archive(destination, archive_format,
                                      base_dir=directory, root_dir=root_dir)
        resolve(archive)
    return prom_type(starter, **kwargs)


def decompress(filename: str, destination: str,
               archive_format: str='zip',
               prom_type=Promise, **kwargs) -> Promise:
    """


    :param filename:
    :param destination:
    :param archive_format:
    :param prom_type:
    :param kwargs:
    :return:
    """
    def starter(resolve, _):
        shutil.unpack_archive(filename, destination, archive_format)
        resolve(destination)
    return prom_type(starter, **kwargs)
