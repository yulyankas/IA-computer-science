import sqlite3
from user import User

class UserRepository:

    @staticmethod
    def get_user_by_email (db_path: str, email: str):
        sql = "SELECT * FROM user WHERE email= ?"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (email,))
        row = cursor.fetchone()
    
        if row is None:
            return None
        
        user_id, user_name, user_email = row
        conn.close()
        return User (user_id,user_name, user_email)