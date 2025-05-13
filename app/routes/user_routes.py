import json
import click
from flask.cli import with_appcontext
from flask import Blueprint, request, jsonify, render_template
from app.database.models import User, Favorites, Recipe, Role
from extentions import db
from app.schemas.schema import UserSchema, FavoritesSchema, ChangePasswordSchema, UpdateUserSchema, LoginSchema,VerifyEmailSchema, ResetPasswordSchema
from app.utils import response, generate_access_token_and_refresh_token, send_verification_email, paginated_result, send_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime, timedelta
from app.auth.auth_decorators import permission_required


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
        user_schema = UserSchema()
        
        try:
            validated_data = user_schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", err.messages)), 400

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
    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500


@bp.route("/verify-email", methods=['POST'])
def verify_email_address():
    """
    This Route will verify verification code and mark user as verified
    """
    try:
        data = request.get_json()
        schema = VerifyEmailSchema()

        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", error=err.messages)), 400

        user = User.query.filter_by(email=validated_data.get('email')).first()
        if not user:
            return jsonify(response(False, "user does not exist ")), 400

        if user.verification_code != validated_data.get('verification_code'):
            return jsonify(response(False, "Invalid verification code")), 400

        if datetime.utcnow() > user.verification_code_expiry:
            return jsonify(response(False, "Verification code expired")), 400

        user.is_verified = True
        db.session.commit()

        tokens = generate_access_token_and_refresh_token(user.user_id, user.email)
        user_tokens = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token')
        }

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
            send_email(
                subject="Verify Your Email Address",
                recipients=[user.email],
                template_name='verification_email.html',
                context={
                    'user': user,
                    'verification_code': user.verification_code,
                    'your_name': "Golden Recipe!!"
                }
            )

            return jsonify(response(True, "Verification code expired, new code sent to email")), 200
        else:
            return jsonify(response(False, "Verification code is still valid")), 400
    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e)))


@bp.route("/signin", methods=["POST"])
def login():
    try:
        data = request.get_json()
        schema = LoginSchema()
        
        try:
            validated_data = schema.load(data)
            print(validated_data, "validated_data")
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", error = err.messages)), 400
        
    
        user = User.query.filter_by(email=validated_data.get('email'), is_deleted = False, is_verified = True).first()
        if not user:
            return jsonify(response(False, "user does not exist")), 400

        if not user.is_verified:
            return jsonify(response(False, "user is not verified")), 400

        if not user.check_password(data.get('password')):
            return jsonify(response(False, "Invalid password")), 401

        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        tokens = generate_access_token_and_refresh_token(user.user_id, user.email)

        user_data['access_token'] = tokens.get('access_token')
        user_data['refresh_token'] = tokens.get('refresh_token')

        return jsonify(response(True, "login success", user_data)), 200
    except Exception as e:
        return jsonify(response(False, "somthing went wrong..!", error=str(e)))


@bp.route("/update-user", methods=["PATCH"])
@permission_required("update_user")
def update_user():
    try:
        user_data = json.loads(get_jwt_identity())
        id = user_data.get('user_id')
        data = request.form.to_dict()
        update_user_schema = UpdateUserSchema()
        

        try:
            validated_data = update_user_schema.load(data, partial=True)
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", err.messages)), 400


        user = User.query.filter_by(user_id=id, is_deleted=False).first()
        if not user:
            return jsonify(response(True, "user does not exist")), 400

        for field, value in validated_data.items():
            if field == 'profile_image' and value:
                # TODO: Upload image to S3 and get URL
                # uploaded_url = upload_to_s3(value)
                # setattr(user, field, uploaded_url)
                setattr(user, field, value)  # Placeholder
            else:
                setattr(user, field, value)
        user_schema = UserSchema()
        user_detail = user_schema.dump(user)
        db.session.commit()
        return jsonify(response(True, "user data updated", user_detail)), 201
    except Exception as e:
        return jsonify(response(False, "somthing went wrong.. ", error=str(e))), 500


