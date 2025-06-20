from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)

# Replace the URI string with your actual MongoDB connection string
app.config["MONGO_URI"] = "mongodb://localhost:27017/notesdb"
mongo = PyMongo(app)

@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    note_id = mongo.db.notes.insert_one({'content': data['content']}).inserted_id
    return jsonify({'id': str(note_id), 'content': data['content']}), 201

@app.route('/notes', methods=['GET'])
def get_notes():
    notes = []
    for note in mongo.db.notes.find():
        notes.append({'id': str(note['_id']), 'content': note['content']})
    return jsonify(notes), 200

@app.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    try:
        result = mongo.db.notes.update_one({'_id': ObjectId(note_id)}, {'$set': {'content': data['content']}})
    except InvalidId:
        return jsonify({'error': 'Invalid note ID'}), 400

    if result.matched_count == 0:
        return jsonify({'error': 'Note not found'}), 404

    return jsonify({'id': note_id, 'content': data['content']}), 200

@app.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        result = mongo.db.notes.delete_one({'_id': ObjectId(note_id)})
    except InvalidId:
        return jsonify({'error': 'Invalid note ID'}), 400

    if result.deleted_count == 0:
        return jsonify({'error': 'Note not found'}), 404

    return jsonify({'message': 'Note deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)