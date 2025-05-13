from marshmallow import Schema, fields, validate, post_load

class RoleSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(max=50))
    description = fields.Str(required=True, validate=validate.Length(max=255))  