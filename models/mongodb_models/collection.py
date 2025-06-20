

from models.mongodb_models.base import MongoBaseModel
import uuid






class MongoCollection(MongoBaseModel):
    """MongoDB model for collections"""
    
    def __init__(self):
        super().__init__('collections')
    
    def create_collection(self, user_id, object_id, object_type="DISH"):
        """Create a new collection entry"""
        document = {
            '_id': str(uuid.uuid4()),  # Generate UUID like PostgreSQL
            'user': user_id,
            'object': object_id,
            'objectType': object_type,
            'flow_document': {"source": "collection", "platform": "mongodb"}
        }
        
        mongo_id = self.insert_one(document)
        return document['_id'], mongo_id  # Return both UUID and MongoDB ObjectId
    
    def find_user_collections(self, user_id, object_ids=None, object_type="DISH"):
        """Find user's collections"""
        if not self._collection:
            return []
        
        filter_dict = {
            'user': user_id,
            'objectType': object_type,
            'deletedAt': None
        }
        
        if object_ids:
            filter_dict['object'] = {'$in': object_ids}
        
        return list(self._collection.find(filter_dict))
    
    def remove_collection(self, user_id, object_id, object_type="DISH"):
        """Soft delete a collection"""
        filter_dict = {
            'user': user_id,
            'object': object_id,
            'objectType': object_type,
            'deletedAt': None
        }
        
        return self.soft_delete(filter_dict)