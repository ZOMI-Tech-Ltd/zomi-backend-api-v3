from extensions import db

class Merchant(db.Model):
    __tablename__ = 'merchants'

    _id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    opening = db.Column(db.Integer, nullable=False)

    #long and lat for distance calculation
    latitude = db.Column("geoCoordinate/lat", db.Float, nullable=True)
    longitude = db.Column("geoCoordinate/lng", db.Float, nullable=True)

    #address
    address = db.Column(db.String(200), nullable=False)
        
    #add icon
    icon = db.Column("brandIcon", db.String(200), nullable=True)
    
    #relationship with dishes(one to many)
    dishes = db.relationship('Dish', back_populates='merchant', foreign_keys='Dish.merchant_col', lazy=True)



    def __repr__(self):
        return f"<name='{self.name}'>"
