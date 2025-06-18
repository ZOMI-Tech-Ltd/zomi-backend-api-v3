from extensions import db
from datetime import datetime




class ThirdPartyDelivery(db.Model):
    """Model for third-party delivery platform information"""
    
    __tablename__ = 'thirdPartyDeliveries'

    _id = db.Column(db.String(50), primary_key=True)
    __v = db.Column('__v', db.Integer, nullable=False, default=0)
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c')


    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    flow_published_at = db.Column(db.DateTime, nullable=True)

    icon = db.Column(db.String(500), nullable=True)
    name = db.Column(db.String(100), nullable=False)  

    redirect_url = db.Column('redirectUrl', db.String(500), nullable=True)

    flow_document = db.Column(db.String(500), nullable=True)


    def __repr__(self):
        return f"<ThirdPartyDelivery(name='{self.name}', icon='{self.icon}')>"

    def construct_url(self, external_id):
        """Construct the full delivery URL by combining base_url with external_id"""
        if not external_id:
            return None
            
        if '{external_id}' in self.redirect_url:
            return self.redirect_url.format(external_id=external_id)
        
        else:
            separator = '' if self.redirect_url.endswith('/') else '/'
            return f"{self.redirect_url}{separator}{external_id}"

    @classmethod
    def get_platform_by_name(cls, name):
        """Get platform by its name"""
        return cls.query.filter_by(name=name).first()



    @classmethod
    def get_all_active_platforms(cls):
        """Get all active platforms"""
        return cls.query.all()