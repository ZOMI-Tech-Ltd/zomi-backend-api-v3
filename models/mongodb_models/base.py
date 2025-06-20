'''mongodb base model
'''

from datetime import datetime
from bson import ObjectId
from extensions import get_mongo_db
import uuid



class MongoBaseModel:
    """Base class for MongoDB models"""
    
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self._db = get_mongo_db()
        self._collection = self._db[collection_name] if self._db else None
    
    def insert_one(self, document):
        """Insert a single document"""
        if not self._collection:
            return None
        
        # Add metadata fields similar to PostgreSQL
        document.update({
            '__v': 0,
            '_meta_op': 'c',
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'flow_published_at': datetime.utcnow(),
            'deletedAt': None
        })
        
        result = self._collection.insert_one(document)
        return str(result.inserted_id)
    
    def find_one(self, filter_dict):
        """Find a single document"""
        if not self._collection:
            return None
        return self._collection.find_one(filter_dict)
    
    def update_one(self, filter_dict, update_dict):
        """Update a single document"""
        if not self._collection:
            return None
        
        update_dict.setdefault('$set', {})['updatedAt'] = datetime.utcnow()
        return self._collection.update_one(filter_dict, update_dict)
    
    def soft_delete(self, filter_dict):
        """Soft delete a document"""
        if not self._collection:
            return None
        
        return self._collection.update_one(
            filter_dict,
            {
                '$set': {
                    'deletedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow(),
                    '_meta_op': 'd'
                }
            }
        )