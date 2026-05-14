from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.db import db
from app.models import Mistake
from app.utils import apply_mistake_json


api_bp = Blueprint("api", __name__, url_prefix="/api")


def require_auth():
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
    return None


def api_mistake_or_response(mistake_id):
    mistake = db.session.get(Mistake, mistake_id)
    if not mistake:
        return None, (jsonify({"error": "Mistake not found"}), 404)
    if mistake.user_id != current_user.id:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return mistake, None


@api_bp.route("/mistakes", methods=["GET"])
def list_api_mistakes():
    auth_response = require_auth()
    if auth_response:
        return auth_response
    mistakes = Mistake.query.filter_by(user_id=current_user.id).order_by(Mistake.created_at.desc()).all()
    return jsonify([mistake.to_dict() for mistake in mistakes])


@api_bp.route("/mistakes/<int:mistake_id>", methods=["GET"])
def get_api_mistake(mistake_id):
    auth_response = require_auth()
    if auth_response:
        return auth_response
    mistake, error = api_mistake_or_response(mistake_id)
    if error:
        return error
    return jsonify(mistake.to_dict())


@api_bp.route("/mistakes", methods=["POST"])
def create_api_mistake():
    auth_response = require_auth()
    if auth_response:
        return auth_response
    data = request.get_json(silent=True) or {}
    mistake = Mistake(user_id=current_user.id)
    error = apply_mistake_json(mistake, data, full_update=True)
    if error:
        db.session.rollback()
        return jsonify({"error": error}), 400
    db.session.add(mistake)
    db.session.commit()
    return jsonify(mistake.to_dict()), 201


@api_bp.route("/mistakes/<int:mistake_id>", methods=["PUT"])
def put_api_mistake(mistake_id):
    auth_response = require_auth()
    if auth_response:
        return auth_response
    mistake, error = api_mistake_or_response(mistake_id)
    if error:
        return error
    data = request.get_json(silent=True) or {}
    error = apply_mistake_json(mistake, data, full_update=True)
    if error:
        db.session.rollback()
        return jsonify({"error": error}), 400
    db.session.commit()
    return jsonify(mistake.to_dict())


@api_bp.route("/mistakes/<int:mistake_id>", methods=["PATCH"])
def patch_api_mistake(mistake_id):
    auth_response = require_auth()
    if auth_response:
        return auth_response
    mistake, error = api_mistake_or_response(mistake_id)
    if error:
        return error
    data = request.get_json(silent=True) or {}
    error = apply_mistake_json(mistake, data, full_update=False)
    if error:
        db.session.rollback()
        return jsonify({"error": error}), 400
    db.session.commit()
    return jsonify(mistake.to_dict())


@api_bp.route("/mistakes/<int:mistake_id>", methods=["DELETE"])
def delete_api_mistake(mistake_id):
    auth_response = require_auth()
    if auth_response:
        return auth_response
    mistake, error = api_mistake_or_response(mistake_id)
    if error:
        return error
    db.session.delete(mistake)
    db.session.commit()
    return jsonify({"message": "Mistake deleted"})
