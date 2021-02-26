import json
import time
import pymongo
import argparse
import sys
import os
from output_handler import get_branches

from bson.objectid import ObjectId

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

client = pymongo.MongoClient("localhost", 27017)
piav_db = client.piav
input_db = piav_db.input
output_db = piav_db.output

class ObjectIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def start_machine(task_id: ObjectId):
    task = input_db.find_one({"_id": task_id})

    task_id = str(task_id)

    with open(os.path.join("input", task_id + ".json"), "w") as input_file:
        json.dump(task, input_file, cls=ObjectIDEncoder)

    # TODO: Spin machine up
    print("Starting machine for task {}".format(task_id))

class SendToMongo(PatternMatchingEventHandler):
    def on_created(self, event):
        # Check whether a output json exists with the same name
        # TODO: Error handling
        task_id = os.path.split(event.src_path)[1].split(".")[0]
        print(os.path.join("output", task_id + ".json"))
        
        if not os.path.exists(os.path.join("output", task_id + ".json")):
            print("New .complete file found but no JSON found - ignoring.")
            return
        
        with open(os.path.join("output", task_id + ".json"), "r") as output_file:
            task_output = json.load(output_file)

        # Insert this output into our database
        output_db.insert_one(task_output)

        # Now feed this data into our branch generator
        task_input = input_db.find_one({"_id": ObjectId(task_output["input_id"])})
        
        # TODO: Insert new branches
        task_ids = []

        for branch in get_branches(task_input, task_output):
            result = input_db.insert_one(branch)
            task_ids.append(result.inserted_id)
        
        # TODO: Spin up new machines
        for task_id in task_ids:
            start_machine(task_id)
        
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "new":
        # TODO: Start a prompt which takes in details about the new program
        print("Please enter task information: ")
        # Empty the databases
        input_db.delete_many({})
        output_db.delete_many({})

        # Input the first task
        response = input_db.insert_one({
            "precursors": []
        })

        print("Starting PIAV...")
        start_machine(response.inserted_id)

    print("Watching output directory...")
    observer = Observer()
    event_handler = SendToMongo(patterns=["*.complete"])
    observer.schedule(event_handler, "output")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ending program...")
        observer.stop()
    observer.join()