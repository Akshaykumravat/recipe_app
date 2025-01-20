import json
from flask import Blueprint, request, jsonify,Response
from app.database.models import User, Recipe
from extentions import db
from app.schemas.schema import RecipeSchema
from app.utils import response, thank_you_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import io


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


@bp.route("/download-recipes", methods=["GET"])
@jwt_required()
def download_recipes():
    """
    Download recipe data in Excel or CSV format.
    Requires a valid JWT token for authentication.
    """
    try:
        file_format = request.args.get('format', 'csv').lower()
        if file_format not in ['csv', 'excel']:
            return jsonify(response(False, "Invalid format. Use 'csv' or 'excel'")), 400

        recipes = Recipe.query.all()
        if not recipes:
            return jsonify(response(False, "No recipes found")), 404

        recipe_data = [{
            "recipe_id": recipe.recipe_id,
            "author_id": recipe.author_id,
            "title" : recipe.title,
            "description": recipe.description,
            "content" : recipe.content,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at
        } for recipe in recipes]
        df = pd.DataFrame(recipe_data)

        if file_format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return Response(
                output,
                mimetype='text/csv',
                headers={"Content-Disposition": "attachment;filename=recipes.csv"}
            )
        elif file_format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Recipes')
            output.seek(0)
            return Response(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-Disposition": "attachment;filename=recipes.xlsx"}
            )

    except SQLAlchemyError as db_err:
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500

    except Exception as e:
        print("Error:", str(e))
        return jsonify(response(False, "An unexpected error occurred", error=str(e))), 500
