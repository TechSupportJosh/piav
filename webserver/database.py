import motor.motor_asyncio

db_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
piav_db = db_client.piav

input_collection = piav_db.get_collection("input")
output_collection = piav_db.get_collection("output")
queue_collection = piav_db.get_collection("queue")