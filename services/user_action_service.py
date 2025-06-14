
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
class UserActionService:

    OBJECT_TYPE_DISH = 'DISH' 
    OBJECT_TYPE_TASTE = 'TASTE'

    TASTE_MESSAGE = "From Quick Recommendation"



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
        if not UserActionService._check_object_exists(dish_id, UserActionService.OBJECT_TYPE_DISH):
            return False, "Object not found", 404

        existing_taste = Taste.query.filter_by(
            userId=user_id,
            dishId=dish_id
        ).first()

        if existing_taste:
            return create_response(code=409, message="Already recommended", data=None)

        new_taste = Taste(userId=user_id, dishId=dish_id,comment = UserActionService.TASTE_MESSAGE,
                          isVerified = False,
                          recommendState = 1,
                          usefulTotal = 0,
                          flow_document = {"Source":"Quick Recommendation"},
                          mediaIds = [],
                          mood = 1,
                          state = 1,
                          createdAt = datetime.utcnow(),
                          updatedAt = datetime.utcnow(),
                          flow_published_at = datetime.utcnow(),
                          _meta_op = 'c'
                          )
        
        db.session.add(new_taste)
       
        db.session.execute(
            db.update(Dish).where(Dish._id == dish_id)
             .values(recommendedCount=db.func.coalesce(Dish.recommendedCount, 0) + 1)
        )


        try:
            db.session.commit()
            return create_response(code=0, message="Recommended successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error recommend object: {e}")
            return create_response(code=500, message="Failed to recommend", data=None)




    @staticmethod
    def unrecommend_dish(user_id, dish_id):
        taste = Taste.query.filter_by(
            userId=user_id,
            dishId=dish_id,
        ).first()

        if not taste:
            return create_response(code=404, message="Not recommended yet", data=None)

        db.session.delete(taste)

        db.session.execute(
            db.update(Dish)
            .where(Dish._id == dish_id)
            .values(recommendedCount=db.func.greatest(db.func.coalesce(Dish.recommendedCount, 0) - 1, 0))
        )
            

        try:
            db.session.commit()
            return create_response(code=0, message="Unrecommended successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error unrecommending object: {e}")
            return create_response(code=500, message="Failed to unrecommend", data=None)



    @staticmethod
    def collect_dish(user_id, dish_id):
        if not UserActionService._check_object_exists(dish_id, UserActionService.OBJECT_TYPE_DISH):
            return create_response(code=404, message="Object not found", data=None)

        existing_collection = Collection.query.filter_by(
            user=user_id,
            object=dish_id,
            objectType=UserActionService.OBJECT_TYPE_DISH
        ).first()

        if existing_collection:
            return create_response(code=409, message="Already collected", data=None)

        new_collection = Collection(user=user_id, object=dish_id, objectType=UserActionService.OBJECT_TYPE_DISH)
        db.session.add(new_collection)

        try:
            db.session.commit()
            return create_response(code=0, message="Collected successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error collecting object: {e}")
            return create_response(code=500, message="Failed to collect", data=None)



    @staticmethod
    def uncollect_dish(user_id, dish_id):
        collection = Collection.query.filter_by(
            user=user_id,
            object=dish_id,
            objectType=UserActionService.OBJECT_TYPE_DISH
        ).first()

        if not collection:
            return create_response(code=404, message="Not collected yet", data=None)

        db.session.delete(collection)

        try:
            db.session.commit()
            return create_response(code=0, message="Uncollected successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error uncollecting object: {e}")
            return create_response(code=500, message="Failed to uncollect", data=None)
        

    @staticmethod
    def like_taste(user_id, taste_id):
        taste = Taste.query.filter_by(
            _id=taste_id
        ).first()

        if not taste:
            return create_response(code=404, message="Taste not found", data=None)
        
        existing_like = Like.query.filter_by(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE
        ).first()

        if existing_like:
            return create_response(code=409, message="Already liked", data=None)
        
        new_like = Like(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
            flow_published_at=datetime.utcnow()
        )

        db.session.add(new_like)

        db.session.execute(
            db.update(Taste)
            .where(Taste._id == taste_id)
            .values(usefulTotal=db.func.coalesce(Taste.usefulTotal, 0) + 1)
        )

        try:
            db.session.commit()
            return create_response(code=0, message="Liked successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error liking taste: {e}")
            return create_response(code=500, message="Failed to like", data=None)
        
        
    @staticmethod
    def unlike_taste(user_id, taste_id):
        like = Like.query.filter_by(
            user=user_id,
            object=taste_id,
            objectType=UserActionService.OBJECT_TYPE_TASTE
        ).first()
        
        if not like:
            return create_response(code=404, message="Not liked yet", data=None)
        
        db.session.delete(like)

        db.session.execute(
            db.update(Taste)
            .where(Taste._id == taste_id)
            .values(usefulTotal=db.func.greatest(db.func.coalesce(Taste.usefulTotal, 0) - 1, 0))
        )

        try:
            db.session.commit()
            return create_response(code=0, message="Unliked successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error unliking taste: {e}")
            return create_response(code=500, message="Failed to unlike", data=None)
        
    
    @staticmethod
    def edit_taste(user_id, dish_id, comment="", media_ids=[], mood=0, tags=[],recommend_state=1):
        try:
            # Find the taste
            taste = Taste.query.filter_by(
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
                taste.recommendState = recommend_state
            
            if media_ids is not None:
                #check if media ids exist in media table
                media_ids = [media_id for media_id in media_ids if Media.query.filter_by(_id=media_id).first()]
                if len(media_ids) != len(media_ids):
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
            # Count recommendations for this dish
            recommend_count = Taste.query.filter_by(
                dishId=dish_id,
                recommendState=TasteRecommendState.YES
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
    def get_taste(user_id, taste_id):
        try:
            taste = Taste.query.filter_by(
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
            total_tastes = Taste.query.filter_by(userId=user_id).count()
            
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
    def create_taste(user_id, dish_id, media_ids=[], comment="", mood=0, tags=[], recommend_state=1):
        try:
            taste = Taste(
                userId=user_id,
                dishId=dish_id,
                comment=comment,
                recommendState=recommend_state,
                mediaIds=media_ids,
                mood=mood,
                tags=tags,
                flow_document = {"Source":"UGC Flow"},
            )
            # Update fields if provided
            if comment is not None:
                taste.comment = comment
            
            if recommend_state is not None:
                if recommend_state not in [0, 1, 2]:
                    return create_response(code=400, message="Invalid recommend state")
                taste.recommendState = recommend_state
            
            if media_ids is not None:
                #check if media ids exist in media table
                media_ids = [media_id for media_id in media_ids if Media.query.filter_by(_id=media_id).first()]
                if len(media_ids) != len(media_ids):
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
            db.session.add(taste)
            db.session.commit()

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
                message="Taste created successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating taste: {e}")
            return create_response(code=500, message="Failed to create taste")

    @staticmethod
    def delete_taste(user_id, taste_id):
        taste = Taste.query.filter_by(
            _id=taste_id,
            userId=user_id
        ).first()

        if not taste:
            return create_response(code=404, message="Taste not found")

        db.session.delete(taste)
        db.session.commit()
        return create_response(code=0, message="Taste deleted successfully")

