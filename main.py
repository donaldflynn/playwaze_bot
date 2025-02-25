from datetime import datetime
from gmail import get_unread_email_thread, Thread, send_reply_to_thread
from selenium_scripts import fetch_session_start_time, book_session
import time
from datetime import datetime, timedelta
from scheduler import Scheduler, Job, JobEnum
from tinydb import TinyDB
from variables import TINY_DB_PATH

class Process:
    def __init__(self, db):
        self.db = db
        self.scheduler = Scheduler(db.table('jobs'))
    
    def main(self):
        self.scheduler.run_jobs_due()
        thread = get_unread_email_thread()
        if thread is not None:
            self.handle_email(thread)
    
    def handle_email(self, thread: Thread):   
        try:
            start_time = fetch_session_start_time(thread.subject)
            booking_time = start_time - timedelta(days=3)
            if booking_time < datetime.now():
                book_session(session_string=thread.subject, booking_time=booking_time.timestamp())
            else:
                schedule_time = booking_time - timedelta(seconds=30)
                job = Job(JobEnum.BookSession, schedule_time, {**thread.to_dict(), "booking_time": booking_time.timestamp()})
                self.scheduler.schedule_job(job)
                send_reply_to_thread(f"Session planned to be booked at {schedule_time}", thread)

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
                
