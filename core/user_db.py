# core/user_db.py
from core.database import get_db_connection
from mysql.connector import Error

def get_user_by_username(username: str):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"获取用户失败: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_user(username: str, hashed_password: str):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"创建用户失败: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
