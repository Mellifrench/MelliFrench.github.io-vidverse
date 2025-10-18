from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session security

# Hardcoded users for demo auth (username: password)
users = {'user1': 'password1', 'user2': 'password2'}

# Folder for uploaded videos
UPLOAD_FOLDER = 'static/videos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
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

# Serve uploaded videos
@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
