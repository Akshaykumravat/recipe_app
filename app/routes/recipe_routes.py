import io
import pandas as pd
import json
from extentions import db
import app.messages as messages
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, request, jsonify,Response
from app.auth.auth_decorators import permission_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.models import User, Recipe, RecipeCategories
from app.utils import response, paginated_result, send_email, validate_schema
from app.schemas.schema import RecipeSchema, RecipeCategoryListSchema, RecipeCategorySchema
from app.db_driver import (get_record_by, 
                           update_record,
                           create_record,
                           delete_record,
                           get_all_records, 
                           create_multiple_records)

bp = Blueprint("recipes", __name__, url_prefix="/recipe")

@bp.route("/add-category", methods=["POST"])
@permission_required("create_category")
def create_categories():
    try:
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        data = request.get_json()
        is_valid, result = validate_schema(RecipeCategoryListSchema(), data)

        if not is_valid:
            return jsonify(response(message=messages.VALIDATION_FAILED, error=result)), 400
        
        user = get_record_by(User, user_id=user_id, is_verified=True, is_deleted=False)
        if not user:
            return jsonify(response(message=messages.USER_NOT_FOUND)), 404


        category_names = list(set(result['categories']))  
        categories_data = [{"category_name": name} for name in category_names]
        new_categories = create_multiple_records(RecipeCategories, categories_data)
        serialized = RecipeCategorySchema(many=True).dump(new_categories)

        return jsonify(response(True, messages.RECIPE_CATEGORIES_CREATED, serialized)), 201

    except Exception as e:
        return jsonify(response(message=messages.GENERIC_ERROR, error=str(e))), 500

    
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
            send_email(
                subject="Thank You for Sharing Your Recipe",
                recipients=[user.email],
                template_name='thankyou.html',
                context={
                    'user': user,
                    'recipe': new_recipe,
                    'app_name':  "Golden Recipe!!"
                }
            )

            recipe_data = schema.dump(new_recipe)
            return jsonify(response(True, "Recipe created successfully", recipe_data)), 201
        except Exception as e:
            db.session.rollback()
            return jsonify(response(False, "Failed to create recipe", error=str(e))), 500

    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500
    

@bp.route("/user", methods=["GET"])
@jwt_required()
# @permission_required("create_comment")
def get_recipes_by_user():
    try:
       
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if not user_id:
            return jsonify(response(False, "User ID not found in token")), 400
        
        user = User.query.filter_by(user_id = user_id, is_verified = True, is_deleted = False).first()
        if not user:
            return jsonify(response(False, "User not found or not verified")), 404
        
        # recipes = Recipe.query.filter_by(author_id=user_id).all()
        query = Recipe.query.filter_by(author_id = user_id)
        result = paginated_result(query, RecipeSchema, page, per_page)
        response_data = {
            'data': result['data'],
            'meta': result['pagination']
        }

        # schema = RecipeSchema(many=True)
        # recipe_data = schema.dump(recipes)

        return jsonify(response(True, "Recipes retrieved successfully", response_data)), 200

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
