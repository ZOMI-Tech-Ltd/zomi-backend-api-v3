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
    merchant = ma.Nested(MerchantSchema, only=('_id', 'name', 'opening', 'distance_km', 'icon', 'icon_dimensions', 'webUrl', 'thirdPartyDeliveryItems'))


    #tag fields
    flavorTags = ma.Method('get_ai_flavor_tags', allow_none=True)
    uniqueTags = ma.Method('get_ai_unique_tags', allow_none=True)

    #ingredients
    ingredients = ma.Method('get_ingredients', required=False, dump_default=None)

    #description
    description = ma.Str(required=False, dump_default=None)

    #new fields for show if current user collected or recommended
    isCollected = ma.Boolean(attribute='_is_collected', dump_only=True)
    isRecommended = ma.Boolean(attribute='_is_recommended', dump_only=True)





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

    def get_ingredients(self, obj):
        return getattr(obj, '_ingredients_data', [])
    

    def get_ai_flavor_tags(self, obj):
        flavor_tags = getattr(obj, '_ai_flavor_tags', [])
        if not flavor_tags:
            return None
        return [tag['text'] for tag in flavor_tags]
    
    def get_ai_unique_tags(self, obj):
        unique_tags = getattr(obj, '_ai_unique_tags', [])
        if not unique_tags:
            return []
        
        return [tag['text'] for tag in unique_tags]



    class Meta:
        fields = (
            '_id', 'title', 'images', 
            'price', 'ratings',
                'recommendedCount', 'merchant', 'flavorTags', 
                'uniqueTags', 'ingredients', 'description', 'isCollected', 'isRecommended'
        )



class DishFlavorProfileSchema(ma.Schema):
    
    dish_id = ma.String(required=True)
    generated_tags = ma.List(ma.Dict(), required=True)
    cuisine = ma.String(allow_none=True)
    main_ingredients = ma.Raw(allow_none=True)
    cooking_methods = ma.List(ma.String(), allow_none=True)
    allergens = ma.Raw(allow_none=True)
    confidence = ma.Raw(required=True)
    needs_review = ma.Boolean(allow_none=True)
    raw_scores = ma.Dict(allow_none=True)
    
    class Meta:
        fields = (
            'dish_id', 'generated_tags', 'cuisine', 'main_ingredients',
            'cooking_methods', 'allergens', 'confidence', 'needs_review', 'raw_scores'
        )


dish_overview_schema = DishOverviewSchema()
dish_flavor_profile_schema = DishFlavorProfileSchema()