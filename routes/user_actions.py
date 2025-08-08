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
            else:
                current_user_id = request.args.get('userId')
                return str(current_user_id)
    except Exception as e:
        print(f"JWT token validation failed: {e}")
    
    return None

@user_actions_bp.route('/taste/userTotal', methods=['POST'])
@jwt_required()
def get_user_taste_total():
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return create_response(code=200, message="User authentication required"), 200
    
    result = UserActionService.get_user_taste_total(
        user_id=current_user_id
    )
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message=result['msg']), 200
    else:
        return create_response(code=200, message=result['msg']), 200



@user_actions_bp.route('/taste/<string:taste_id>', methods=['GET'])
@jwt_required()
def get_taste(taste_id):
    current_user_id = get_current_user_id()
    
    if not current_user_id:
            return create_response(code=200, message="User authentication required"), 200
    
    result = UserActionService.get_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )
    
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message="Success"), 200
    else:
        return create_response(code=200, message=result['msg']), 200



@user_actions_bp.route('/taste/createMany', methods=['POST'])
@jwt_required()
def create_many_tastes():
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return create_response(code=200, message="User authentication required"), 200

    #iterate over items in request body
    items = request.get_json().get('items',[])

    results = []
    for item in items:
        result = UserActionService.create_taste(
            user_id=current_user_id,
            dish_id=item.get('dishId',""),
            comment=item.get('comment',""),
            media_ids=item.get('mediaIds',[]),
            mood=item.get('mood',0),
            tags=item.get('tags',[]),
        )
        results.append(result)
    print(results)
    if all(result['code'] == 0 for result in results):
        return create_response(code=0, data=results, message="Taste created successfully"), 200
    else:
        return create_response(code=200, message="Failed to create tastes"), 200



@user_actions_bp.route('/taste/create', methods=['POST'])
@jwt_required()
def create_taste():
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return create_response(code=200, message="User authentication required"), 200
    
    data = request.get_json()

    result = UserActionService.create_taste(
        user_id=current_user_id,
        dish_id=data.get('dishId',""),
        comment=data.get('comment',""),
        media_ids=data.get('mediaIds',[]),
        mood=data.get('mood',0),
        tags=data.get('tags',[]),
    )


    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message="Taste created successfully"), 200
    else:
        return create_response(code=200, message=result['msg']), 200




@user_actions_bp.route('/taste/edit/<string:taste_id>', methods=['POST'])
@jwt_required()
def edit_taste(taste_id):
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return create_response(code=200, message="User authentication required"), 200
    
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return create_response(code=200, message="Request body is required"), 200
    

    result = UserActionService.edit_taste(
        user_id=current_user_id,
        dish_id=data.get('dishId',""),
        comment=data.get('comment',""),
        media_ids=data.get('mediaIds', []),
        mood=data.get('mood', 0),
        tags=data.get('tags', []),
        taste_id=taste_id,
        recommend_state=data.get('recommendState', 1)
    )
    
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message="Taste updated successfully"), 200
    else:
        return create_response(code=200, message=result['msg']), 200


@user_actions_bp.route('/taste/delete', methods=['POST'])
@jwt_required()
def delete_taste():
    current_user_id = get_current_user_id()
        
    if not current_user_id:
        return create_response(code=200, message="User authentication required"), 200
    
    data = request.get_json()
    taste_id = data.get('id',"")

    result = UserActionService.delete_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )

    if result['code'] == 0:
        return create_response(code=0, message="Taste deleted successfully"), 200
    else:
        return create_response(code=200, message=result['msg']), 200





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
        return create_response(code=200, message="User authentication required"), 200
    
    result = UserActionService.get_user_merchant_items(
        user_id=current_user_id,
        merchant_id=merchant_id
    )
    
    # Response already formatted by service
    return create_response(code=0, data=result['data'], message=result['msg']), 200


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
        status_code = 0
    else:
        status_code = 200
    
    return create_response(code=status_code, data=result['data'], message=result['msg']), 200


@user_actions_bp.route('/dish/recommend/<string:dish_id>', methods=['DELETE'])
@jwt_required()
def unrecommend_dish(dish_id):

    current_user_id = get_current_user_id()

    result = UserActionService.unrecommend_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )

    if result['code']==0:
        status_code = 0
    else:
        status_code = 200

    return create_response(code=status_code, data=result['data'], message=result['msg']), 200



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
        status_code = 0
    else:   
        status_code = 0
    return create_response(code=status_code, data=result['data'], message=result['msg']), 200




@user_actions_bp.route('/dish/collect/<string:dish_id>', methods=['DELETE'])
@jwt_required()
def uncollect_dish(dish_id):
    current_user_id = get_current_user_id()
    result = UserActionService.uncollect_dish(
        user_id=current_user_id,
        dish_id=dish_id
    )
    
    return create_response(code=0, data=result['data'], message=result['msg']), 200


@user_actions_bp.route('/taste/like/<string:taste_id>', methods=['POST'])
@jwt_required()
def like_taste(taste_id):
    current_user_id = get_current_user_id()
    result = UserActionService.like_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )
    
    return create_response(code=0, data=result['data'], message=result['msg']), 200


@user_actions_bp.route('/taste/like/<string:taste_id>', methods=['DELETE'])
@jwt_required()
def unlike_taste(taste_id):
    current_user_id = get_current_user_id()
    result = UserActionService.unlike_taste(
        user_id=current_user_id,
        taste_id=taste_id
    )

    return create_response(code=0, data=result['data'], message=result['msg']), 200



# Add this new route for UGC dish creation
@user_actions_bp.route('/taste/addDish', methods=['POST'])
@jwt_required(optional=True)
def add_dish_ugc():

    current_user_id = get_current_user_id()
    
    # if not current_user_id:
    #     return create_response(code=200, message="User authentication required"), 200
    
    data = request.get_json()
    if not data:
        return create_response(code=200, message="Request body is required"), 200
    
    if not data.get('merchantId'):
        return create_response(code=200, message="Merchant ID is required"), 200
    
    if not data.get('name'):
        return create_response(code=200, message="Dish name is required"), 200
    

    result = UserActionService.create_dish_ugc(
        user_id=current_user_id,
        merchant_id=data.get('merchantId'),
        name=data.get('name'),
        price=data.get('price',0),
        media_ids=data.get('mediaIds',[]),
        description=data.get('description',''),
        characteristic=data.get('characteristic','')
    )
    

    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message=result['msg']), 200
    else:
        return create_response(code=200, message=result['msg']), 200
