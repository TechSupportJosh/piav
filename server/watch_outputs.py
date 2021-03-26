import json
import time
import pymongo
import argparse
import sys
import os
import logging

from CustomFormatter import CustomFormatter
from output_handler import get_branches

from bson.objectid import ObjectId

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

task_logger = logging.getLogger("tasks")
task_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
task_logger.addHandler(ch)

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
    task_logger.info("Starting machine for task %s", task_id)

class SendToMongo(PatternMatchingEventHandler):
    def on_created(self, event):
        # Check whether a output json exists with the same name
        # TODO: Error handling
        task_id = os.path.split(event.src_path)[1].split(".")[0]
        
        if not os.path.exists(os.path.join("output", task_id + ".json")):
            task_logger.warning("New .complete file found but no JSON found - ignoring")
            return
        
        with open(os.path.join("output", task_id + ".json"), "r") as output_file:
            task_output = json.load(output_file)
        
        # Only consider duplicate outputs if they're alive 
        if task_output["application_alive"]:
            # Detect whether this output is identical to another output, in which case we don't need to process it
            output_search = output_db.find_one({"top_window_texts": task_output["top_window_texts"], "found_controls": task_output["found_controls"]})

            if output_search is not None:
                # This output is identical to another output, indiciating that maybe we've hit a "back" button or cancel on a dialog.
                # Rather than inserting the output, insert a entry to the already discovered one
                output_db.insert_one({
                    "input_id": task_output["input_id"],
                    "same_as": output_search["_id"]
                })

                task_logger.info("Output of task %s same as %s, inserting same_as entry", task_id, output_search["_id"])
                return

        # Insert this output into our database
        output_db.insert_one(task_output)

        # If the application has died, we can end here.
        if not task_output["application_alive"]:
            if task_output["program_installed"]:
                task_logger.info("Application successfully installed after task %s", task_id)
            else:
                task_logger.info("Application process ended after task %s", task_id)
            return

        # Now feed this data into our branch generator
        task_input = input_db.find_one({"_id": ObjectId(task_output["input_id"])})
        
        task_ids = []

        for branch in get_branches(task_input, task_output):
            result = input_db.insert_one(branch)
            task_ids.append(result.inserted_id)
        
        for task_id in task_ids:
            start_machine(task_id)
        
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "new":
        # TODO: Start a prompt which takes in details about the new program
        print("Please enter task information: ")

        # Empty the databases
        input_db.delete_many({})
        output_db.delete_many({})

        # Empty input and output files
        # Doesn't currently work because of VM shared folders being "in use"
        if False:
            for file in os.listdir("input"):
                if file.endswith(".json"):
                    os.remove(os.path.join("input", file))

            for file in os.listdir("output"):
                if file.endswith(".json") or file.endswith(".complete"):
                    os.remove(os.path.join("output", file))

        # Input the first task
        response = input_db.insert_one({
            "precursors": []
        })

        task_logger.info("Starting PIAV...")
        start_machine(response.inserted_id)

    task_logger.info("Watching output directory...")
    observer = Observer()
    event_handler = SendToMongo(patterns=["*.complete"])
    observer.schedule(event_handler, "output")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        task_logger.info("Ending program...")
        observer.stop()
    observer.join()