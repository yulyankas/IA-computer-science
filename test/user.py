import sqlite3
class User:
    def __init__(self,id:int,email:str,name:str):
        self.id=id
        self.email=email
        self.name=name

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
       
        sql = "SELECT * FROM user WHERE email= ?"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (self.email,))
        row = cursor.fetchone()
    
        if row is None:
            return None
        
        user_id, user_name, user_email = row
        conn.close()
        return User (user_id,user_name, user_email)

    def process_user(self, db_path):
        select_user =  self.get_user_by_email(db_path)
        if select_user is None:
            self.add_user(db_path)
            result_user = self.get_user_by_email(db_path)
            return result_user
        else:
            return select_user
        
    


   


