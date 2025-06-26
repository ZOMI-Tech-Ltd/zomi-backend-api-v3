from extensions import db
from models.dish import Dish
from models.merchant import Merchant
from models.collection import Collection
from models.taste import Taste
from models.thirdparty import ThirdPartyDelivery
from utils.response_utils import create_response
from schemas.dish import dish_overview_schema


from services.tag_gen import FlavorTagService
from utils.geo_utils import haversine
from utils.img_util import get_image_dimensions_safe
import requests
from models.dish_profile import DishProfile

import os
import dotenv

dotenv.load_dotenv()

INGREDIENT_API_BASE_URL = os.getenv('INGREDIENT_API_BASE_URL')


class DishService:
    @staticmethod
    def get_dish_overview(dish_id, user_lat, user_lon, current_user_id):
        try:
            dish = db.session.query(Dish).options(
                db.joinedload(Dish.merchant)
            ).filter(Dish._id == dish_id).first()
        

            if not dish:
                return None,'Dish not found' , 404

            merchant = dish.merchant
            distance = None

            if user_lat and user_lon:
                if merchant.latitude is not None and merchant.longitude is not None:
                    try:
                        distance = haversine(user_lat, user_lon, merchant.latitude, merchant.longitude)
                        merchant._distance_km = distance

                    except Exception as e:
                        merchant._distance_km = None

            else:
                merchant._distance_km = None


            #fetch icon dimensions
            if merchant.icon:

                merchant._icon_dimensions = get_image_dimensions_safe(merchant.icon)
            else:
                merchant._icon_dimensions = None




            dish_profile = DishProfile.query.filter_by(dish_id=dish_id).first()

            if dish_profile:
                ai_tags = FlavorTagService.generate_flavor_tags(dish_profile)
                formatted_tags = FlavorTagService.format_tags_for_display(ai_tags)


                dish._ai_flavor_tags  = [tag for tag in formatted_tags
                                        if tag['category'] in ['basic_flavor', 'detail_flavor', 'texture']]
                dish._ai_unique_tags  = [tag['tag'] for tag in formatted_tags
                                         if tag['category'] == ['texture', 'combined_texture', 'cuisine']]
            else:
                dish._ai_flavor_tags = []
                dish._ai_unique_tags = []

            #logic for show if current user collected or recommended
            is_collected = False
            is_recommended = False

            if current_user_id:
                is_collected = Collection.active_collections().filter_by(
                    user=current_user_id,
                    object=dish_id
                ).first() is not None
                
                is_recommended = Taste.active_tastes().filter_by(
                    userId=current_user_id,
                    dishId=dish_id
                ).first() is not None
    

            dish._is_collected = is_collected
            dish._is_recommended = is_recommended

            
    
            

            result = dish_overview_schema.dump(dish)

            return create_response(code=0, data=result, message="Success")
        
        except Exception as e:
            print(f"Error getting dish overview: {e}")
            return create_response(code=500, message="Failed to get dish overview", data=None)
    

    @staticmethod
    def get_dish_flavor_profile(dish_id):

        try:
            dish_profile = DishProfile.query.filter_by(dish_id=dish_id).first()
            
            if not dish_profile:
                return create_response(code=404, message="Dish flavor profile not found", data=None)
            
            
            ai_tags = FlavorTagService.generate_flavor_tags(dish_profile, max_tags=10)
            
            profile_data = {
                'dish_id': dish_id,
                'generated_tags': ai_tags,
                'cuisine': dish_profile.background_cuisine,
                'main_ingredients': dish_profile.ingredients_main,
                'cooking_methods': dish_profile.ingredients_methods,
                'needs_review': dish_profile.needs_review,
                
                'raw_scores': {
                    'basic_flavors': {
                        'sweet': dish_profile.basic_sweet,
                        'sour': dish_profile.basic_sour,
                        'salty': dish_profile.basic_salty,
                        'spicy': dish_profile.basic_spicy,
                        'umami': dish_profile.basic_umami,
                        'rich': dish_profile.basic_greasy,
                        'savory': dish_profile.basic_fat_richness
                    },
                    'detail_flavors': {
                        'smoky': dish_profile.detail_smoky,
                        'roasted': dish_profile.detail_roasted,
                        'caramelized': dish_profile.detail_caramelized,
                        'fruity': dish_profile.detail_fruity,
                        'herbal': dish_profile.detail_herbal,
                        'nutty': dish_profile.detail_nutty,
                        'meaty': dish_profile.detail_meaty,
                        'marine': dish_profile.detail_marine
                    },
                    'textures': {
                        'crispy': dish_profile.texture_crispiness,
                        'crunchy': dish_profile.texture_crunchiness,
                        'tender': dish_profile.texture_tenderness,
                        'juicy': dish_profile.texture_juiciness,
                        'creamy': dish_profile.texture_creaminess,
                        'smooth': dish_profile.texture_smoothness
                    }
                }
            }
            
            return create_response(code=0, data=profile_data, message="Success")
            
        except Exception as e:
            print(f"Error getting dish flavor profile: {e}")
            return create_response(code=500, message="Failed to get flavor profile", data=None)