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
    
    #add external id
    external_id_dd = db.Column("externalIds/DOORDASH", db.String(200), nullable=True)
    external_id_ub = db.Column("externalIds/UBER_EATS", db.String(200), nullable=True)
    external_id_ft = db.Column("externalIds/FANTUAN", db.String(200), nullable=True)
    external_id_st = db.Column("externalIds/SKIP_THE_DISHES", db.String(200), nullable=True)

    # Platform key mapping to column attributes
    _PLATFORM_COLUMN_MAP = {
        'DOORDASH': 'external_id_dd',
        'UBER_EATS': 'external_id_ub', 
        'FANTUAN': 'external_id_ft',
        'SKIP_THE_DISHES': 'external_id_st'
    }


    #relationship with dishes(one to many)
    dishes = db.relationship('Dish', back_populates='merchant', foreign_keys='Dish.merchant_col', lazy=True)


    def get_external_id(self, platform_name):
        column_name = self._PLATFORM_COLUMN_MAP.get(platform_name.lower())
        if column_name:
            return getattr(self, column_name, None)
        return None

    def set_external_id(self, platform_name, external_id):
        external_ids = {}
        for platform_key, column_name in self._PLATFORM_COLUMN_MAP.items():
            external_id = getattr(self, column_name, None)
            if external_id:
                external_ids[platform_name] = external_id.get(platform_name)
        return external_ids

    def get_all_external_ids(self,):
        external_ids = {}
        for platform_key, column_name in self._PLATFORM_COLUMN_MAP.items():
            external_id = getattr(self, column_name, None)
            if external_id:
                external_ids[platform_key] = external_id
        return external_ids
    


    def __repr__(self):
        return f"<name='{self.name}'>"
