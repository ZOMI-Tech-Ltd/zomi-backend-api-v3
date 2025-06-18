from extensions import db
from models.thirdparty import ThirdPartyDelivery
from models.merchant import Merchant
from utils.response_utils import create_response

class DeliveryService:

    @staticmethod
    def get_merchant_delivery_links(merchant_id):
        """
        Get all available delivery links for a merchant
        
        Args:
            merchant_id (str): Merchant ID
            
        Returns:
            dict: Response with delivery links
        """
        try:
            # Get merchant
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            
            # Get all active delivery platforms
            platforms = ThirdPartyDelivery.get_all_active_platforms()
            
            delivery_links = []
            merchant_external_ids = merchant.get_all_external_ids()
            # print(merchant_external_ids)
            for platform in platforms:
                external_id = merchant_external_ids.get(platform.name)
                if external_id:
                    delivery_url = platform.construct_url(external_id)
                    if delivery_url:
                        delivery_links.append({
                            "id": platform._id,
                            "name": platform.name,
                            "redirect_url": delivery_url,
                            "icon": platform.icon,
                        })
            
            return create_response(
                code=0,
                data={
                    "merchant_id": merchant_id,
                    "merchant_name": merchant.name,
                    "delivery_links": delivery_links,
                    "total_platforms": len(delivery_links)
                },
                message="Success"
            )
            
        except Exception as e:
            print(f"Error getting merchant delivery links: {e}")
            return create_response(code=500, message="Failed to get delivery links")
    
    @staticmethod
    def get_delivery_link(merchant_id, platform_name):
        """
        Get delivery link for a specific merchant and platform
        
        Args:
            merchant_id (str): Merchant ID
            platform_key (str): Platform key (e.g., 'uber', 'skip')
            
        Returns:
            dict: Response with delivery link
        """
        try:
            # Get merchant
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            
            # Get platform
            platform = ThirdPartyDelivery.get_platform_by_name(platform_name)
            if not platform:
                return create_response(code=404, message="Delivery platform not found")
            
            # Get external ID
            external_id = merchant.get_external_id(platform_name)
            if not external_id:
                return create_response(
                    code=404, 
                    message=f"Merchant not available on {platform.name}"
                )
            
            # Construct URL
            delivery_url = platform.construct_url(external_id)
            if not delivery_url:
                return create_response(code=500, message="Failed to construct delivery URL")
            
            return create_response(
                code=0,
                data={
                    "merchant_id": merchant_id,
                    "merchant_name": merchant.name,
                    "platform_name": platform.name,
                    "platform_key": platform.name,
                    "delivery_url": delivery_url,
                    "external_id": external_id
                },
                message="Success"
            )
            
        except Exception as e:
            print(f"Error getting delivery link: {e}")
            return create_response(code=500, message="Failed to get delivery link")
    
    @staticmethod
    def create_delivery_platform(name, base_url):
        """
        Create a new delivery platform
        
        Args:
            name (str): Platform name
            platform_key (str): Unique platform key
            base_url (str): Base URL template
            
        Returns:
            dict: Response with created platform
        """
        try:
            # Check if platform key already exists
            existing = ThirdPartyDelivery.query.filter_by(name=name).first()
            if existing:
                return create_response(code=409, message="Platform key already exists")
            
            # Create new platform
            platform = ThirdPartyDelivery(
                name=name,
                base_url=base_url
            )
            
            db.session.add(platform)
            db.session.commit()
            
            return create_response(
                code=0,
                data={
                    "id": platform._id,
                    "name": platform.name,
                    "platform_key": platform.platform_key,
                    "base_url": platform.base_url
                },
                message="Delivery platform created successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating delivery platform: {e}")
            return create_response(code=500, message="Failed to create delivery platform")
    
    @staticmethod
    def update_merchant_external_ids(merchant_id, external_ids):
        """Update merchant's external IDs for delivery platforms"""
        try:
            merchant = Merchant.query.filter_by(_id=merchant_id).first()
            if not merchant:
                return create_response(code=404, message="Merchant not found")
            
            # Update external IDs
            merchant.external_ids = external_ids
            db.session.commit()
            
            return create_response(
                code=0,
                data={
                    "merchant_id": merchant_id,
                    "external_ids": external_ids
                },
                message="External IDs updated successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating merchant external IDs: {e}")
            return create_response(code=500, message="Failed to update external IDs")