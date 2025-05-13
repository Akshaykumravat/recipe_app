import json
from flask import Blueprint, request, jsonify, render_template
from app.database.models import User, Role, Permission
from extentions import db
from app.schemas.role_schema import RoleSchema
from app.utils import response, generate_access_token_and_refresh_token, send_verification_email, paginated_result, send_email
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime, timedelta


bp = Blueprint("roles", __name__, url_prefix="/roles")

@bp.route('/create-role', methods=['POST'])
def create_role():
    try:
        data = request.get_json()
        schema = RoleSchema()

        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(response(False, err.messages)), 400
        
        if Role.query.filter_by(name = validated_data.get('name')).first():
            return jsonify(response(False, "Role already exists")), 400
        
        role = Role(**validated_data)
        db.session.add(role)
        db.session.commit()

        role_data = schema.dump(role)
        return jsonify(response(True, "Role created successfully", role_data)), 201
    except Exception as e:
            return jsonify(response(False, "Something went wrong", error=str(e))), 500



@bp.route('/roles/<role_id>/assign-permissions', methods=['POST'])
def assign_permissions_to_role(role_id):
    data = request.get_json()
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Role not found"}), 404

    for perm_id in data.get('permission_ids', []):
        perm = Permission.query.get(perm_id)
        if perm and perm not in role.permissions:
            role.permissions.append(perm)

    db.session.commit()
    return jsonify({"message": "Permissions assigned to role"}), 200

@bp.route('/users/<user_id>/assign-roles', methods=['POST'])
def assign_roles_to_user(user_id):
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    for role_id in data.get('role_ids', []):
        role = Role.query.get(role_id)
        if role and role not in user.roles:
            user.roles.append(role)

    db.session.commit()
    return jsonify({"message": "Roles assigned to user"}), 200
