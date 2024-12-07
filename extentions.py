from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flask_mail import Mail

from app.utils import response
from flask import jsonify

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
jwt = JWTManager()
mail = Mail()

"""
Custom error handling for JWT
"""
@jwt.unauthorized_loader
def missing_token_response(error):
    return jsonify(response(False, "Token is missing or invalid", error=str(error))), 401


@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_data):
    return jsonify(response(False, "Token has expired", error="Authorization token has expired")), 401


@jwt.invalid_token_loader
def invalid_token_response(error):
    return jsonify(response(False, "Invalid token", error=str(error))), 401