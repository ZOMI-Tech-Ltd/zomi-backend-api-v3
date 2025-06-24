from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.dish_service import DishService
from routes.user_actions import get_current_user_id
from schemas.dish import dish_overview_schema, dish_flavor_profile_schema
from utils.response_utils import create_response


dish_bp = Blueprint('dish', __name__, url_prefix='/v3/dish')




def get_current_user_id():
    current_user_id = None
    if request.headers.get('Authorization') and request.headers.get('Authorization').startswith('Bearer '):
        current_user_id = get_jwt_identity()
    else:
        current_user_id = None
    return current_user_id



@dish_bp.route('/<string:dish_id>/overview', methods=['GET'])
@jwt_required(optional=True)
def get_dish_overview(dish_id):
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)



    current_user_id = get_current_user_id()

    response = DishService.get_dish_overview(dish_id, lat, lon, current_user_id)
    
    if response['code'] == 0:
        return create_response(code=0,data=response['data'], message=response['msg']), 200
    
    else:
        return create_response(code=200, data=response['data'], message=response['msg']), 200
    
    

    
@dish_bp.route('/<string:dish_id>/flavor-profile', methods=['GET'])
@jwt_required(optional=True)
def get_dish_flavor_profile(dish_id):
    """
    Get detailed AI-generated flavor profile for a dish
    
    Returns:
        JSON with comprehensive flavor analysis, raw scores, and confidence data
        Useful for admin interfaces, debugging, or detailed flavor exploration
    """
    response = DishService.get_dish_flavor_profile(dish_id)
    
    if response['code'] == 0:
        return create_response(code=0, data=response['data'], message=response['msg']), 200
    else:
        return create_response(code=response['code'], data=response['data'], message=response['msg']), 200


@dish_bp.route('/batch/flavor-tags', methods=['POST'])
@jwt_required(optional=True)
def get_batch_flavor_tags():
    """
    Get AI flavor tags for multiple dishes (batch endpoint)
    
    Request Body:
        {
            "dish_ids": ["dish1", "dish2", "dish3"],
            "max_tags": 5  // optional, default 5
        }
    
    Returns:
        JSON with flavor tags for each requested dish
    """
    try:
        data = request.get_json()
        dish_ids = data.get('dish_ids', [])
        max_tags = data.get('max_tags', 5)
        
        if not dish_ids or not isinstance(dish_ids, list):
            return create_response(code=400, message="dish_ids must be a non-empty list"), 400
        
        if len(dish_ids) > 50:  # Reasonable limit
            return create_response(code=400, message="Maximum 50 dishes per batch request"), 400
        
        # Import here to avoid circular imports
        from models.dish_profile import DishProfile
        from services.flavor_tag_service import FlavorTagService
        
        # Fetch profiles for all requested dishes
        profiles = DishProfile.query.filter(DishProfile.dish_id.in_(dish_ids)).all()
        profile_map = {profile.dish_id: profile for profile in profiles}
        
        results = {}
        for dish_id in dish_ids:
            if dish_id in profile_map:
                ai_tags = FlavorTagService.generate_flavor_tags(profile_map[dish_id], max_tags=max_tags)
                formatted_tags = FlavorTagService.format_tags_for_display(ai_tags)
                
                results[dish_id] = {
                    'flavor_tags': [tag['text'] for tag in formatted_tags 
                                   if tag['category'] in ['basic_flavor', 'detail_flavor', 'combined_flavor']],
                    'unique_tags': [tag['text'] for tag in formatted_tags 
                                   if tag['category'] in ['texture', 'combined_texture', 'cuisine']],
                    'all_tags': formatted_tags
                }
            else:
                results[dish_id] = {
                    'flavor_tags': [],
                    'unique_tags': [],
                    'all_tags': [],
                    'error': 'No AI profile found'
                }
        
        return create_response(
            code=0, 
            data={
                'results': results,
                'total_requested': len(dish_ids),
                'total_found': len(profiles)
            }, 
            message="Success"
        ), 200
        
    except Exception as e:
        print(f"Error in batch flavor tags: {e}")
        return create_response(code=500, message="Failed to get batch flavor tags"), 500