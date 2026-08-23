from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Category
from app.utils.decorators import role_required

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')


@categories_bp.route('', methods=['POST'])
@role_required('admin')
def create_category():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = str(data.get('name', '')).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    new_category = Category(
        name=name,
        description=data.get('description')
    )
    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        "message": "Category created successfully",
        "data": new_category.to_dict()
    }), 201


@categories_bp.route('', methods=['GET'])
def get_categories():
    categories = Category.query.order_by(Category.id).all()

    return jsonify({
        "message": "Categories retrieved successfully",
        "data": [c.to_dict() for c in categories]
    }), 200


@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category =  Category.query.get(category_id)
    if category is None:
        return jsonify({
            "error" : "Category not found"
        }), 404
    
    result = category.to_dict()
    result['products'] = [p.to_dict() for p in category.products]
    
    return jsonify({
        "message" : "Category retrieved successfully",
        "data" : result
    }),200
    

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@role_required('admin')
def update_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        return jsonify({
            "error" : "Category not found"
        }),404
        
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error" : "Request body is required"
        }),400
    
    name = str(data.get('name', '')).strip()
    if not name:
        return jsonify({
            "error" : "Name is required"
        }), 400
    
    category.name = name
    category.description = data.get('description', category.description)
    db.session.commit()
    
    return jsonify({
        "message": "Category updated successfully", 
        "data" : category.to_dict()
    }), 200
    

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@role_required('admin')
def delete_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        return jsonify({
            "error" : "Category not found"
        }),404
    
    if category.products:
        return jsonify({
            "error" : "Cannot delete category with existing products"
        }), 409
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({
        "message" : "Category deleted successfully"
    }),200
    