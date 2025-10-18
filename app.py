from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os
import secrets
import sqlite3

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session security

# Database setup
DB_NAME = 'vidverse.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  bio TEXT DEFAULT '')''')
    conn.commit()
    conn.close()

init_db()

# Folder for uploaded videos
UPLOAD_FOLDER = 'static/videos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            session['user'] = username
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
        finally:
            conn.close()
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Home page (video import and feed) - protected by auth
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get list of uploaded videos
    videos = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.webm', '.mov'))]
    return render_template('index.html', videos=videos, user=session['user'])

# Profile page
@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, bio FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    conn.close()
    
    if not user_data:
        return 'User not found', 404
    
    # Get user's videos (filtered by filename prefix)
    all_videos = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.webm', '.mov'))]
    user_videos = [v for v in all_videos if v.startswith(username + '_')]
    
    is_own_profile = session['user'] == username
    
    if request.method == 'POST' and is_own_profile:
        bio = request.form['bio']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET bio = ? WHERE username = ?", (bio, username))
        conn.commit()
        conn.close()
        return redirect(url_for('profile', username=username))
    
    return render_template('profile.html', profile_user=user_data[1], bio=user_data[2], videos=user_videos, is_own=is_own_profile)

# Rules page
@app.route('/rules')
def rules():
    return render_template('rules.html')

# Upload video route
@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if 'video' not in request.files:
        return 'No video file'
    
    file = request.files['video']
    if file.filename == '':
        return 'No selected file'
    
    if file:
        filename = f"{session['user']}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index'))

# Report video route (demo: just logs to console)
@app.route('/report', methods=['POST'])
def report():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    video = data.get('video')
    if video:
        print(f"Reported video: {video} by user {session['user']}")
        return jsonify({'message': 'Reported successfully'})
    return jsonify({'error': 'No video specified'}), 400

# Serve uploaded videos
@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
