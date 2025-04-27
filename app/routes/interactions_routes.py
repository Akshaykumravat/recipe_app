import json
from flask import Blueprint, request, jsonify, render_template
from app.database.models import User, Favorites, Comments
from extentions import db
from app.schemas.interactions_schema import CommentsSchema
from app.utils import response, is_valid_email, generate_access_token_and_refresh_token, send_verification_email, paginated_result, send_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime, timedelta

bp = Blueprint("interactions", __name__, url_prefix="/interactions")

@bp.route("/comments", methods=["POST"])
@jwt_required()
def create_comment():
    schema = CommentsSchema()
    
    try:
        data = request.get_json()
        user_data = json.loads(get_jwt_identity())
        user_id = user_data.get('user_id')

        # Validate incoming data
        try:
            validated_data = schema.load({**data, "user_id": user_id})
        except ValidationError as err:
            return jsonify(response(False, "Validation failed", error=err.messages)), 400

        # Check user existence
        user = User.query.filter_by(user_id=user_id, is_deleted=False, is_verified=True).first()
        if not user:
            return jsonify(response(False, "User does not exist")), 400

        # Create comment
        try:
            comment = Comments(**validated_data)
            db.session.add(comment)
            db.session.commit()
            
            comment_data = schema.dump(comment)
            return jsonify(response(True, "Comment created successfully", comment_data)), 201

        except Exception as e:
            db.session.rollback()
            return jsonify(response(False, "Comment creation failed", error=str(e))), 500

    except Exception as e:
        return jsonify(response(False, "Something went wrong", error=str(e))), 500
