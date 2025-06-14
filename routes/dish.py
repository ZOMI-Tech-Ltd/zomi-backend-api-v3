from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.dish_service import DishService
from routes.user_actions import get_current_user_id

from utils.response_utils import create_response


dish_bp = Blueprint('dish', __name__, url_prefix='/v3/dish')




def get_current_user_id():
    current_user_id = None
    if request.headers.get('Authorization') and request.headers.get('Authorization').startswith('Bearer '):
        current_user_id = get_jwt_identity()

    return current_user_id



@dish_bp.route('/<string:dish_id>/overview', methods=['GET'])
@jwt_required()
def get_dish_overview(dish_id):
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)



    current_user_id = get_current_user_id()

    response = DishService.get_dish_overview(dish_id, lat, lon, current_user_id)
    
    if response['code'] == 0:
        return create_response(code=0,data=response['data'], message=response['msg']), 200
    
    else:
        return create_response(code=response['code'], data=response['data'], message=response['msg']), response['code']
    
    
    
