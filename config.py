import os 
from dotenv import load_dotenv

load_dotenv()


class Config:
    #database connection configs
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_SCHEMA = os.getenv('POSTGRES_SCHEMA', 'mongodb')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?options=-csearch_path%3D{POSTGRES_SCHEMA}"
 
    #JWT config
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_secret_key')

    
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    #redis(for further use)
    # REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    # REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    # REDIS_DB = os.getenv('REDIS_DB', 0)
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
    MONGODB_DB = os.getenv('MONGODB_DB', 'zomi_backend')
    
    ENABLE_MONGODB_WRITE = os.getenv('ENABLE_MONGODB_WRITE', 'true').lower() == 'true'
    MONGODB_FIRST = os.getenv('MONGODB_FIRST', 'true').lower() == 'true'  # Write to MongoDB first







