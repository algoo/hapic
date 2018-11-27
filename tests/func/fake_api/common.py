from collections import OrderedDict

from serpyco import StringFormat

SWAGGER_DOC_API = {
 'definitions': {
     'AboutResponseSchema': {'properties': {
                                'datetime': {'format': 'date-time',
                                             'type': 'string'},
                                'version': {'type': 'string'}
                                },
                             'required': ['datetime', 'version'],
                             'type': 'object'},
     'ListsUserSchema': {'properties':  {
                            'item_nb': {'format': 'int32',
                                        'minimum': 0,
                                        'type': 'integer'},
                            'items': {
                                'items': {'$ref': '#/definitions/UserSchema_without_email_address_first_name_last_name'},
                                'type': 'array'},
                            'pagination': {'$ref': '#/definitions/PaginationSchema'}},
                         'required': ['item_nb'],
                         'type': 'object'},
     'NoContentSchema': {'properties': {},
                         'type': 'object'},
     'PaginationSchema': {'properties': {
                            'current_id': {'format': 'int32', 'type': 'integer'},
                            'first_id': {'format': 'int32', 'type': 'integer'},
                            'last_id': {'format': 'int32', 'type': 'integer'}},
                          'required': ['current_id', 'first_id', 'last_id'],
                          'type': 'object'},
     'UserSchema': {'properties': {
                        'company': {'type': 'string'},
                        'display_name': {'type': 'string'},
                        'email_address': {'format': 'email', 'type': 'string'},
                        'first_name': {'type': 'string'},
                        'id': {'format': 'int32', 'type': 'integer'},
                        'last_name': {'type': 'string'},
                        'username': {'type': 'string'}},
                    'required': ['company',
                                 'display_name',
                                 'email_address',
                                 'first_name',
                                 'id',
                                 'last_name',
                                 'username'],
                    'type': 'object'},
    'UserSchema_without_id': {
        'properties': {
            'username': {'type': 'string'},
            'display_name': {'type': 'string'},
            'company': {'type': 'string'},
            'last_name': {'type': 'string'},
            'email_address': {'format': 'email', 'type': 'string'},
            'first_name': {'type': 'string'}},
        'required': ['company', 'display_name', 'email_address', 'first_name',
                     'last_name', 'username'], 'type': 'object'},
    'UserSchema_without_email_address_first_name_last_name': {
        'properties': {
            'username': {'type': 'string'},
            'id': {'format': 'int32', 'type': 'integer'},
            'company': {'type': 'string'},
            'display_name': {'type': 'string'}},
        'required': ['company', 'display_name', 'id', 'username'], 'type': 'object'
    },
    },
 'info': {'description': 'just an example of hapic API', 'title': 'Fake API', 'version': '1.0.0'},
 'parameters': {},
 'paths': OrderedDict(
     [('/about', {
         'get': {
           'description': 'General information about this API.',
           'responses': {200: {
               'description': '200',
               'schema': {'$ref': '#/definitions/AboutResponseSchema'}}}}}),
      ('/users', {
         'get': {
           'description': 'Obtain users list.',
           'responses': {200: {
               'description': '200',
               'schema': {'$ref': '#/definitions/ListsUserSchema'}}}}}),
      ('/users/{id}', {
         'delete': {
           'description': 'delete user',
           'parameters': [{'format': 'int32',
                           'minimum': 1,
                           'in': 'path',
                           'name': 'id',
                           'required': True,
                           'type': 'integer'}],
           'responses': {204: {
               'description': '204',
               'schema': {'$ref': '#/definitions/NoContentSchema'}}}},
         'get': {
             'description': 'Obtain one user',
             'parameters': [{'format': 'int32',
                             'in': 'path',
                             'minimum': 1,
                             'name': 'id',
                             'required': True,
                             'type': 'integer'}],
             'responses': {200: {
                 'description': '200',
                 'schema': {'$ref': '#/definitions/UserSchema'}}}}}),
      ('/users/', {
         'post': {
             'description': 'Add new user',
             'parameters': [{'in': 'body',
                             'name': 'body',
                             'schema': {'$ref': '#/definitions/UserSchema_without_id'}}],
             'responses': {200: {
                 'description': '200',
                 'schema': {'$ref': '#/definitions/UserSchema'}}}}}),
      ( '/users2', {
          'get': {
              'description': 'Obtain users list.',
              'responses': {200: {
                  'description': '200',
                  'schema': {'type': 'array',
                             'items': {'$ref': '#/definitions/UserSchema_without_email_address_first_name_last_name'}
                             }
          }}}}
        )]),
 'swagger': '2.0',
 'tags': []
}

