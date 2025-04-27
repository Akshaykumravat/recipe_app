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

class UpdateUserSchema(Schema):
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    phone_number = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(validate=validate.Length(max=20))
    profile_image = fields.Str()


class ChangePasswordSchema(Schema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=lambda x: len(x) >= 8,)


class RecipeSchema(Schema):
    recipe_id = fields.UUID(dump_only=True)  
    title = fields.Str(required=True, validate=validate.Length(max=255))  
    description = fields.Str(allow_none=True) 
    content = fields.Str(required=True) 
    author_id = fields.UUID(required=True, load_only=True)  
    created_at = fields.DateTime(dump_only=True) 
    updated_at = fields.DateTime(dump_only=True)  

    # Relationships (optional if you need nested data later)
    author = fields.Nested("UserSchema", dump_only=True) 

class FavoritesSchema(Schema):
    id = fields.UUID(dump_only=True)  
    recipe_id = fields.UUID(required=True, load_only=True)
    user_id = fields.UUID(required=True, load_only=True)  
    created_at = fields.DateTime(dump_only=True) 
    updated_at = fields.DateTime(dump_only=True)  

    # Relationships (optional if you need nested data later)
    user = fields.Nested("UserSchema", dump_only=True) 
    recipe = fields.Nested("RecipeSchema", exclude=("author",), dump_only=True)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

class VerifyEmailSchema(Schema):
    email = fields.Email(required=True)
    verification_code = fields.Str(required=True, validate=validate.Length(equal=6))

class ResetPasswordSchema(Schema):
    token = fields.Str(required=True, validate=validate.Length(min=36, max=36)) 
    new_password = fields.Str(required=True, validate=validate.Length(min=8)) 