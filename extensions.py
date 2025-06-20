from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient



db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()
mongo_client = None
mongo_db = None



def init_extensions(app):
    global mongo_client, mongo_db
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    # Initialize MongoDB connection
    if app.config.get('ENABLE_MONGODB_WRITE', False):
        try:
            mongo_client = MongoClient(app.config['MONGODB_URL'])
            mongo_db = mongo_client[app.config['MONGODB_DB']]
            print("MongoDB connection established")


        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            mongo_db = None


def get_mongo_db():
    """Get MongoDB database instance"""
    return mongo_db

