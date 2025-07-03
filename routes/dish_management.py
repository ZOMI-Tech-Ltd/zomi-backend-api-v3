"""
Dish Management Routes
Handles dish creation, update, and deletion operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from services.dish_management_service import DishManagementService
from schemas.dish_management import (
    DishCreateSchema, 
    DishUpdateSchema,
    DishBulkDeleteSchema
)
from utils.response_utils import create_response
from extensions import db
import logging

logger = logging.getLogger(__name__)

dish_management_bp = Blueprint('dish_management', __name__, url_prefix='/v3/dish_management')

# Initialize schemas
dish_create_schema = DishCreateSchema()
dish_update_schema = DishUpdateSchema()
dish_bulk_delete_schema = DishBulkDeleteSchema()


def get_current_user_id():
    current_user_id = None
    if request.headers.get('Authorization') and request.headers.get('Authorization').startswith('Bearer '):
        current_user_id = get_jwt_identity()
    else:
        current_user_id = None
    return current_user_id



@dish_management_bp.route('/create', methods=['POST'])
@jwt_required(optional=True)
def create_dish():
    """
    Create a new dish
    
    Required fields:
    - title: Dish name
    - merchantId: Associated merchant
    - price: Price in cents
    - description: Optional description
    - media: Optional array of media objects
    
    Returns:
        JSON response with created dish data
    """
    try:
        # Get current user
        current_user_id = get_current_user_id()
        
        # Validate request data
        data = request.get_json()
        if not data:
            return create_response(code=200, message="Request body is required"), 200
            
        try:
            validated_data = dish_create_schema.load(data)
        except ValidationError as e:
            return create_response(code=200, message="Validation error", data=e.messages), 200
        
        # Create dish through service
        result = DishManagementService.create_dish(
            user_id=current_user_id,
            **validated_data
        )
        
        if result['code'] == 0:
            return create_response(
                code=0, 
                data=result['data'], 
                message="Dish created successfully"
            ), 200
        else:
            return create_response(
                code=result['code'], 
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error creating dish: {str(e)}")
        return create_response(code=200, message="Failed to create dish"), 200


@dish_management_bp.route('/<string:dish_id>', methods=['PUT'])
@jwt_required(optional=True)
def update_dish(dish_id):
    """
    Update an existing dish
    
    Path Parameters:
        dish_id: The dish ID to update
        
    Body Parameters:
        All fields are optional - only provided fields will be updated
        
    Returns:
        JSON response with updated dish data
    """
    try:
        # Get current user
        current_user_id = get_current_user_id()
        
        # Validate request data
        data = request.get_json()
        if not data:
            return create_response(code=200, message="Request body is required"), 200
            
        try:
            validated_data = dish_update_schema.load(data)
        except ValidationError as e:
            return create_response(code=200, message="Validation error", data=e.messages), 200
        
        # Update dish through service
        result = DishManagementService.update_dish(
            dish_id=dish_id,
            user_id=current_user_id,
            **validated_data
        )
        
        if result['code'] == 0:
            return create_response(
                code=0, 
                data=result['data'], 
                message="Dish updated successfully"
            ), 200
        else:
            return create_response(
                code=result['code'], 
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error updating dish: {str(e)}")
        return create_response(code=200, message="Failed to update dish"), 200


@dish_management_bp.route('/<string:dish_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_dish(dish_id):
    """
    Soft delete a single dish
    
    Path Parameters:
        dish_id: The dish ID to delete
        
    Returns:
        JSON response confirming deletion
    """
    try:
        # Get current user
        current_user_id = get_current_user_id()
        
        # Delete dish through service
        result = DishManagementService.delete_dish(
            dish_id=dish_id,
            user_id=current_user_id
        )
        
        if result['code'] == 0:
            return create_response(
                code=0, 
                message="Dish deleted successfully"
            ), 200
        else:
            return create_response(
                code=result['code'], 
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error deleting dish: {str(e)}")
        return create_response(code=200, message="Failed to delete dish"), 200


@dish_management_bp.route('/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_dishes():
    """
    Soft delete multiple dishes at once
    
    Request Body:
        dish_ids: Array of dish IDs to delete
        
    Returns:
        JSON response with deletion summary
    """
    try:
        # Get current user
        current_user_id = get_current_user_id()
        
        # Validate request data
        data = request.get_json()
        if not data:
            return create_response(code=200, message="Request body is required"), 200
            
        try:
            validated_data = dish_bulk_delete_schema.load(data)
        except ValidationError as e:
            return create_response(code=200, message="Validation error", data=e.messages), 200
        
        # Bulk delete through service
        result = DishManagementService.bulk_delete_dishes(
            dish_ids=validated_data['dish_ids'],
            user_id=current_user_id
        )
        
        if result['code'] == 0:
            return create_response(
                code=0, 
                data=result['data'],
                message="Dishes deleted successfully"
            ), 200
        else:
            return create_response(
                code=result['code'], 
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error bulk deleting dishes: {str(e)}")
        return create_response(code=200, message="Failed to delete dishes"), 200


@dish_management_bp.route('/restore/<string:dish_id>', methods=['POST'])
@jwt_required()
def restore_dish(dish_id):
    """
    Restore a soft-deleted dish
    
    Path Parameters:
        dish_id: The dish ID to restore
        
    Returns:
        JSON response with restored dish data
    """
    try:
        # Get current user
        current_user_id = get_current_user_id()
        
        # Restore dish through service
        result = DishManagementService.restore_dish(
            dish_id=dish_id,
            user_id=current_user_id
        )
        
        if result['code'] == 0:
            return create_response(
                code=0, 
                data=result['data'],
                message="Dish restored successfully"
            ), 200
        else:
            return create_response(
                code=result['code'], 
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error restoring dish: {str(e)}")
        return create_response(code=200, message="Failed to restore dish"), 200