import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import google_auth_oauthlib.flow
import urllib.parse
import threading
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes for Gmail and Sheets APIs
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/spreadsheets']

TOKEN_FILE = 'token.json'

def get_credentials():
    # Check if token.json exists
    if os.path.exists(TOKEN_FILE):
        print("Loading saved credentials from token.json...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            print("✅ Token is valid, skipping authentication.")
            return creds
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Token expired, refreshing...")
            creds.refresh(Request())
            return creds
    
    # Start OAuth Flow if no valid token exists
    print("Starting OAuth flow...")
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json', SCOPES
    )
    flow.redirect_uri = 'http://localhost:8080'

    # Generate the OAuth URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    print("Please go to this URL and authorize access:")
    print(authorization_url)

    # Define a simple HTTP handler to catch the OAuth response
    class OAuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                print("Authorization Code received.")
                flow.fetch_token(code=params['code'][0])
                creds = flow.credentials
                
                # Save the credentials to token.json
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("✅ Credentials saved to token.json.")
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Authentication successful. You can close this window.')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Authentication failed.')

    # Start the HTTP server in a separate thread
    def start_server():
        server = HTTPServer(('localhost', 8080), OAuthHandler)
        print("Listening on http://localhost:8080...")
        server.handle_request()
        server.server_close()

    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    server_thread.join()

    return flow.credentials

def get_latest_email(creds):
    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    
    # List the latest email from the inbox
    results = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])

    if not messages:
        print("📭 No unread messages found.")
        return

    # Get the latest message ID
    latest_message_id = messages[0]['id']
    
    # Fetch the full message details
    message = service.users().messages().get(userId='me', id=latest_message_id, format='full').execute()
    
    # Extract headers
    headers = message['payload']['headers']
    subject = sender = ''
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'From':
            sender = header['value']
    
    # Extract snippet
    snippet = message.get('snippet', '')

    print(f"📧 Latest Email:")
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Snippet: {snippet}")

# Get credentials
credentials = get_credentials()
print("✅ Authentication successful!")
print(f"Access Token: {credentials.token}")

# Call the function after authentication
get_latest_email(credentials)
