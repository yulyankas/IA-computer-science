from datetime import date,datetime 
from task import Task
class Event:
    def __init__(self,id:int,task:Task,start_time:datetime,end_time:datetime,status:str):
        self.id=id
        self.task=task
        self.start_time=start_time
        self.end_time=end_time
        self.status=status

    def __str__(self):
        return f"{self.id},{self.task},{self.start_time},{self.end_time},{self.status}"

