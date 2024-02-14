from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
import sqlite3
import os

app = Flask(__name__, template_folder=os.path.abspath('templates'))
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key'
DATABASE = "database.db"

def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, content TEXT, user_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))")
    conn.commit()
    conn.close()


create_table()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE user_id=?", (user_id,))
    notes = cursor.fetchall()
    conn.close()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    content = request.form['content']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (content, user_id) VALUES (?, ?)", (content, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (id, user_id))
        note = cursor.fetchone()
        conn.close()

        if not note:
            return redirect(url_for('index'))

        return render_template('edit.html', note=note)

    elif request.method == 'POST':
        new_content = request.form['content']
        cursor.execute("UPDATE notes SET content=? WHERE id=? AND user_id=?", (new_content, id, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
