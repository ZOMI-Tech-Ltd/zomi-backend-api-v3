from extensions import db
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean

from extensions import db
from sqlalchemy.dialects.postgresql import JSON

class DishProfile(db.Model):
    
    __tablename__ = 'dwd_dish_profile_batch'
    __table_args__ = {'schema': 'model_result'}

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.String(64), nullable=False)
    dish_id = db.Column(db.String(64), nullable=False)
    
    # Texture scalars
    texture_dryness = db.Column('flavor/texture_scalar/dryness', db.Float)
    texture_hardness = db.Column('flavor/texture_scalar/hardness', db.Float)
    texture_chewiness = db.Column('flavor/texture_scalar/chewiness', db.Float)
    texture_juiciness = db.Column('flavor/texture_scalar/juiciness', db.Float)
    texture_moistness = db.Column('flavor/texture_scalar/moistness', db.Float)
    texture_creaminess = db.Column('flavor/texture_scalar/creaminess', db.Float)
    texture_crispiness = db.Column('flavor/texture_scalar/crispiness', db.Float)
    texture_smoothness = db.Column('flavor/texture_scalar/smoothness', db.Float)
    texture_stickiness = db.Column('flavor/texture_scalar/stickiness', db.Float)
    texture_tenderness = db.Column('flavor/texture_scalar/tenderness', db.Float)
    texture_crunchiness = db.Column('flavor/texture_scalar/crunchiness', db.Float)
    texture_springiness = db.Column('flavor/texture_scalar/springiness', db.Float)
    
    # Basic flavor scalars
    basic_sour = db.Column('flavor/basic_flavor_scalar/sour', db.Float)
    basic_salty = db.Column('flavor/basic_flavor_scalar/salty', db.Float)
    basic_spicy = db.Column('flavor/basic_flavor_scalar/spicy', db.Float)
    basic_sweet = db.Column('flavor/basic_flavor_scalar/sweet', db.Float)
    basic_umami = db.Column('flavor/basic_flavor_scalar/umami', db.Float)
    basic_greasy = db.Column('flavor/basic_flavor_scalar/greasy', db.Float)
    basic_bitterness = db.Column('flavor/basic_flavor_scalar/bitterness', db.Float)
    basic_astringency = db.Column('flavor/basic_flavor_scalar/astringency', db.Float)
    basic_fat_richness = db.Column('flavor/basic_flavor_scalar/fat_richness', db.Float)
    
    # Detail flavor scalars
    detail_burnt = db.Column('flavor/detail_flavor_scalar/burnt', db.Float)
    detail_dairy = db.Column('flavor/detail_flavor_scalar/dairy', db.Float)
    detail_meaty = db.Column('flavor/detail_flavor_scalar/meaty', db.Float)
    detail_nutty = db.Column('flavor/detail_flavor_scalar/nutty', db.Float)
    detail_smoky = db.Column('flavor/detail_flavor_scalar/smoky', db.Float)
    detail_earthy = db.Column('flavor/detail_flavor_scalar/earthy', db.Float)
    detail_floral = db.Column('flavor/detail_flavor_scalar/floral', db.Float)
    detail_fruity = db.Column('flavor/detail_flavor_scalar/fruity', db.Float)
    detail_herbal = db.Column('flavor/detail_flavor_scalar/herbal', db.Float)
    detail_marine = db.Column('flavor/detail_flavor_scalar/marine', db.Float)
    detail_toasty = db.Column('flavor/detail_flavor_scalar/toasty', db.Float)
    detail_citrusy = db.Column('flavor/detail_flavor_scalar/citrusy', db.Float)
    detail_peppery = db.Column('flavor/detail_flavor_scalar/peppery', db.Float)
    detail_roasted = db.Column('flavor/detail_flavor_scalar/roasted', db.Float)
    detail_fermented = db.Column('flavor/detail_flavor_scalar/fermented', db.Float)
    detail_medicinal = db.Column('flavor/detail_flavor_scalar/medicinal', db.Float)
    detail_sulfurous = db.Column('flavor/detail_flavor_scalar/sulfurous', db.Float)
    detail_caramelized = db.Column('flavor/detail_flavor_scalar/caramelized', db.Float)
    detail_offal_gamey = db.Column('flavor/detail_flavor_scalar/offal_gamey', db.Float)
    detail_spice_aroma = db.Column('flavor/detail_flavor_scalar/spice_aroma', db.Float)
    
    # Allergy and business info
    business_name = db.Column('business/name', db.Text)
    business_dish_id = db.Column('business/dish_id', db.Text)
    business_name_zh = db.Column('business/name_zh', db.Text)
    business_category = db.Column('business/category', db.Text)
    business_store_id = db.Column('business/store_id', db.Text)
    business_store_name = db.Column('business/store_name', db.Text)
    business_category_id = db.Column('business/category_id', db.Text)
    business_description = db.Column('business/description', db.Text)
    
    # Background and ingredients
    background_cuisine = db.Column('background/cuisine', db.Text)
    ingredients_main = db.Column('ingredients/main', JSON)
    ingredients_methods = db.Column('ingredients/methods', db.ARRAY(db.Text))
    
    
    needs_review = db.Column(db.Boolean)
    
    
    def __repr__(self):
        return f"<DishProfile(dish_id={self.dish_id}, merchant_id={self.merchant_id})>"