from extensions import db
from models.dish import Dish
from models.merchant import Merchant
from models.collection import Collection
from models.taste import Taste
from utils.response_utils import create_response
from schemas.dish import dish_overview_schema

from utils.geo_utils import haversine
from utils.img_util import get_image_dimensions_safe
import requests


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




            try:
                
                ingredient_api_url = f"{INGREDIENT_API_BASE_URL}?dishId={dish_id}&num_tags=5"
                response = requests.get(ingredient_api_url, timeout=3) 
                response.raise_for_status()
                ingredients_data = response.json()


                if isinstance(ingredients_data, dict) and "data" in ingredients_data:
                    ingredients_data = ingredients_data["data"]
                    
                elif not isinstance(ingredients_data, list):
                    print(f"Unexpected ingredient API response for dish {dish_id}: {ingredients_data}")
                    ingredients_data = None
                
            except requests.exceptions.Timeout:
                print(f"Ingredient API timeout for dish {dish_id}")
                ingredients_data = None
            except requests.exceptions.RequestException as e:
                print(f"Error calling Ingredient API for dish {dish_id}: {e}")
                ingredients_data = None
            
            dish._ingredients_data = ingredients_data


            #logic for show if current user collected or recommended
            is_collected = False
            is_recommended = False

            if current_user_id:
                is_collected = Collection.query.filter_by(
                    user=current_user_id,
                    object=dish_id
                ).first() is not None
                
                is_recommended = Taste.query.filter_by(
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
    

