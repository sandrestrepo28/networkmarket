import sqlite3

def init_db():
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('Santiago', 'abc123'))
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('Restrepo', '123abc'))
    conn.commit()
    conn.close()

def validar_usuario(username, password):
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

if __name__ == "__main__":
    init_db()