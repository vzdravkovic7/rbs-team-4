import sqlite3

from flask import Blueprint, jsonify, request

from audit import audit
from models.user import authenticate_user, create_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if len(username) < 3 or len(password) < 8:
        return jsonify({"error": "Username must have 3+ chars and password 8+ chars"}), 400

    try:
        user = create_user(username, password)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

    audit("user_registered", user_id=user["id"], username=username)
    return jsonify({"username": username, "api_token": user["api_token"]}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    user = authenticate_user(username, password)
    if not user:
        audit("login_failed", username=username)
        return jsonify({"error": "Invalid username or password"}), 401

    audit("login_success", user_id=user["id"], username=username)
    return jsonify({"username": username, "api_token": user["api_token"]})
