from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload

from app.models import Category, db
from app.utils.decorators import roles_required

category_bp = Blueprint("category_bp", __name__)


def build_tree(nodes):
    """Convert flat Category rows into nested tree for frontend"""
    id_to_node = {c.id: {**c.__dict__, "children": []} for c in nodes}
    roots = []
    for c in nodes:
        node = id_to_node[c.id]
        node.pop("_sa_instance_state", None)
        if c.parent_id:
            parent = id_to_node.get(c.parent_id)
            if parent:
                parent["children"].append(node)
            else:
                roots.append(node)
        else:
            roots.append(node)

    # sort by sort_order
    def sort_fn(cat):
        return cat.get("sort_order", 0)

    def sort_tree(lst):
        lst.sort(key=sort_fn)
        for n in lst:
            sort_tree(n["children"])

    sort_tree(roots)
    return roots


@category_bp.route("/categories", methods=["GET"])
@jwt_required()
@roles_required(["manager", "cashier", "courier"])
def get_categories():
    cats = Category.query.order_by(Category.sort_order).all()
    tree = build_tree(cats)
    return jsonify(tree), 200


@category_bp.route("/categories", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def create_category():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"message": "Name is required"}), 400
    if Category.query.filter_by(parent_id=data.get("parent_id"), name=name).first():
        return jsonify({"message": "Category name already exists at this level"}), 409
    cat = Category(  # type: ignore
        name=name, sort_order=data.get("sort_order", 0), parent_id=data.get("parent_id")
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id}), 201


@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if name:
        dup = Category.query.filter_by(
            parent_id=data.get("parent_id", cat.parent_id), name=name
        ).first()
        if dup and dup.id != cat.id:
            return (
                jsonify({"message": "Category name already exists at this level"}),
                409,
            )
        cat.name = name
    if "sort_order" in data:
        cat.sort_order = data["sort_order"]
    if "parent_id" in data:
        cat.parent_id = data["parent_id"]
    db.session.commit()
    return jsonify({"message": "updated"}), 200


@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@jwt_required()
@roles_required(["manager"])
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.children.count():
        return (
            jsonify({"message": "Category has subcategories; delete them first"}),
            400,
        )
    if cat.menu_items.count():
        return (
            jsonify(
                {"message": "Category has menu items; reassign or delete them first"}
            ),
            400,
        )
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
