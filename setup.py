from setuptools import setup

setup(
    name='prompy',
    version='0.0.1',
    packages=['prompy', 'prompy.networkio', 'prompy.threadio', 'prompy.processio', 'prompy.promio'],
    url='',
    install_requires=['chardet>=3.0.4'],
    python_requires='>=3.5',
    license='MIT',
    author='T4rk',
    author_email='t4rk@outlook.com',
    description='Promises for python'
)
