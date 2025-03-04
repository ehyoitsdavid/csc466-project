import uuid
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
rooms = {}
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/stats', methods=['POST'])
def collect_stats():
    stats = request.json()
    print(stats)
    return jsonify({"status": "Success"})
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {str(uuid.uuid4())}")
@socketio.on('join')
def handle_join(room_id):
    sid = str(uuid.uuid4())
    print(f"Client joining room {room_id}")
    if room_id not in rooms:
        rooms[room_id] = set()
    if len(rooms[room_id]) >=2:
        emit("Full", room_id)
        return
    join_room(room_id)
    rooms[room_id].add(sid)
    if len(rooms[room_id]) == 1:
        emit("Created", {"room":room_id, "sid":sid})
        return
    else:
        emit("Joined",{"room":room_id, "sid":sid})
        emit("Ready", to=room_id)
        return
@socketio.on('offer')
def handle_offer(data):
    sid = str(uuid.uuid4())
    room_id = data.get("room")
    emit("Offer",data, to=room_id)
@socketio.on('leave')
def handle_leave(data):
    sid = str(uuid.uuid4())
    room_id = data.get("room")
    leave_room(room_id)
    rooms[room_id].remove(sid)
    if len(rooms[room_id]) == 0:
        emit("Offer", to=room_id)
        return


def main():
    socketio.run(app)
if __name__ == '__main__':
    main()
