from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return {"status": "OK"}

@app.route("/count")
def count():
    count = len(parse_json(db.songs.find()))
    return {"count": parse_json(count)}, 200

@app.route("/song")
def songs():
    find = db.songs.find()
    return {"count": parse_json(find)}, 200

@app.route("/song/<int:id>")
def get_song_by_id(id):
    find = db.songs.find_one({"id" : id})
    if find:
        return { str(id) : parse_json(find)}, 200
    else:
        return { "message" : "song with id not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    try:
        song = request.get_json()
        song_id = song.get('id')
        find = db.songs.find_one({"id": song_id})

        if find:
            return {"message": f"Song with id {song_id} already exists in the database"}, 323
        else:
            db.songs.insert_one(song)
            return {"message": "Song inserted", str(song_id) : str(song) }, 200
    except KeyError:
        return {"message": "Invalid input, 'id' key is missing"}, 400
    except Exception:
        return {"message": "Internal Server Error"}, 500


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        song = request.get_json()
        find = db.songs.find_one({"id": id})

        if not find:
            return {"message": f"Song with id {id} doesn't exists in the database"}, 323
        else:
            db.songs.update_one({"id" : id}, {"$set" : song })
            return {"message": "Song updated", str(id) : str(song) }, 200
    except KeyError:
        return {"message": "Invalid input, 'id' key is missing"}, 400
    except Exception:
        return {"message": "Internal Server Error"}, 500


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        find = db.songs.find_one({"id": id})

        if not find:
            return {"message": f"Song with id {id} doesn't exists in the database"}, 323
        else:
            db.songs.delete_one({"id" : id})
            return {"message": "Song deleted", str(id) : id }, 200
    except KeyError:
        return {"message": "Invalid input, 'id' key is missing"}, 400
    except Exception:
        return {"message": "Internal Server Error"}, 500