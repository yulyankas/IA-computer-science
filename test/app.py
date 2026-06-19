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
            ordered_tasks = sort_tasks_by_priority_and_deadline(tasks)

            for task in ordered_tasks:
             print("ORDER:", task.title, task.priority, task.deadline)
            session_user["db_id"]=app_user.id
            flask.session["user"]=session_user
            print (flask.session.get("user"))

    return render_template("dashboard.html", user=app_user, tasks=tasks)

def create_calendar_event_from_task(title, deadline, estimated_minutes):
    creds_data = flask.session.get("credentials")
    if not creds_data:
        return None

    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )

    service = build("calendar", "v3", credentials=creds)

    tz = "Europe/Warsaw"
    now = datetime.now(timezone.utc)

    deadline_dt = datetime.fromisoformat(deadline).replace(
        hour=23,
        minute=59,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    duration = timedelta(minutes=int(estimated_minutes))

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=deadline_dt.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        timeZone=tz,
    ).execute()

    events = events_result.get("items", [])
    candidate_start = now

    for event in events:
        start_raw = event.get("start", {}).get("dateTime")
        end_raw = event.get("end", {}).get("dateTime")

        if not start_raw or not end_raw:
            continue

        event_start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        event_end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))

        if candidate_start + duration <= event_start:
            break

        if event_end > candidate_start:
            candidate_start = event_end

    if candidate_start + duration > deadline_dt:
        return None

    study_event = {
        "summary": f"Study: {title}",
        "description": f"Preparation block before deadline: {deadline}",
        "start": {
            "dateTime": candidate_start.isoformat(),
            "timeZone": tz,
        },
        "end": {
            "dateTime": (candidate_start + duration).isoformat(),
            "timeZone": tz,
        },
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=study_event,
    ).execute()

    return {
        "id": created_event.get("id"),
        "htmlLink": created_event.get("htmlLink"),
        "start": candidate_start.isoformat(),
        "end": (candidate_start + duration).isoformat(),
    }
@app.route("/add-task", methods=["POST"])
def add_task():
    title = request.form.get("title")
    priority = request.form.get("priority")
    deadline = request.form.get("deadline")
    estimated_minutes = request.form.get("estimated_minutes")

    user_id = flask.session.get("user").get("db_id")

    if not deadline:
        return "Deadline is required", 400

    deadline_date = datetime.fromisoformat(deadline).date()
    today = datetime.today().date()

    if deadline_date < today:
        return "You cannot add a task with a past deadline.", 400
    

    if not title or not title.strip():
        return "Title is required.", 400

    try:
        priority_value = int(priority)
        estimated_minutes_value = int(estimated_minutes)
    except (TypeError, ValueError):
        return "Priority and estimated minutes must be numbers.", 400

    if priority_value < 1 or priority_value > 5:
        return "Priority must be between 1 and 5.", 400

    if estimated_minutes_value <= 0:
        return "Estimated minutes must be greater than 0.", 400

    TaskController.create_task_from_form(
        title,
        priority_value,
        deadline,
        estimated_minutes_value,
        user_id,
        DB_PATH
    )

    create_calendar_event_from_task(title, deadline, estimated_minutes)

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
    if not deadline:
        return "Deadline is required",400
    deadline_date=datetime.fromisoformat(deadline).date()
    today=datetime.today().date()
    if not title or not title.strip():
        return "Title is required.", 400

    try:
        priority_value = int(priority)
        estimated_minutes_value = int(estimated_minutes)
    except (TypeError, ValueError):
        return "Priority and estimated minutes must be numbers.", 400

    if priority_value < 1 or priority_value > 5:
        return "Priority must be between 1 and 5.", 400

    if estimated_minutes_value <= 0:
        return "Estimated minutes must be greater than 0.", 400
    if deadline_date<today:
        return "You cane't update task to a past"
    Task.update_task(task_id, title, deadline, priority_value, estimated_minutes_value, DB_PATH)
    
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

def sort_tasks_by_priority_and_deadline(tasks):
    return sorted(
        tasks,
        key=lambda task: (int(task.priority), task.deadline)
    )

def schedule_tasks_in_priority_order(tasks):
    ordered_tasks = sort_tasks_by_priority_and_deadline(tasks)

    results = []
    for task in ordered_tasks:
        created_event = create_calendar_event_from_task(
            task.title,
            task.deadline,
            task.estimated_minutes
        )
        results.append((task, created_event))

    return results


app.run(debug=True)


