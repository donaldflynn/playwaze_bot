from googleapiclient.discovery import build
from typing import Optional
import base64
from dataclasses import dataclass
from run_gmail_auth import get_gmail_auth

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

def get_unread_email_thread() -> Optional[Thread]:
  creds = get_gmail_auth()
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

def _send_email(encoded_body) -> str:
  """Sends email, returning Message-Id"""
  creds = get_gmail_auth()
  service = build('gmail', 'v1', credentials=creds)

  # Send the message
  sent_message = service.users().messages().send(userId="me", body=encoded_body).execute()
  sent_message_id = sent_message['id']
  print("Sending email..")

  # Retrieve the sent message to get the Message-ID header
  full_message = service.users().messages().get(userId="me", id=sent_message_id, format="metadata").execute()
  print(full_message['payload']['headers'])

  headers = {header['name']: header['value'] for header in full_message['payload']['headers']}
  return headers.get('Message-Id')

def send_reply_to_thread(body: str, thread: Thread):
  
  subject = f"Re: {thread.subject}"
  in_reply_to = thread.message_ids[-1]
  thread_id = thread.thread_id
  references = " ".join(thread.message_ids)

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
  message_id = _send_email(encoded_body=message)
  thread.message_ids.append(message_id)
  return thread

def send_outgoing_email(subject: str, body: str, address: str):
  message_text = (
        f"To: {address}\n"
        f"Subject: {subject}\n\n{body}"
    )
  
   # Encode the message
  message = {
      'raw': base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8"),
  }

  _send_email(encoded_body=message)
