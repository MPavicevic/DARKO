#!/usr/bin/env python

from setuptools import setup, find_packages
import codecs
import os
HERE = os.path.abspath(os.path.dirname(__file__))

# FINAL_RELEASE is the last stable version of Dispa-SET
# A more precisely version try to be automatically determined from the git repository using setuptools_scm.
# If it's not possible (using git archive tarballs for example), FINAL_RELEASE will be used as fallback version.
# edited manually when a new release is out (git tag -a)
FINAL_RELEASE = open(os.path.join(HERE, 'VERSION')).read().strip()

def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

# Sets the __version__ variable
__version__ = None
exec(open('darko/_version.py').read())

setup(
    name='darko',
    description='Day-ahead Market Optimization',
    author='Matija Pavičević',
    author_email='matija.pavicevic@kuleuven.be',
    url='https://github.com/MPavicevic/DARKO',
    license='EUPL v1.2',
    packages=find_packages(),
    include_package_data=True,
    use_scm_version={
        'version_scheme': 'post-release',
        'local_scheme': lambda version: version.format_choice("" if version.exact else "+{node}", "+dirty"),
        'fallback_version': FINAL_RELEASE,
    },
    setup_requires=["setuptools_scm"],
    install_requires=[
        "future >= 0.15",
        "click >= 3.3",
        "numpy >= 1.12",
        "pandas >= 0.19",
        "xlrd == 1.2",
        "matplotlib >= 1.5.1",
        "gdxcc >= 7",
        "gamsxcc",
        "optcc",
        "xlsxwriter",
        "setuptools_scm",
        "pytest",
        "pytest-cov",
        "codecov",
    ],
    entry_points={
        'console_scripts': [
            'darko = darko.cli:cli'
        ]},
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python'
    ],
    keywords=['day-ahead market', 'energy systems analysis', 'optimization']
)