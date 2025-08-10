from extensions import db
from datetime import datetime
import uuid
class Collection(db.Model):

    __tablename__ = 'collections'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()) )
    __v = db.Column('__v', db.Integer, nullable=False, default=0) 
    createdAt = db.Column(db.DateTime, default = datetime.utcnow)
    
    
    object = db.Column(db.String(255), nullable=False)
    objectType = db.Column(db.String(255), nullable=False)
    
    updatedAt = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)

    #deletedAt
    deleteAt = db.Column(db.DateTime, nullable=True)


    user = db.Column('user' ,db.String(255), db.ForeignKey('users._id'), nullable=False)



    #define relation
    user_relation = db.relationship('User', back_populates='collection', lazy=True)



    #unique constraint
    __table_args__ = (db.UniqueConstraint('user', 'object', name='_user_object_collection_uc'),)



    #soft delete
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
    def active_collections(cls):
        return cls.query.filter(cls.deletedAt.is_(None))

    @classmethod
    def deleted_collections(cls):
        return cls.query.filter(cls.deletedAt.isnot(None))



    def __repr__(self):
        return f"<Collection(user_id={self.user_id}, object={self.object}, objectType={self.objectType})>"
