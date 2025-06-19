import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials():
    creds = None
    if os.path.exists(os.getenv("TOKEN_PATH")):
        creds = Credentials.from_authorized_user_file(os.getenv("TOKEN_PATH"), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(os.getenv("CREDENTIALS_PATH"), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(os.getenv("TOKEN_PATH"), "w") as token:
            token.write(creds.to_json())
    return creds

def get_calendar_service():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service