from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.extensions import db
from app.models import User
from app.utils.decorators import role_required

users_bp = Blueprint('users', __name__, url_prefix='/users')

ALLOWED_ROLES = ('customer', 'admin')


@users_bp.route('', methods=['GET'])
@role_required('admin')
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    role = request.args.get('role')
    search = request.args.get('search')

    query = User.query

    if role:
        query = query.filter_by(role=role)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(User.username.ilike(pattern), User.email.ilike(pattern))
        )

    pagination = query.order_by(User.id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "message": "Users retrieved successfully",
        "data": [u.to_dict() for u in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages
        }
    }), 200


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    is_admin = get_jwt().get("role") == "admin"
    is_self = get_jwt_identity() == str(user_id)

    if not is_admin and not is_self:
        return jsonify({"error": "Forbidden: insufficient permissions"}), 403

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if 'username' in data:
        username = str(data['username']).strip()
        if not username:
            return jsonify({"error": "Username cannot be empty"}), 400

    if 'email' in data:
        email = str(data['email']).strip().lower()
        if not email:
            return jsonify({"error": "Email cannot be empty"}), 400
        existing = User.query.filter_by(email=email).first()
        if existing is not None and existing.id != user.id:
            return jsonify({"error": "Email is already registered"}), 409

    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

    if 'role' in data:
        if not is_admin:
            return jsonify({"error": "Forbidden: only admins can change roles"}), 403
        if data['role'] not in ALLOWED_ROLES:
            return jsonify({
                "error": f"Role must be one of: {', '.join(ALLOWED_ROLES)}"
            }), 400

    if 'username' in data:
        user.username = username
    if 'email' in data:
        user.email = email
    if 'password' in data:
        user.password_hash = generate_password_hash(password)
    if 'role' in data:
        user.role = data['role']

    db.session.commit()

    return jsonify({
        "message": "User updated successfully",
        "data": user.to_dict()
    }), 200
