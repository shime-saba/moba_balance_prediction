import os
import json
from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient()
    db = client['match_database']
    tab = db['match_table']

    for filename in os.listdir('/home/ubuntu/matches'):
        with open('/home/ubuntu/matches/{0}'.format(filename)) as f:
            match = json.load(f)
        tab.insert_one(match)
