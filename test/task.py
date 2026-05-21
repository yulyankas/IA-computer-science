from datetime import datetime,date,time
import sqlite3
from user import User
class Task:
    def __init__(self,id:int,user:User,title:str,deadline:date,priority:int,estimated_minutes:int,status:str):
        self.id=id
        self.user=user
        self.title=title
        self.deadline=deadline
        self.priority=priority
        self.estimated_minutes=estimated_minutes
        self.status=status

    def __str__(self):
        return f"{self.id},{self.user},{self.title},{self.deadline},{self.priority},{self.estimated_minutes},{self.status}"
        #return "123123123123123"

    def connectDB():
        return sqlite3.connect("DB/study_schedule_DB01.db")
    

    def update_task(conn,self):
        sql="UPDATE task SET title=",self.title,", USER=",self.user, ", DEADLINE=",self.deadline,",PRIORITY=",self.priority,"ESTIMATED TIME=",self.estimatedtime," WHERE id=",self.id
        cursor = conn.cursor()
        cursor.execute(sql)
    
        if cursor.rowcount == 0:
            print("No task found.")
        else:
            print("Updated.")
        conn.commit()




    def get_taskbyid(self,db_path):
        sql="SELECT*FROM task WHERE id=?"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql,(self.id,))  
        row=cursor.fetchone()

        if row is None:
            return None
        
        task_id, task_deadline,task_priority = row
        conn.close()
        return Task (task_id,task_deadline, task_priority)
    

    def get_taskbyuser(user_id,db_path):
        sql = """
        SELECT id, user, title, deadline, priority, estimated_minutes, status
        FROM task
        WHERE user = ?
        AND date(deadline) >= date('now')
        """
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row=cursor.fetchone()

        if row is None:
            return None
        
        task_id, task_deadline,task_priority = row
        conn.close()
        return Task (task_id,task_deadline, task_priority)       

        