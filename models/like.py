from extensions import db
from datetime import datetime
import uuid

class Like(db.Model):
    """Model to track which users liked which taste (UGC) entries"""
    
    __tablename__ = 'likes'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    __v = db.Column('__v', db.Integer, nullable=False, default=0)
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c')
    
    # User who liked the taste
    user = db.Column(db.String(255), db.ForeignKey('users._id'), nullable=False)
    
    # Taste that was liked
    object = db.Column(db.String(255), nullable=False)
    objectType = db.Column(db.String(255), nullable=False)
    
    # Timestamps
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    flow_published_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Flow document for additional metadata
    flow_document = db.Column(db.JSON, default={"source": "like"})
    
    # Relationships
    user_relation = db.relationship('User', back_populates = 'user_likes', lazy = True)
    
    #state
    # state = db.Column(db.Integer, nullable=False, default=0)

    #soft delete
    deletedAt = db.Column(db.DateTime, nullable=True)



    # Unique constraint to prevent duplicate likes by same user on same object type
    __table_args__ = (
        db.UniqueConstraint('user', 'object', 'objectType', name='_user_object_type_like_uc'),
    )

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
    def active_likes(cls):
        return cls.query.filter(cls.deletedAt.is_(None))

    @classmethod
    def deleted_likes(cls):
        return cls.query.filter(cls.deletedAt.isnot(None))
    


    def __repr__(self):
        return f"<TasteLike(user_id={self.user_id}, taste_id={self.taste_id})>"