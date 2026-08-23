from app.extensions import db


class User(db.Model):
    __tablename__ = 'users'
    
    id =db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable = False )
    role = db.Column(db.String(20), nullable=False, server_default='customer')
    created_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=db.func.now(), 
        onupdate=db.func.now()
    )
    
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def to_dict(self) :
        return {
            "id" : self.id,
            "username": self.username,
            "email" : self.email, 
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    