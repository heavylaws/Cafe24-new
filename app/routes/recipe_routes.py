from flask import Blueprint, request, jsonify, current_app
from app.models import db, Recipe, MenuItem, Ingredient
from app.utils.decorators import token_required, roles_required
import datetime

recipe_bp = Blueprint('recipe_bp', __name__)

@recipe_bp.route('/<int:menu_item_id>/recipe', methods=['GET'])
@token_required
@roles_required(['manager', 'barista'])
def get_recipe_for_menu_item(current_user, menu_item_id):
    """Get recipe (ingredients and amounts) for a specific menu item."""
    try:
        menu_item = MenuItem.query.get_or_404(menu_item_id)
        recipes = Recipe.query.filter_by(menu_item_id=menu_item_id).all()
        
        result = {
            'menu_item': {
                'id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description
            },
            'ingredients': []
        }
        
        for recipe in recipes:
            result['ingredients'].append({
                'ingredient_id': recipe.ingredient_id,
                'ingredient_name': recipe.ingredient.name,
                'unit': recipe.ingredient.unit,
                'amount': recipe.amount,
                'current_stock': recipe.ingredient.current_stock,
                'is_sufficient': recipe.ingredient.current_stock >= recipe.amount
            })
        
        # Return only the ingredients as an array for frontend compatibility
        return jsonify(result['ingredients']), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching recipe for menu item {menu_item_id}: {e}")
        return jsonify({'message': 'Could not retrieve recipe.'}), 500

@recipe_bp.route('/<int:menu_item_id>/recipe', methods=['POST'])
@token_required
@roles_required(['manager'])
def create_or_update_recipe(current_user, menu_item_id):
    """Create or update recipe for a menu item."""
    try:
        menu_item = MenuItem.query.get_or_404(menu_item_id)
        data = request.get_json()
        current_app.logger.info(f"Received recipe payload: {data}")

        # Accept both {ingredients: [...]} and raw array
        if isinstance(data, list):
            ingredients = data
        elif isinstance(data, dict) and 'ingredients' in data and isinstance(data['ingredients'], list):
            ingredients = data['ingredients']
        else:
            return jsonify({'message': 'Ingredients list is required'}), 400

        if len(ingredients) == 0:
            return jsonify({'message': 'Ingredients list is required'}), 400
        
        # Remove existing recipes for this menu item
        Recipe.query.filter_by(menu_item_id=menu_item_id).delete()

        # Add new recipes
        for ingredient_data in ingredients:
            if not isinstance(ingredient_data, dict) or 'ingredient_id' not in ingredient_data or 'amount' not in ingredient_data:
                return jsonify({'message': 'Each ingredient must have ingredient_id and amount'}), 400
            
            ingredient = Ingredient.query.get(ingredient_data['ingredient_id'])
            if not ingredient or not ingredient.is_active:
                return jsonify({'message': f'Ingredient with ID {ingredient_data["ingredient_id"]} not found or inactive'}), 400
            
            if float(ingredient_data['amount']) <= 0:
                return jsonify({'message': 'Amount must be greater than 0'}), 400
            
            recipe = Recipe(
                menu_item_id=menu_item_id,
                ingredient_id=ingredient_data['ingredient_id'],
                amount=float(ingredient_data['amount'])
            )
            db.session.add(recipe)
        
        db.session.commit()
        
        return jsonify({'message': 'Recipe updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating recipe for menu item {menu_item_id}: {e}")
        return jsonify({'message': 'Could not update recipe.'}), 500

@recipe_bp.route('/<int:menu_item_id>/recipe', methods=['OPTIONS'])
def recipe_options(menu_item_id):
    return ('', 204, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,Authorization'})

@recipe_bp.route('/<int:menu_item_id>/recipe', methods=['DELETE'])
@token_required
@roles_required(['manager'])
def delete_recipe(current_user, menu_item_id):
    """Delete recipe for a menu item."""
    try:
        Recipe.query.filter_by(menu_item_id=menu_item_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'Recipe deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting recipe for menu item {menu_item_id}: {e}")
        return jsonify({'message': 'Could not delete recipe.'}), 500

@recipe_bp.route('/check-availability/<int:menu_item_id>/<int:quantity>', methods=['GET'])
@token_required
@roles_required(['manager', 'cashier', 'courier'])
def check_item_availability(current_user, menu_item_id, quantity):
    """Check if menu item can be made with current stock."""
    try:
        menu_item = MenuItem.query.get_or_404(menu_item_id)
        recipes = Recipe.query.filter_by(menu_item_id=menu_item_id).all()
        
        if not recipes:
            return jsonify({
                'available': True,
                'message': 'No recipe defined - assuming available'
            }), 200
        
        insufficient_ingredients = []
        
        for recipe in recipes:
            required_amount = recipe.amount * quantity
            if recipe.ingredient.current_stock < required_amount:
                insufficient_ingredients.append({
                    'ingredient_name': recipe.ingredient.name,
                    'required': required_amount,
                    'available': recipe.ingredient.current_stock,
                    'shortage': required_amount - recipe.ingredient.current_stock,
                    'unit': recipe.ingredient.unit
                })
        
        if insufficient_ingredients:
            return jsonify({
                'available': False,
                'message': 'Insufficient ingredients',
                'insufficient_ingredients': insufficient_ingredients
            }), 200
        else:
            return jsonify({
                'available': True,
                'message': 'Item can be made'
            }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error checking availability for menu item {menu_item_id}: {e}")
        return jsonify({'message': 'Could not check availability.'}), 500

@recipe_bp.route('/all', methods=['GET'])
@token_required
@roles_required(['manager'])
def get_all_recipes(current_user):
    """Get all recipes for all menu items."""
    try:
        recipes = db.session.query(Recipe, MenuItem, Ingredient).join(
            MenuItem, Recipe.menu_item_id == MenuItem.id
        ).join(
            Ingredient, Recipe.ingredient_id == Ingredient.id
        ).filter(
            MenuItem.is_active == True,
            Ingredient.is_active == True
        ).order_by(MenuItem.name.asc(), Ingredient.name.asc()).all()
        
        result = {}
        for recipe, menu_item, ingredient in recipes:
            if menu_item.id not in result:
                result[menu_item.id] = {
                    'menu_item': {
                        'id': menu_item.id,
                        'name': menu_item.name,
                        'description': menu_item.description
                    },
                    'ingredients': []
                }
            
            result[menu_item.id]['ingredients'].append({
                'ingredient_id': ingredient.id,
                'ingredient_name': ingredient.name,
                'unit': ingredient.unit,
                'amount': recipe.amount,
                'current_stock': ingredient.current_stock
            })
        
        return jsonify(list(result.values())), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching all recipes: {e}")
        return jsonify({'message': 'Could not retrieve recipes.'}), 500
