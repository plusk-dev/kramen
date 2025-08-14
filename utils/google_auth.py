import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Google Calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Your Google OAuth credentials - Load from environment variables
def get_client_config():
    """Get Google OAuth client configuration from environment variables."""
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "project_id": os.getenv("GOOGLE_PROJECT_ID", "tutorial-424112"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uris": [
                os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/callback")
            ]
        }
    }

def get_google_calendar_tokens():
    """Get Google Calendar OAuth tokens"""
    creds = None
    
    # Check if we have stored credentials
    if os.path.exists('token.json'):
        print("Found existing token.json, loading...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Running OAuth flow...")
            print("A browser window will open for you to authorize the application.")
            
            # Create flow from client config
            client_config = get_client_config()
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
            
            # Use manual flow with exact redirect URI
            flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/callback")
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"Please visit this URL to authorize: {auth_url}")
            
            # Start local server to handle callback
            import http.server
            import socketserver
            import urllib.parse
            
            auth_code = None
            
            class CallbackHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    nonlocal auth_code
                    if self.path.startswith('/callback'):
                        # Parse the authorization code from the callback
                        query = urllib.parse.urlparse(self.path).query
                        params = urllib.parse.parse_qs(query)
                        if 'code' in params:
                            auth_code = params['code'][0]
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>')
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(b'<html><body><h1>Authorization failed!</h1></body></html>')
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, msg_format, *args):
                    pass  # Suppress server logs
            
            # Start server
            with socketserver.TCPServer(("", 5173), CallbackHandler) as httpd:
                print("Server started at http://localhost:5173")
                print("Waiting for authorization...")
                
                # Wait for authorization code
                while auth_code is None:
                    httpd.handle_request()
                
                print("Authorization code received!")
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
        
        # Save credentials for next time
        with open('token.json', 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
        print("Credentials saved to token.json")
    
    return creds

def format_headers(creds):
    """Format credentials for proxy headers"""
    
    # Convert to the format your proxy expects
    auth_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }
    
    # Format as headers dictionary
    headers = {
        "X-Auth": json.dumps(auth_data),
        "X-TimeZone": "America/New_York",  # Change this to your timezone
        "Content-Type": "application/json"
    }
    
    return headers, auth_data

if __name__ == "__main__":
    try:
        print("Getting Google Calendar OAuth tokens...")
        creds = get_google_calendar_tokens()
        
        print("\n✅ Successfully obtained credentials!")
        print(f"Token expires at: {creds.expiry}")
        
        headers, auth_data = format_headers(creds)
        
        print("\n" + "="*50)
        print("HEADERS FOR YOUR PROXY:")
        print("="*50)
        
        print("\nPython dictionary format:")
        print("headers = {")
        for key, value in headers.items():
            print(f'    "{key}": "{value}",')
        print("}")
        
        print("\n" + "="*50)
        print("X-Auth JSON (formatted):")
        print("="*50)
        print(json.dumps(auth_data, indent=2))
        
        print("\n" + "="*50)
        print("CURL EXAMPLE:")
        print("="*50)
        print("curl -X GET 'http://localhost:8000/calendar/events' \\")
        print(f"  -H 'X-Auth: {json.dumps(auth_data)}' \\")
        print("  -H 'X-TimeZone: America/New_York' \\")
        print("  -H 'Content-Type: application/json'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have installed the required packages:")
        print("pip install google-auth google-auth-oauthlib google-auth-httplib2")
        raise
