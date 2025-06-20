'''
'''

from models.mongodb_models.base import MongoBaseModel
import uuid






class MongoLike(MongoBaseModel):
    """MongoDB model for likes"""
    
    def __init__(self):
        super().__init__('likes')
    
    def create_like(self, user_id, object_id, object_type="TASTE"):
        """Create a new like entry"""
        document = {
            '_id': str(uuid.uuid4()),
            'user': user_id,
            'object': object_id,
            'objectType': object_type,
            'state': 1,
            'flow_document': {"source": "like", "platform": "mongodb"}
        }
        
        mongo_id = self.insert_one(document)
        return document['_id'], mongo_id
    
    def remove_like(self, user_id, object_id, object_type="TASTE"):
        """Soft delete a like"""
        filter_dict = {
            'user': user_id,
            'object': object_id,
            'objectType': object_type,
            'deletedAt': None
        }
        
        return self.soft_delete(filter_dict)