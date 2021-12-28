import argparse
import json
import os
from pathlib import Path

from pymongo import MongoClient

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('asr_json', type=Path)
    parser.add_argument('name')

    args = parser.parse_args()

    mongo = MongoClient(
        f'mongodb://{os.getenv("DB_HOST", "localhost")}:{int(os.getenv("DB_PORT", 27017))}/corrector').get_database()

    col = mongo[f'speech_{args.name}']
    docs = []
    with open(args.asr_json) as f:
        for id, l in enumerate(f):
            doc = json.loads(l.strip())
            doc['id'] = id
            docs.append(doc)

    col.delete_many({})
    col.insert_many(docs)
