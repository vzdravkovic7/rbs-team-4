from functools import wraps

from flask import jsonify, request

from models.user import get_user_by_token


def auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()

        if not token:
            return jsonify({"error": "Missing bearer token"}), 401

        user = get_user_by_token(token)
        if not user:
            return jsonify({"error": "Invalid bearer token"}), 401

        return view(user, *args, **kwargs)

    return wrapper
