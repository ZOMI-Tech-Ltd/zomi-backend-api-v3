from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.delivery import DeliveryService
from utils.response_utils import create_response
from models.thirdparty import ThirdPartyDelivery

delivery_bp = Blueprint('delivery', __name__, url_prefix='/v3/delivery')

@delivery_bp.route('/merchant/<string:merchant_id>/links', methods=['GET'])
def get_merchant_delivery_links(merchant_id):
    """
    Get all available delivery links for a merchant
    
    Path Parameters:
        merchant_id: The merchant ID
        
    Returns:
        JSON with delivery links for the merchant
    """
    result = DeliveryService.get_merchant_delivery_links(merchant_id)
    
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message=result['msg']), 200
    else:
        return create_response(code=result['code'], message=result['msg']), result['code']


@delivery_bp.route('/merchant/<string:merchant_id>/platform/<string:platform_key>', methods=['GET'])
def get_delivery_link(merchant_id, platform_key):
    """
    Get delivery link for a specific merchant and platform
    
    Path Parameters:
        merchant_id: The merchant ID
        platform_key: The platform key (e.g., 'uber', 'skip')
        
    Query Parameters:
        redirect: If 'true', redirect to the delivery URL instead of returning JSON
        
    Returns:
        JSON with delivery link or redirect to the delivery platform
    """
    should_redirect = request.args.get('redirect', '').lower() == 'true'
    
    result = DeliveryService.get_delivery_link(merchant_id, platform_key)
    
    if result['code'] == 0:
        if should_redirect:
            # Redirect to the delivery platform
            delivery_url = result['data']['delivery_url']
            return redirect(delivery_url, code=302)
        else:
            # Return JSON response
            return create_response(code=0, data=result['data'], message=result['msg']), 200
    else:
        if should_redirect:
            # If redirect was requested but failed, return a 404 page or error
            return create_response(code=result['code'], message=result['msg']), result['code']
        else:
            return create_response(code=result['code'], message=result['msg']), result['code']


@delivery_bp.route('/platforms', methods=['GET'])
def get_all_platforms():
    """
    Get all available delivery platforms
    
    Returns:
        JSON with list of all active delivery platforms
    """
    try:
        
        platforms = ThirdPartyDelivery.get_all_active_platforms()
        
        platform_data = []
        for platform in platforms:
            platform_data.append({
                "id": platform._id,
                "name": platform.name,
                "platform_key": platform.platform_key,
                "base_url": platform.base_url,
                "is_active": platform.is_active
            })
        
        return create_response(
            code=0,
            data={
                "platforms": platform_data,
                "total": len(platform_data)
            },
            message="Success"
        ), 200
        
    except Exception as e:
        print(f"Error getting platforms: {e}")
        return create_response(code=500, message="Failed to get platforms"), 500


@delivery_bp.route('/platforms', methods=['POST'])
@jwt_required()
def create_delivery_platform():
    """
    Create a new delivery platform (Admin only)
    
    Request Body:
        {
            "name": "Platform Name",
            "platform_key": "platform_key",
            "base_url": "https://platform.com/restaurant/{external_id}"
        }
        
    Returns:
        JSON with created platform information
    """
    data = request.get_json()
    
    if not data:
        return create_response(code=400, message="Request body is required"), 400
    
    name = data.get('name')
    platform_key = data.get('platform_key')
    base_url = data.get('base_url')
    
    if not all([name, platform_key, base_url]):
        return create_response(
            code=400, 
            message="Name, platform_key, and base_url are required"
        ), 400
    
    result = DeliveryService.create_delivery_platform(name, platform_key, base_url)
    
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message=result['msg']), 201
    else:
        return create_response(code=result['code'], message=result['msg']), result['code']


@delivery_bp.route('/merchant/<string:merchant_id>/external-ids', methods=['PUT'])
@jwt_required()
def update_merchant_external_ids(merchant_id):
    """
    Update merchant's external IDs for delivery platforms (Admin only)
    
    Path Parameters:
        merchant_id: The merchant ID
        
    Request Body:
        {
            "external_ids": {
                "uber": "restaurant_123",
                "skip": "store_456",
                "doordash": "merchant_789"
            }
        }
        
    Returns:
        JSON confirmation of update
    """
    data = request.get_json()
    
    if not data or 'external_ids' not in data:
        return create_response(code=400, message="external_ids field is required"), 400
    
    external_ids = data['external_ids']
    
    if not isinstance(external_ids, dict):
        return create_response(code=400, message="external_ids must be a dictionary"), 400
    
    result = DeliveryService.update_merchant_external_ids(merchant_id, external_ids)
    
    if result['code'] == 0:
        return create_response(code=0, data=result['data'], message=result['msg']), 200
    else:
        return create_response(code=result['code'], message=result['msg']), result['code']


@delivery_bp.route('/merchant/<string:merchant_id>/external-ids', methods=['GET'])
def get_merchant_external_ids(merchant_id):
    """
    Get merchant's external IDs for delivery platforms
    
    Path Parameters:
        merchant_id: The merchant ID
        
    Returns:
        JSON with merchant's external IDs
    """
    try:
        from models.merchant import Merchant
        
        merchant = Merchant.query.filter_by(_id=merchant_id).first()
        if not merchant:
            return create_response(code=404, message="Merchant not found"), 404
        
        return create_response(
            code=0,
            data={
                "merchant_id": merchant_id,
                "merchant_name": merchant.name,
                "external_ids": merchant.get_all_external_ids()
            },
            message="Success"
        ), 200
        
    except Exception as e:
        print(f"Error getting merchant external IDs: {e}")
        return create_response(code=500, message="Failed to get external IDs"), 500