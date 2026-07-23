# Packaging of hapic

## Prerequisite

### Create a clean environment

```commandline
cd /tmp
mkdir hapic
cd hapic
```
### Create the publication configuration

```commandline
cat > .pypirc << 'EOF'
[distutils]
index-servers = pypi

[pypi]
repository: https://upload.pypi.org/legacy/
username: algoo
EOF
```

### Create the python environment

```commandline
python3 -mvenv env/
source env/bin/activate
pip install --upgrade setuptools wheel twine
```

## Package and publish the module

### Define the release to publish

Define the git tag 

```commandline
TAG=release_1.00
```

Get the code in the expected version

```
git clone git@github.com:algoo/hapic.git /tmp/hapic-clone
shopt -s dotglob        # so *, also matches dotfiles like .git, .gitignore
mv /tmp/hapic-clone/* .
rmdir /tmp/hapic-clone
git checkout ${TAG}
```

### Upload to pypi

```
twine upload dist/*
```

If you want give a try before, use:

```
twine upload --repository-url https://test.pypi.org/legacy/ dist/hapic-VERSION.tar.gz
```

