import os
import bcrypt
from pymongo import MongoClient

mongo = MongoClient(
    f'mongodb://{os.getenv("DB_HOST", "localhost")}:{int(os.getenv("DB_PORT", 27017))}/corrector').get_database()

mongo.users.insert_one(
    {'username': 'admin', 'password': bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()),
     'roles': ['admin'], 'change': True, 'retry_count': 0})
