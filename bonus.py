import asyncio
import json
from quart import Quart, websocket, request
from quart_cors import cors
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = Quart(__name__)
app = cors(app, allow_origin="*")

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client.noteswsdb
notes_collection = db.notes

# Cap for total number of notes
MAX_NOTES = 5

def serialize_note(note):
    return {"id": str(note["_id"]), "content": note["content"]}

@app.websocket('/ws/notes')
async def ws_notes():
    while True:
        try:
            data = await websocket.receive()
            msg = json.loads(data)
            action = msg.get("action")
            # CREATE
            if action == "create":
                content = msg.get("content")
                if not content:
                    await websocket.send(json.dumps({"error": "Content is required"}))
                    continue
                notes_count = await notes_collection.count_documents({})
                if notes_count >= MAX_NOTES:
                    await websocket.send(json.dumps({"error": f"Cannot add more than {MAX_NOTES} notes."}))
                    continue
                result = await notes_collection.insert_one({"content": content})
                note = {"_id": result.inserted_id, "content": content}
                # (1) Confirmation Packet
                await websocket.send(json.dumps({"confirmation": "Note created successfully"}))
                # (2) Contents Packet
                await websocket.send(json.dumps({"note": serialize_note(note)}))
            # READ ALL
            elif action == "read_all":
                notes = []
                async for note in notes_collection.find({}):
                    notes.append(serialize_note(note))
                await websocket.send(json.dumps({"notes": notes}))
            # UPDATE
            elif action == "update":
                note_id = msg.get("id")
                content = msg.get("content")
                if not (note_id and content):
                    await websocket.send(json.dumps({"error": "ID and content required"}))
                    continue
                result = await notes_collection.update_one(
                    {"_id": ObjectId(note_id)}, {"$set": {"content": content}}
                )
                if result.matched_count == 0:
                    await websocket.send(json.dumps({"error": "Note not found"}))
                else:
                    await websocket.send(json.dumps({"confirmation": "Note updated", "id": note_id}))
            # DELETE
            elif action == "delete":
                note_id = msg.get("id")
                if not note_id:
                    await websocket.send(json.dumps({"error": "ID required"}))
                    continue
                result = await notes_collection.delete_one({"_id": ObjectId(note_id)})
                if result.deleted_count == 0:
                    await websocket.send(json.dumps({"error": "Note not found"}))
                else:
                    await websocket.send(json.dumps({"confirmation": "Note deleted", "id": note_id}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    app.run()