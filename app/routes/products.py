from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Product, Category
from app.utils.decorators import role_required

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('', methods=['POST'])
@role_required('admin')
def create_product():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error" : "Request body is required"
        }), 400
    
    missing = [f for f in('category_id', 'name', 'price') if f not in data]
    if missing:
        return jsonify({
            "error" : f"Missing required fields: {', '.join(missing)}"
        }), 400
    
    name = str(data['name']).strip()
    if not name:
        return jsonify({
            "error": "Name cannot be empty"
        }), 400
    if db.session.get(Category, data['category_id']) is None:
        return jsonify({
            "error" : "category_id does not reference an existing category"
        }), 400
    
    if isinstance(data['price'], bool):
        return jsonify({"error": "Price must be a number"}), 400
    try:
        price = float(data['price'])
    except (TypeError, ValueError):
        return jsonify({"error" :"Price must be a number"}),400
    if price < 0:
        return jsonify({"error": "Price must be >= 0"}), 400


    stock = data.get('stock', 0)
    if not isinstance(stock, int) or isinstance(stock,bool) or stock < 0 :
        return jsonify({
            "error" :"Stock must be a non-negative integer"
        }), 400
    
    new_product = Product(
        category_id=data['category_id'],
        name=name,
        price=price,
        stock=stock,
        description=data.get('description'),
        is_active=bool(data.get('is_active', True))
    )
    
    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        "message": "Product created successfully",
        "data": new_product.to_dict()
    }), 201
    


@products_bp.route('', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    category_id = request.args.get('category_id', type=int)
    is_active = request.args.get('is_active')
    search = request.args.get('search')
    
    query = Product.query
    
    if category_id is not None: 
        query = query.filter_by(category_id=category_id)
    if is_active is not None:
        query = query.filter_by(is_active = is_active.lower() == 'true')
    if search :
        query = query.filter(Product.name.ilike(f"%{search}%"))
        
    pagination = query.order_by(Product.id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "message": "Products retrieved successfully",
        "data": [p.to_dict() for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages
        }
    }), 200

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    
    if product is None:
        return jsonify({
            "error" :"Product not found "
        }), 404
    
    return jsonify({
        "message" :"Product retrieved successfully",
        "data" :product.to_dict()
    }),200


@products_bp.route('/<int:product_id>', methods=['PUT'])
@role_required('admin')
def update_product(product_id):
    product = db.session.get(Product, product_id)
    
    if product is None:
        return jsonify({
            "error": "Product not found"
        }), 404
    
    data = request.get_json(silent=True)
    if not data :
        return jsonify({
            "error" :"Request body is required"
        }), 400 
    if 'category_id' in data and db.session.get(Category, data['category_id']) is None:
        return jsonify({
            "error" :"category_id does not reference an existing category"
        }), 400
    if 'name' in data and not str(data['name']).strip():
        return jsonify({"error": "Name cannot be empty"}), 400
    
    if 'price' in data :
        if isinstance(data['price'], bool):
            return jsonify({
                "error" : "price must be a number"
            }), 400
        try:
            price = float(data['price'])
        except(TypeError, ValueError):
            return jsonify({
                "error" : "price must be a number"
            }), 400
        if price < 0 :
            return jsonify({
                "error" : "price must be >= 0 "
            }), 400 
    if 'stock' in data :
        stock = data['stock']
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            return jsonify({"error": "Stock must be a non-negative integer"}), 400
    

    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'name' in data:
        product.name = str(data['name']).strip()
    if 'price' in data:
        product.price = price
    if 'stock' in data:
        product.stock = stock
    if 'description' in data:
        product.description = data['description']
    if 'is_active' in data:
        product.is_active = bool(data['is_active'])

    db.session.commit()

    return jsonify({
        "message": "Product updated successfully",
        "data": product.to_dict()
    }), 200

@products_bp.route('/<int:product_id>', methods=['DELETE'])
@role_required('admin')
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({
            "error" :"Product not found"
        }), 404
    if product.order_items:
        return jsonify({"error": "Cannot delete product with existing orders"}), 409

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Product deleted successfully"
    }), 200
    