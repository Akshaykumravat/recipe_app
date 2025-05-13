import json
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.models import User
from app.utils import response

def get_current_user():
    user_data = json.loads(get_jwt_identity())
    user_id = user_data.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()                     
        def wrapper(*args, **kwargs):
            user = get_current_user()
            print(user, "user")
            if not user:
                return jsonify(response(False, "Unauthorized")), 401

            # admins always pass
            if user.has_role('admin'):
                return fn(*args, **kwargs)

            if not user.has_permission(permission_name):
                return jsonify(response(False, "missing permission")), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
