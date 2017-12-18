[![Build Status](https://travis-ci.org/algoo/hapic.svg?branch=master)](https://travis-ci.org/algoo/hapic)
[![Coverage Status](https://coveralls.io/repos/github/algoo/hapic/badge.svg?branch=master)](https://coveralls.io/github/algoo/hapic?branch=master)

# Hapic in a nutshell

Hapic is a framework-agnostic library for implementation of professionnal REST APIs.

Why you should use Hapic :

- Hapic adapt naturally to your existing libraries
- Hapic map exceptions to HTTP errors without effort
- Hapic really auto-documents your APIs according to marshmallow,  apispec and web framework routing. You do not "write your doc in docstrings": the documentation is really auto-generated
- Hapic can be used out-of-the-box with Bottle, Flask or Pyramid

Hapic works with JSON, but it can be used for XML or virtually any data structure format.

Auto-generated documentation can be visualised with swagger.

## Philosophy

Hapic as been developed by algoo in the context of a large client project. The lack of a tool allowing real auto-documentation of Rest API has decided us to develop Hapic.

Target projects of Hapic are not "quick and dirty" but professionnally architectured projects.

The separation of concerns between REST APIs layer and Business Stuff layer is in the DNA of Hapic. Hapic is *just* the HTTP Layer over your business code.

## Licence

Hapic is licenced under the MIT licence. You can use it in your projects, closed or open sourced.

## Status, contributions

Hapic source code is ready for production. Some refactoring are identified and required for maintainability, but public APIs are stable so you can rely on Hapic for your developments.

Hapic is under active development, based on Algoo projects. We will answer your questions and accept merge requests if you find bugs or want to include functionnalities.

## TODO references

TODO can make reference to #X, this is github issues references.

## Installation

```
virtualenv -p /usr/bin/python3 venv
source venv/bin/activate
python setup.py develop
```
 
## Give it a try

### Fast Flask example

```
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

```
$ curl "http://127.0.0.1:8080/hello/michel"
# {"now": "2017-12-18T12:37:10.751623+00:00", "name": "michel"}
```

```
$ curl "http://127.0.0.1:8080/hello/michel/age/17"
# {"name": "damien", "greetings": "Hello damien, it looks like you are 17", "now": "2017-12-18T12:41:58.229679+00:00"}
```

Error case (returns a 400):

```
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

```
pip install bottle flask pyramid`
```

Run the instance you wan to test (one of the three following lines):

```
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