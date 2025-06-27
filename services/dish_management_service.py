

from extensions import db
from models.dish import Dish
from models.merchant import Merchant
from models.media import Media
from models.collection import Collection
from models.taste import Taste
from utils.response_utils import create_response
from sqlalchemy import and_, or_
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class DishManagementService:



    @staticmethod
    def create_dish(user_id, title, merchant_id, price, description=None, 
                   media_ids=None, ingredients=None, **kwargs):
        """
        Create a new dish with validation and related data setup
        
        Args:
            user_id: ID of the user creating the dish
            title: Dish name
            merchant_id: Associated merchant ID
            price: Price in cents
            description: Optional description
            media_ids: Optional list of media IDs
            ingredients: Optional list of ingredients
            **kwargs: Additional dish attributes
            
        Returns:
            dict: Response with created dish data or error
        """
        try:
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=200, message="Merchant not found")
            
            
            if media_ids:
                valid_media = Media.query.filter(Media._id.in_(media_ids)).all()
                if len(valid_media) != len(media_ids):
                    return create_response(code=200, message="Some media IDs are invalid")
            
            new_dish = Dish(
                _id=str(uuid.uuid4()),
                title=title,
                merchant_col=merchant_id,
                price=price,
                description=description,
                # Set media as JSON array matching the Go structure
                media=[{"mediaId": media_id} for media_id in (media_ids or [])]
            )
            
            # Set additional attributes from kwargs
            allowed_attrs = ['pickup_enabled', 'delivery_enabled', 'dine_in_enabled',
                           'cuisine', 'meal_type', 'flavor', 'course_type']
            for attr in allowed_attrs:
                if attr in kwargs:
                    setattr(new_dish, attr, kwargs[attr])
            
            # Set default values
            new_dish.recommendedCount = 0
            new_dish.is_verified = False
            new_dish.created_at = datetime.utcnow()
            new_dish.updated_at = datetime.utcnow()
            
            # Add to session and commit
            db.session.add(new_dish)
            db.session.commit()
            
            # Return created dish data
            return create_response(
                code=0,
                data={
                    "_id": new_dish._id,
                    "title": new_dish.title,
                    "merchant_id": new_dish.merchant_col,
                    "price": new_dish.price,
                    "description": new_dish.description,
                    "media": new_dish.media,
                    "created_at": new_dish.created_at.isoformat()
                },
                message="Dish created successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating dish: {str(e)}")
            return create_response(code=500, message=f"Failed to create dish: {str(e)}")
    
    @staticmethod
    def update_dish(dish_id, user_id, **update_data):
        """
        Update an existing dish
        
        Args:
            dish_id: ID of the dish to update
            user_id: ID of the user performing the update
            **update_data: Fields to update
            
        Returns:
            dict: Response with updated dish data or error
        """
        try:
            # Find the dish
            dish = Dish.query.filter_by(_id=dish_id).first()
            if not dish:
                return create_response(code=404, message="Dish not found")
            
            # TODO: Add permission check here
            # Verify user has permission to update this dish
            
            # Handle media update if provided
            if 'media_ids' in update_data:
                media_ids = update_data.pop('media_ids')
                if media_ids is not None:
                    # Validate media IDs
                    valid_media = Media.query.filter(Media._id.in_(media_ids)).all()
                    if len(valid_media) != len(media_ids):
                        return create_response(code=400, message="Some media IDs are invalid")
                    
                    dish.media = [{"mediaId": media_id} for media_id in media_ids]
            
            # Update allowed fields
            allowed_updates = ['title', 'description', 'price', 'pickup_enabled',
                             'delivery_enabled', 'dine_in_enabled', 'cuisine',
                             'meal_type', 'flavor', 'course_type']
            
            for field, value in update_data.items():
                if field in allowed_updates and hasattr(dish, field):
                    setattr(dish, field, value)
            
            # Update timestamp
            dish.updated_at = datetime.utcnow()
            
            # Commit changes
            db.session.commit()
            
            # Update recommendation count if needed
            DishManagementService._update_dish_stats(dish_id)
            
            return create_response(
                code=0,
                data={
                    "_id": dish._id,
                    "title": dish.title,
                    "price": dish.price,
                    "description": dish.description,
                    "updated_at": dish.updated_at.isoformat()
                },
                message="Dish updated successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating dish: {str(e)}")
            return create_response(code=500, message=f"Failed to update dish: {str(e)}")
    
    @staticmethod
    def delete_dish(dish_id, user_id):
        """
        Soft delete a dish
        
        Args:
            dish_id: ID of the dish to delete
            user_id: ID of the user performing the deletion
            
        Returns:
            dict: Response confirming deletion or error
        """
        try:
            # Find the dish
            dish = Dish.query.filter_by(_id=dish_id).first()
            if not dish:
                return create_response(code=404, message="Dish not found")
            
            # Check if already deleted
            if dish.deleted_at is not None:
                return create_response(code=400, message="Dish is already deleted")
            
            # TODO: Add permission check here
            
            # Soft delete the dish
            dish.deleted_at = datetime.utcnow()
            dish.updated_at = datetime.utcnow()
            
            # Also soft delete related collections and tastes
            Collection.query.filter_by(
                object=dish_id,
                objectType='DISH'
            ).update({
                'deletedAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            })
            
            Taste.query.filter_by(dishId=dish_id).update({
                'deletedAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            })
            
            db.session.commit()
            
            return create_response(code=0, message="Dish deleted successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting dish: {str(e)}")
            return create_response(code=500, message=f"Failed to delete dish: {str(e)}")
    
    @staticmethod
    def bulk_delete_dishes(dish_ids, user_id):
        """
        Soft delete multiple dishes at once
        
        Args:
            dish_ids: List of dish IDs to delete
            user_id: ID of the user performing the deletion
            
        Returns:
            dict: Response with deletion summary
        """
        try:
            # Find all dishes
            dishes = Dish.query.filter(
                Dish._id.in_(dish_ids),
                Dish.deleted_at.is_(None)
            ).all()
            
            if not dishes:
                return create_response(code=404, message="No valid dishes found to delete")
            
            # TODO: Add permission check for each dish
            
            deleted_count = 0
            failed_ids = []
            
            for dish in dishes:
                try:
                    # Soft delete the dish
                    dish.deleted_at = datetime.utcnow()
                    dish.updated_at = datetime.utcnow()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete dish {dish._id}: {str(e)}")
                    failed_ids.append(dish._id)
            
            # Bulk update related collections and tastes
            if deleted_count > 0:
                valid_dish_ids = [d._id for d in dishes if d._id not in failed_ids]
                
                Collection.query.filter(
                    Collection.object.in_(valid_dish_ids),
                    Collection.objectType == 'DISH'
                ).update({
                    'deletedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }, synchronize_session=False)
                
                Taste.query.filter(
                    Taste.dishId.in_(valid_dish_ids)
                ).update({
                    'deletedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }, synchronize_session=False)
            
            db.session.commit()
            
            return create_response(
                code=0,
                data={
                    "deleted_count": deleted_count,
                    "failed_ids": failed_ids,
                    "requested_count": len(dish_ids)
                },
                message=f"Successfully deleted {deleted_count} dishes"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error bulk deleting dishes: {str(e)}")
            return create_response(code=500, message=f"Failed to delete dishes: {str(e)}")
    
    @staticmethod
    def restore_dish(dish_id, user_id):
        """
        Restore a soft-deleted dish
        
        Args:
            dish_id: ID of the dish to restore
            user_id: ID of the user performing the restoration
            
        Returns:
            dict: Response with restored dish data or error
        """
        try:
            # Find the deleted dish
            dish = Dish.query.filter_by(_id=dish_id).first()
            if not dish:
                return create_response(code=404, message="Dish not found")
            
            if dish.deleted_at is None:
                return create_response(code=400, message="Dish is not deleted")
            
            # TODO: Add permission check here
            
            # Restore the dish
            dish.deleted_at = None
            dish.updated_at = datetime.utcnow()
            
            # Optionally restore related collections and tastes
            # This is a business decision - you might not want to restore these
            
            db.session.commit()
            
            # Update dish statistics
            DishManagementService._update_dish_stats(dish_id)
            
            return create_response(
                code=0,
                data={
                    "_id": dish._id,
                    "title": dish.title,
                    "restored_at": dish.updated_at.isoformat()
                },
                message="Dish restored successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring dish: {str(e)}")
            return create_response(code=500, message=f"Failed to restore dish: {str(e)}")
    
    @staticmethod
    def _update_dish_stats(dish_id):
        """
        Update dish statistics (recommendation count, collection count, etc.)
        
        Args:
            dish_id: ID of the dish to update stats for
        """
        try:
            # Count active recommendations
            recommend_count = Taste.active_tastes().filter_by(
                dishId=dish_id,
                recommendState=1  # YES
            ).count()
            
            # Count active collections
            collection_count = Collection.active_collections().filter_by(
                object=dish_id,
                objectType='DISH'
            ).count()
            
            # Update dish
            Dish.query.filter_by(_id=dish_id).update({
                'recommendedCount': recommend_count,
                'collection_cnt': collection_count
            })
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating dish stats: {str(e)}")
            # Don't fail the main operation if stats update fails