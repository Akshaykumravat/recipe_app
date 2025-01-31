import json
from flask import Blueprint, request, jsonify
from app.database.models import User, Favorites, Recipe
from extentions import db
from app.schemas.schema import UserSchema, FavoritesSchema, ChangePasswordSchema
from app.utils import response, is_valid_email, generate_access_token_and_refresh_token, send_verification_email, paginated_result
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError




bp = Blueprint("users", __name__, url_prefix="/users")


@bp.route("/singup", methods=["POST"])
def create_user():
    """
        This route creates a new user.

        Expected payload:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePassword123"
        }
    """
    try:
        data = request.get_json()
        # print(data)
        user_schema = UserSchema()
        validated_data = user_schema.load(data)
        # print(validated_data)

        if User.query.filter_by(email=data.get('email')).first():
            return jsonify(response(False, "email already exist")), 400

        try:
            user = User(**validated_data)
            user.hash_password(data.get('password'))
            user.set_verification_code()
            db.session.add(user)
            db.session.commit()

            send_verification_email(user)

            user_data = user_schema.dump(user)
            return jsonify(
                response(True, "User registration successful, verification code sent to email", user_data)), 201
        except Exception as e:
            db.session.rollback()
            return jsonify(response(False, "registration failed", error=str(e)))
    except ValidationError as ve:
        return jsonify(response(False, "Validation failed", error=ve.messages)), 400
    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500


@bp.route("/verify-email", methods=['POST'])
def verify_email_address():
    """
    This Route will verify verification code and mark user as verified
    """
    try:
        data = request.get_json()
        required_fields = ["email", "verification_code"]
        for field in required_fields:
            if field not in data:
                return jsonify(response(False, f"{field} is required", )), 400

        user = User.query.filter_by(email=data.get('email')).first()

        if not user:
            return jsonify(response(False, "user does not exist ")), 400

        if user.verification_code != data.get('verification_code'):
            return jsonify(response(False, "Invalid verification code")), 400

        if datetime.utcnow() > user.verification_code_expiry:
            return jsonify(response(False, "Verification code expired")), 400

        user.is_verified = True
        db.session.commit()

        tokens = generate_access_token_and_refresh_token(user.user_id, user.email)
        # print(tokens, "tokens")
        user_tokens = {}
        user_tokens['access_token'] = tokens.get('access_token')
        user_tokens['refresh_token'] = tokens.get('refresh_token')

        return jsonify(response(True, "Email verified successfully", user_tokens)), 200

    except Exception as e:
        return jsonify(response(False, "somthing went wrong.. ", error=str(e)))


@bp.route("/resend-verification-code", methods=["POST"])
def resend_verification_code():
    """
    This route regenerates and sends a new verification code if the previous one has expired.

    Expected payload:
    {
        "email": "john.doe@example.com"
    }
    """
    try:
        data = request.get_json()
        if not data.get('email'):
            return jsonify(response(False, "Email is required")), 400

        user = User.query.filter_by(email=data.get('email')).first()
        if not user:
            return jsonify(response(False, "User not found")), 404

        if datetime.utcnow() > user.verification_code_expiry:
            user.reset_verification_code()
            send_verification_email(user)
            return jsonify(response(True, "Verification code expired, new code sent to email")), 200
        else:
            return jsonify(response(False, "Verification code is still valid")), 400
    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e)))


@bp.route("/signin", methods=["POST"])
def login():
    try:
        data = request.get_json()
        required_field = ["email", "password"]
        for field in required_field:
            if field not in data:
                return jsonify(response(False, f"{field} is required", )), 400

        if not is_valid_email(data.get('email')):
            return jsonify(response(False, "invalid email address")), 400

        user = User.query.filter_by(email=data.get('email'), is_deleted = False).first()
        if not user:
            return jsonify(response(True, "user does not exist")), 400

        if not user.is_verified:
            return jsonify(response(True, "user is not verified")), 400

        if not user.check_password(data.get('password')):
            return jsonify(response(False, "Invalid password")), 401

        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        tokens = generate_access_token_and_refresh_token(user.user_id, user.email)
        print(tokens, "tokens")
        user_data['access_token'] = tokens.get('access_token')
        user_data['refresh_token'] = tokens.get('refresh_token')

        return jsonify(response(True, "login success", user_data)), 201
    except Exception as e:
        return jsonify(response(False, "somthing went wrong.. ", error=str(e)))


