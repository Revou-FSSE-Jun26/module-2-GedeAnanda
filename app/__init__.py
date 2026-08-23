from flask import Flask
from app.config import Config
from app.extensions import db, migrate,jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app import models
    from app.models.token import TokenBlocklist
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None
    
    from app.routes.auth import auth_bp
    from app.routes.categories import categories_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)
    
    return app

