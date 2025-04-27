from marshmallow import Schema, fields, validate, post_load


class CommentsSchema(Schema):
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(required=True, load_only=True)  
    recipe_id = fields.UUID(required=True, load_only=True)    
    Comment = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True) 
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (optional if you need nested data later)
    user = fields.Nested("UserSchema", dump_only=True) 
    recipe = fields.Nested("RecipeSchema", exclude=("author",), dump_only=True)