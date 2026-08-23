from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import HTTPException
from app.extensions import db


def register_error_handlers(app):

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        db.session.rollback()
        app.logger.warning(f"IntegrityError: {err}")
        return jsonify({"error": "Data conflicts with existing records or constraints"}), 409

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(err):
        db.session.rollback()
        app.logger.error(f"Database error: {err}", exc_info=True)
        return jsonify({"error": "A database error occurred"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        app.logger.error(f"Unhandled exception: {err}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500