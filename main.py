import logging
from data.credentials import telegram_token
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from selenium_scripts import get_session_id_and_date, book_session
from tinydb import TinyDB
from scheduler import Scheduler
from telegram_funcs import book
from variables import TINY_DB_PATH

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_token).build()
    scheduler = Scheduler(
        jobs_table=TinyDB(TINY_DB_PATH).table('jobs'),
        job_queue=application.job_queue
    )
    application.scheduler = scheduler
    start_handler = CommandHandler('book', book)
    application.add_handler(start_handler)
    application.run_polling()





# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)s %(name)s: %(message)s"
# )
# level = os.getenv("LOG_LEVEL", "INFO").upper()
# logging.basicConfig(
#     level=level,
#     format="%(asctime)s %(levelname)s %(name)s: %(message)s",
#     handlers=[logging.StreamHandler(sys.stdout)],
#     force=True,
# )
# # keep noisy deps quiet even on DEBUG
# logging.getLogger("selenium").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logger = logging.getLogger(__name__)


# class Process:
#     def __init__(self, db):
#         self.db = db
#         self.scheduler = Scheduler(db.table('jobs'))
    
#     def main(self):
#         self.scheduler.run_jobs_due()
#         thread = get_unread_email_thread()
#         if thread is not None:
#             self.handle_email(thread)
    
#     def handle_email(self, thread: Thread):   
#         try:
#             session_id, start_time = get_session_id_and_date(thread.subject)
#             booking_time = start_time - timedelta(days=3)
#             if booking_time < datetime.now():
#                 book_session(session_id=session_id, booking_time=booking_time.timestamp())
#             else:
#                 schedule_time = booking_time - timedelta(seconds=20)
#                 job = Job(JobEnum.BookSession, schedule_time, session_id, {**thread.to_dict(), "booking_time": booking_time.timestamp()})
#                 self.scheduler.schedule_job(job)
#                 send_reply_to_thread(f"Session planned to be booked at {schedule_time}", thread)

#         except ValueError as e:
#             logger.ERROR(f"Failed to handle email: {e}")
#             send_reply_to_thread(f"Failure: {e}", thread)
#             pass

# if __name__ == "__main__":
#     db = TinyDB(TINY_DB_PATH)
#     process = Process(db=db)
#     while True:
#         process.main()
#         time.sleep(5)
                
