
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from ..models import User
from ..extensions import db
import re

auth_bp = Blueprint("auth", __name__)


def validate_email(email):
    if not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.fullmatch(pattern, email.strip()) is not None


def validate_password(password):
    return isinstance(password, str) and len(password) >= 8


def get_json_data():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Please provide valid JSON data"}), 400

    required = ["email", "password", "first_name", "last_name"]

    for field in required:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return jsonify({"error": f"{field} is required"}), 400

    email = data["email"].strip().lower()
    password = data["password"]
    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()

    if not validate_email(email):
        return jsonify({"error": "Invalid email address"}), 400

    if not validate_password(password):
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    phone = data.get("phone", "")
    if phone is not None and not isinstance(phone, str):
        return jsonify({"error": "Phone must be text"}), 400

    account_mode = data.get("account_mode", "individual")
    if account_mode not in ("individual", "family"):
        return jsonify({"error": "Invalid account mode"}), 400

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone.strip() if phone else None,
        account_mode=account_mode,
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            "message": "Registration successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }), 201

    except Exception:
        db.session.rollback()
        raise


@auth_bp.route("/login", methods=["POST"])
def login():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Please provide valid JSON data"}), 400

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400

    email = email.strip().lower()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(
        email=email,
        is_active=True
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(user_id))

    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user ID"}), 401

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user ID"}), 401

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"error": "User not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Please provide valid JSON data"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return jsonify({"error": "Both passwords must be text"}), 400

    if not current_password or not new_password:
        return jsonify({
            "error": "Current password and new password are required"
        }), 400

    if not user.check_password(current_password):
        return jsonify({
            "error": "Current password is incorrect"
        }), 400

    if not validate_password(new_password):
        return jsonify({
            "error": "New password must be at least 8 characters"
        }), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200
