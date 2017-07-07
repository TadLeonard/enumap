import sys
from setuptools import setup
import enumap


if sys.version_info < (3, 6):
    print("Python 3.6+ is required")
    sys.exit(-1)


version = enumap.__version__
url = "https://github.com/TadLeonard/enumap"
download = "{}/archive/{}.tar.gz".format(url, version)
description = "Ordered collections inspired by Enum"
long_description = f"""
Enumap: ordered data kept orderly
=================================

Enumap is an Enum that helps you manage named, ordered values in a strict but convenient way. Enumap isn't yet another collection, it's a store of keys that creates familiar ordered collections in a more expressive and less error prone way.


Documentation
=============

See {url} for more."""


classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Developers',
  'Operating System :: OS Independent',
  'Programming Language :: Python :: 3',
  'Programming Language :: Python :: 3 :: Only',
]


setup(name="enumap",
      version=version,
      py_modules=["enumap"],
      url=url,
      description=description,
      long_description=long_description,
      classifiers=classifiers,
      author="Tad Leonard",
      author_email="tadfleonard@gmail.com",
      download_url=download
)
