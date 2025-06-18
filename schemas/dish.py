from extensions import ma
from schemas.merchant import MerchantSchema
from models.media import Media


class DishOverviewSchema(ma.Schema):


    #basic info
    _id = ma.String(required=True)
    title = ma.Str(required=True)
    price = ma.Integer(required=True)

    #images
    images = ma.Method('get_image_data', allow_none=True)

    #ratings
    # uber_eats_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # skip_the_dishes_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # fantuan_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # gm_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # doordash_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # open_table_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    # yelp_rating = ma.Float(required=False, allow_none=True, dump_default=None)
    ratings = ma.Method('get_ratings', allow_none=True)
    
    #recommended count in ZOMI
    recommendedCount = ma.Integer(required= True, dump_default=None)

    #merchant info
    merchant = ma.Nested(MerchantSchema, only=('_id', 'name', 'opening', 'distance_km', 'icon', 'icon_dimensions'))


    #tag fields
    flavorTags = ma.List(ma.Str, required=True,allow_none=True, dump_default=None)
    uniqueTags = ma.List(ma.Str, required=True,allow_none=True, dump_default=None)

    #ingredients
    ingredients = ma.Method('get_ingredients', required=False, dump_default=None)

    #description
    description = ma.Str(required=False, dump_default=None)

    #new fields for show if current user collected or recommended
    isCollected = ma.Boolean(attribute='_is_collected', dump_only=True)
    isRecommended = ma.Boolean(attribute='_is_recommended', dump_only=True)

    thirdPartyDeliveryItems = ma.List(ma.Dict, attribute='_third_party_delivery_items', dump_only=True, allow_none = True)

    def get_image_data(self, obj):
        if not obj.media:
            return None

        media_item_data = obj.media[0] if obj.media else None
        
        media_id = media_item_data.get("mediaId")

        if not media_id:
            return None
        
        media_item = Media.query.get(media_id)

        width = None
        height = None

        if media_item.width:
            if isinstance(media_item.width, (int, float)):
                width = media_item.width

            elif isinstance(media_item.width, dict):
                width = media_item.width.get('value') or media_item.width.get('width')
            
            elif isinstance(media_item.width, list) and len(media_item.width) > 0:
                width = media_item.width[0]

        if media_item.height:
            if isinstance(media_item.height, (int, float)):
                height = media_item.height

            elif isinstance(media_item.height, dict):
                height = media_item.height.get('value') or media_item.height.get('height')

            elif isinstance(media_item.height, list) and len(media_item.height) > 0:
                height = media_item.height[0]



        return {
            'url': media_item.url,
            'height': height,
            'width': width
        } 

    def get_ratings(self, obj):
        return {
            "uber_eats": getattr(obj, 'uber_eats_rating', None),
            "skip_the_dishes": getattr(obj, 'skip_the_dishes_rating', None),
            "fantuan": getattr(obj, 'fantuan_rating', None),
            "google_maps": getattr(obj, 'gm_rating', None),
            "doordash": getattr(obj, 'doordash_rating', None),
            "open_table": getattr(obj, 'open_table_rating', None),
            "yelp": getattr(obj, 'yelp_rating', None)
        }

    def get_third_party_delivery_items(self, obj):
        return {}

    def get_ingredients(self, obj):
        return getattr(obj, '_ingredients_data', [])
    

    class Meta:
        fields = (
            '_id', 'title', 'images', 
            'price', 'ratings',
                'recommendedCount', 'merchant', 'flavorTags', 
                'uniqueTags', 'ingredients', 'description', 'isCollected', 'isRecommended', 'thirdPartyDeliveryItems'
        )

dish_overview_schema = DishOverviewSchema()
