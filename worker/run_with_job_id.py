from pymongo import MongoClient
from bson import ObjectId
import os
import subprocess
import sys

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["filesure"]
jobs = db["jobs"]

# Find a pending job without modifying it
job = jobs.find_one({"jobStatus": "pending"})

if not job:
    print("No pending job found.")
    sys.exit(0)

job_id = str(job["_id"])
print(f"Running job: {job_id}")

# Run the actual downloader
subprocess.run(["python", "downloader.py", job_id])