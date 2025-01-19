import json
from flask import Blueprint, request, jsonify
from app.database.models import User, Recipe
from extentions import db
from app.schemas.schema import RecipeSchema
from app.utils import response, thank_you_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError



bp = Blueprint("recipes", __name__, url_prefix="/recipe")

@bp.route("/add-recipe", methods=["POST"])
@jwt_required()
def create_recipe():
    try:
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        data = request.get_json()
        schema = RecipeSchema()

        user = User.query.filter_by(user_id=user_id, is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found")), 404

        try:
            validated_data = schema.load({**data, "author_id": user_id})
        except ValidationError as err:
            return jsonify(response(False, err.messages)), 400

        try:
            new_recipe = Recipe(**validated_data)
            db.session.add(new_recipe)
            db.session.commit()
            thank_you_email(user_data, new_recipe)
            recipe_data = schema.dump(new_recipe)
            return jsonify(response(True, "Recipe created successfully", recipe_data)), 201
        except Exception as e:
            db.session.rollback()
            return jsonify(response(False, "Failed to create recipe", error=str(e))), 500

    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500
    

@bp.route("/user", methods=["GET"])
@jwt_required()
def get_recipes_by_user():
    try:
       
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        if not user_id:
            return jsonify(response(False, "User ID not found in token")), 400
        
        user = User.query.filter_by(user_id=user_id, is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found or not verified")), 404
        
        recipes = Recipe.query.filter_by(author_id=user_id).all()

        schema = RecipeSchema(many=True)
        recipe_data = schema.dump(recipes)

        return jsonify(response(True, "Recipes retrieved successfully", recipe_data)), 200

    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500
