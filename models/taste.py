from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.sql import func
from bson import ObjectId
from enum import IntEnum, Enum


class TasteRecommendState(Enum):
    DEFAULT = 0
    YES = 1
    NO = 2


class TasteState(Enum):
    #eaten = 0 
    DEFAULT = 0 
    #eaten + like
    RECOMMEND = 1
    #eaten + dislike
    NOT_RECOMMEND = 2

    #comment_only
    COMMENT = 30
    #comment_only + like
    COMMENT_AND_RECOMMEND = 3
    #comment_only + dislike
    COMMENT_AND_NOT_RECOMMEND = 31

    #media_only
    MEDIA = 40
    #media_only + like
    MEDIA_AND_RECOMMEND = 4
    #media_only + dislike
    MEDIA_AND_NOT_RECOMMEND = 41

    #comment_and_media
    COMMENT_AND_MEDIA = 5
    #comment_and_media + like
    COMMENT_AND_MEDIA_AND_RECOMMEND = 100
    #comment_and_media + dislike
    COMMENT_AND_MEDIA_AND_NOT_RECOMMEND = 101

    


class Mood(IntEnum):
    DEFAULT = 0
    MUST_TRY = 1
    TO_BE_REPEATED = 2
    WORTH_A_SHOT = 3




class Taste(db.Model):

    __tablename__ = 'taste'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(ObjectId()) )
    
    dishId = db.Column(db.String(50), nullable=False, default = "")
    comment = db.Column(db.String(50), nullable=True, default = None)
    isVerified= db.Column(db.Boolean, nullable = False, default  = False)
    recommendState = db.Column(db.Integer, nullable=False, default = 1)
    usefulTotal = db.Column(db.Integer, nullable=False, default = 0)
    
    tags = db.Column(db.JSON)
    mediaIds = db.Column(db.JSON)
    userId = db.Column(db.String(50), db.ForeignKey('users._id'), nullable=False)
    mood = db.Column(db.Integer)
    state = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, default = datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)
    deletedAt = db.Column(db.DateTime, nullable=True)


   
   
    __v = db.Column('__v', db.Integer, nullable=False, default = 0) 
   
    user_relation = db.relationship('User', back_populates='taste', lazy=True)



    __table_args__ =(
        db.UniqueConstraint('userId', 'dishId', name='_user_dish_taste_uc'),
    )



    # calculates states after editing a taste
    def calculate_state(self):
        """
        Calculate state based on content and recommendation state.
        
        Logic:
        - No Comment and Media:
          Eaten Only = 0, Eaten + Like = 1, Eaten + Dislike = 2
        - Comment Only:
          Eaten + Comment = 30, Eaten + Comment + Like = 3, Eaten + Comment + Dislike = 31
        - Media Only:
          Eaten + Media = 40, Eaten + Media + Like = 4, Eaten + Media + Dislike = 41
        - Comment and Media:
          Eaten + Comment + Media = 5, Eaten + Comment + Media + Like = 100, 
          Eaten + Comment + Media + Dislike = 101
        """
        has_comment = bool(self.comment and self.comment.strip())
        has_media = bool(self.mediaIds and len(self.mediaIds) > 0)

        # Both comment and media exist
        if has_comment and has_media:
            if self.recommendState == TasteRecommendState.YES.value:
                state = TasteState.COMMENT_AND_MEDIA_AND_RECOMMEND.value  # 100
            elif self.recommendState == TasteRecommendState.NO.value:
                state = TasteState.COMMENT_AND_MEDIA_AND_NOT_RECOMMEND.value  # 101
            else:
                state = TasteState.COMMENT_AND_MEDIA.value  # 5

        # Comment only
        elif has_comment:
            if self.recommendState == TasteRecommendState.YES.value:
                state = TasteState.COMMENT_AND_RECOMMEND.value  # 3
            elif self.recommendState == TasteRecommendState.NO.value:
                state = TasteState.COMMENT_AND_NOT_RECOMMEND.value  # 31
            else:
                state = TasteState.COMMENT.value  # 30

        # Media only
        elif has_media:
            if self.recommendState == TasteRecommendState.YES.value:
                state = TasteState.MEDIA_AND_RECOMMEND.value  # 4
            elif self.recommendState == TasteRecommendState.NO.value:
                state = TasteState.MEDIA_AND_NOT_RECOMMEND.value  # 41
            else:
                state = TasteState.MEDIA.value  # 40

        # No content (eaten only)
        else:
            if self.recommendState == TasteRecommendState.YES.value:
                state = TasteState.RECOMMEND.value  # 1
            elif self.recommendState == TasteRecommendState.NO.value:
                state = TasteState.NOT_RECOMMEND.value  # 2
            else:
                state = TasteState.DEFAULT.value  # 0

        return state




        # if self.recommendState == TasteRecommendState.YES:
        #     state = TasteState.RECOMMEND
        # elif self.recommendState == TasteRecommendState.NO:
        #     state = TasteState.NOT_RECOMMEND
        
        # # General evaluation
        # if self.mood > Mood.DEFAULT or len(self.tags or []) > 0 or self.comment or len(self.mediaIds or []) > 0:
        #     state = TasteState.GENERAL
        
        # if self.comment:
        #     state = TasteState.COMMENT
        
        # if len(self.mediaIds or []) > 0:
        #     state = TasteState.MEDIA
        
        # if self.comment and len(self.mediaIds or []) > 0:
        #     state = TasteState.COMMENT_AND_MEDIA
        
        # # Complete evaluation
        # if (self.mood > Mood.DEFAULT and self.comment and 
        #     len(self.mediaIds or []) > 0 and len(self.tags or []) > 0):
        #     state = TasteState.COMPLETE
        
        return state
    

    def soft_delete(self):
        self.deletedAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
        

    def restore(self):
        self.deletedAt = None
        self.updatedAt = datetime.utcnow()

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


