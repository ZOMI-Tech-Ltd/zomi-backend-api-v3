

from extensions import db
from sqlalchemy.dialects.postgresql import ARRAY, JSON

class Dish(db.Model):

    __tablename__ = 'dishes'

    _id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    media = db.Column('media',db.JSON, nullable=False)
    price = db.Column(db.Integer, nullable=False)


    #rating fields
    recommendedCount = db.Column('tasteRecommendTotal', nullable=True)
    # uber_eats_rating = db.Column(db.Float, nullable=True, default=0)
    # skip_the_dishes_rating = db.Column(db.Float, nullable=True, default=0)
    # fantuan_rating = db.Column(db.Float, nullable=True, default=0)
    # gm_rating = db.Column(db.Float, nullable=True, default=0)
    # doordash_rating = db.Column(db.Float, nullable=True, default=0)
    # open_table_rating = db.Column(db.Float, nullable=True, default=0)
    # yelp_rating = db.Column(db.Float, nullable=True, default=0)  


    # #relationship with merchant(many to one)
    merchant_col = db.Column('merchant', db.String(50), db.ForeignKey('merchants._id'), nullable=False)
    merchant = db.relationship('Merchant', back_populates='dishes', lazy=True)

    # #tags
    # flavor_tags = db.Column(ARRAY(db.String), nullable=True, default=[])
    # unique_tags = db.Column(ARRAY(db.String), nullable=True, default=[])

    #ingredients    
    #ingredients = db.Column(ARRAY(db.String), nullable=True)

    #description
    description = db.Column(db.String(200), nullable=True)




    

    def __repr__(self):
        return f"<name='{self.title}'>"

