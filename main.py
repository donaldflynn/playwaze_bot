from datetime import datetime
from gmail import get_unread_email_thread, Thread, send_reply_to_thread
from selenium_scripts import fetch_session_start_time, book_session
import time
from datetime import datetime, timedelta
from scheduler import Scheduler, Job, JobEnum
from credentials_manager import CredentialsManager
from tinydb import TinyDB
from variables import TINY_DB_PATH

class Process:
    def __init__(self, db):
        self.db = db
        self.credentials_manager = CredentialsManager(db.table('creds'))
        self.scheduler = Scheduler(db.table('jobs'))
    
    def main(self):
        self.scheduler.run_jobs_due()
        thread = get_unread_email_thread()
        if thread is not None:
            self.handle_email(thread)
    
    def handle_email(self, thread: Thread):
        updated = self.credentials_manager.perform_potential_password_update(
            thread.external_address,
            thread.initial_body
        )
        if updated:
            send_reply_to_thread("Password Updated", thread)
        try:
            username, password = self.credentials_manager.get_credentials_from_email(thread.external_address)
            start_time = fetch_session_start_time(thread.subject, username, password)
            booking_time = start_time - timedelta(days=3)
            if booking_time < datetime.now():
                book_session(thread.subject, username, password)
            else:
                job = Job(
                    job_enum=JobEnum.BookSession,
                    time=booking_time, 
                    priority=self.credentials_manager.get_priority_from_email(thread.external_address),
                    kwargs=thread.to_dict()
                )
                self.scheduler.schedule_job(job)
                send_reply_to_thread(f"Session planned to be booked at {booking_time}", thread)

        except ValueError as e:
            print(f"Failed to handle email: {e}")
            send_reply_to_thread(f"Failure: {e}", thread)
            pass

if __name__ == "__main__":
    db = TinyDB(TINY_DB_PATH)
    process = Process(db=db)
    while True:
        process.main()
        time.sleep(5)
                
