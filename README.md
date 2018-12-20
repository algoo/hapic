[![Build Status](https://travis-ci.org/algoo/hapic.svg?branch=master)](https://travis-ci.org/algoo/hapic)
[![Coverage Status](https://coveralls.io/repos/github/algoo/hapic/badge.svg?branch=master)](https://coveralls.io/github/algoo/hapic?branch=master)

# hapic in a nutshell

hapic is a framework-agnostic library for coding professionnal REST APIs.

# Philosophy

hapic as been developed by algoo in the context of a large service oriented project. The lack of a tool allowing real auto-documentation of Rest API has decided us to develop hapic.

target usage is not for "quick and dirty" stuff but for professionnal, maintainable, long-term targeted projects.

The separation of concerns between REST APIs layer and business stuff layer is in the DNA of hapic.

hapic is *just* the HTTP layer glue code over your business code.

# Direct benefits of using hapic

When you decide to base your development on hapic, you'll get direct benefits:

## Ready-to-use

- supports aiohttp, flask, pyramid and bottle 
- ready-to-use with your existing libraries
- effortless mapping of exceptions to HTTP errors
- serialisation based on marshmallow schemas or serpyco dataclasses

## Full API documentation ready

- your code *IS* the documentation
- swagger generated documentation
- embed the documentation in 1 line of code
- supports python 3.5, 3.6 and 3.7 

## Professionnal and maintanable source code

- separation of concerns between business logic and HTTP stuff
- very fast when used in conjunction with both aiohttp and serpyco
- extensible framework for supporting other web framework and serialisation libraries

# Licence

hapic is licenced under the MIT licence. You can use it in your projects, closed or open sourced.

## status, contributions

hapic source code is ready for production. Some refactoring are identified and required for maintainability, but public APIs are stable so you can rely on hapic for your developments.

hapic is under active development, based on different professional projects. we will answer your questions and accept merge requests if you find bugs or want to include features.

hapic is automatically tested on python 3.5, 3.6 and 3.7

## TODO references

TODOs in the code can include some `#xxx` - these are github issues references.

## Installation

For better performances with yaml module, you can install following (debian instruction):

    sudo apt-get install libyaml-dev

`libyaml-dev` package can be removed after hapic install.

## From source code

``` bash
virtualenv -p /usr/bin/python3 venv
source venv/bin/activate
python setup.py develop
```

To work with Marshmallow schemas, install necessary dependencies:

    pip install -e ".[marshmallow]"

To work with Serpyco dataclasses, install necessary dependencies:

    pip install -e ".[serpyco]"

To have full environment (for developpers):

    pip install -e ".[dev"]

## From pypi

To work with Marshmallow schemas, install necessary dependencies:

    pip install hapic[marshmallow]

To work with Serpyco dataclasses, install necessary dependencies:

    pip install hapic[serpyco]
 
## Give it a try

### short Flask example

``` python
from datetime import datetime
import flask
import marshmallow
import hapic
from hapic.ext.flask import FlaskContext
import json

hapic = hapic.Hapic()
app = flask.Flask(__name__)


class UriPathSchema(marshmallow.Schema):  # schema describing the URI and allowed values
    name = marshmallow.fields.String(required=True)
    age = marshmallow.fields.Integer(required=False)


class HelloResponseSchema(marshmallow.Schema): # schema of the API response
    name = marshmallow.fields.String(required=True)
    now = marshmallow.fields.DateTime(required=False)
    greetings = marshmallow.fields.String(required=False)


@app.route('/hello/<name>')  # flask route. must always be before hapic decorators
@hapic.with_api_doc()  # the first hapic decorator. Register the method for auto-documentation
@hapic.input_path(UriPathSchema())  # validate the URI structure
@hapic.output_body(HelloResponseSchema())  # define output structure
def hello(name='<No name>', hapic_data=None):
    return {
        'name': name,
        'now': datetime.now(),
        'dummy': { 'some': 'dummy' }  # will be ignored
    }

class UriPathSchemaWithAge(marshmallow.Schema):  # schema describing the URI and allowed values
    name = marshmallow.fields.String(required=True)
    age = marshmallow.fields.Integer(required=False)


@app.route('/hello/<name>/age/<age>')
@hapic.with_api_doc()
@hapic.input_path(UriPathSchemaWithAge())
@hapic.output_body(HelloResponseSchema())
def hello2(name='<No name>', age=42, hapic_data=None):
    return {
        'name': name,
        'age': age,
        'greetings': 'Hello {name}, it looks like you are {age}'.format(
            name=name,
            age=age
        ),
        'now': datetime.now(),
        'dummy': { 'some': 'dummy' }  # will be ignored
    }


hapic.set_context(FlaskContext(app))
print(json.dumps(hapic.generate_doc(title='API Doc', description='doc desc.')))  # Generate the documentation
app.run('127.0.0.1', 8080, debug=True)
```

How to use it:

Nominal cases:

``` bash
$ curl "http://127.0.0.1:8080/hello/michel"
# {"now": "2017-12-18T12:37:10.751623+00:00", "name": "michel"}
```

``` bash
$ curl "http://127.0.0.1:8080/hello/michel/age/17"
# {"name": "damien", "greetings": "Hello damien, it looks like you are 17", "now": "2017-12-18T12:41:58.229679+00:00"}
```

Error case (returns a 400):

``` bash
$ curl "http://127.0.0.1:8080/hello/michel/age/mistaken"
# {"details": {"age": ["Not a valid integer."]}, "message": "Validation error of input data"}
```


### A complete user API

In the `example/usermanagement` directory you can find a complete example of an API allowing to manage users.

Features are: 

- get list of all users
- get detail of a given user
- create a user
- delete a user

In order to test it :

Install the required dependencies:

``` bash
pip install bottle flask pyramid`
```

Run the instance you wan to test (one of the three following lines):

``` bash
python example/usermanagement/serve_bottle.py
python example/usermanagement/serve_flask.py
python example/usermanagement/serve_pyramid.py
```

Features shown :

- auto-generation of the documentation
- managing parameters in the uri path
- managing input schemas
- managing output schema
- management of error cases (404, 500, etc)
- nice exception handling
- automatic dict/object serialization
