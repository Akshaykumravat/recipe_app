from marshmallow import Schema, fields, validate, post_load

class RoleSchema(Schema):
    role_id = fields.UUID(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(max=50))
    description = fields.Str(required=True, validate=validate.Length(max=255))  