@bp.route("/update-user", methods=["PATCH"])
@jwt_required()
def update_user():
    try:
        user_data = json.loads(get_jwt_identity())
        id = user_data.get('user_id')
        data = request.get_json()
        profile_image = data.get('profile_image')
        if profile_image:
            # upload image to s3 bucket
            pass

        user = User.query.filter_by(user_id=id, is_deleted=False).first()
        if not user:
            return jsonify(response(True, "user does not exist")), 400

        user.phone_number = data.get('phone_number', None)
        user.country = data.get('country', None)
        user_schema = UserSchema()
        user_detail = user_schema.dump(user)
        db.session.commit()
        return jsonify(response(True, "user data updated", user_detail)), 201
    except Exception as e:
        return jsonify(response(False, "somthing went wrong.. ", error=str(e)))


@bp.route("/get-user", methods=["GET"])
@jwt_required()
def get_user():
    try:
        user_data = json.loads(get_jwt_identity())
        id = user_data.get('user_id')
        user = User.query.filter_by(user_id=id, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "user does not exist ")), 400

        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        return jsonify(response(True, "user retrived successfully", user_data))
    except Exception as e:
        return jsonify({"message": "somthing went wrong", "error": str(e)})


@bp.route("/delete-user", methods=['PATCH'])
@jwt_required()
def delete_user():
    try:
        user_data = json.loads(get_jwt_identity())
        id = user_data.get('user_id')
        user = User.query.filter_by(user_id=id).first()
        if not user:
            return jsonify(response(True, "user does not exist")), 400

        user.is_deleted = True
        db.session.commit()
        return jsonify(response(True, "user deleted success")), 201
    except Exception as e:
        return jsonify(response(False, "somthing went wrong.. ", error=str(e)))
    

@bp.route("/get-all-user", methods=["GET"])
@jwt_required()
def get_all_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        query = User.query.filter_by(is_deleted = False)
        result = paginated_result(query, UserSchema, page, per_page)
        response_data = {
            'data': result['data'],
            'meta': result['pagination']
        }
        return jsonify(response(True, "Success", response_data)), 200
    except Exception as e:
         return jsonify(response(False, "Something went wrong", error=str(e))), 500


@bp.route("/update-password", methods=["POST"])
@jwt_required()
def change_password():
    """
    Endpoint to allow a user to change their password.
    Requires a valid JWT token for authentication.
    """
    try:
        user_data = json.loads(get_jwt_identity())
        user_id  = user_data.get('user_id')
        data =  request.get_json()
        schema = ChangePasswordSchema()

        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", err.messages)), 400
    
        user = User.query.filter_by(user_id = user_id, is_verified = True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found")), 404
        

        if not user.check_password(validated_data['old_password']):
            return jsonify(response(False, "Invalid current password")), 401
        
        user.hash_password(data.get('new_password'))
        db.session.commit()

        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        return jsonify(response(True, "password updated success", user_data)), 200
    except SQLAlchemyError as db_err:
        db.session.rollback()
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500
    except Exception as e:
        return jsonify(response(False, "Something went wrong..", error=str(e))), 500


@bp.route("/add-to-favorite", methods=["POST"])
@jwt_required()
def add_to_favorite():
    """
    Add a recipe to the user's favorites.
    Requires a valid JWT token for authentication.
    """
    try:
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        data = request.get_json()
        if not data:
            return jsonify(response(False, "Invalid input: No data provided")), 400

        schema = FavoritesSchema()

        user = User.query.filter_by(user_id=user_id, is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found or not active")), 404

        try:
            validated_data = schema.load({**data, "user_id": user_id})
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", err.messages)), 400

        recipe = Recipe.query.filter_by(recipe_id=data.get('recipe_id')).first()
        if not recipe:
            return jsonify(response(False, "Recipe not found")), 404

        favorite_existing = Favorites.query.filter_by(recipe_id=data.get('recipe_id'), user_id=user_id).first()
        if favorite_existing:
            return jsonify(response(False, "Recipe already added to favorites")), 409

        favorites = Favorites(**validated_data)
        db.session.add(favorites)
        db.session.commit()

        favorite_data = schema.dump(favorites)
        return jsonify(response(True, "Recipe added to favorites successfully", favorite_data)), 200

    except SQLAlchemyError as db_err:
        db.session.rollback()
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500

    except Exception as e:
        print("error", str(e))
        return jsonify(response(False, "An unexpected error occurred", error=str(e))), 500