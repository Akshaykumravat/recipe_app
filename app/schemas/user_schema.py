from marshmallow import Schema, fields, validate, post_load



class UserSchema(Schema):
    user_id = fields.UUID(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(max=100))
    last_name = fields.Str(required=True, validate=validate.Length(max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    phone_number = fields.Str(validate=validate.Length(max=20))
    is_verified = fields.Bool()
    is_deleted = fields.Bool(dump_only=True)
    verification_code = fields.Str(load_only=True, validate=validate.Length(equal=6))
    verification_code_expiry = fields.DateTime(load_only=True)
    country = fields.Str(validate=validate.Length(max=20))
    profile_image = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
