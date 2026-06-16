#from flask import Flask
import flask
from taskController import TaskController
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
from flask import render_template, request, redirect
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1" #allows google auth to work on local 

app = flask.Flask(__name__)
app.secret_key="dev_secret"        
BASE_DIR = Path(__file__).resolve().parent
CLIENTS_SECRET_FILE=BASE_DIR.parent/"credentials.config.json"       #credentials location


SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
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
   
    session_user = flask.session.get("user")
    print (session_user)

    # # TEMP: if not logged in, create a fake session user for testing
    # if not session_user:
    #     session_user = {
    #         "email": "test@example.com",
    #         "name": "Test Student"
    #     }
    #     flask.session["user"] = session_user

    app_user = None
    tasks = []

    if session_user:
       
        app_user = UserRepository.get_user_by_email(DB_PATH, session_user.get("email"))
        if app_user:
            tasks = app_user.get_user_tasks(DB_PATH)
            session_user["db_id"]=app_user.id
            flask.session["user"]=session_user
            print (flask.session.get("user"))

    return render_template("dashboard.html", user=app_user, tasks=tasks)

@app.route ("/add-task", methods={"POST"}) #reads data and send it to database http
def add_task():
    title = request.form.get("title")
    prioroty = request.form.get("priority")
    deadline = request.form.get("deadline")
    estimated_minutes = request.form.get("estimated_minutes")
    user_id = flask.session.get("user").get("db_id")
    TaskController.create_task_from_form (title,prioroty,deadline,estimated_minutes,user_id,DB_PATH)
    return redirect("/")

#creates task in database

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

#say to google what permissions we need and where it should redirect us after login.
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

    flask.session.pop("code_verifier", None) #i dont want google id
    
    db_user = User(
    None,
    user_info.get("email"),
    user_info.get("name")
    )
    db_user=db_user.process_user(DB_PATH);
    print (db_user.__str__)
    # t1=Task(123,db_user,"llalalala",datetime(2026,2,18,9,10),1,90,"urgent")
    # print(t1)
    return flask.redirect("/")
#request the loggedin user profile data.
def get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if response.ok:
        return response.json()
    return None


@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    Task.delete_task(task_id, DB_PATH)
    return redirect("/")



@app.route("/edit-task", methods=["POST"])
def edit_task():
    task_id = request.form.get("task_id")
    title = request.form.get("title")
    deadline = request.form.get("deadline")
    priority = request.form.get("priority")
    estimated_minutes = request.form.get("estimated_minutes")

    Task.update_task(task_id, title, deadline, priority, estimated_minutes, DB_PATH)
    return redirect("/")
    
@app.route("/create-test-event")
def create_test_event():
    creds_data=flask.session.get("credentials")
    if not creds_data:
        return redirect("/login")
    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )
    try:
        service = build("calendar", "v3", credentials=creds)

        start_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        end_time = start_time + timedelta(minutes=30)

        event = {
            "summary": "Study Planner test event",
            "description": "Created from Flask app",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Created event: <a href='{created.get('htmlLink')}' target='_blank'>open in Google Calendar</a>"

    except HttpError as error:
        return f"An error occurred: {error}", 400



app.run(debug=True)


