#from flask import Flask
import flask
from user import User
from task import Task
from event import Event
from datetime import date, datetime
from event import Event
from pathlib import Path
from typing import List
import sqlite3
import string, secrets
import requests
import google_auth_oauthlib.flow
import pathlib
import os
from UserRepository import UserRepository
from flask import render_template
os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1" #allows google auth to work on local 

app = flask.Flask(__name__)
app.secret_key="dev_secret"        
BASE_DIR = Path(__file__).resolve().parent
CLIENTS_SECRET_FILE=BASE_DIR.parent/"credentials.config.json"       #credentials location


SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
] 
DB_PATH = Path(__file__).resolve().parent.parent/"DB"/"study_schedule_DB01.db"

# def connectDB():#a method which connects to DB and returns connection object
#     dbPath = Path(__file__).resolve().parent.parent/"DB"/"study_schedule_DB01.db"
#     return sqlite3.connect(dbPath)
# conn = connectDB()

def list_users():
    sql = "SELECT * FROM user"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    result = cursor.execute(sql)
    userlist = []
    for row in result:
        user = User (row[0],row[1],row[2])
        userlist.append(user)
        print (row[0],row[1],row[2])
    print (result)
    return userlist

def generate_code_verifier (length=64): #secure string for Google OAuth login
    alphabet = string.ascii_letters + string.digits+"-._"
    return "".join(secrets.choice(alphabet) for _ in range (length))

@app.route("/")
def index():
    # u1=User (1234,"tupaja@pl","Julianna")
    # taskTitle = "task1"
    # t1=Task(1, u1, taskTitle, date(2026,6,30), 3, 90,"zhopa")
    # s=str(u1.email+u1.name)
    # t = t1.__str__()
    # event3= Event(809,t1,datetime(2026,2,18,9,10), datetime(2026,2,18,9,30), "gauno")
    # users: List [User] = list_users()
    # print ("Place0002",users, users.__str__)
    # strResult = str(" ")
    # for user in users:
    #     print ("Place0003",user.__str__())
    #     userId = user.id
    #     strResult+=str(user.id)+" "+user.name+" "+user.email+"\r\n"
    #return "111"+strResult

    session_user = flask.session.get("user")

    # TEMP: if not logged in, create a fake session user for testing
    if not session_user:
        session_user = {
            "email": "test@example.com",
            "name": "Test Student"
        }
        flask.session["user"] = session_user

    app_user = None
    tasks = []

    if session_user:
        app_user = UserRepository.get_user_by_email(DB_PATH, session_user.get("email"))
        if app_user:
            tasks = app_user.get_user_tasks(DB_PATH)

    return render_template("dashboard.html", user=app_user, tasks=tasks)

@app.route("/login")
def login():
    code_verifier = generate_code_verifier()
    flow = createFlow(code_verifier=code_verifier)

    authotization_url, state = flow.authorization_url (
        access_type="offline", #oauthflow 
        include_granted_scopes="true",
        prompt="consent"
    )
#save the data 
    flask.session ["state"] = state
    flask.session["code_verifier"] = code_verifier

    return flask.redirect (authotization_url)


def createFlow (state=None, code_verifier=None):
    flow=google_auth_oauthlib.flow.Flow.from_client_secrets_file (
        str(CLIENTS_SECRET_FILE),
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier
    )
    flow.redirect_uri = flask.url_for("oauth2callback", _external=True)
    return flow

@app.route("/oauth2callback")
#processes Google login callback and retrieves user credentials
def oauth2callback():
    state = flask.session.get("state")
    code_verifier = flask.session.get("code_verifier")
    print (code_verifier)
    if flask.request.args.get("state") != state:
        return "Invalid state parameter", 400
    
    if not state or not code_verifier:
        return "Invalid OAuth session parameters", 400

    flow = createFlow(state=state, code_verifier=code_verifier) #exchange google response for actual credentails
    flow.fetch_token(authorization_response=flask.request.url)

    credentials = flow.credentials

    flask.session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "granted_scopes": credentials.granted_scopes,
    }

    user_info = get_user_info(credentials.token)
    if not user_info:
        return "impossible to reach user's data ", 400

    flask.session["user"] = {
        "id": user_info.get("sub"),
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
    }

    flask.session.pop("code_verifier", None)
    
    db_user = User(
    None,
    user_info.get("email"),
    user_info.get("name")
    )
    db_user=db_user.process_user(DB_PATH);
    print (db_user.__str__)
    t1=Task(123,db_user,"llalalala",datetime(2026,2,18,9,10),1,90,"urgent")
    print(t1)
    return flask.redirect("/")

def get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if response.ok:
        return response.json()
    return None


 


    


app.run(debug=True)

