## Addtionals fields supported

Using marshmallow schema, you can add some extra field in field who are
automatically added into field description in schema.
```
        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                required=True,
                description='a description',
                example='00010',
                format='binary',
                enum=['01000', '11111'],
                maxLength=5,
                minLength=5,
            )
```

Not all field are fully supported now by Hapic.

## Supported Additional Fields in Hapic for query/path/body :

General types:

- format
- description
- enum
- example (example is converted at the end of description for query/path)

Number type:

- maximum
- exclusiveMaximum
- minimum
- exclusiveMinimum
- multipleOf

String type:

- maxLength
- minLength

Theses field are related to OpenApiv2 spec, see this :
https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#definitionsObject
