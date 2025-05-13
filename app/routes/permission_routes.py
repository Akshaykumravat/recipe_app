import json
from flask import Blueprint, request, jsonify, render_template
from app.database.models import Permission
from extentions import db
from app.schemas.permission_schema import PermissionSchema
from app.utils import response, generate_access_token_and_refresh_token, send_verification_email, paginated_result, send_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime, timedelta

bp = Blueprint("permissions", __name__, url_prefix="/permissions")


@bp.route('/create-permission', methods=['POST'])
def create_permission():
    try:
        data = request.get_json()
        schema = PermissionSchema()

        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, err.messages)), 400
        
        if Permission.query.filter_by(name = validated_data.get('name')).first():
            return jsonify(response(False, "Permission already exists")), 400
        
        permission = Permission(**validated_data)
        db.session.add(permission)
        db.session.commit()

        Permission_data = schema.dump(permission)
        return jsonify(response(True, "Permission created successfully", Permission_data)), 201
    except Exception as e:
            return jsonify(response(False, "Something went wrong", error=str(e))), 500