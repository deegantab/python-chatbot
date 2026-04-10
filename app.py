import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room


app = Flask(__name__)
app.secret_key = 'secretkey123'  # For session handling
socketio = SocketIO(app, async_mode='eventlet', manage_session=False)

# Store online users
users = {}  # {session_id: username}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'], room=session['room'])

@socketio.on('connect')
def connect():
    username = session.get('username')
    room = session.get('room')

    if not username or not room:
        return False   # disconnect if no session

    users[request.sid] = {"username": username, "room": room}
    join_room(room)

    emit('message', {
        'username': 'System',
        'message': f'{username} has joined the room.'
    }, room=room)
import logging
logging.basicConfig(level=logging.DEBUG)

@socketio.on('message')
def handle_message(data):
    username = users.get(request.sid, 'Anonymous')
    msg = {'username': username, 'message': data['message']}
    emit('message', msg, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    users.pop(request.sid, None)
    emit('user_list', list(users.values()), broadcast=True)


import os
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
