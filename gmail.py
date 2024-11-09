import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Optional, NamedTuple
import base64
from dataclasses import dataclass

# If modifying these scopes, delete the file token.json.
SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly",
  'https://www.googleapis.com/auth/gmail.modify', 
  "https://www.googleapis.com/auth/gmail.send"
]

@dataclass
class Thread():
  thread_id: str
  external_address: str
  subject: str
  message_ids: list[str]
  
  def to_dict(self):
    return {
      "thread_id": self.thread_id,
      "external_address": self.external_address,
      "subject": self.subject,
      "message_ids": self.message_ids
    }
  
  @staticmethod
  def from_dict(dict):
    return Thread(
      thread_id=dict['thread_id'],
      external_address=dict['external_address'],
      subject=dict['subject'],
      message_ids=dict['message_ids']
    )



def _get_gmail_auth():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return creds

def get_unread_email_thread() -> Optional[Thread]:
  creds = _get_gmail_auth()
  # Call the Gmail API
  service = build('gmail', 'v1', credentials=creds)  # Assuming 'creds' is your authenticated credentials

  # Get the first unread message
  results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
  messages = results.get('messages', [])

  if not messages:
    print('No new messages.')
    return

  message_id = messages[0]['id']  

  # Get the message details
  msg = service.users().messages().get(userId='me', id=message_id).execute()

  headers = {header['name']: header['value'] for header in msg['payload']['headers']}
  
  thread = Thread(
    subject = headers.get('Subject'),
    thread_id = msg['threadId'],
    external_address = headers.get('From'),
    message_ids=[headers.get('Message-ID')]
  )

  # Mark the message as read
  service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()
  print(f"Found new thread: {thread.subject}")

  return thread

def send_reply_to_thread(body: str, thread: Thread):
  creds = _get_gmail_auth()

  subject = f"Re: {thread.subject}"
  in_reply_to = thread.message_ids[-1]
  thread_id = thread.thread_id
  references = " ".join(thread.message_ids)

  service = build('gmail', 'v1', credentials=creds)

  # Create the message with required headers
  message_text = (
        f"To: {thread.external_address}\n"
        f"Subject: {subject}\n"
        f"In-Reply-To: {in_reply_to}\n"
        f"References: {references}\n\n{body}"
    )

  # Encode the message
  message = {
      'raw': base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8"),
      'threadId': thread_id  # Include the thread ID to send within the same thread
  }

  # Send the message
  sent_message = service.users().messages().send(userId="me", body=message).execute()
  sent_message_id = sent_message['id']
  print("Sending reply..")

  # Retrieve the sent message to get the Message-ID header
  full_message = service.users().messages().get(userId="me", id=sent_message_id, format="metadata").execute()
  print(full_message['payload']['headers'])

  headers = {header['name']: header['value'] for header in full_message['payload']['headers']}
  message_id = headers.get('Message-Id')
  print(message_id)

  thread.message_ids.append(message_id)
  return thread