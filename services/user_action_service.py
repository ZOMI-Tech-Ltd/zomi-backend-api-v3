
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
        if not UserActionService._check_object_exists(dish_id, UserActionService.OBJECT_TYPE_DISH):
            return False, "Object not found", 404

        existing_taste = Taste.active_tastes().filter_by(
            userId=user_id,
            dishId=dish_id
        ).first()

        if existing_taste:
            return create_response(code=409, message="Already recommended", data=None)
        

        deleted_taste = Taste.deleted_tastes().filter_by(
            userId=user_id,
            dishId=dish_id
        ).first()
        
        if deleted_taste:
            # Restore the deleted taste
            deleted_taste.restore()
            deleted_taste.recommendState = TasteRecommendState.YES
            deleted_taste.state = deleted_taste.calculate_state()
            deleted_taste.updatedAt = datetime.utcnow()


        else:
            new_taste = Taste(
                            userId=user_id, 
                            dishId=dish_id,
                            comment = None,
                          isVerified = False,
                          recommendState = TasteRecommendState.YES,
                          usefulTotal = 0,
                          mediaIds = [],
                          mood = 1,
                          state = 1,
                          createdAt = datetime.utcnow(),
                          updatedAt = datetime.utcnow(),
                          )
        
            db.session.add(new_taste)


        UserActionService._update_dish_recommend_count(dish_id)


        try:
            db.session.commit()

            if deleted_taste:
                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                taste_id=deleted_taste._id,
                user_id=user_id,
                dish_id=dish_id,
                comment="",
                recommend_state=TasteRecommendState.YES,
                media_ids=[]
            )

            else:
                rabbitmq = UserActionService._get_rabbitmq_service()
                rabbitmq.send_taste_create(
                    taste_id=new_taste._id,
                    user_id=user_id,
                    dish_id=dish_id,
                    comment="",
                    recommend_state=TasteRecommendState.YES,
                    media_ids=[]
                )
            

            return create_response(code=0, message="Recommended successfully", data=None)
        except Exception as e:
            db.session.rollback()
            print(f"Error recommend object: {e}")
            return create_response(code=500, message="Failed to recommend", data=None)



    @staticmethod
    def unrecommend_dish(user_id, dish_id):
        taste = Taste.active_tastes().filter_by(
            userId=user_id,
            dishId=dish_id,
        ).first()

        if not taste:
            return create_response(code=404, message="Not recommended yet", data=None)

        taste.recommendState = TasteRecommendState.NO
        taste.state = taste.calculate_state()


        taste.soft_delete()
        UserActionService._update_dish_recommend_count(dish_id)
            

        try:
            db.session.commit()

            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_taste_create(
                taste_id=taste._id,
                user_id=user_id,
                dish_id=dish_id,
                comment="",
                recommend_state=TasteRecommendState.NO,
                media_ids=[]
            )
            return create_response(code=0, message="Unrecommended successfully", data=None)
        
        except Exception as e:
            db.session.rollback()
            print(f"Error unrecommending object: {e}")
            return create_response(code=500, message="Failed to unrecommend", data=None)



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
    def edit_taste(user_id, dish_id, comment="", media_ids=[], mood=0, tags=[],recommend_state=1, taste_id=None):
        try:
            # Find the taste
            taste = Taste.active_tastes().filter_by(
                _id=taste_id,
                dishId=dish_id,
                userId=user_id
            ).first()
            
            print(taste)

            if not taste:
                return create_response(code=404, message="Taste not found or you don't have permission to edit")
            
            # Update fields if provided
            if comment is not None:
                taste.comment = comment
            
            if recommend_state is not None:
                if recommend_state not in [0, 1, 2]:
                    return create_response(code=400, message="Invalid recommend state")
                else:
                    if recommend_state == 0:
                        recommendState = RecommendState.DEFAULT
                    elif recommend_state == 1:
                        recommendState = RecommendState.RECOMMEND
                    elif recommend_state == 2:
                        recommendState = RecommendState.NOT_RECOMMEND
            

            taste.recommendState = recommendState.value

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

            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_taste_create(
                taste_id=taste._id,
                user_id=taste.userId,
                dish_id=taste.dishId,
                comment=taste.comment,
                recommend_state=recommendState,
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
            # Count recommendations for this dish
            recommend_count = Taste.active_tastes().filter_by(
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
                return create_response(code=0, message="Taste not found")
            
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
            return create_response(code=0, message="Failed to get taste")


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
            return create_response(code=0, message="Failed to get user taste total")

    @staticmethod
    def create_taste(user_id, dish_id, media_ids=[], comment="", mood=0, tags=[], recommend_state=1):
        try:
            existing_taste = Taste.active_tastes().filter_by(
                userId=user_id,
                dishId=dish_id
            ).first()

            if existing_taste:
                return create_response(code=409, message="Already recommended", data=None)
        
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
                # Update fields if provided
                if comment is not None:
                    taste.comment = comment
                
                if recommend_state is not None:
                    if recommend_state not in [0, 1, 2]:
                        return create_response(code=0, message="Invalid recommend state")
                    taste.recommendState = recommend_state
                
                if media_ids:
                    valid_media_ids = []
                    for media_id in media_ids:
                        if Media.query.filter_by(_id=media_id).first():
                            valid_media_ids.append(media_id)
                    if len(valid_media_ids) != len(media_ids):
                        return create_response(code=0, message="Invalid media ids")   
                    taste.mediaIds = valid_media_ids
                
                if mood is not None:
                    if mood not in [0, 1, 2, 3]:
                        return create_response(code=0, message="Invalid mood value")
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
                    recommend_state=RecommendState.RECOMMEND,
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
            return create_response(code=200, message="Taste not found")

        else:
            rabbitmq = UserActionService._get_rabbitmq_service()
            rabbitmq.send_taste_create(
                    taste_id=taste._id,
                    user_id=taste.userId,
                    dish_id=taste.dishId,
                    comment=taste.comment,
                    recommend_state=RecommendState.NOT_RECOMMEND,
                    media_ids=taste.mediaIds
                )

            taste.soft_delete()
            UserActionService._update_dish_recommend_count(taste.dishId)


            taste.recommendState = RecommendState.NOT_RECOMMEND.value
            taste.state = taste.calculate_state()

            db.session.commit()
            return create_response(code=0, message="Taste deleted successfully")

    @staticmethod
    def create_dish_ugc(user_id, merchant_id, name, price=None, media_ids=None, 
                       description=None, characteristic=None):
       
        try:
            
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            

            if media_ids:
                valid_media = Media.query.filter(Media._id.in_(media_ids)).all()
                if len(valid_media) != len(media_ids):
                    return create_response(code=400, message="Some media IDs are invalid")
            
            response=  DishManagementService.create_dish(
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
                        "dish_id": dish_id,
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