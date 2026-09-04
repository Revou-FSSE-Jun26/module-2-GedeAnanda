from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate,jwt, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'],
                  supports_credentials=False)
    
    from app import models
    from app.models.token import TokenBlocklist
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None
    
    from app.routes.auth import auth_bp
    from app.routes.categories import categories_bp
    from app.routes.products import products_bp
    from app.routes.orders import orders_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
        
    @app.get('/')
    def index():
        return jsonify(service='revoshop-api', status='ok')

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    from app.utils.errors import register_error_handlers
    register_error_handlers(app)
    
    return app

