import sqlite3
from task import Task
class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    # def __init__(self,email:str,name:str):
    #     self.email=email
    #     self.name=name
    
    def __str__(self):
        return f"{self.id},{self.email},{self.name}"
    
    def connectDB():
        return sqlite3.connect("DB/study_schedule_DB01.db")

    

    def add_user(self, db_path):
        try:

            sql="INSERT INTO user(name,email) VALUES (?,? )"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(sql, (self.name,self.email))
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            print("Insert failed:", e)
        except:
            print("Invalid input")
        
        


    def update_user(conn,self):
        sql="UPDATE user SET name="+self.name+", EMAIL="+self.email+" WHERE id="+self.id
        cursor = conn.cursor()
        cursor.execute(sql)
    
        if cursor.rowcount == 0:
            print("No student found.")
        else:
            print("Updated.")
        conn.commit()


    #TODO: create get_user_by_email def  
    def get_user_by_email(self, db_path):
        sql = "SELECT * FROM user WHERE email = ?"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (self.email,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return None

        user_id, user_name, user_email = row
        conn.close()
        return User(user_id, user_email, user_name)
    def process_user(self, db_path):
        select_user =  self.get_user_by_email(db_path)
        if select_user is None:
            self.add_user(db_path)
            result_user = self.get_user_by_email(db_path)
            return result_user
        else:
            return select_user
        

    def get_user_tasks (self, db_path):
        sql = """
        SELECT id, user, title, deadline, priority, estimated_minutes, status
        FROM task
        WHERE user = ?
        
        """

        print (sql)
        print("ID="+str(self.id))
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (self.id,))
        rows=cursor.fetchall()
        print(len(rows))

        tasks = []
        if rows is None:
            return None
        for row in rows:
            print("row="+str(row))
            task_id, task_user, task_title, task_deadline, task_priority, task_estimated,task_status = row
            tasks.append (Task (task_id, self, task_title, task_deadline, task_priority,task_estimated, task_status))
        return tasks
    


   


