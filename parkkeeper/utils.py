# coding: utf-8
from pymongo import MongoClient
from pymongo.database import Database
from django.conf import settings

def get_mongo_db() -> Database:
    if settings.MONGODB.get('PASSWORD'):
        host = 'mongodb://%s:%s@%s:%s/' % (
            settings.MONGODB['USER'], settings.MONGODB['PASSWORD'],
            settings.MONGODB['HOST'], settings.MONGODB.get('PORT', '27017')
        )
    else:
        host = 'mongodb://%s:%s/' % (
            settings.MONGODB['HOST'], settings.MONGODB.get('PORT', '27017')
        )

    client = MongoClient(host)
    db = client[settings.MONGODB['NAME']]
    return db
