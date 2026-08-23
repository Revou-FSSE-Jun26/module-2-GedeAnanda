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
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({
            "error": "username, email, and password are required"
        }), 400
    
    if len(data['password']) < 8 :
        return jsonify({
            "error" : "password must be at least 8 characters"
        }), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            "error" : "Email already registered"
        }), 409
    
    new_user = User(
        username = data['username'], 
        email = data['email'],
        password_hash = generate_password_hash(data['password'])
    )

    db.session.add(new_user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(new_user.id), additional_claims={"role":new_user.role})
    refresh_token = create_refresh_token(identity=str(new_user.id))
    
    return jsonify({
        "user":new_user.to_dict(),
        "access_token" : access_token,
        "refresh_token" : refresh_token
    }), 201
    

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "email and password are required"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password'] ):
        return jsonify({
            "error" : "Invalid email or password"
        }), 401
    
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200
    

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    
    if not user:
        return jsonify({
            "error" : "User not found"
        }), 404

    access_token = create_access_token(identity=identity, additional_claims={"role": user.role})
    return jsonify({
        "access_token" : access_token
    }), 200 
    

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    return jsonify({"message": "Successfully logged out"}), 200

    
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    
    if not user: 
        return jsonify({
            "error" : "User not found"
        }), 404
    return jsonify(
        user.to_dict()
    ),200