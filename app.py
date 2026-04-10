import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.secret_key = 'secretkey123'

# IMPORTANT
socketio = SocketIO(app, async_mode='eventlet', manage_session=False)

users = {}  # {sid: {username, room}}

# ---------------- ROUTES ---------------- #

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        room = request.form.get('room')

        # store in session
        session['username'] = username
        session['room'] = room

        return redirect(url_for('chat'))

    return render_template('index.html')


@app.route('/chat')
def chat():
    username = session.get('username')
    room = session.get('room')

    # if session missing → go back
    if not username or not room:
        return redirect(url_for('index'))

    return render_template('chat.html', username=username, room=room)


# ---------------- SOCKET ---------------- #

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    room = session.get('room')

    if not username or not room:
        return False

    users[request.sid] = {"username": username, "room": room}
    join_room(room)

    emit('message', {
        'username': 'System',
        'message': f'{username} joined the room'
    }, room=room)


@socketio.on('message')
def handle_message(data):
    user = users.get(request.sid)

    if not user:
        return

    username = user['username']
    room = user['room']

    emit('message', {
        'username': username,
        'message': data['message']
    }, room=room)


@socketio.on('disconnect')
def handle_disconnect():
    user = users.pop(request.sid, None)

    if user:
        leave_room(user['room'])
        emit('message', {
            'username': 'System',
            'message': f"{user['username']} left the room"
        }, room=user['room'])


# ---------------- RUN ---------------- #

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