@bp.route("/get-user", methods=["GET"])
@jwt_required()
def get_user():
    try:
        user_data = json.loads(get_jwt_identity())
        id = user_data.get('user_id')

        user = User.query.filter_by(user_id=id, is_verified = True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "user does not exist ")), 400

        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        return jsonify(response(True, "user retrived successfully", user_data))
    except Exception as e:
        return jsonify({"message": "somthing went wrong", "error": str(e)})


@bp.route("/delete-user", methods=['PATCH'])
@permission_required("delete_user")
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
    
        user = User.query.filter_by(user_id = user_id, is_verified = True, is_deleted = False).first()
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


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Handle forgot password request.
    Send a password reset link or OTP to user's email.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify(response(False, "Invalid input: No data provided")), 400

        email = data.get('email')
        if not email:
            return jsonify(response(False, "Email is required")), 400

        user = User.query.filter_by(email=email, is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found or not active")), 404

       
        reset_token = str(uuid.uuid4()) 
        print(reset_token, "reset_token") 
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30) 
        db.session.commit()

        reset_link = f"http://localhost:5000/users/reset-password?token={reset_token}"
        send_email(
            subject="Reset Your Password",
            recipients=[user.email],
            template_name="reset_password_email.html",
             context={
                    'user': user,
                    "reset_link": reset_link,
                    'app_name':  "Golden Recipe!!",
                    "current_year": datetime.utcnow().year
                }
        )
        return jsonify(response(True, "Password reset link has been sent to your email")), 200

    except SQLAlchemyError as db_err:
        db.session.rollback()
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500

    except Exception as e:
        print("error", str(e))
        return jsonify(response(False, "An unexpected error occurred", error=str(e))), 500


@bp.route("/api/reset-password", methods=["POST"])
def reset_password():
    """
    Reset the user's password using the reset token.
    """
    try:
        data = request.get_json()
        schema = ResetPasswordSchema()

        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", error=err.messages)), 400


        user = User.query.filter_by(reset_token=validated_data.get('token'), is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "Invalid or expired token")), 400

        if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
            return jsonify(response(False, "Reset token has expired")), 400

        user.hash_password(validated_data.get('new_password')) 
        user.reset_token = None 
        user.reset_token_expiry = None
        db.session.commit()

        return jsonify(response(True, "Password has been reset successfully")), 200

    except SQLAlchemyError as db_err:
        db.session.rollback()
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500

    except Exception as e:
        print("error", str(e))
        return jsonify(response(False, "An unexpected error occurred", error=str(e))), 500


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
    

@bp.route("/favorites", methods=["GET"])
@jwt_required()
def get_favorites():
    """
    Get all favorite recipes for the authenticated user.
    Requires a valid JWT token for authentication.
    """
    try:
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        user = User.query.filter_by(user_id=user_id, is_verified=True, is_deleted=False).first()
        if not user:
            return jsonify(response(False, "User not found or not active")), 404

        favorites = Favorites.query.filter_by(user_id=user_id).all()

        if not favorites:
            return jsonify(response(True, "No favorite recipes found", [])), 200

        schema = FavoritesSchema(many=True)
        favorites_data = schema.dump(favorites)

        return jsonify(response(True, "Favorite recipes fetched successfully", favorites_data)), 200

    except SQLAlchemyError as db_err:
        db.session.rollback()
        return jsonify(response(False, "Database error occurred", error=str(db_err))), 500

    except Exception as e:
        print("error", str(e))
        return jsonify(response(False, "An unexpected error occurred", error=str(e))), 500


@bp.route("/reset-password")
def reset_password_page():
    token = request.args.get('token')
    if not token:
        return "Invalid reset link", 400
    return render_template('reset-password.html', token=token)



@click.command("createadmin")
@with_appcontext
def create_admin():
    """Create an admin user with first name, last name, email, and password"""
    
    first_name = click.prompt("First Name")
    last_name = click.prompt("Last Name")
    email = click.prompt("Email")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    # Check or create 'admin' role
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()
        click.echo("Created 'admin' role.")

    # Check or create user
    user = User.query.filter_by(email=email).first()
    if user:
        click.echo("User already exists.")
    else:
        user = User(
            email = email,
            first_name = first_name,
            last_name = last_name,
            is_verified = True
        )
        user.hash_password(password) 
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin user '{email}' created.")