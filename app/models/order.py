from app.extensions import db


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint('total_amount >= 0', name='orders_total_amount_check'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=False
    )
    status = db.Column(db.String(50), nullable=False, server_default='pending')
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, server_default=db.text('0'))
    created_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=db.func.now(), 
        onupdate=db.func.now()
    )

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict_with_items(self):
        data = self.to_dict()
        data["items"] = [item.to_dict_with_product() for item in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='order_items_quantity_check'),
        db.CheckConstraint('price >= 0', name='order_items_price_check'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, server_default=db.text('1'))
    price = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', backref='order_items', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": float(self.price),
            "subtotal": float(self.price) * self.quantity,
        }

    def to_dict_with_product(self):
        data = self.to_dict()
        data["product"] = self.product.to_dict() if self.product else None
        return data