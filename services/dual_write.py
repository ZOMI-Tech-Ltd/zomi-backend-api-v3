# services/dual_write_service.py
from datetime import datetime
from extensions import db, get_mongo_db
from models.collection import Collection
from models.taste import Taste
from models.like import Like
from models.mongodb_models.collection import MongoCollection
from models.mongodb_models.taste import MongoTaste
from models.mongodb_models.like import MongoLike
from flask import current_app
import uuid



class DualWriteService:
    """
    Service for handling dual writes to MongoDB and PostgreSQL.
    Writes to MongoDB first to get ObjectId, then writes to PostgreSQL.
    """
    
    def __init__(self):
        self.mongo_collection = MongoCollection()
        self.mongo_taste = MongoTaste()
        self.mongo_like = MongoLike()
        self.mongodb_enabled = current_app.config.get('ENABLE_MONGODB_WRITE', False)
    
    def create_collection(self, user_id, object_id, object_type="DISH"):
        """
        Create collection with dual write: MongoDB first, then PostgreSQL
        
        Returns:
            dict: {
                'success': bool,
                'pg_id': str,
                'mongo_id': str,
                'error': str (if any)
            }
        """
        pg_id = None
        mongo_id = None
        
        try:
            # Step 1: Write to MongoDB first (if enabled)
            if self.mongodb_enabled:
                try:
                    pg_id, mongo_object_id = self.mongo_collection.create_collection(
                        user_id, object_id, object_type
                    )
                    mongo_id = mongo_object_id
                    print(f"MongoDB collection created: {mongo_id}")
                except Exception as e:
                    print(f"MongoDB write failed: {e}")
                    # Continue with PostgreSQL even if MongoDB fails
                    pg_id = str(uuid.uuid4())
            else:
                pg_id = str(uuid.uuid4())
            
            # Step 2: Write to PostgreSQL with the same ID
            pg_collection = Collection(
                _id=pg_id,
                user=user_id,
                object=object_id,
                objectType=object_type,
                flow_document={"source": "dual_write", "mongo_id": mongo_id}
            )
            
            db.session.add(pg_collection)
            db.session.commit()
            
            return {
                'success': True,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'error': None
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'error': str(e)
            }
    
    def remove_collection(self, user_id, object_id, object_type="DISH"):
        """
        Remove collection with dual write: MongoDB first, then PostgreSQL
        """
        try:
            # Step 1: Soft delete in MongoDB (if enabled)
            if self.mongodb_enabled:
                try:
                    self.mongo_collection.remove_collection(user_id, object_id, object_type)
                    print("MongoDB collection soft deleted")
                except Exception as e:
                    print(f"MongoDB delete failed: {e}")
            
            # Step 2: Soft delete in PostgreSQL
            pg_collection = Collection.active_collections().filter_by(
                user=user_id,
                object=object_id,
                objectType=object_type
            ).first()
            
            if pg_collection:
                pg_collection.soft_delete()
                db.session.commit()
                
                return {
                    'success': True,
                    'pg_id': pg_collection._id,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'Collection not found'
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_taste(self, user_id, dish_id, comment="", recommend_state=1, 
                    media_ids=None, mood=0, tags=None):
        """
        Create taste with dual write: MongoDB first, then PostgreSQL
        """
        pg_id = None
        mongo_id = None
        
        try:
            # Step 1: Write to MongoDB first (if enabled)
            if self.mongodb_enabled:
                try:
                    pg_id, mongo_object_id = self.mongo_taste.create_taste(
                        user_id, dish_id, comment, recommend_state, 
                        media_ids, mood, tags
                    )
                    mongo_id = mongo_object_id
                    print(f"MongoDB taste created: {mongo_id}")
                except Exception as e:
                    print(f"MongoDB write failed: {e}")
                    pg_id = str(uuid.uuid4())
            else:
                pg_id = str(uuid.uuid4())
            
            # Step 2: Write to PostgreSQL with the same ID
            pg_taste = Taste(
                _id=pg_id,
                userId=user_id,
                dishId=dish_id,
                comment=comment,
                isVerified=False,
                recommendState=recommend_state,
                usefulTotal=0,
                mediaIds=media_ids or [],
                mood=mood,
                tags=tags or [],
                flow_document={"source": "dual_write", "mongo_id": mongo_id}
            )
            
            # Calculate state using the existing method
            pg_taste.state = pg_taste.calculate_state()
            
            db.session.add(pg_taste)
            db.session.commit()
            
            return {
                'success': True,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'taste': pg_taste,
                'error': None
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'error': str(e)
            }
    
    def update_taste(self, taste_id, user_id, update_data):
        """
        Update taste with dual write: MongoDB first, then PostgreSQL
        """
        try:
            # Step 1: Update in MongoDB (if enabled)
            if self.mongodb_enabled:
                try:
                    self.mongo_taste.update_taste(taste_id, update_data)
                    print("MongoDB taste updated")
                except Exception as e:
                    print(f"MongoDB update failed: {e}")
            
            # Step 2: Update in PostgreSQL
            pg_taste = Taste.active_tastes().filter_by(
                _id=taste_id,
                userId=user_id
            ).first()
            
            if not pg_taste:
                return {
                    'success': False,
                    'error': 'Taste not found'
                }
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(pg_taste, key):
                    setattr(pg_taste, key, value)
            
            # Recalculate state
            pg_taste.state = pg_taste.calculate_state()
            pg_taste.updatedAt = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'pg_id': taste_id,
                'taste': pg_taste,
                'error': None
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_taste(self, user_id, dish_id):
        """
        Remove taste with dual write: MongoDB first, then PostgreSQL
        """
        try:
            # Step 1: Soft delete in MongoDB (if enabled)
            if self.mongodb_enabled:
                try:
                    self.mongo_taste.remove_taste(user_id, dish_id)
                    print("MongoDB taste soft deleted")
                except Exception as e:
                    print(f"MongoDB delete failed: {e}")
            
            # Step 2: Soft delete in PostgreSQL
            pg_taste = Taste.active_tastes().filter_by(
                userId=user_id,
                dishId=dish_id
            ).first()
            
            if pg_taste:
                pg_taste.soft_delete()
                db.session.commit()
                
                return {
                    'success': True,
                    'pg_id': pg_taste._id,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'Taste not found'
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_like(self, user_id, object_id, object_type="TASTE"):
        """
        Create like with dual write: MongoDB first, then PostgreSQL
        """
        pg_id = None
        mongo_id = None
        
        try:
            # Step 1: Write to MongoDB first (if enabled)
            if self.mongodb_enabled:
                try:
                    pg_id, mongo_object_id = self.mongo_like.create_like(
                        user_id, object_id, object_type
                    )
                    mongo_id = mongo_object_id
                    print(f"MongoDB like created: {mongo_id}")
                except Exception as e:
                    print(f"MongoDB write failed: {e}")
                    pg_id = str(uuid.uuid4())
            else:
                pg_id = str(uuid.uuid4())
            
            # Step 2: Write to PostgreSQL with the same ID
            pg_like = Like(
                _id=pg_id,
                user=user_id,
                object=object_id,
                objectType=object_type,
                state=1,
                flow_document={"source": "dual_write", "mongo_id": mongo_id}
            )
            
            db.session.add(pg_like)
            db.session.commit()
            
            return {
                'success': True,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'error': None
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'pg_id': pg_id,
                'mongo_id': mongo_id,
                'error': str(e)
            }
    
    def remove_like(self, user_id, object_id, object_type="TASTE"):
        """
        Remove like with dual write: MongoDB first, then PostgreSQL
        """
        try:
            # Step 1: Soft delete in MongoDB (if enabled)
            if self.mongodb_enabled:
                try:
                    self.mongo_like.remove_like(user_id, object_id, object_type)
                    print("MongoDB like soft deleted")
                except Exception as e:
                    print(f"MongoDB delete failed: {e}")
            
            # Step 2: Soft delete in PostgreSQL
            pg_like = Like.active_likes().filter_by(
                user=user_id,
                object=object_id,
                objectType=object_type
            ).first()
            
            if pg_like:
                pg_like.soft_delete()
                db.session.commit()
                
                return {
                    'success': True,
                    'pg_id': pg_like._id,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'Like not found'
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }