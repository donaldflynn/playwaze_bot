from datetime import datetime
from gmail import get_unread_email_thread, Thread, send_reply_to_thread
from selenium_scripts import fetch_session_start_time, book_session
import time
from datetime import datetime, timedelta
from scheduler import Scheduler, Job, JobEnum

class Process:
    def __init__(self, db_path):
        self.scheduler = Scheduler(db_path)
    
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
                book_session(session_string=thread.subject)
            else:
                job = Job(JobEnum.BookSession, booking_time, thread.to_dict())
                self.scheduler.schedule_job(job)
                send_reply_to_thread(f"Session planned to be booked at {booking_time}", thread)

        except ValueError as e:
            print(f"Failed to handle email: {e}")
            send_reply_to_thread(f"Failure: {e}", thread)
            pass

if __name__ == "__main__":
    process = Process(db_path='tinydb.json')
    while True:
        process.main()
        time.sleep(5)
                
