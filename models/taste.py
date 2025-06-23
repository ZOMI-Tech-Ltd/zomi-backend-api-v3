from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.sql import func
import uuid
from enum import IntEnum


class TasteRecommendState(IntEnum):
    DEFAULT = 0
    YES = 1
    NO = 2


class TasteState(IntEnum):
    DEFAULT = 0
    RECOMMEND = 1
    NOT_RECOMMEND = 2
    COMMENT = 3
    MEDIA = 4
    COMMENT_AND_MEDIA = 5
    GENERAL = 100
    COMPLETE = 500


class Mood(IntEnum):
    DEFAULT = 0
    MUST_TRY = 1
    TO_BE_REPEATED = 2
    WORTH_A_SHOT = 3




class Taste(db.Model):

    __tablename__ = 'taste'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()) )
    
    dishId = db.Column(db.String(50), nullable=False, default = "")
    comment = db.Column(db.String(50), nullable=True, default = None)
    isVerified= db.Column(db.Boolean, nullable = False, default  = False)
    recommendState = db.Column(db.Integer, nullable=False, default = 1)
    usefulTotal = db.Column(db.Integer, nullable=False, default = 0)
    flow_document = db.Column(db.JSON, default = {"from taste model":"from taste model"})
    tags = db.Column(db.JSON)
    mediaIds = db.Column(db.JSON)
    userId = db.Column(db.String(50), db.ForeignKey('users._id'), nullable=False)
    mood = db.Column(db.Integer)
    state = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, default = datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)
    deletedAt = db.Column(db.DateTime, nullable=True)
    flow_published_at = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)
   
    __v = db.Column('__v', db.Integer, nullable=False, default=0) 
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c') 



    user_relation = db.relationship('User', back_populates='taste', lazy=True)



    __table_args__ =(
        db.UniqueConstraint('userId', 'dishId', name='_user_dish_taste_uc'),
    )



    # calculates states after editing a taste
    def calculate_state(self):
        state = TasteState.DEFAULT
        
        if self.recommendState == TasteRecommendState.YES:
            state = TasteState.RECOMMEND
        elif self.recommendState == TasteRecommendState.NO:
            state = TasteState.NOT_RECOMMEND
        
        # General evaluation
        if self.mood > Mood.DEFAULT or len(self.tags) > 0 or self.comment or len(self.mediaIds) > 0:
            state = TasteState.GENERAL
        
        if self.comment:
            state = TasteState.COMMENT
        
        if len(self.mediaIds) > 0:
            state = TasteState.MEDIA
        
        if self.comment and len(self.mediaIds) > 0:
            state = TasteState.COMMENT_AND_MEDIA
        
        # Complete evaluation
        if (self.mood > Mood.DEFAULT and self.comment and 
            len(self.mediaIds) > 0 and len(self.tags) > 0):
            state = TasteState.COMPLETE
        
        return state
    

    def soft_delete(self):
        self.deletedAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
        self._meta_op = 'd'

    def restore(self):
        self.deletedAt = None
        self.updatedAt = datetime.utcnow()
        self._meta_op = 'u'

    @property
    def is_deleted(self):
        return self.deletedAt is not None

    @classmethod
    def active_tastes(cls):
        return cls.query.filter(cls.deletedAt.is_(None))

    @classmethod
    def deleted_tastes(cls):
        return cls.query.filter(cls.deletedAt.isnot(None))





    def __repr__(self):
        return f"<Taste(id={self._id}, dishId={self.dishId}, mediaIds={self.mediaIds}, mood={self.mood}, state={self.state}, createdAt={self.createdAt}, updatedAt={self.updatedAt})>"


