from pymongo import MongoClient
import os

# ---------------- CONNECTION ----------------

# You can replace this with MongoDB Atlas URL later if needed
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)

# ---------------- DATABASE ----------------

db = client["vc_simulator"]

# Collection for storing startup evaluations
collection = db["startup_evaluations"]

# ---------------- OPTIONAL: TEST CONNECTION ----------------

def test_connection():
    try:
        client.admin.command("ping")
        print("✅ MongoDB Connected Successfully")
        return True
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)
        return False