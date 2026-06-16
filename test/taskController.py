import sqlite3

class TaskController:
    @staticmethod       #can be user without object
    def create_task_from_form(title, priority,deadline,estimated_time, user_id, db_path):
        sql= """INSERT  INTO task (title, priority, deadline, estimated_minutes, user) VALUES (?,?,?,?,?)"""
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute (sql, (title,priority,deadline,estimated_time, user_id))
        conn.commit()
        conn.close()
        
        
