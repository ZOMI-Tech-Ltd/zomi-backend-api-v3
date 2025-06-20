


from models.mongodb_models.base import MongoBaseModel


class MongoTaste(MongoBaseModel):
    """MongoDB model for tastes (recommendations)"""
    
    def __init__(self):
        super().__init__('tastes')
    
    def create_taste(self, user_id, dish_id, comment="", recommend_state=1, 
                    media_ids=None, mood=0, tags=None):
        """Create a new taste entry"""
        document = {
            '_id': str(uuid.uuid4()),  # Generate UUID like PostgreSQL
            'userId': user_id,
            'dishId': dish_id,
            'comment': comment,
            'isVerified': False,
            'recommendState': recommend_state,
            'usefulTotal': 0,
            'mediaIds': media_ids or [],
            'mood': mood,
            'tags': tags or [],
            'state': self._calculate_state(recommend_state, comment, media_ids, mood, tags),
            'flow_document': {"source": "taste", "platform": "mongodb"}
        }
        
        mongo_id = self.insert_one(document)
        return document['_id'], mongo_id  # Return both UUID and MongoDB ObjectId
    
    def find_user_tastes(self, user_id, dish_ids=None):
        """Find user's tastes"""
        if not self._collection:
            return []
        
        filter_dict = {
            'userId': user_id,
            'deletedAt': None
        }
        
        if dish_ids:
            filter_dict['dishId'] = {'$in': dish_ids}
        
        return list(self._collection.find(filter_dict))
    
    def update_taste(self, taste_id, update_data):
        """Update a taste entry"""
        # Recalculate state if relevant fields changed
        if any(key in update_data for key in ['recommendState', 'comment', 'mediaIds', 'mood', 'tags']):
            update_data['state'] = self._calculate_state(
                update_data.get('recommendState', 1),
                update_data.get('comment', ''),
                update_data.get('mediaIds', []),
                update_data.get('mood', 0),
                update_data.get('tags', [])
            )
        
        return self.update_one(
            {'_id': taste_id, 'deletedAt': None},
            {'$set': update_data}
        )
    
    def remove_taste(self, user_id, dish_id):
        """Soft delete a taste"""
        filter_dict = {
            'userId': user_id,
            'dishId': dish_id,
            'deletedAt': None
        }
        
        return self.soft_delete(filter_dict)
    
    def _calculate_state(self, recommend_state, comment, media_ids, mood, tags):
        """Calculate taste state based on content - mirrors PostgreSQL logic"""
        state = 0  # DEFAULT
        
        if recommend_state == 1:
            state = 1  # RECOMMEND
        elif recommend_state == 2:
            state = 2  # NOT_RECOMMEND
        
        # General evaluation
        if mood > 0 or len(tags or []) > 0 or comment or len(media_ids or []) > 0:
            state = 100  # GENERAL
        
        if comment:
            state = 3  # COMMENT
        
        if len(media_ids or []) > 0:
            state = 4  # MEDIA
        
        if comment and len(media_ids or []) > 0:
            state = 5  # COMMENT_AND_MEDIA
        
        # Complete evaluation
        if (mood > 0 and comment and 
            len(media_ids or []) > 0 and len(tags or []) > 0):
            state = 500  # COMPLETE
        
        return state