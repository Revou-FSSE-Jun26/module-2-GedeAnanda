from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from app.extensions import db
from app.models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = str(data.get('username', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email, and password are required"
        }), 400

    if not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "error": "Email is already registered"
        }), 409

    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id), additional_claims={"role": new_user.role})
    refresh_token = create_refresh_token(identity=str(new_user.id))

    return jsonify({
        "message": "User registered successfully",
        "data": {
            "user": new_user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    email = str(data.get('email', '')).strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "data": {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    access_token = create_access_token(identity=identity, additional_claims={"role": user.role})

    return jsonify({
        "message": "Access token refreshed successfully",
        "data": {
            "access_token": access_token
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()

    return jsonify({
        "message": "Logged out successfully"
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "message": "User retrieved successfully",
        "data": user.to_dict()
    }), 200