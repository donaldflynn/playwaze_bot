import os.path
import base64
import json
import re
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging
import requests

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify']

# def readEmails():
#     """Shows basic usage of the Gmail API.
#     Lists the user's Gmail labels.
#     """
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(               
#                 # your creds file here. Please create json file as here https://cloud.google.com/docs/authentication/getting-started
#                 'my_cred_file.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     try:
#         # Call the Gmail API
#         service = build('gmail', 'v1', credentials=creds)
#         results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
#         messages = results.get('messages',[]);
#         if not messages:
#             print('No new messages.')
#         else:
#             message_count = 0
#             for message in messages:
#                 msg = service.users().messages().get(userId='me', id=message['id']).execute()                
#                 email_data = msg['payload']['headers']
#                 for values in email_data:
#                     name = values['name']
#                     if name == 'From':
#                         from_name= values['value']                
#                         for part in msg['payload']['parts']:
#                             try:
#                                 data = part['body']["data"]
#                                 byte_code = base64.urlsafe_b64decode(data)

#                                 text = byte_code.decode("utf-8")
#                                 print ("This is the message: "+ str(text))

#                                 # mark the message as read (optional)
#                                 msg  = service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()                                                       
#                             except BaseException as error:
#                                 pass                            
#     except Exception as error:
#         print(f'An error occurred: {error}')

# readEmails()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 'https://www.googleapis.com/auth/gmail.modify']


def get_gmail_auth():
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

def get_first_unread_email_subject(creds):
  try:
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

    # Extract the subject from the message headers
    for header in msg['payload']['headers']:
      if header['name'] == 'Subject':
        subject = header['value']
        break

    print(f"Subject of the first unread email: {subject}")

    # Mark the message as read
    service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()

  except Exception as error:
    print(f'An error occurred: {error}')

if __name__ == "__main__":
  creds = get_gmail_auth()
  while True:
    get_first_unread_email_subject(creds)
    time.sleep(5)