from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.extensions import db
from app.models import Order, OrderItem, Product

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

VALID_STATUSES = ('pending', 'paid', 'shipped', 'completed', 'cancelled')


def _current_user_id():
    return int(get_jwt_identity())


def _is_admin():
    return get_jwt().get('role') == 'admin'


@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    items = data.get('items')
    if not isinstance(items, list) or not items:
        return jsonify({"error": "items must be a non-empty list"}), 400

    requested = {}
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Each item must be an object"}), 400

        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        if not isinstance(product_id, int) or isinstance(product_id, bool):
            return jsonify({"error": "product_id must be an integer"}), 400
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            return jsonify({"error": "quantity must be a positive integer"}), 400

        requested[product_id] = requested.get(product_id, 0) + quantity

    products = Product.query.filter(
        Product.id.in_(requested.keys())
    ).with_for_update().all()
    product_map = {p.id: p for p in products}

    missing = [pid for pid in requested if pid not in product_map]
    if missing:
        db.session.rollback()
        return jsonify({
            "error": f"Product not found: {', '.join(str(p) for p in missing)}"
        }), 404


    for product_id, quantity in requested.items():
        product = product_map[product_id]
        if not product.is_active:
            db.session.rollback()
            return jsonify({"error": f"Product '{product.name}' is not available"}), 409
        if product.stock < quantity:
            db.session.rollback()
            return jsonify({
                "error": f"Insufficient stock for '{product.name}': requested {quantity}, available {product.stock}"
            }), 409

    order = Order(user_id=_current_user_id(), status='pending', total_amount=0)
    db.session.add(order)
    db.session.flush() 

    total = 0
    for product_id, quantity in requested.items():
        product = product_map[product_id]
        price = product.price

        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=price
        ))

        product.stock -= quantity
        total += float(price) * quantity

    order.total_amount = total
    db.session.commit()

    return jsonify({
        "message": "Order created successfully",
        "data": order.to_dict_with_items()
    }), 201


@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')

    query = Order.query

    if not _is_admin():
        query = query.filter_by(user_id=_current_user_id())

    if status:
        if status not in VALID_STATUSES:
            return jsonify({
                "error": f"status must be one of: {', '.join(VALID_STATUSES)}"
            }), 400
        query = query.filter_by(status=status)

    pagination = query.order_by(Order.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "message": "Orders retrieved successfully",
        "data": [o.to_dict() for o in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages
        }
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    if order.user_id != _current_user_id() and not _is_admin():
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "message": "Order retrieved successfully",
        "data": order.to_dict_with_items()
    }), 200


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    if not _is_admin():
        return jsonify({"error": "Forbidden: insufficient permissions"}), 403

    data = request.get_json(silent=True)
    if not data or not data.get('status'):
        return jsonify({"error": "status is required"}), 400

    status = str(data['status']).strip().lower()
    if status not in VALID_STATUSES:
        return jsonify({
            "error": f"status must be one of: {', '.join(VALID_STATUSES)}"
        }), 400

    order.status = status
    db.session.commit()

    return jsonify({
        "message": "Order status updated successfully",
        "data": order.to_dict()
    }), 200


@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    if order.user_id != _current_user_id() and not _is_admin():
        return jsonify({"error": "Order not found"}), 404

    if order.status == 'cancelled':
        return jsonify({"error": "Order is already cancelled"}), 409

    if order.status != 'pending':
        return jsonify({
            "error": f"Cannot cancel an order with status '{order.status}'"
        }), 409

    product_ids = {item.product_id for item in order.items}

    if product_ids:
        Product.query.filter(Product.id.in_(product_ids)).with_for_update().all()

        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

    order.status = 'cancelled'
    db.session.commit()

    return jsonify({
        "message": "Order cancelled successfully",
        "data": order.to_dict_with_items()
    }), 200