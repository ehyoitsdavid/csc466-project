import uuid

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
rooms = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rooms')
def list_rooms():
    results = []
    for room_id, room_info in rooms.items():
        results.append({"room_id": room_id, "room_info": room_info})
    return jsonify(results)


@app.route('/stats', methods=['POST'])
def collect_stats():
    stats = request.json
    print(stats)
    return jsonify({"status": "Success"})


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('create_or_join')
def handle_create_or_join(data):
    client_id = request.sid
    room_id = data.get("room")
    if not room_id:
        room_id = str(uuid.uuid4())
    print(f"Client joining room {room_id}")
    if room_id not in rooms:
        rooms[room_id] = set()
    if len(rooms[room_id]) >= 2:
        emit("full", room_id)
        return
    join_room(room_id)
    rooms[room_id].add(client_id)
    if len(rooms[room_id]) == 1:
        emit("created", {"room": room_id, "sid": client_id})
        return
    else:
        emit("joined", {"room": room_id, "sid": client_id})
        emit("ready", to=room_id)
        return


@socketio.on('offer')
def handle_offer(data):
    room_id = data.get("room")
    if room_id in rooms:
        emit("offer", data, to=room_id, skip_sid=request.sid)
        print(f"Forwarding offer to room {room_id}")


@socketio.on('answer')
def handle_answer(data):
    """Handles SDP answer messages."""

    room_id = data.get('room')
    if room_id in rooms:
        emit("answer", data, to=room_id, skip_sid=request.sid)
        print(f"Forwarding answer message to room {room_id}")


@socketio.on('candidate')
def handle_candidate(data):
    """Handles ICE candidate messages."""

    room_id = data.get('room')
    if room_id in rooms:
        emit('candidate', data, to=room_id, skip_sid=request.sid)
        print(f"Forwarding ICE candidate message to room {room_id}")


@socketio.on('leave')
def handle_leave(data):
    """Handles a request to leave a room."""

    room_id = data.get('room')

    if room_id in rooms and request.sid in rooms[room_id]:
        leave_room(room_id)
        rooms[room_id].remove(request.sid)
        print(f"Client {request.sid} left room {room_id}")

        # Notify other clients in the room
        emit('peer_left', {'room': room_id}, to=room_id)

        # If the room is empty, delete it
        if not rooms[room_id]:
            del rooms[room_id]
            print(f"Room {room_id} has been cleared")


@socketio.on('disconnect')
def handle_disconnect():
    # Clean up rooms
    for room_id, clients in list(rooms.items()):
        if request.sid in clients:
            clients.remove(request.sid)
            print(f"Client {request.sid} left room {room_id}")

            # If the room is empty, delete it
            if not clients:
                del rooms[room_id]
                print(f"Room {room_id} has been cleared")


def main():
    socketio.run(app)


if __name__ == '__main__':
    main()
