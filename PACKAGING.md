# Packaging of hapic

## Prerequisite

Prepare a `~/.pypirc` configuration file, eg:

    [distutils]
    index-servers = pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: algoo

Upgrade or install packages:

    pip install --upgrade setuptools wheel twine

## Package and distribute

Checkout on branch `master` (or other branch if you know what you are doing):

    git checkout master

Build the package:

    python setup.py sdist

Upload it:

    twine upload dist/*

If you want give a try before, use:

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
