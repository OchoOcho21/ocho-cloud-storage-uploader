from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests, hashlib, os, json
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'niggatron123456')
app.permanent_session_lifetime = timedelta(days=1)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'sql12.freesqldatabase.com'),
    'database': os.environ.get('DB_NAME', 'sql12788430'),
    'user': os.environ.get('DB_USER', 'sql12788430'),
    'password': os.environ.get('DB_PASSWORD', '1dTBhdAYxP'),
    'port': os.environ.get('DB_PORT', '3306')
}

API_ENDPOINTS = {
    'login': "https://www.linkbox.to/api/user/login_email",
    'upload': "https://www.linkbox.to/api/open/folder_upload_file",
    'rename': "https://www.linkbox.to/api/open/file_rename",
    'delete': "https://www.linkbox.to/api/open/file_del",
    'save': "https://www.linkbox.to/api/open/file_save",
    'move': "https://www.linkbox.to/api/open/file_move",
    'create_folder': "https://www.linkbox.to/api/open/folder_create",
    'delete_folder': "https://www.linkbox.to/api/open/folder_del",
    'move_folder': "https://www.linkbox.to/api/open/folder_move",
    'edit_folder': "https://www.linkbox.to/api/open/folder_edit",
    'folder_details': "https://www.linkbox.to/api/open/folder_details",
    'search': "https://www.linkbox.to/api/open/file_search"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    token TEXT NOT NULL,
                    nickname VARCHAR(255),
                    storage_used BIGINT,
                    storage_capacity BIGINT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    details TEXT,
                    status VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "msg": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "msg": "Email and password are required"}), 400
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "msg": "Email already registered"}), 400
            
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, password_hash)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            session['user_id'] = user_id
            session['email'] = email
            
            return jsonify({"success": True, "msg": "Registration successful"})
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"success": False, "msg": "Registration failed"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "msg": "Email and password are required"}), 400
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], password):
                return jsonify({"success": False, "msg": "Invalid email or password"}), 401
            
            url = f"{API_ENDPOINTS['login']}?email={email}&pwd={password}&platform=web&pf=web&lan=en"
            res = requests.get(url).json()
            
            if res.get("status") == 1:
                token = res['data']['token']
                nickname = res['data']['nickname']
                size_curr = res['data']['userInfo']['size_curr']
                size_cap = res['data']['userInfo']['size_cap']
                
                save_account_to_db(user['id'], email, token, nickname, size_curr, size_cap)
                
                session['user_id'] = user['id']
                session['email'] = email
                session['token'] = token
                session['nickname'] = nickname
                session.permanent = True
                
                return jsonify({
                    "success": True,
                    "nickname": nickname,
                    "storage": size_curr,
                    "storage_max": size_cap
                })
            
            return jsonify({"success": False, "msg": res.get("msg", "Login failed")})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "msg": "Login failed"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def save_account_to_db(user_id, email, token, nickname, size_curr, size_cap):
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM accounts WHERE user_id = %s AND email = %s",
                (user_id, email))
            account = cursor.fetchone()
            
            if account:
                cursor.execute("""
                    UPDATE accounts 
                    SET token = %s, nickname = %s, storage_used = %s, storage_capacity = %s 
                    WHERE id = %s
                """, (token, nickname, size_curr, size_cap, account[0]))
            else:
                cursor.execute("""
                    INSERT INTO accounts (user_id, email, token, nickname, storage_used, storage_capacity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, email, token, nickname, size_curr, size_cap))
            
            conn.commit()
    except Exception as e:
        print(f"Error saving account: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "msg": "No file selected"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "msg": "No file selected"}), 400
    
    try:
        md5 = hashlib.md5(file.read(10 * 1024 * 1024)).hexdigest()
        file.seek(0)
        
        params = {
            "fileMd5ofPre10m": md5,
            "fileSize": request.form.get("size", file.content_length),
            "pid": request.form.get("pid", 0),
            "diyName": file.filename,
            "token": session.get('token')
        }
        
        res = requests.get(API_ENDPOINTS['upload'], params=params).json()
        return jsonify(res)
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"success": False, "msg": "Upload failed"}), 500

@app.route('/accounts')
@login_required
def get_accounts():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT email, nickname, storage_used, storage_capacity 
                FROM accounts 
                WHERE user_id = %s
            """, (session['user_id'],))
            accounts = cursor.fetchall()
            return jsonify({"success": True, "accounts": accounts})
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return jsonify({"success": False, "msg": "Error fetching accounts"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/rename', methods=['POST'])
@login_required
def rename():
    token = session.get('token')
    item_id = request.form['itemId']
    new_name = request.form['name']
    res = requests.get(API_ENDPOINTS['rename'], params={
        "itemId": item_id,
        "name": new_name,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/delete', methods=['POST'])
@login_required
def delete():
    token = session.get('token')
    item_id = request.form['itemId']
    res = requests.get(API_ENDPOINTS['delete'], params={
        "itemIds": item_id,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/save', methods=['POST'])
@login_required
def save_file():
    token = session.get('token')
    item_id = request.form['itemId']
    res = requests.get(API_ENDPOINTS['save'], params={
        "itemIds": item_id,
        "pid": 0,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/move', methods=['POST'])
@login_required
def move_file():
    token = session.get('token')
    item_id = request.form['itemId']
    pid = request.form.get('pid', 0)
    res = requests.get(API_ENDPOINTS['move'], params={
        "itemIds": item_id,
        "pid": pid,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    token = session.get('token')
    name = request.form['name']
    res = requests.get(API_ENDPOINTS['create_folder'], params={
        "name": name,
        "pid": 0,
        "token": token,
        "isShare": 0,
        "canInvite": 0,
        "canShare": 0,
        "withBodyImg": 0,
        "desc": ""
    }).json()
    return jsonify(res)

@app.route('/delete_folder', methods=['POST'])
@login_required
def delete_folder():
    token = session.get('token')
    dir_id = request.form['dirId']
    res = requests.get(API_ENDPOINTS['delete_folder'], params={
        "dirIds": dir_id,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/move_folder', methods=['POST'])
@login_required
def move_folder():
    token = session.get('token')
    dir_id = request.form['dirId']
    pid = request.form.get('pid', 0)
    res = requests.get(API_ENDPOINTS['move_folder'], params={
        "dirIds": dir_id,
        "pid": pid,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/edit_folder', methods=['POST'])
@login_required
def edit_folder():
    token = session.get('token')
    dir_id = request.form['dirId']
    name = request.form['name']
    desc = request.form.get('desc', '')
    res = requests.get(API_ENDPOINTS['edit_folder'], params={
        "dirId": dir_id,
        "name": name,
        "token": token,
        "canShare": 0,
        "canInvite": 0,
        "change_avatar": 0,
        "desc": desc
    }).json()
    return jsonify(res)

@app.route('/folder_details', methods=['GET'])
@login_required
def folder_details():
    token = session.get('token')
    dir_id = request.args.get('dirId', 0)
    res = requests.get(API_ENDPOINTS['folder_details'], params={
        "dirId": dir_id,
        "token": token
    }).json()
    return jsonify(res)

@app.route('/search', methods=['GET'])
@login_required
def search():
    token = session.get('token')
    name = request.args.get('name')
    res = requests.get(API_ENDPOINTS['search'], params={
        "name": name,
        "pid": 0,
        "token": token,
        "pageNo": 1,
        "pageSize": 20
    }).json()
    return jsonify(res)

if __name__ == '__main__':
    init_db()  
    app.run(host='0.0.0.0', port=3000)
