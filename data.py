from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from urllib.parse import quote_plus
import os
import sys
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

client = None
db = None

def connect_mongodb():
    global client, db
    try:
        username = quote_plus(os.getenv("MONGODB_USER"))
        password = quote_plus(os.getenv("MONGODB_PASS"))
        cluster = os.getenv("MONGODB_CLUSTER")
        database = os.getenv("MONGODB_DATABASE")

        uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"

        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[database]
        print("Connected to MongoDB successfully.")
    except ServerSelectionTimeoutError as e:
        print(f"Failed to connect to MongoDB server: {e}")
        client = None
        db = None
    except OperationFailure as e:
        print(f"MongoDB auth failed: {e}")
        sys.exit("Exiting due to auth failure")
    except Exception as e:
        print(f"Other MongoDB connection error: {e}")
        sys.exit("Exiting due to connection error")

def load():
    if not db:
        return {"people": [], "daily_availability": [], "eagle_slots": [],
                "eagle_assignments": [], "attendance": [], "trainer_state": []}
    return {
        "people": list(db.people.find({"active": True})),
        "daily_availability": list(db.daily_availability.find({})),
        "eagle_slots": list(db.eagle_slots.find({})),
        "eagle_assignments": list(db.eagle_assignments.find({})),
        "attendance": list(db.attendance.find({})),
        "trainer_state": list(db.trainer_state.find({})),
    }
    try:
        data = load()
        st.write("DEBUG: Data loaded successfully")
        st.write({key: len(value) for key, value in data.items()})
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


def upsert_record(collection_name, person_id, day, fields):
    if not db:
        print("No DB connection")
        return False
    try:
        pid = ObjectId(person_id) if ObjectId.is_valid(person_id) else person_id
        collection = db[collection_name]
        collection.update_one({'person_id': pid, 'date': day}, {'$set': fields}, upsert=True)
        return True
    except Exception as e:
        print(f"Error upserting record: {e}")
        return False

connect_mongodb()
