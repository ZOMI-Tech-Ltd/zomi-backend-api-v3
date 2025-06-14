from extensions import ma
from utils.img_util import get_image_dimensions_safe

class MerchantSchema(ma.Schema):

    _id = ma.String(required=True)
    name = ma.Str(required=True)
    opening = ma.Int(required=True)
    distance_km = ma.Float(attribute='_distance_km', dump_only=True)
    icon = ma.Str(required= False, allow_none=True)
    icon_dimensions = ma.Method('get_icon_dimensions', allow_none=True)

    def get_icon_dimensions(self, obj):
        return getattr(obj, '_icon_dimensions', None)
        
        
        


    class Meta:
        fields = ('_id', 'name', 'opening', 'distance_km', 'icon', 'icon_dimensions')

