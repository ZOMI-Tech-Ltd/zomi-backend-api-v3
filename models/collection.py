from extensions import db
from datetime import datetime
import uuid
class Collection(db.Model):

    __tablename__ = 'collections'

    _id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()) )
    __v = db.Column('__v', db.Integer, nullable=False, default=0) 
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c') 
    createdAt = db.Column(db.DateTime, default = datetime.utcnow)
    flow_published_at = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)

    object = db.Column(db.String(255), nullable=False)
    objectType = db.Column(db.String(255), nullable=False)
    
    updatedAt = db.Column(db.DateTime, default  = datetime.utcnow, onupdate=datetime.utcnow)


    user = db.Column('user' ,db.String(255), db.ForeignKey('users._id'), nullable=False)

    flow_document = db.Column(db.JSON, default = {"test":"test"})

    #define relation
    user_relation = db.relationship('User', back_populates='collection', lazy=True)



    #unique constraint
    __table_args__ = (db.UniqueConstraint('user', 'object', name='_user_object_collection_uc'),)


    def __repr__(self):
        return f"<Collection(user_id={self.user_id}, object={self.object}, objectType={self.objectType})>"
