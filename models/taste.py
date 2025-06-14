from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.sql import func
import uuid

class Taste(db.Model):

    __tablename__ = 'taste'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()) )
    
    dishId = db.Column(db.String(50), nullable=False, default = "Test")
    comment = db.Column(db.String(50), nullable=False, default = "Test")
    isVerified= db.Column(db.Boolean, nullable = False, default  = False)
    recommendState = db.Column(db.Integer, nullable=False, default = 1)
    usefulTotal = db.Column(db.Integer, nullable=False, default = 0)
    flow_document = db.Column(db.JSON, default = {"test":"test"})

    mediaIds = db.Column(db.JSON)
    userId = db.Column(db.String(50), db.ForeignKey('users._id'), nullable=False)
    mood = db.Column(db.Integer)
    state = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, default = datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)
    
    flow_published_at = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)
   
    __v = db.Column('__v', db.Integer, nullable=False, default=0) 
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c') 



    user_relation = db.relationship('User', back_populates='taste', lazy=True)



    __table_args__ =(
        db.UniqueConstraint('userId', 'dishId', name='_user_dish_taste_uc'),
    )

    def __repr__(self):
        return f"<Taste(id={self._id}, dishId={self.dishId}, mediaIds={self.mediaIds}, mood={self.mood}, state={self.state}, createdAt={self.createdAt}, updatedAt={self.updatedAt})>"


