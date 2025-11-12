from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB_NAME, IS_PRODUCTION
import re
import os

# Extract database name from URI if present, otherwise use config
db_name = MONGODB_DB_NAME
# Check if database name is in the URI
# Format: mongodb+srv://.../dbname?... or mongodb://.../dbname?...
match = re.search(r'mongodb(\+srv)?://[^/]+/([^?]+)', MONGODB_URI)
if match:
    db_name = match.group(2)

# MongoDB connection configuration
# Production (MongoDB Atlas) vs Local development
def create_mongodb_client():
    """
    Create MongoDB client with appropriate configuration based on environment.
    Production (Atlas): Uses SSL/TLS with certificate verification
    Local: No SSL/TLS required
    """
    if IS_PRODUCTION or MONGODB_URI.startswith('mongodb+srv://'):
        # Production: MongoDB Atlas requires SSL/TLS
        import certifi
        return MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w='majority',
            tlsCAFile=certifi.where(),  # Use certifi's CA bundle for certificate verification
            tlsAllowInvalidCertificates=False,  # Verify certificates properly
        )
    else:
        # Local development: No SSL/TLS needed
        return MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w='majority',
        )

client = create_mongodb_client()

db = client[db_name]

# Collections
apps_collection = db["apps"]
widgets_collection = db["widgets"]

