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



    def get_icon_dimensions(self, obj):
        return getattr(obj, '_icon_dimensions', None)
        
    
    def get_delivery_links(self, obj):
        if not hasattr(obj, '_delivery_links_cache'):
            
            delivery_links = []
            
            if obj.external_ids:
                # Get all active platforms
                platforms = ThirdPartyDelivery.get_all_active_platforms()
                
                for platform in platforms:
                    external_id = obj.external_ids.get(platform.platform_key)
                    if external_id:
                        delivery_url = platform.construct_url(external_id)
                        if delivery_url:
                            delivery_links.append({
                                "platform_name": platform.name,
                                "platform_key": platform.platform_key,
                                "delivery_url": delivery_url
                            })
            
            obj._delivery_links_cache = delivery_links
        
        return obj._delivery_links_cache

    class Meta:
        fields = ('_id', 'name', 'opening', 'distance_km', 'icon', 'icon_dimensions')


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