
from extensions import db
from models.dish import Dish 
from models.taste import Taste
from models.collection import Collection
from models.like import Like
from datetime import datetime
from utils.response_utils import create_response
from sqlalchemy.orm import joinedload
from models.merchant import Merchant
from models.media import Media
from models.taste import TasteRecommendState
from mq.enums import *
from services.rabbitmq_service import RabbitMQService
from services.dish_management_service import DishManagementService

class UserActionService:

    OBJECT_TYPE_DISH = 'DISH' 
    OBJECT_TYPE_TASTE = 'TASTE'

    TASTE_MESSAGE = "From Quick Recommendation"


    @staticmethod
    def _get_rabbitmq_service():
        return RabbitMQService()

    @staticmethod
    def _check_object_exists(object_id, object_type):
        if object_type == UserActionService.OBJECT_TYPE_DISH:
            dish = db.session.query(Dish).filter(Dish._id == object_id).first()
            return dish is not None
        #Can add more object types here...
        return False

    @staticmethod
    def get_user_merchant_items(user_id, merchant_id):
        """
        Get user's collected and recommended dishes within a specific merchant.
        
        Args:
            user_id: The user ID
            merchant_id: The merchant ID
            
        Returns:
            dict: Standardized response with collected and recommended dish lists
        """
        try:
            # Verify merchant exists
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            
            # Get all dishes for this merchant with proper eager loading
            merchant_dishes = db.session.query(Dish).filter(
                Dish.merchant_col == merchant_id
            ).options(
                joinedload(Dish.merchant)
            ).all()
            
            if not merchant_dishes:
                return create_response(
                    code=0, 
                    data={"collected": [], "recommended": []},
                    message="No dishes found for this merchant"
                )
            
            dish_ids = [dish._id for dish in merchant_dishes]
            
            # Get user's collections for these dishes
            user_collections = Collection.query.filter(
                Collection.user == user_id,
                Collection.object.in_(dish_ids),
                Collection.objectType == UserActionService.OBJECT_TYPE_DISH
            ).all()
            
            # Get user's recommendations (tastes) for these dishes
            user_recommendations = Taste.query.filter(
                Taste.userId == user_id,
                Taste.dishId.in_(dish_ids)
            ).all()
            
            
            return create_response(
                code=0,
                data={
                    "collected": [dish._id for dish in user_collections],
                    "recommended": [taste._id for taste in user_recommendations],
                    "merchant": {
                        "_id": merchant._id,
                        "name": merchant.name
                    }
                },
                message=f"Found {len(user_collections)} collected and {len(user_recommendations)} recommended dishes"
            )
            
        except Exception as e:
            print(f"Error getting user merchant items: {e}")
            return create_response(code=500, message="Failed to retrieve user items")



    @staticmethod
    def recommend_dish(user_id, dish_id):
        """
        Quick recommendation for a dish (eaten only, recommendState=0).
        Uses the unified process_taste method internally.
        """
        # Use the unified process_taste method with recommendState=0 (eaten only)
        result = UserActionService.process_taste(
            user_id=user_id,
            dish_id=dish_id,
            taste_id=None,
            comment="",
            media_ids=[],
            mood=0,
            tags=[],
            recommend_state=0  # Eaten only
        )
        
        # Adjust the message for backward compatibility
        if result['code'] == 0:
            result['msg'] = "Recommended successfully"
        
        return result



    @staticmethod
    def unrecommend_dish(user_id, dish_id):
        """
        Unrecommend a dish (delete the taste).
        Uses the unified process_taste method internally with recommendState=None.
        """
        # Use the unified process_taste method with recommendState=None (delete)
        result = UserActionService.process_taste(
            user_id=user_id,
            dish_id=dish_id,
            taste_id=None,
            comment="",
            media_ids=[],
            mood=0,
            tags=[],
            recommend_state=None  # Delete the taste
        )
        
        # Adjust the message for backward compatibility
        if result['code'] == 0:
            result['msg'] = "Unrecommended successfully"
        elif result['code'] == 404:
            result['msg'] = "Not recommended yet"
        
        return result



    @staticmethod
    def collect_dish(user_id, dish_id):
        if not UserActionService._check_object_exists(dish_id, UserActionService.OBJECT_TYPE_DISH):
            return create_response(code=404, message="Object not found", data=None)

        existing_collection = Collection.active_collections().filter_by(
            user=user_id,
            object=dish_id,
            objectType=UserActionService.OBJECT_TYPE_DISH
        ).first()

        if existing_collection:
            return create_response(code=409, message="Already collected", data=None)

        deleted_collection = Collection.deleted_collections().filter_by(
            user=user_id,
            object=dish_id,
            objectType=UserActionService.OBJECT_TYPE_DISH
        ).first()

        if deleted_collection:
            # Restore the deleted collection
            deleted_collection.restore()


        else:
            new_collection = Collection(user=user_id, 
                                        object=dish_id, 
                                        objectType=UserActionService.OBJECT_TYPE_DISH
                                        )
                                    
            db.session.add(new_collection)

        try:
            db.session.commit()

            rabbitmq = UserActionService._get_rabbitmq_service()

            rabbitmq.send_dish_collect(user_id=user_id, 
                                       dish_id=dish_id, 
                                       state=CollectState.COLLECT)
            

            return create_response(code=0, message="Collected successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error collecting object: {e}")
            return create_response(code=500, message="Failed to collect", data=None)



    @staticmethod
    def uncollect_dish(user_id, dish_id):
        collection = Collection.active_collections().filter_by(
            user=user_id,
            object=dish_id,
            objectType=UserActionService.OBJECT_TYPE_DISH
        ).first()

        if not collection:
            return create_response(code=200, message="Not collected yet", data=None)

        collection.soft_delete()

        try:
            db.session.commit()

            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_dish_collect(user_id=user_id, 
                                       dish_id=dish_id, 
                                       state=CollectState.UNCOLLECT)

            return create_response(code=0, message="Uncollected successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error uncollecting object: {e}")
            return create_response(code=200, message="Failed to uncollect", data=None)
        

    @staticmethod
    def like_taste(user_id, taste_id):
        taste = Taste.active_tastes().filter_by(
            _id=taste_id
        ).first()

        if not taste:
            return create_response(code=404, message="Taste not found", data=None)
        
        existing_like = Like.active_likes().filter_by(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE,
        ).first()

        if existing_like:
            return create_response(code=409, message="Already liked", data=None)
        
        deleted_like = Like.deleted_likes().filter_by(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE,
        ).first()
        

        if deleted_like:
            # Restore the deleted like
            deleted_like.restore()

        else:
            new_like = Like(
                user=user_id,
                object=taste_id,
                objectType=UserActionService.OBJECT_TYPE_TASTE,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow(),
                # state = 1
            )

            db.session.add(new_like)

        UserActionService._update_taste_useful_total(taste_id)


        try:
            db.session.commit()
            return create_response(code=0, message="Liked successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error liking taste: {e}")
            return create_response(code=500, message="Failed to like", data=None)
        
        
    @staticmethod
    def unlike_taste(user_id, taste_id):
        like = Like.active_likes().filter_by(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE
        ).first()
        
        if not like:
            return create_response(code=404, message="Not liked yet", data=None)
        
        like.soft_delete()

        UserActionService._update_taste_useful_total(taste_id)

        try:
            db.session.commit()
            return create_response(code=0, message="Unliked successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error unliking taste: {e}")
            return create_response(code=500, message="Failed to unlike", data=None)
        
    
    @staticmethod
    def edit_taste(user_id, dish_id, comment="", media_ids=[], mood=0, tags=[],recommend_state=0, taste_id=None):
        try:
            # Find the taste
            taste = Taste.active_tastes().filter_by(
                _id=taste_id,
                dishId=dish_id,
                userId=user_id
            ).first()
            

            if not taste:
                return create_response(code=404, message="Taste not found or you don't have permission to edit")
            
            # Update fields if provided
            if comment is not None:
                taste.comment = comment
            
            if recommend_state is not None:
                if recommend_state not in [0, 1, 2]:
                    return create_response(code=400, message="Invalid recommend state")
                
            else:
                taste.recommendState = recommend_state

            if media_ids is not None:
                #check if media ids are objectids or urls
                valid_media_ids = []
                for media_id in media_ids:
                    if media_id.startswith('http'):
                        media = Media.query.filter_by(url=media_id).first()
                        if not media:
                            return create_response(code=400, message="Invalid media url")
                        valid_media_ids.append(media._id)
                    else:
                        if not Media.query.filter_by(_id=media_id).first():
                            return create_response(code=400, message="Invalid media ids")
                        valid_media_ids.append(media_id)
                
                if len(valid_media_ids) != len(media_ids):
                    return create_response(code=400, message="Invalid media ids")
                
                
                taste.mediaIds = media_ids
            

            if mood is not None:
                if mood not in [0, 1, 2, 3]:
                    return create_response(code=400, message="Invalid mood value")
                taste.mood = mood
            
            
            if tags is not None:
                taste.tags = tags
            
            # Update verification status since content changed
            taste.isVerified = False
            
            # Recalculate state based on new values
            taste.state = taste.calculate_state()
            
            # Update timestamp
            taste.updatedAt = datetime.utcnow()
            
            # Commit changes
            db.session.commit()

            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_taste_create(
                taste_id=taste._id,
                user_id=taste.userId,
                dish_id=taste.dishId,
                comment=taste.comment,
                recommend_state=recommend_state,
                media_ids=taste.mediaIds
            )   

            # Update dish statistics if recommendation state changed
            if recommend_state is not None:
                UserActionService._update_dish_recommend_count(taste.dishId)
             
            return create_response(
                code=0, 
                data={
                    "id": taste._id,
                    "state": taste.state,
                    "recommendState": taste.recommendState
                },
                message="Taste updated successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            print(f"Error editing taste: {e}")
            return create_response(code=500, message="Failed to update taste")


    @staticmethod
    def _update_dish_recommend_count(dish_id):
        """
        Update the recommendation count for a dish.
        
        Args:
            dish_id: The dish ID
        """
        try:
            # Count recommendations for this dish (both YES and DEFAULT states)
            recommend_count = Taste.active_tastes().filter(
                Taste.dishId == dish_id,
                Taste.recommendState.in_([TasteRecommendState.YES.value, TasteRecommendState.DEFAULT.value])
            ).count()
            
            # Update dish
            db.session.execute(
                db.update(Dish)
                .where(Dish._id == dish_id)
                .values(recommendedCount=recommend_count)
            )
            
            db.session.commit()
        except Exception as e:
            print(f"Error updating dish recommend count: {e}")


    @staticmethod
    def _update_taste_useful_total(taste_id):
        try:
            # Count active likes for this taste
            useful_count = Like.active_likes().filter_by(
                object=taste_id,
                objectType=UserActionService.OBJECT_TYPE_TASTE
            ).count()
            
            # Update taste
            db.session.execute(
                db.update(Taste)
                .where(Taste._id == taste_id)
                .values(usefulTotal=useful_count)
            )
            
            db.session.commit()
        except Exception as e:
            print(f"Error updating taste useful count: {e}")


    @staticmethod
    def get_taste(user_id, taste_id):
        try:
            taste = Taste.active_tastes().filter_by(
                _id=taste_id,
                userId=user_id
            ).first()
            
            if not taste:
                return create_response(code=404, message="Taste not found")
            
            taste_data = {
                "id": taste._id,
                "dishId": taste.dishId,
                "comment": taste.comment,
                "recommendState": taste.recommendState,
                "mediaIds": taste.mediaIds or [],
                "mood": taste.mood,
                "tags": taste.tags or [],
                "state": taste.state,
                "isVerified": taste.isVerified,
                "usefulTotal": taste.usefulTotal,
                "createdAt": taste.createdAt.isoformat() if taste.createdAt else None,
                "updatedAt": taste.updatedAt.isoformat() if taste.updatedAt else None
            }
        
            return create_response(code=0, data=taste_data, message="Success")
        
        except Exception as e:
            print(f"Error getting taste: {e}")
            return create_response(code=500, message="Failed to get taste")


    @staticmethod
    def get_user_taste_total(user_id):
        try:
            # Count total tastes for the user
            total_tastes = Taste.active_tastes().filter_by(userId=user_id).count()
            
            return create_response(
                code=0,
                data={
                    "total": total_tastes
                },
                message="Success"
            )
        
        except Exception as e:
            print(f"Error getting user taste total: {e}")
            return create_response(code=500, message="Failed to get user taste total")

    @staticmethod
    def process_taste(user_id, dish_id, taste_id=None, media_ids=[], comment="", mood=0, tags=[], recommend_state=None):
        """
        Unified method to handle taste create, update, and delete operations.
        
        Args:
            user_id: User ID performing the action
            dish_id: Dish ID for the taste
            taste_id: Optional taste ID for direct updates
            media_ids: List of media IDs or URLs
            comment: Comment text
            mood: Mood value (0-3)
            tags: List of tags
            recommend_state: 0 (eaten), 1 (like), 2 (dislike), or None (delete)
            
        Returns:
            Response dict with code, data, and message
        """
        try:
            print(f"Processing taste: user_id={user_id}, dish_id={dish_id}, taste_id={taste_id}, recommend_state={recommend_state}")
            
            # Validate dish exists if dish_id provided
            if dish_id and not UserActionService._check_object_exists(dish_id, UserActionService.OBJECT_TYPE_DISH):
                return create_response(code=404, message="Dish not found")
            
            # Find existing taste by tasteId or (userId + dishId)
            if taste_id:
                # Query by taste ID first if provided
                existing_taste = Taste.active_tastes().filter_by(
                    _id=taste_id,
                    userId=user_id  # Ensure user owns this taste
                ).first()
                
                deleted_taste = None
                if not existing_taste:
                    deleted_taste = Taste.deleted_tastes().filter_by(
                        _id=taste_id,
                        userId=user_id
                    ).first()
            else:
                # Query by user_id and dish_id combination
                existing_taste = Taste.active_tastes().filter_by(
                    userId=user_id,
                    dishId=dish_id
                ).first()
                
                deleted_taste = Taste.deleted_tastes().filter_by(
                    userId=user_id,
                    dishId=dish_id
                ).first()

            print(f"Found existing_taste: {existing_taste}, deleted_taste: {deleted_taste}")

            # Handle DELETE operation (recommendState is None/null)
            if recommend_state is None:
                if existing_taste:
                    print(f"Soft deleting taste: {existing_taste._id}")
                    # Soft delete the taste
                    existing_taste.soft_delete()
                    UserActionService._update_dish_recommend_count(existing_taste.dishId)
                    
                    db.session.commit()
                    
                    # Send RabbitMQ notification for deletion
                    rabbitmq = UserActionService._get_rabbitmq_service()
                    rabbitmq.send_taste_create(
                        taste_id=existing_taste._id,
                        user_id=user_id,
                        dish_id=existing_taste.dishId,
                        comment="",
                        recommend_state=TasteRecommendState.DEFAULT.value,
                        media_ids=[]
                    )
                    
                    return create_response(
                        code=0,
                        data={
                            "id": existing_taste._id,
                            "action": "deleted",
                            "dishId": existing_taste.dishId
                        },
                        message="Taste deleted successfully"
                    )
                else:
                    # No taste to delete
                    return create_response(
                        code=404,
                        message="Taste not found for deletion"
                    )

            # Validate recommend_state for create/update operations
            if recommend_state not in [0, 1, 2]:
                print(f"Invalid recommend_state: {recommend_state}")
                return create_response(code=400, message="Invalid recommend state. Must be 0, 1, 2, or null")
            
            # Validate and process media IDs (handle both IDs and URLs)
            valid_media_ids = []
            if media_ids:
                for media_id in media_ids:
                    if isinstance(media_id, str) and media_id.startswith('http'):
                        # Handle URL-based media
                        media = Media.query.filter_by(url=media_id).first()
                        if media:
                            valid_media_ids.append(media._id)
                        else:
                            print(f"Invalid media URL: {media_id}")
                            return create_response(code=400, message=f"Invalid media URL: {media_id}")
                    else:
                        # Handle ID-based media
                        if Media.query.filter_by(_id=media_id).first():
                            valid_media_ids.append(media_id)
                        else:
                            print(f"Invalid media ID: {media_id}")
                            return create_response(code=400, message=f"Invalid media ID: {media_id}")
            
            # Validate mood value
            if mood not in [0, 1, 2, 3]:
                print(f"Invalid mood value: {mood}")
                return create_response(code=400, message="Invalid mood value. Must be 0, 1, 2, or 3")

            # Handle UPDATE or RESTORE operation (existing taste found)
            if existing_taste or deleted_taste:
                taste = existing_taste if existing_taste else deleted_taste
                
                # If it's a deleted taste, restore it
                if deleted_taste and not existing_taste:
                    print(f"Restoring deleted taste: {taste._id}")
                    taste.restore()
                    action = "restored"
                else:
                    action = "updated"
                    print(f"Updating existing taste: {taste._id}")
                
                # Update taste fields
                taste.comment = comment or ""
                taste.recommendState = recommend_state
                taste.mediaIds = valid_media_ids
                taste.mood = mood
                taste.tags = tags or []
                taste.isVerified = False
                
                # Recalculate state based on new values
                taste.state = taste.calculate_state()
                taste.updatedAt = datetime.utcnow()
                
                db.session.commit()
                
                # Update dish recommendation count
                UserActionService._update_dish_recommend_count(taste.dishId)
                
                # Send RabbitMQ notification
                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=recommend_state,
                    media_ids=taste.mediaIds
                )
                
                print(f"Taste {action}: id={taste._id}, state={taste.state}, recommendState={taste.recommendState}")
                
                return create_response(
                    code=0,
                    data={
                        "id": taste._id,
                        "state": taste.state,
                        "recommendState": taste.recommendState,
                        "action": action,
                        "dishId": taste.dishId
                    },
                    message=f"Taste {action} successfully"
                )
            
            # Handle CREATE operation (no existing taste)
            else:
                print(f"Creating new taste for user={user_id}, dish={dish_id}")
                
                # Create new taste
                taste = Taste(
                    userId=user_id,
                    dishId=dish_id,
                    comment=comment or "",
                    recommendState=recommend_state,
                    mediaIds=valid_media_ids,
                    mood=mood,
                    tags=tags or [],
                    isVerified=False,
                    usefulTotal=0
                )
                
                # Calculate state based on content
                taste.state = taste.calculate_state()
                taste.createdAt = datetime.utcnow()
                taste.updatedAt = datetime.utcnow()
                
                db.session.add(taste)
                db.session.commit()
                
                # Update dish recommendation count
                UserActionService._update_dish_recommend_count(dish_id)
                
                # Send RabbitMQ notification
                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=recommend_state,
                    media_ids=taste.mediaIds
                )
                
                print(f"Taste created: id={taste._id}, state={taste.state}, recommendState={taste.recommendState}")
                
                return create_response(
                    code=0,
                    data={
                        "id": taste._id,
                        "state": taste.state,
                        "recommendState": taste.recommendState,
                        "action": "created",
                        "dishId": taste.dishId
                    },
                    message="Taste created successfully"
                )
                
        except Exception as e:
            db.session.rollback()
            print(f"Error processing taste: {e}")
            import traceback
            traceback.print_exc()
            return create_response(code=500, message=f"Failed to process taste: {str(e)}")

    @staticmethod
    def create_taste(user_id, dish_id, media_ids=[], comment="", mood=0, tags=[], recommend_state=0):
        """
        This module includes creating/updating tastes, fix bug for not updating existing tastes.
        """
        try:
            existing_taste = Taste.active_tastes().filter_by(
                userId=user_id,
                dishId=dish_id
            ).first()

            deleted_taste = Taste.deleted_tastes().filter_by(
                userId=user_id,
                dishId=dish_id
            ).first()

            if existing_taste or deleted_taste:
                taste = existing_taste if existing_taste else deleted_taste

                if deleted_taste and not existing_taste:
                    taste.restore()
                    
                taste.comment = comment

                if recommend_state not in [0,1,2]:
                    return create_response(code=400, message="Invalid recommend state")

                taste.recommendState = recommend_state

                if media_ids:
                    valid_media_ids = []
                    for media_id in media_ids:
                        if Media.query.filter_by(_id=media_id).first():
                            valid_media_ids.append(media_id)
                    if len(valid_media_ids) != len(media_ids):
                        return create_response(code=400, message="Invalid media ids")   
                    taste.mediaIds = valid_media_ids
                else: 
                    taste.mediaIds = []

                if mood not in [0,1,2,3]:
                    return create_response(code=400, message="Invalid mood value")
                taste.mood = mood

                taste.tags = tags or []

                taste.isVerified = False
                taste.state = taste.calculate_state()
                taste.updatedAt = datetime.utcnow()

                db.session.commit()

                UserActionService._update_dish_recommend_count(taste.dishId)

                #call rabbitmq
                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=recommend_state,
                    media_ids=taste.mediaIds
                )

                return create_response(
                    code=0, 
                    data={
                        "id": taste._id,
                        "state": taste.state,
                        "recommendState": taste.recommendState,
                        "updated" :True
                    },
                    message="Taste created successfully"
                )
            
            else:
                taste = Taste(
                    userId=user_id,
                    dishId=dish_id,
                    comment=comment,
                    recommendState=recommend_state,
                    mediaIds=media_ids,
                    mood=mood,
                    tags=tags
                )
                
                
                if comment is not None:
                    taste.comment = comment
                
                if recommend_state is not None:
                    if recommend_state not in [0, 1, 2]:
                        return create_response(code=400, message="Invalid recommend state")
                    taste.recommendState = recommend_state
                
                if media_ids:
                    valid_media_ids = []
                    for media_id in media_ids:
                        if Media.query.filter_by(_id=media_id).first():
                            valid_media_ids.append(media_id)
                    if len(valid_media_ids) != len(media_ids):
                        return create_response(code=400, message="Invalid media ids")   
                    taste.mediaIds = valid_media_ids
                
                if mood is not None:
                    if mood not in [0, 1, 2, 3]:
                        return create_response(code=400, message="Invalid mood value")
                    taste.mood = mood
                
                
                taste.tags= tags or []
            
                # Update verification status since content changed
                taste.isVerified = False
                
                # Recalculate state based on new values
                taste.state = taste.calculate_state()
                
                # Update timestamp
                taste.updatedAt = datetime.utcnow()
                
                # Commit changes
                db.session.add(taste)
                db.session.commit()

                UserActionService._update_dish_recommend_count(taste._id)


                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=recommend_state,
                    media_ids=taste.mediaIds
                )


                return create_response(
                    code=0, 
                    data={
                        "id": taste._id,
                        "state": taste.state,
                        "recommendState": taste.recommendState
                    },
                    message="Taste created successfully"
                )
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating taste: {e}")
            return create_response(code=500, message="Failed to create taste")




    @staticmethod
    def delete_taste(user_id, taste_id):
        taste = Taste.active_tastes().filter_by(
            _id=taste_id,
            userId=user_id
        ).first()

    
        if not taste:
            return create_response(code=404, message="Taste not found")

        else:
            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=TasteRecommendState.DEFAULT.value,
                    media_ids=taste.mediaIds
                )

            taste.recommendState = TasteRecommendState.DEFAULT.value
            taste.state = taste.calculate_state()

            taste.soft_delete()

            UserActionService._update_dish_recommend_count(taste.dishId)

            db.session.commit()
            return create_response(code=0, message="Taste deleted successfully")

    @staticmethod
    def create_dish_ugc(user_id, merchant_id, name, price=None, media_ids=None, 
                       description=None, characteristic=None):
        """
        This module includes updateing and creating tastes.
        """
        try:
            
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            

            if media_ids:
                valid_media = Media.query.filter(Media._id.in_(media_ids)).all()
                if len(valid_media) != len(media_ids):
                    return create_response(code=400, message="Some media IDs are invalid")
            
            response =  DishManagementService.create_dish(
                user_id=user_id,
                merchant_id=merchant_id,
                title=name,
                price=price,
                media_ids=media_ids,
                description=description
            )

            dish_id = response["data"]["_id"]

            rabbitmq = UserActionService._get_rabbitmq_service()
            success = rabbitmq.send_taste_add_dish(
                id=dish_id,
                user_id=user_id,
                merchant_id=merchant_id,
                name=name,
                price=price,
                media_ids=media_ids,
                description=description,
                characteristic=characteristic
            )
            
            if success:
                return create_response(
                    code=0,
                    data={
                        "id": dish_id,
                        "merchant_id": merchant_id,
                        "name": name,
                        "status": "pending_creation"
                    },
                    message="Dish creation request submitted successfully"
                )
            else:
                return create_response(
                    code=500,
                    message="Failed to submit dish creation request"
                )
                
        except Exception as e:
            print(f"Error creating dish through UGC: {e}")
            return create_response(code=500, message="Failed to create dish")



    """
    --------------------------------New Features supporting version 0.7.0-----------------------------------
    """

         