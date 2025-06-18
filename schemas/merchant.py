from extensions import ma
from utils.img_util import get_image_dimensions_safe
from models.thirdparty import ThirdPartyDelivery

class MerchantSchema(ma.Schema):

    _id = ma.String(required=True)
    name = ma.Str(required=True)
    opening = ma.Int(required=True)
    distance_km = ma.Float(attribute='_distance_km', dump_only=True)
    icon = ma.Str(required= False, allow_none=True)
    icon_dimensions = ma.Method('get_icon_dimensions', allow_none=True)

    delivery_links = ma.Method('get_delivery_links', allow_none=True)
    external_ids = ma.Raw(dump_only=True)

    verified = ma.Boolean(required=False, dump_default=False)
    webUrl = ma.Method('get_website_if_verified', allow_none=True)

    thirdPartyDeliveryItems = ma.Method('get_third_party_delivery_items', allow_none=True)

    def get_icon_dimensions(self, obj):
        return getattr(obj, '_icon_dimensions', None)
        



    def get_website_if_verified(self, obj):
        if getattr(obj, 'isVerified',False) and hasattr(obj, 'website'):
            return obj.website
        return None
    


    def get_third_party_delivery_items(self, obj):
        if not hasattr(obj, '_third_party_delivery_items_cache'):
            obj._third_party_delivery_items_cache = []
            platforms = ThirdPartyDelivery.get_all_active_platforms()
            merchant_external_ids = obj.get_all_external_ids()
                
            for platform in platforms:
                external_id = merchant_external_ids.get(platform.name)
                if external_id:
                    delivery_url = platform.construct_url(external_id)
                    if delivery_url:
                        obj._third_party_delivery_items_cache.append(
                        {
                            "id": platform._id,
                            "name": platform.name,
                            "redirect_url": delivery_url,
                            "icon": platform.icon
                        })
        
        return obj._third_party_delivery_items_cache

    class Meta:
        fields = ('_id', 'name', 'opening', 'distance_km', 'icon', 'icon_dimensions', 'webUrl', 'thirdPartyDeliveryItems')


class MerchantDeliverySchema(ma.Schema):
    
    _id = ma.String(required=True)
    name = ma.Str(required=True)
    delivery_links = ma.Method('get_delivery_links')
    
    def get_delivery_links(self, obj):
        delivery_links = []
        
        if obj.external_ids:
            platforms = ThirdPartyDelivery.get_all_active_platforms()
            
            for platform in platforms:
                external_id = obj.external_ids.get(platform.platform_key)
                if external_id:
                    delivery_url = platform.construct_url(external_id)
                    if delivery_url:
                        delivery_links.append({
                            "platform_id": platform._id,
                            "platform_name": platform.name,
                            "platform_key": platform.platform_key,
                            "delivery_url": delivery_url,
                            "external_id": external_id
                        })
        
        return delivery_links
    
    class Meta:
        fields = ('_id', 'name', 'delivery_links')


merchant_schema = MerchantSchema()
merchant_delivery_schema = MerchantDeliverySchema()