"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os

from setuptools import setup, find_packages

import mapry_meta

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))  # pylint: disable=invalid-name

with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()  # pylint: disable=invalid-name

with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as fid:
    install_requires = [
        line for line in fid.read().splitlines() if line.strip()
    ]

setup(
    name=mapry_meta.__title__,
    version=mapry_meta.__version__,
    description=mapry_meta.__description__,
    long_description=long_description,
    url=mapry_meta.__url__,
    author=mapry_meta.__author__,
    author_email=mapry_meta.__author_email__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    license='License :: OSI Approved :: MIT License',
    keywords='object mapping json serialization deserialization graph',
    packages=find_packages(exclude=['doc', 'tests*', 'test_cases*']),
    install_requires=install_requires,
    extras_require={
        # yapf: disable
        'dev': [
            'coverage>=4.5.1,<5',
            'pydocstyle>=3.0.0,<4',
            'mypy==0.670',
            'pylint==2.3.0',
            'yapf==0.27.0',
            'temppathlib>=1.0.3,<2',
            'isort>=4.3.4,<5',
            'twine>=1.12.1,<2',
            'pyicontract-lint>=2.0.0,<3',
        ],
        'testcpp': [
            'conan>=1.13.0,<2',
            'temppathlib>=1.0.3,<2',
        ],
        'testgo': [],
        'testpy': [
            'pytz==2018.9',
            'temppathlib>=1.0.3,<2',

            # needed so that we can mypy the generated code
            'mypy==0.670'
        ],
        # yapf: enable
    },
    py_modules=['mapry', 'mapry_meta'],
    scripts=['bin/mapry-to'],
    package_data={"mapry": ["py.typed"]})
