from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Unit, User, UserRole
from app.utils.decorators import roles_required
from app.schemas import UnitSchema

unit_bp = Blueprint('unit', __name__, url_prefix='/api/v1/units')
unit_schema = UnitSchema()
units_schema = UnitSchema(many=True)

@unit_bp.route('/', methods=['GET'])
@jwt_required()
@roles_required('manager', 'cashier', 'barista')
def get_units():
    """Get all active units"""
    try:
        units = Unit.query.filter_by(is_active=True).order_by(Unit.name).all()
        return jsonify({
            'success': True,
            'data': units_schema.dump(units),
            'message': 'Units retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving units: {str(e)}'
        }), 500

@unit_bp.route('/<int:unit_id>', methods=['GET'])
@jwt_required()
@roles_required('manager', 'cashier', 'barista')
def get_unit(unit_id):
    """Get a specific unit by ID"""
    try:
        unit = Unit.query.get_or_404(unit_id)
        return jsonify({
            'success': True,
            'data': unit_schema.dump(unit),
            'message': 'Unit retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving unit: {str(e)}'
        }), 500

@unit_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required('manager')
def create_unit():
    """Create a new unit (Manager only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('abbreviation'):
            return jsonify({
                'success': False,
                'message': 'Name and abbreviation are required'
            }), 400
        
        # Check if unit already exists
        existing_unit = Unit.query.filter(
            (Unit.name == data['name']) | (Unit.abbreviation == data['abbreviation'])
        ).first()
        
        if existing_unit:
            return jsonify({
                'success': False,
                'message': 'Unit with this name or abbreviation already exists'
            }), 400
        
        # Create new unit
        new_unit = Unit(
            name=data['name'],
            abbreviation=data['abbreviation'],
            description=data.get('description', '')
        )
        
        db.session.add(new_unit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': unit_schema.dump(new_unit),
            'message': 'Unit created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating unit: {str(e)}'
        }), 500

@unit_bp.route('/<int:unit_id>', methods=['PUT'])
@jwt_required()
@roles_required('manager')
def update_unit(unit_id):
    """Update an existing unit (Manager only)"""
    try:
        unit = Unit.query.get_or_404(unit_id)
        data = request.get_json()
        
        # Check if name or abbreviation conflicts with other units
        if 'name' in data or 'abbreviation' in data:
            existing_unit = Unit.query.filter(
                Unit.id != unit_id,
                ((Unit.name == data.get('name', unit.name)) | 
                 (Unit.abbreviation == data.get('abbreviation', unit.abbreviation)))
            ).first()
            
            if existing_unit:
                return jsonify({
                    'success': False,
                    'message': 'Unit with this name or abbreviation already exists'
                }), 400
        
        # Update fields
        if 'name' in data:
            unit.name = data['name']
        if 'abbreviation' in data:
            unit.abbreviation = data['abbreviation']
        if 'description' in data:
            unit.description = data['description']
        if 'is_active' in data:
            unit.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': unit_schema.dump(unit),
            'message': 'Unit updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating unit: {str(e)}'
        }), 500

@unit_bp.route('/<int:unit_id>', methods=['DELETE'])
@jwt_required()
@roles_required('manager')
def delete_unit(unit_id):
    """Delete a unit (Manager only) - Soft delete by setting is_active to False"""
    try:
        unit = Unit.query.get_or_404(unit_id)
        
        # Check if unit is being used by any ingredients
        if unit.ingredients:
            return jsonify({
                'success': False,
                'message': 'Cannot delete unit that is being used by ingredients'
            }), 400
        
        # Soft delete
        unit.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Unit deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting unit: {str(e)}'
        }), 500 