# TODO BS 2018-11-27; Used for test
# tests.func.fake_api.test_fake_api\
#     .test_func__test_fake_api_doc_ok__aiohttp_serpyco
# But must be replaced by atomic testing
serpyco_SWAGGER_DOC_API = {
    'info': {'description': 'just an example of hapic API',
             'title': 'Fake API', 'version': '1.0.0'},
    'paths': OrderedDict([('/about',
                         {'get': {'responses': {200: {'description': '200'
                         ,
                         'schema': {'$ref': '#/definitions/AboutResponseSchema'
                         }}},
                         'description': 'General information about this API.'
                         }}), ('/users',
                         {'get': {'responses': {200: {'description': '200'
                         ,
                         'schema': {'$ref': '#/definitions/ListsUserSchema'
                         }}}, 'description': 'Obtain users list.'}}),
                         ('/users2',
                         {'get': {'responses': {200: {'description': '200'
                         , 'schema': {'$ref': '#/definitions/UserSchema'
                         }}}, 'description': 'Obtain users list.'}}),
                         ('/users/{id}',
                         {'get': {'responses': {200: {'description': '200'
                         , 'schema': {'$ref': '#/definitions/UserSchema'
                         }}}, 'parameters': [{
        'type': 'integer',
        'minimum': 1,
        'in': 'path',
        'name': 'id',
        'required': True,
        }], 'description': 'Obtain one user'},
            'delete': {'responses': {204: {'description': '204',
                       'schema': {'$ref': '#/definitions/NoContentSchema'
                       }}}, 'parameters': [{
        'type': 'integer',
        'minimum': 1,
        'in': 'path',
        'name': 'id',
        'required': True,
        }], 'description': 'delete user'}}), ('/users/',
                {'post': {'parameters': [{'in': 'body', 'name': 'body',
                'schema': {'$ref': '#/definitions/UserSchema'}}],
                'responses': {200: {'description': '200',
                'schema': {'$ref': '#/definitions/UserSchema'}}},
                'description': 'Add new user'}})]),
    'tags': [],
    'swagger': '2.0',
    'parameters': {},
    'responses': {},
    'definitions': {
        'PaginationSchema': {
            'type': 'object',
            'properties': {'first_id': {'type': 'integer'},
                           'last_id': {'type': 'integer'},
                           'current_id': {'type': 'integer'}},
            'required': ['first_id', 'last_id', 'current_id'],
            'description': 'A docstring to prevent auto generated docstring',
            },
        'UserSchema_only_id_username_display_name_company': {
            'type': 'object',
            'properties': {
                'display_name': {'type': 'string'},
                'company': {'type': 'string'},
                'username': {'type': 'string', 'pattern': '[\\w-]+'},
                'id': {'type': 'integer', 'default': None},
                },
            'required': ['display_name', 'company', 'username', 'id'],
            'description': 'A docstring to prevent auto generated docstring',
            },
        'ListsUserSchema': {
            'type': 'object',
            'properties': {'pagination': {'$ref': '#/definitions/PaginationSchema_exclude_first_id_last_id_current_id'},
                           'item_nb': {'type': 'integer',
                           'minimum': 0}, 'items': {'type': 'array',
                           'items': {'$ref': '#/definitions/UserSchema_exclude_first_name_last_name_email_address'}}},
            'required': ['pagination', 'item_nb', 'items'],
            'description': 'A docstring to prevent auto generated docstring',
            },
        'AboutResponseSchema': {
            'type': 'object',
            'properties': {'version': {'type': 'string'},
                           'datetime': {'type': 'string',
                           'format': 'date-time'}},
            'required': ['version', 'datetime'],
            'description': 'A docstring to prevent auto generated docstring',
            },
        'UserSchema': {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'display_name': {'type': 'string'},
                'company': {'type': 'string'},
                'username': {'type': 'string', 'pattern': '[\\w-]+'},
                'email_address': {'type': 'string',
                                  'format': StringFormat.EMAIL},
                'id': {'type': 'integer', 'default': None},
                },
            'required': [
                'first_name',
                'last_name',
                'display_name',
                'company',
                'username',
                'email_address',
                'id',
                ],
            'description': 'A docstring to prevent auto generated docstring',
            },
        'NoContentSchema': {
            'type': 'object',
            'properties': {},
            'description': 'A docstring to prevent auto generated docstring',
        },
        },
    }
