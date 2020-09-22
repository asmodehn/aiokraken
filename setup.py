#!/usr/bin/env python3
import setuptools
import runpy

# Ref : https://packaging.python.org/single_source_version/#single-sourcing-the-version
# runpy is safer and a better habit than exec
version = runpy.run_path('aiokraken/_version.py')
__version__ = version.get('__version__')

setuptools.setup(
    name='aiokraken',
    version=__version__,
    description='Python client library for the Kraken Rest and Websocket API using asyncio and aiohttp',
    long_description='Python client library for the Kraken Rest and Websocket API using asyncio and aiohttp',  # TODO : duplicate a README.rst
    long_description_content_type='text/x-rst',
    author='AlexV',
    author_email='asmodehn@gmail.com',
    url='https://github.com/asmodehn/aiokraken',
    packages=setuptools.find_packages(),
    install_requires=[
        "aiohttp",
        "aiodns",
        "cchardet"
    ],
    license='GPL',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here.
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)


# Release process:
# 1) make sure .pypirc is setup properly (or you will have to authenticate manually)
# 2) run 'python3 setup.py sdist bdist_wheel' to obtain artifacts in dist/
# 3) run 'python3 -m twine upload dist/*' to upload.
# Specify '--repository testpypi' if you want to use the testpypi instance
