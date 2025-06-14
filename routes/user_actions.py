from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.user_action_service import UserActionService
from utils.response_utils import create_response


user_actions_bp = Blueprint('user_actions', __name__, url_prefix='/v3')



def get_current_user_id():
    """
    Helper function to extract user ID from JWT token or query parameters.
    Provides fallback mechanism for development/testing.
    
    Returns:
        str: User ID if found, None otherwise
    """
    current_user_id = None
    
    # Try to get from JWT token first
    try:
        if request.headers.get('Authorization') and request.headers.get('Authorization').startswith('Bearer '):
            current_user_id = get_jwt_identity()
            if current_user_id:
                return str(current_user_id)
    except Exception as e:
        print(f"JWT token validation failed: {e}")
    
    # Fallback to query parameter (for development/testing)
    user_id_param = request.args.get('user_id')
    if user_id_param:
        return str(user_id_param)
    
    return None


@user_actions_bp.route('/merchant/<string:merchant_id>/user-items', methods=['GET'])
@jwt_required()
def get_user_merchant_items(merchant_id):
    """
    Get user's collected and recommended dishes within a specific merchant.
    
    Path Parameters:
        merchant_id: The merchant ID
        
    Returns:
        JSON with two lists: collected dishes and recommended dishes
    """
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return create_response(code=401, message="User authentication required"), 401
    
    result = UserActionService.get_user_merchant_items(
        user_id=current_user_id,
        merchant_id=merchant_id
    )
    
    # Response already formatted by service
    return jsonify(result), result.get('code', 0) == 0 and 200 or 404


# recommend dish
@user_actions_bp.route('/dish/recommend/<string:dish_id>', methods=['POST'])
@jwt_required()
def recommend_dish(dish_id):
    # current_user_id = get_jwt_identity()
    current_user_id = get_current_user_id()

    result = UserActionService.recommend_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )
    
    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code


@user_actions_bp.route('/dish/recommend/<string:dish_id>', methods=['DELETE'])
@jwt_required()
def unrecommend_dish(dish_id):

    current_user_id = get_current_user_id()

    result = UserActionService.unrecommend_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )

    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code



# collect dish
@user_actions_bp.route('/dish/collect/<string:dish_id>', methods=['POST'])
@jwt_required()
def collect_dish(dish_id):
    current_user_id = get_current_user_id()
    result = UserActionService.collect_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )
    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code




@user_actions_bp.route('/dish/collect/<string:dish_id>', methods=['DELETE'])
@jwt_required()
def uncollect_dish(dish_id):
    current_user_id = get_current_user_id()
    result = UserActionService.uncollect_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )
    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code


@user_actions_bp.route('/taste/like/<string:taste_id>', methods=['POST'])
@jwt_required()
def like_taste(taste_id):
    current_user_id = get_current_user_id()
    result = UserActionService.like_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )
    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code


@user_actions_bp.route('/taste/like/<string:taste_id>', methods=['DELETE'])
@jwt_required()
def unlike_taste(taste_id):
    current_user_id = get_current_user_id()
    result = UserActionService.unlike_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )
    if result['code']==0:
        status_code = 200
    elif result['code']==409:
        status_code = 409
    else:
        status_code = 404
    return create_response(code=result['code'], data=result['data'], message=result['msg']), status_code
