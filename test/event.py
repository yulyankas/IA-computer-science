from datetime import date,datetime 
from task import Task
import sqlite3
class Event:
    def __init__(self,id:int,task:Task,start_time:datetime,end_time:datetime,status:str):
        self.id=id
        self.task=task
        self.start_time=start_time
        self.end_time=end_time
        self.status=status

    def __str__(self):
        return f"{self.id},{self.task},{self.start_time},{self.end_time},{self.status}"


    def connectDB():
        return sqlite3.connect("DB/study_schedule_DB01.db")

    def update_event(self, db_path):
        sql = """
        UPDATE event
        SET title = ?, user = ?, deadline = ?, priority = ?, estimated_minutes = ?, status = ?
        WHERE id = ?
        """
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (
            self.title,
            self.user,
            self.deadline,
            self.priority,
            self.estimated_minutes,
            self.status,
            self.id
        ))

        if cursor.rowcount == 0:
            print("No event found.")
        else:
            print("Updated.")
        conn.commit()


    def get_eventbyid(db_path, self):

        sql = "SELECT * FROM event WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (self.id,))
        row = cursor.fetchone()
        conn=sqlite3.connect(db_path)
        if row is None:
            return None

        return Event(*row)


    def get_eventbyuser(db_path, self):
        sql = """
        SELECT * FROM event
        WHERE user = ?
        AND date(deadline) >= date('now')
        """
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (self.user,))
        rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append(Event(*row))

        return events
    
    def get_eventbytask(db_path,self):
        sql='''
        SELECT * FROM event
        WHERE task = ?
        AND date(deadline) >= date('now')
        '''
        conn=sqlite3.connect(db_path)
        cursor=conn.cursor()
        cursor.execute(sql,(self.task,))
        rows=cursor.fetchall()

        events = []
        for row in rows:
            events.append(Event(*row))


        return events

