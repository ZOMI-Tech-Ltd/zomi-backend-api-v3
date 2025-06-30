"""
Media Model
Enhanced model for storing media information including blurhash and S3 data
"""

from extensions import db
from datetime import datetime
from sqlalchemy import Sequence
from bson import ObjectId

from bson import ObjectId
class Media(db.Model):
    """
    Media model for storing image and video information
    Supports both direct uploads and URL imports
    """
    
    __tablename__ = 'media'
    __table_args__ = {'schema': 'mongodb'}
    
    _id = db.Column('_id', db.String(100), primary_key=True, default= lambda:str(ObjectId()))
    pg_id = db.Column(db.Integer, nullable = True)


    url = db.Column(db.String(500), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    fileSize = db.Column("fileSize", nullable=True)
    blurHash = db.Column("blurHash", nullable=True)
    media_type = db.Column("media_type", nullable=True, default = "IMAGE")
    source = db.Column("source", nullable=True)
    tags = db.Column("tags", nullable=True)
    video_id = db.Column("vid", nullable=True)
    userId = db.Column("userId", nullable=True, default = '')


    createdAt = db.Column("createdAt", default=datetime.utcnow)
    updatedAt = db.Column("updatedAt", default=datetime.utcnow, onupdate=datetime.utcnow)
    # deletedAt = db.Column("deletedAt", nullable=True)
    blurHashAt = db.Column("blurHashAt", nullable=True)
    duration = db.Column("duration", nullable=True)


    __v = db.Column('__v', db.Integer, nullable=False, default=0)
    _meta_op = db.Column('_meta/op', db.String, nullable=False, default='c') 

    flow_document = db.Column(db.JSON, default = {"":""})



    def __repr__(self):
        return f"<Media(id={self._id}, url={self.url}, type={self.type})>"
    
    def to_dict(self, include_meta=False):
        data = {
            '_id': self._id,
            'pg_id': self.pg_id,
            'url': self.url,
            'type': self.media_type,
            'width': self.width,
            'height': self.height,
            'blurHash': self.blurHash,
            'fileSize': self.fileSize
        }
        
        if include_meta:
            data.update({
                'source': self.source,
                'tags': self.tags,
                'video_id': self.video_id,
                'userId': self.userId,
                'createdAt': self.createdAt.isoformat() if self.createdAt else None,
                'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None
            })
        
        return data
    
    
    @property
    def is_processed(self):
        return self.url is not None and self.blurHash is not None
    
    @property
    def is_deleted(self):
        return self.deletedAt is not None
    
    def soft_delete(self):
        self.deletedAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
    
    def restore(self):
        self.deletedAt = None
        self.updatedAt = datetime.utcnow()
    