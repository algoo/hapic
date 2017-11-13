# coding: utf-8
# Always prefer setuptools over distutils
from setuptools import setup
from setuptools import find_packages
from os import path

here = path.abspath(path.dirname(__file__))

install_requires = [
    # TODO: Bottle will be an extension in future, see #1
    # TODO: marshmallow an extension too ? see #2
    'bottle',
    'marshmallow',
    'apispec==0.25.4-algoo',
    'multidict'
]
dependency_links = [
    'git+https://github.com/algoo/apispec.git@dev-algoo#egg=apispec-0.25.4-algoo'  # nopep8
]
tests_require = [
    'pytest',
]
dev_require = [
    'requests',
]

setup(
    name='hapic',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.10',

    description='HTTP api input/output manager',
    # long_description=long_description,
    long_description='',

    # The project's main homepage.
    url='http://gitlab.algoo.fr:10080/algoo/hapic.git',

    # Author details
    author='Algoo Development Team',
    author_email='contact@algoo.fr',

    # Choose your license
    license='',

    # What does your project relate to?
    keywords='http api validation',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires,
    dependency_links=dependency_links,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e ".[test]"
    extras_require={
        'test': tests_require,
        'dev': dev_require,
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'sample': ['package_data.dat'],
    # },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={},

    setup_requires=[],
    tests_require=tests_require,
)
